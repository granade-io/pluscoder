import asyncio
import re
from pathlib import Path
from typing import  List, Literal
from langgraph.graph import StateGraph
from langgraph.prebuilt import ToolNode
from pluscoder.exceptions import AgentException
from pluscoder.io_utils import io
from pluscoder.logs import file_callback
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableMap, Runnable
from pluscoder.fs import apply_block_update, get_formatted_files_content
from pluscoder.message_utils import get_message_content_str
from pluscoder.repo import Repository
from pluscoder.config import config
from pluscoder.agents.event.config import event_emitter
from pluscoder.type import AgentState
from langchain_community.callbacks.manager import get_openai_callback

def parse_block(text):
    pattern = r'`([^`\n]+):?`\n{1,2}^```(\w*)\n(.*?)^```'
    matches = re.findall(pattern, text, re.DOTALL | re.MULTILINE)
    return [{'file_path': m[0], 'language': m[1], 'content': m[2].strip()} for m in matches]

def parse_mentioned_files(text):
    # Extract filenames from the text within `` blocks
    mentioned_files = re.findall(r'`([^`\n]+\.\w+)`', text)
    
    # Remove duplicates
    mentioned_files = list(set(mentioned_files))
    
    return mentioned_files

class Agent:
    
    state_schema = AgentState
    
    def __init__(self, llm, system_message: str, name: str, tools=[], extraction_tools=[], default_context_files: List[str] = []):
        self.name = name
        self.llm = llm
        self.system_message = system_message
        self.tools = tools
        self.extraction_tools = extraction_tools
        self.default_context_files = default_context_files
        self.graph = self.get_graph()
        self.max_deflections = 3
        self.current_deflection = 0
        self.repo = Repository(io=io)
        self.state = None
        
    def get_context_files(self, state):
        state.get("context_files") or []
        # files = [*self.default_context_files, *state_files]
        files = [*self.default_context_files]
        
        # remove duplicates
        files = list(set(files))
        return files
        
    def get_context_files_panel(self, files):
        if files:
            files_context = f"{" ".join(files[0:5])}{f' (+{len(files) - 5} files)' if len(files) > 5 else ''}"
        else:
            files_context = "<No files available>"
        return f"> Files context: {files_context}"
    
    def get_files_context_prompt(self, state):
        
        return f"""
Here are repository files content you already have access to: \n\n{{files_content}}

Here are all repositoy files you don't have access yet: \n\n{self.repo.get_tracked_files()}
"""

    def get_system_message(self, state: AgentState):
        return self.system_message
    
    def build_assistant_prompt(self, state: AgentState, deflection_messages: list):
        # last_message = state["messages"][-1]
        # check if last message is from a tool
        # if last_message.type == "tool":
        #     user_message_list = []
        #     place_holder_messages = state["messages"]
        # else:
        #     user_message_list = [state["messages"][-1]]
        #     place_holder_messages = state["messages"][:-1]
        
        context_files = self.get_context_files(state)
        files_content = get_formatted_files_content(context_files)
        assistant_prompt = RunnableMap({
            "messages": lambda x: state["messages"] + deflection_messages,
            "files_content": lambda x: files_content
            }) | ChatPromptTemplate.from_messages([
                ("system", self.get_system_message(state)),
                # Context files
                ("user", self.get_files_context_prompt(state)),
                AIMessage(content="ok"),
                ("placeholder", "{messages}"),
            ]# + user_message_list
        )
        return assistant_prompt
    
    
    def get_tool_choice(self, state: AgentState) -> str:
        """Chooses a the tool to use when calling the llm"""
        return "auto"
    
    def _invoke_llm_chain(self, state: AgentState, deflection_messages: List[str] = []):

        assistant_prompt = self.build_assistant_prompt(state, deflection_messages=deflection_messages)
        chain: Runnable = assistant_prompt | self.llm.bind_tools(self.tools + self.extraction_tools, tool_choice=self.get_tool_choice(state)) 
        response = chain.invoke({
            "messages": state["messages"], 
            "deflection_messages": deflection_messages}, {"callbacks": [file_callback]})

            
        return response
    
    def call_agent(self, state):
        """When entering this agent graph, this function is the first node to be called"""
        
        # last_message = state["messages"][-1]
        # io.error_console.print(f"Received message: {last_message.content}")
        
        self.get_context_files(state)
        # io.event(self.get_context_files_panel(context_files))
        
        interaction_msgs = []
        state_updates = {}
        
        with get_openai_callback() as cb:
            while True:
                try:
                    llm_response = self._invoke_llm_chain(state, interaction_msgs)
                    interaction_msgs.append(llm_response)
                    state_updates = self.process_agent_response(state, llm_response)
                    break
                except AgentException as e:
                    io.console.log(f"Error: {str(e)}")
                    if self.current_deflection < self.max_deflections:
                        self.current_deflection += 1
                        interaction_msgs.append(HumanMessage(content=f"An error ocurrred: {str(e)}"))
                    else:
                        break
                except Exception as e:
                    io.console.log(f"State that causes raise: {state}")
                    raise e

        new_state = {"messages": interaction_msgs, 
                     "token_usage": {
                        "total_tokens": cb.total_tokens,
                        "prompt_tokens": cb.prompt_tokens,
                        "completion_tokens": cb.completion_tokens,
                        "total_cost": cb.total_cost
                    },
                     **state_updates
                     }
        return new_state
    
    def agent_router(self, state: AgentState) -> Literal["tools", "__end__"]:
        """Edge to chose next node after agent was executed"""
        # Ends agent if max deflections reached
        if self.current_deflection >= self.max_deflections:
            io.console.log("Maximum deflections reached. Stopping.", style="bold dark_goldenrod")
            return "__end__"
        
        messages = state["messages"]
        last_message = messages[-1]
        
        if last_message.tool_calls:            
            return "tools"
        
        return "__end__"

    def parse_tool_node(self, state: AgentState):
        messages = state["messages"]
        last_message = messages[-2]  # Last message that contains ToolMessage with executed tool data. We need to extract tool args from AIMessage at index -2
        tool_data = {}
        
        for tool_call in last_message.tool_calls:
            if tool_call['name'] in [tool.name for tool in self.extraction_tools]:
                tool_data[tool_call['name']] = tool_call["args"]
        
        return {**state, "tool_data": tool_data}
    
    def parse_tools_router(self, state: AgentState) -> Literal["__end__", "agent"]:
        """Edge to decide where to go after all tools data was extracted"""
        
        last_message = state["messages"][-1]
        
        # check if called tool were extraction tools
        if last_message.type == "tool" and last_message.name in [tool.name for tool in self.extraction_tools]:
            # Extractions tools dosn't need to go back to agent to review them. 
            return "__end__"
        
        # If a normal tool was used, go back to agent to review its output and generate a new response.
        return "agent"
        
        
    def get_graph(self):
        tool_node = ToolNode(self.tools)
        
        workflow = StateGraph(self.state_schema)
        
        workflow.add_node("agent", self.call_agent)
        workflow.add_node("tools", tool_node)
        workflow.add_node("parse_tools", self.parse_tool_node)
        
        workflow.add_conditional_edges("agent", self.agent_router)
        workflow.add_edge("tools", "parse_tools")
        workflow.add_conditional_edges("parse_tools", self.parse_tools_router)
        
        workflow.set_entry_point("agent")
        
        return workflow.compile()
        
    async def graph_node(self, state):
        """Node for handling interactions with the user and other nodes. Called every time a new message is received."""
        state_updates = {**state}
        
        # Restart deflection counter
        self.current_deflection = 0
        
        if config.streaming:
            
            io.start_stream()
            async for event in self.graph.astream_events(state_updates, version="v1"):
                kind = event["event"]
                if kind == "on_chat_model_stream":
                    content = event["data"]["chunk"].content
                    if content:
                        if type(content) is str:
                            io.stream(content)
                        elif type(content) is list:
                            for entry in content:
                                if "text" in entry:
                                    # io.console.print(entry["text"], style="bright_green", end="")
                                    io.stream(entry["text"])
                elif kind == "on_tool_start":
                    io.console.print(f"> Tool calling: {event['data'].get('input')}", style="blue")
                elif kind == "on_tool_end":
                    pass
                    # io.console.print(Text(f"Tool output: {event['data'].get('output')}", style="italic"))
                elif kind == "on_chain_end" and event["name"] == "LangGraph":
                    # io.console.print("inner on_chain_end", event)
                    state_updates = {**state_updates, **event["data"]["output"]["agent"]}
            io.stop_stream()
        else:
            state_updates = self.graph.invoke(state_updates, {"callbacks": [file_callback]})
            # get last message
            last_message = state_updates["messages"][-1]
            
            io.console.print(get_message_content_str(last_message))
            
        io.console.print("")
        print("state after agent response:", state_updates)
        return state_updates
    
    def process_agent_response(self, state, response: AIMessage):
        content_text = get_message_content_str(response)
        
        found_blocks = parse_block(content_text)
        mentioned_files = parse_mentioned_files(content_text)
        
        # Todo: deprecated at the moment. File mentions doesn't have an specific use right now
        # if mentioned_files:
        #     io.event(f"Mentioned files: {', '.join(mentioned_files)}")
            
        self.process_blocks(found_blocks)
        
        # handle file mentions
        context_files = self.get_context_files(state)
        
        for file_path in mentioned_files:
            
            # ignore files that are already in the context
            if file_path in context_files:
                continue
            
            path = Path(file_path)
            if not path.is_file():
                # io.console.print(Text(f"File not found: {path.name}"))
                continue
            
            context_files = [*context_files, file_path]
        return {"context_files": context_files}
            
        
    def process_blocks(self, file_blocks):
        # Process the blocks found in the response to replace/create files in the project
        updated_files = []
        error_messages = []
        for block in file_blocks:
            file_path = block["file_path"]
            content = block["content"]
            block["language"]
            
            if file_path.startswith("/"):
                file_path = file_path[1:]
            
            # Apply the block update to the file
            error_msg = apply_block_update(file_path, content)
            if not error_msg:
                updated_files.append(file_path)
            else:
                error_messages.append(error_msg)
        
        if updated_files:
            asyncio.run(event_emitter.emit("files_updated", updated_files=updated_files))
        if error_messages:
            raise AgentException("Some files couldn't be updated: \n" + "\n".join(error_messages))


import asyncio
import re
from time import sleep
from typing import List, Literal

from langchain_community.callbacks.manager import get_openai_callback
from langchain_core.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable, RunnableMap
from langgraph.graph import StateGraph
from langgraph.prebuilt import ToolNode

from pluscoder.agents.event.config import event_emitter
from pluscoder.agents.prompts import (
    REMINDER_PREFILL_FILE_OPERATIONS_PROMPT,
    REMINDER_PREFILL_PROMP,
)
from pluscoder.config import config
from pluscoder.exceptions import AgentException
from pluscoder.fs import apply_block_update, get_formatted_files_content
from pluscoder.io_utils import io
from pluscoder.logs import file_callback
from pluscoder.message_utils import HumanMessage, get_message_content_str
from pluscoder.repo import Repository
from pluscoder.type import AgentState


def parse_block(text):
    pattern = r"`([^`\n]+):?`\n{1,2}^<source>\n(>>> FIND.*?===.*?<<< REPLACE|.*?)\n^<\/source>$"
    matches = re.findall(pattern, text, re.DOTALL | re.MULTILINE)
    return [{"file_path": m[0], "content": m[1].strip()} for m in matches]


def parse_mentioned_files(text):
    # Extract filenames from the text within `` blocks
    mentioned_files = re.findall(r"`([^`\n]+\.\w+)`", text)

    # Remove duplicates
    mentioned_files = list(set(mentioned_files))

    return mentioned_files


class Agent:
    state_schema = AgentState

    def __init__(
        self,
        llm,
        system_message: str,
        name: str,
        tools=[],
        extraction_tools=[],
        default_context_files: List[str] = [],
    ):
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
        state_files = state.get("context_files") or []
        files = [*self.default_context_files, *state_files]
        # files = [*self.default_context_files]

        # remove duplicates
        files = list(set(files))
        return files

    def get_context_files_panel(self, files):
        if files:
            files_context = f"{" ".join(files[0:5])}{f' (+{len(files) - 5} files)' if len(files) > 5 else ''}"
        else:
            files_context = "<No files available>"
        return f"> Files context: {files_context}"

    def get_files_not_in_context(self, state):
        context_files = set(self.get_context_files(state))
        all_tracked_files = set(self.repo.get_tracked_files())
        return sorted(all_tracked_files - context_files)

    def get_files_context_prompt(self, state):
        files_not_in_context = self.get_files_not_in_context(state)

        prompt = f"""
Here is the latest content of those repository files that you already have access to read/edit: \n\n{{files_content}}

Here are all repository files you don't have access yet: \n\n{files_not_in_context}
"""

        if config.use_repomap:
            prompt += "\n\nHere is the repository map summary so you can handle request better:\n\n{repomap}\n"

        return prompt

    def get_repomap(self):
        return self.repo.generate_repomap()

    def get_system_message(self, state: AgentState):
        return self.system_message

    def get_reminder_prefill(self, state: AgentState) -> str:
        return REMINDER_PREFILL_PROMP + REMINDER_PREFILL_FILE_OPERATIONS_PROMPT

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
        assistant_prompt = RunnableMap(
            {
                "messages": lambda x: state["messages"] + deflection_messages,
                "files_content": lambda x: files_content,
                "repomap": lambda x: self.get_repomap() if config.use_repomap else "",
            }
        ) | ChatPromptTemplate.from_messages(
            [
                ("system", self.get_system_message(state)),
                # Context files
                ("user", self.get_files_context_prompt(state)),
                AIMessage(content="ok"),
                ("placeholder", "{messages}"),
            ]  # + user_message_list
        )
        return assistant_prompt

    def get_tool_choice(self, state: AgentState) -> str:
        """Chooses a the tool to use when calling the llm"""
        return "auto"

    def _invoke_llm_chain(self, state: AgentState, deflection_messages: List[str] = []):
        assistant_prompt = self.build_assistant_prompt(
            state, deflection_messages=deflection_messages
        )
        chain: Runnable = assistant_prompt | self.llm.bind_tools(
            self.tools + self.extraction_tools, tool_choice=self.get_tool_choice(state)
        )
        response = chain.invoke(
            {"messages": state["messages"], "deflection_messages": deflection_messages},
            {"callbacks": [file_callback]},
        )

        return response

    def call_agent(self, state):
        """When entering this agent graph, this function is the first node to be called"""

        self.get_context_files(state)
        # io.event(self.get_context_files_panel(context_files))

        interaction_msgs = []
        post_process_state = {}

        with get_openai_callback() as cb:
            while self.current_deflection <= self.max_deflections:
                try:
                    llm_response = self._invoke_llm_chain(state, interaction_msgs)
                    interaction_msgs.append(llm_response)
                    post_process_state = self.process_agent_response(
                        state, llm_response
                    )
                    break
                except AgentException as e:
                    # io.console.print(f"Error: {e!s}")
                    io.console.print(
                        "::re-thinking due an issue:: ", style="bold dark_goldenrod"
                    )
                    if self.current_deflection <= self.max_deflections:
                        self.current_deflection += 1
                        interaction_msgs.append(
                            HumanMessage(content=f"An error ocurrred: {e!s}")
                        )
                except Exception as e:
                    # Handles unknown exceptions, maybe caused by llm api or wrong state
                    io.console.log(f"An error occurred: {e!s}", style="bold red")
                    io.log_to_debug_file("########### CALL AGENT ERROR ###########")
                    io.log_to_debug_file(f"Error: {e!s}")
                    io.log_to_debug_file("State:")
                    io.log_to_debug_file(message=str(state))
                    io.log_to_debug_file("Deflection messages:")
                    io.log_to_debug_file(message=str(interaction_msgs))
                    sleep(1)  # Wait a bit, some api calls need time to recover
                    interaction_msgs.append(
                        HumanMessage(
                            content="An error ocurrred. Please try exactly the same again"
                        )
                    )
                    if self.current_deflection <= self.max_deflections:
                        self.current_deflection += 1

        new_state = {
            "messages": interaction_msgs,
            "token_usage": {
                "total_tokens": cb.total_tokens,
                "prompt_tokens": cb.prompt_tokens,
                "completion_tokens": cb.completion_tokens,
                "total_cost": cb.total_cost,
            },
            **post_process_state,
        }
        return new_state

    def agent_router(self, state: AgentState) -> Literal["tools", "__end__"]:
        """Edge to chose next node after agent was executed"""
        # Ends agent if max deflections reached
        if self.current_deflection > self.max_deflections:
            io.console.log(
                "Maximum deflections reached. Stopping.", style="bold dark_goldenrod"
            )
            return "__end__"

        messages = state["messages"]
        last_message = messages[-1]

        if last_message.tool_calls:
            return "tools"

        return "__end__"

    def parse_tool_node(self, state: AgentState):
        messages = state["messages"]
        last_message = messages[
            -2
        ]  # Last message that contains ToolMessage with executed tool data. We need to extract tool args from AIMessage at index -2
        tool_data = {}
        loaded_files = []

        for tool_call in last_message.tool_calls:
            # Extract data if extraction tool was used
            if tool_call["name"] in [tool.name for tool in self.extraction_tools]:
                tool_data[tool_call["name"]] = tool_call["args"]

            # Extract files if read_files were used
            # This is a patch because tools can't read/edit agent state or call agent methods
            # DEPRECATED: files body are inyected by the tool because performance decreases significantly using this method
            # if tool_call['name'] in ["read_files"]:
            #     loaded_files = tool_call["args"].get("file_paths", [])
            #     io.event(f"> The latest version of these files were added to the chat: {', '.join(loaded_files)}")

        return {
            **state,
            "tool_data": tool_data,
            "context_files": state["context_files"] + loaded_files,
        }

    def parse_tools_router(self, state: AgentState) -> Literal["__end__", "agent"]:
        """Edge to decide where to go after all tools data was extracted"""

        last_message = state["messages"][-1]

        # check if called tool were extraction tools
        if last_message.type == "tool" and last_message.name in [
            tool.name for tool in self.extraction_tools
        ]:
            # Extractions tools dosn't need to go back to agent to review them.
            return "__end__"

        # If a normal tool was used, go back to agent to review its output and generate a new response.
        return "agent"

    def get_graph(self):
        tool_node = ToolNode(self.tools + self.extraction_tools)

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
                elif kind == "on_chat_model_end":
                    io.flush()
                    # io.console.print("on_chat_model_end")
                    io.end_block()
                    # io.console.print("\n")
                elif kind == "on_llm_end":
                    pass
                    # io.console.print("on_llm_end")
                    # io.console.print("\n")
                elif kind == "on_tool_start":
                    # io.console.print("on_tool_start")
                    io.end_block()
                    # io.console.print(f"> Tool calling: {event['data'].get('input')}", style="blue")
                    pass
                elif kind == "on_tool_end":
                    pass
                    # io.console.print(Text(f"Tool output: {event['data'].get('output')}", style="italic"))
                elif kind == "on_chain_end" and event["name"] == "LangGraph":
                    # io.console.print("on_chain_end")
                    if "agent" in event["data"]["output"]:
                        state_updates = {
                            **state_updates,
                            **event["data"]["output"]["agent"],
                        }
                    else:
                        state_updates = {**state_updates, **event["data"]["output"]}
            io.stop_stream()
        else:
            state_updates = self.graph.invoke(
                state_updates, {"callbacks": [file_callback]}
            )
            # get last message
            last_message = state_updates["messages"][-1]

            io.console.print(get_message_content_str(last_message))

        io.console.print("")
        return state_updates

    def process_agent_response(self, state, response: AIMessage):
        if config.read_only:
            # Ignore file editions when readonly
            return {}

        content_text = get_message_content_str(response)

        found_blocks = parse_block(content_text)
        self.process_blocks(found_blocks)

        return {}

    def process_blocks(self, file_blocks):
        # Process the blocks found in the response to replace/create files in the project
        updated_files = []
        error_messages = []
        for block in file_blocks:
            file_path = block["file_path"]
            content = block["content"]

            if file_path.startswith("/"):
                file_path = file_path[1:]

            # Apply the block update to the file
            error_msg = apply_block_update(file_path, content)
            if not error_msg:
                updated_files.append(file_path)
            else:
                error_messages.append(error_msg)

        if error_messages:
            raise AgentException(
                "Some files couldn't be updated:\n" + "\n".join(error_messages)
            )

        if updated_files:
            # Run tests and linting if enabled
            lint_error = self.repo.run_lint()
            test_error = self.repo.run_test()

            if lint_error or test_error:
                error_message = "Errors found:\n"
                if lint_error:
                    error_message += f"Linting: {lint_error}\n"
                if test_error:
                    error_message += f"Tests: {test_error}\n"
                raise AgentException(error_message)

        if updated_files:
            asyncio.run(
                event_emitter.emit("files_updated", updated_files=updated_files)
            )

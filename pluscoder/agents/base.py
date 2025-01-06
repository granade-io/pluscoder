import asyncio
import re
import traceback
from time import sleep
from typing import Callable
from typing import List
from typing import Literal
from typing import cast

from langchain_community.callbacks.manager import get_openai_callback
from langchain_core.messages import AIMessage
from langchain_core.messages import BaseMessageChunk
from langchain_core.messages import convert_to_messages
from langchain_core.messages import message_chunk_to_message
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from langchain_core.runnables import RunnableMap
from langgraph.graph import StateGraph
from langgraph.prebuilt import ToolNode

from pluscoder import tools
from pluscoder.agents.event.config import event_emitter
from pluscoder.agents.prompts import REMINDER_PREFILL_FILE_OPERATIONS_PROMPT
from pluscoder.agents.prompts import REMINDER_PREFILL_PROMPT
from pluscoder.agents.prompts import build_system_prompt
from pluscoder.agents.stream_parser import XMLStreamParser
from pluscoder.config import config
from pluscoder.exceptions import AgentException
from pluscoder.exceptions import WorkflowException
from pluscoder.fs import get_formatted_files_content
from pluscoder.io_utils import io
from pluscoder.logs import file_callback
from pluscoder.message_utils import HumanMessage
from pluscoder.message_utils import build_file_editions_tool_message
from pluscoder.message_utils import filter_messages
from pluscoder.message_utils import mask_stale_file_messages
from pluscoder.message_utils import tag_messages
from pluscoder.model import get_llm
from pluscoder.model import get_model_validation_message
from pluscoder.repo import Repository
from pluscoder.type import AgentConfig
from pluscoder.type import OrchestrationState


def parse_block(text):
    # Pre-process the text to merge multiple <source> blocks for the same file
    merged_text = re.sub(
        r"^<\/source>$(?!\n*`[^\s]+`\n*<source>)[^(?>$<)]*<source>",
        "",
        text,
        flags=re.DOTALL | re.MULTILINE,
    )

    pattern = r"`([^`\n]+):?`\n{1,2}^<source>\n(>>> FIND.*?===.*?<<< REPLACE|.*?)\n^<\/source>$"
    matches = re.findall(pattern, merged_text, re.DOTALL | re.MULTILINE)
    return [{"file_path": m[0], "content": m[1].strip()} for m in matches]


def parse_mentioned_files(text):
    # Extract filenames from the text within `` blocks
    mentioned_files = re.findall(r"`([^`\n]+\.\w+)`", text)

    # Remove duplicates
    return list(set(mentioned_files))


class Agent:
    state_schema = OrchestrationState

    def __init__(
        self, agent_config: AgentConfig, stream_parser: XMLStreamParser, extraction_tools: list[Callable] = []
    ):
        self.id = agent_config.id
        self.name = agent_config.name
        self.system_message = agent_config.prompt
        self.tools = [getattr(tools, tool, None) for tool in agent_config.tools if getattr(tools, tool, None)]
        self.provider = agent_config.provider
        self.model = agent_config.model
        self.extraction_tools = extraction_tools
        self.default_context_files = agent_config.default_context_files
        self.graph = self.get_graph()
        self.max_deflections = 3
        self.current_deflection = 0
        self.repo = Repository(io=io)
        self.state = None
        self.disable_reminder = False
        self.read_only = agent_config.read_only
        self.description = agent_config.description
        self.reminder = agent_config.reminder
        self.repository_interaction = agent_config.repository_interaction
        self.stream_parser = stream_parser
        self.updated_files = set()

    def get_context_files(self, state):
        state_files = state.get("context_files") or []
        files = [*self.default_context_files, *state_files]

        # remove duplicates
        return list(set(files))

    def get_context_files_panel(self, files):
        if files:
            files_context = " ".join(files[0:5]) + (f" (+{len(files) - 5} files)" if len(files) > 5 else "")
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

    def get_system_message(self, state: OrchestrationState):
        return build_system_prompt(
            self.system_message,
            can_read_files=self.repository_interaction,
            can_edit_files=not self.read_only and not config.read_only and self.repository_interaction,
        )

    def get_reminder_prefill(self, state: OrchestrationState) -> str:
        prompt = REMINDER_PREFILL_PROMPT
        if not config.read_only and not self.read_only and self.repository_interaction:
            prompt += REMINDER_PREFILL_FILE_OPERATIONS_PROMPT
        if self.reminder:
            prompt += self.reminder
        return prompt

    def get_prompt_template_messages(self, state: OrchestrationState):
        templates_messages = [("system", self.get_system_message(state))]

        if self.repository_interaction:
            # Context files
            templates_messages += [
                ("user", self.get_files_context_prompt(state)),
                AIMessage(content="ok", name=self.id),
            ]
        return templates_messages + [
            ("placeholder", "{messages}"),
        ]

    def build_assistant_prompt(self, state: OrchestrationState, deflection_messages: list):
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

        # reminders
        reminder_messages = []
        if not self.disable_reminder:
            reminder_messages.append(HumanMessage(content=self.get_reminder_prefill(state), tags=[self.id]))

        # Get stale content version of messages
        all_messages = state["messages"] + deflection_messages + reminder_messages
        processed_messages = mask_stale_file_messages(all_messages)

        # assistant_prompt
        return RunnableMap(
            {
                "messages": lambda x: processed_messages,
                "files_content": lambda x: files_content,
                "repomap": lambda x: self.get_repomap() if config.use_repomap else "",
            }
        ) | ChatPromptTemplate.from_messages(self.get_prompt_template_messages(state))

    def get_tool_choice(self, state: OrchestrationState) -> str:
        """Chooses a the tool to use when calling the llm"""
        return "auto"

    def get_agent_model(self):
        llm = get_llm(self.provider, self.model)
        if not llm:
            raise WorkflowException(get_model_validation_message(self.provider))
        return llm

    def _stream_events(self, chain, state: OrchestrationState, deflection_messages: List[str]):
        self.stream_parser.start_stream()
        first = True
        gathered = None
        try:
            for chunk in chain.stream(
                {
                    "messages": state["messages"],
                    "deflection_messages": deflection_messages,
                },
                {"callbacks": [file_callback]},
            ):
                if first:
                    self.stream_parser.stream(chunk.content)
                    gathered = chunk
                    first = False
                else:
                    self.stream_parser.stream(chunk.content)
                    gathered = gathered + chunk
        finally:
            try:
                self.stream_parser.close_stream()
            except Exception as e:
                print(f"Error in stream events: {e}")

        # coerce to message
        return message_chunk_to_message(cast(BaseMessageChunk, convert_to_messages([gathered])[0]))  # type: ignore

    def _invoke_llm_chain(self, state: OrchestrationState, deflection_messages: List[str] = []):
        assistant_prompt = self.build_assistant_prompt(state, deflection_messages=deflection_messages)
        llm = self.get_agent_model()

        chain: Runnable = assistant_prompt | llm.bind_tools(
            self.tools + self.extraction_tools, tool_choice=self.get_tool_choice(state)
        )

        if config.streaming:
            return self._stream_events(chain, state, deflection_messages)

        # response
        return chain.invoke(
            {
                "messages": state["messages"],
                "deflection_messages": deflection_messages,
            },
            {"callbacks": [file_callback]},
        )

    def call_agent(self, state):
        """When entering this agent graph, this function is the first node to be called"""

        self.get_context_files(state)
        self.disable_reminder = False
        # io.event(self.get_context_files_panel(context_files))

        interaction_msgs = []
        post_process_state = {}

        with get_openai_callback() as cb:
            backoff_time = 2  # Start with 3 seconds
            while self.current_deflection <= self.max_deflections:
                try:
                    llm_response = self._invoke_llm_chain(state, interaction_msgs)
                    llm_response.tags = [self.id]

                    interaction_msgs.append(llm_response)
                    post_process_state = self.process_agent_response(state, llm_response)
                    backoff_time = 2  # Reset backoff time on success
                    break
                except AgentException as e:
                    # Disable sysetem reminders when solving specific errors
                    self.disable_reminder = True

                    io.log_to_debug_file("## AgentException Deflection")
                    io.log_to_debug_file(e.message, indent=4)

                    # io.print(f"Error: {e!s}")
                    io.print("::re-thinking due an issue:: ", style="bold dark_goldenrod")
                    if self.current_deflection <= self.max_deflections:
                        self.current_deflection += 1
                        interaction_msgs.append(HumanMessage(content=f"An error ocurred: {e!s}", tags=[self.id]))
                        sleep(backoff_time)
                        backoff_time *= 2  # Exponential backoff
                except WorkflowException:
                    raise
                except Exception as e:
                    # Handles unknown exceptions, maybe caused by llm api or wrong state
                    io.print(f"An error ocurred when calling model: {e!s}", style="bold red")
                    error_traceback = traceback.format_exc()
                    if config.debug:
                        io.console.log(f"Traceback:\n{error_traceback}", style="bold red")
                    io.log_to_debug_file(f"\n\nTraceback:\n{error_traceback}", indent=4)
                    io.log_to_debug_file("State:")
                    io.log_to_debug_file(message=str(state), indent=4)
                    io.log_to_debug_file("Deflection messages:")
                    io.log_to_debug_file(message=str(interaction_msgs), indent=4)
                    sleep(backoff_time)  # Wait a bit, some api calls need time to recover
                    interaction_msgs.append(
                        HumanMessage(content="An error occurred. Please try exactly the same again", tags=[self.id])
                    )
                    if self.current_deflection <= self.max_deflections:
                        self.current_deflection += 1
                        sleep(backoff_time)
                        backoff_time *= 2  # Exponential backoff

        # new_state
        return {
            "messages": interaction_msgs + post_process_state.get("messages", []),
            "token_usage": {
                "total_tokens": cb.total_tokens,
                "prompt_tokens": cb.prompt_tokens,
                "completion_tokens": cb.completion_tokens,
                "total_cost": cb.total_cost,
            },
        }

    def agent_router(self, state: OrchestrationState) -> Literal["tools", "__end__"]:
        """Edge to chose next node after agent was executed"""
        # Ends agent if max deflections reached
        if self.current_deflection > self.max_deflections:
            io.console.log("Maximum deflections reached. Stopping.", style="bold dark_goldenrod")
            return "__end__"

        messages = state["messages"]
        last_message = messages[-1]

        if last_message.tool_calls:
            return "tools"

        return "__end__"

    def parse_tool_node(self, state: OrchestrationState):
        messages = state["messages"]

        # Mark tool message for filtering
        messages = tag_messages(messages, tags=[self.id], exclude_tagged=True)

        last_message = filter_messages(messages, include_types=["ai"])[-1]
        # Last message that contains ToolMessage with executed tool data. We need to extract tool args from AIMessage at index -2
        tool_data = {}

        for tool_call in last_message.tool_calls:
            # Extract data if extraction tool was used
            if tool_call["name"] in [tool.name for tool in self.extraction_tools]:
                tool_data[tool_call["name"]] = tool_call["args"]

        return {
            **state,
            "tool_data": tool_data,
            # "context_files": state["context_files"] + loaded_files,
        }

    def parse_tools_router(self, state: OrchestrationState) -> Literal["__end__", "agent"]:
        """Edge to decide where to go after all tools data was extracted"""

        last_message = state["messages"][-1]

        # check if called tool were extraction tools
        if last_message.type == "tool" and last_message.name in [tool.name for tool in self.extraction_tools]:
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

        # Restart deflection counter
        self.current_deflection = 0

        # Resets updated files of this call
        self.updated_files = set()

        state_updates = self.graph.invoke(state, {"callbacks": [file_callback]})

        io.print("")
        return {**state, **state_updates, "messages": state_updates["messages"]}

    def process_agent_response(self, state, response: AIMessage):
        # Ignore process until all tools are executed
        if response.tool_calls:
            return {}

        # Ignore process until all tools are executed
        if response.tool_calls:
            return {}

        # Updated files of the call
        call_updated_files = self.stream_parser.get_updated_files()
        self.updated_files.update(call_updated_files)

        error_messages = self.stream_parser.agent_errors

        # check if last message has tool calls to ignore lint/test when files were edited during tool call

        if error_messages:
            updated_files_msg = (
                f"You successfully updated these files: {', '.join(call_updated_files)}, but there are some issues.\n"
                if call_updated_files
                else ""
            )
            raise AgentException(
                "Some errors occurred when executing your actions:\n\n"
                + "\n".join(error_messages)
                + "\nPlease review all errors and solve the present issues if you can. Maybe you will need to read files again to understand what is missing or what happened."
                + updated_files_msg
            )

        if call_updated_files:
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

        # Updated files during entire agent execution
        file_editions_msgs = []
        if self.updated_files:
            try:
                if len(self.updated_files) > 1:
                    io.event(f"> These files were successfully updated: {', '.join(self.updated_files)}")
                # Try to get current event loop
                loop = asyncio.get_running_loop()
                # If exists, run in current loop
                loop.create_task(event_emitter.emit("files_updated", updated_files=self.updated_files))  # noqa: RUF006
            except RuntimeError:
                # If no loop exists, create new one
                asyncio.run(event_emitter.emit("files_updated", updated_files=self.updated_files))
            finally:
                file_editions_msgs = [build_file_editions_tool_message(list(self.updated_files), agent_id=self.id)]
                self.updated_files = set()

        # Add file editions tool message so agent can understand files was updated successfully
        return {"messages": file_editions_msgs}

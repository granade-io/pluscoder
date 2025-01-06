from operator import add
from typing import Annotated
from typing import Dict
from typing import List
from typing import Literal
from typing import Optional

from langchain_core.messages import AnyMessage
from langchain_core.messages import BaseMessage
from langgraph.graph import add_messages
from pydantic import BaseModel
from typing_extensions import TypedDict


class TokenUsage(TypedDict):
    total_tokens: int
    prompt_tokens: int
    completion_tokens: int
    total_cost: float

    @classmethod
    def default(cls):
        return {
            "total_tokens": 0,
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_cost": 0.0,
        }


class AgentState(TypedDict, total=False):
    # Token usage data
    token_usage: TokenUsage

    # Deprecated: Context for loaded files
    context_files: Annotated[List[str], add]

    # List of messages of this agent with the caller
    messages: Annotated[List[AnyMessage], add_messages]

    # List of messages of this agent with other agent (support only one agent at a time)
    agent_messages: List[AnyMessage]

    # static function with default AgentState values
    @classmethod
    def default(cls):
        return {
            "messages": [],
            "agent_messages": [],
            "tool_data": {},
            "status": "active",
        }


class AgentConfig(BaseModel):
    """AgentConfig model defines the behavior of an agent in a conversation or during an execution.

    Args:
        id (str): Unique identifier of the agent.
        name (str): Name of the agent. It should be human-readable. Its displayed in the interactive mode.
        description (str): Description of the agent. It should provide a brief overview of the agent's capabilities.
        prompt (str): System prompt fragment for specialization.

            Agents have complex system prompt for properly working on repositories; they have all details about its context, their capabilities and their expected role.
            We must only specify how do we want agents to behave in this repository context.

            We have a generic prompt for developer our agent, we would define other specialization instructions like:
            - Generating a plan before coding
            - Asking key questions before coding
            - Deeply review some guidelines when proposing a design or solution
            - Give the user instructions of how to test/try the given code after editions
            - Propose next steps after the code is done
            - Etc

            I.e: "Developer"

                *SPECIALIZATION INSTRUCTIONS*:
                Your role is to implement software development tasks based on detailed plans provided. You should write high-quality, maintainable code that adheres to the project's coding guidelines and integrates seamlessly with the existing codebase.

                Key Responsibilities:
                1. Review the overview, guidelines and repository files to determine which files to load to solve the user requirements.
                2. Review relevant existing code and project files to ensure proper integration.
                3. Adhere strictly to the project's coding guidelines and best practices when coding
                4. Ensure your implementation aligns with the overall project architecture and goals.

                Guidelines:
                - Always reuse project-specific coding standards and practices.
                - Follow the project's file structure and naming conventions.

                *IMPORTANT*:
                1. Always read the relevant project files and existing code before thinking a solution
                2. Ensure your code integrates smoothly with the existing codebase and doesn't break any functionality.
                3. If you encounter any ambiguities or potential issues with the task description, ask for clarification before proceeding.

        reminder (str): Reminder message to send to the agent at the end of each user message.

            Agents tends to forget their role or instructions while a conversation is happening, even if these are present in the system prompt.
            Use the reminder to keep the agent focused on its role and responsibilities.

            I.e: "Remember to review CODE_OF_CONDUCT.md file before proposing a solution"

        tools (List[str]): List of tools available for the agent.

            Agents have access to a pre-defined set of tools by default; move_files, read_files, read_file_from_url, query_repository.

            ```
            from pluscoder.tools import base_tools
            from pluscoder.type import AgentConfig
            from pluscoder.agents.core import DeveloperAgent

            # Override agent default tools
            tool_names = [tool.name for tool in tools.base_tools]
            developer_agent: AgentConfig = DeveloperAgent.to_agent_config(tools=tool_names)
            ```

            For custom tools, you can define a new tool and add it to the agent tools list, along with the default tools.
            Note that in this case tool list has a tool instances instead of tool names.

            ```
            from langchain_core.tools import tool
            from pluscoder.tools import base_tools
            from pluscoder.type import AgentConfig
            from pluscoder.agents.core import DeveloperAgent

            @tool
            def add(
                number_a: Annotated[int, "Number to be added."],
                number_b: Annotated[int, "Second number to be added."],
            ) -> Dict[str, bool]:
                "Add two numbers."
                return number_a + number_b

            # Override agent default tools
            my_tools = tools.base_tools + [add]
            developer_agent: AgentConfig = DeveloperAgent.to_agent_config(tools=my_tools)
            ```

        provider (str): Provider of the agent. Can be 'openai', 'anthropic', 'vertexai', 'google', 'aws_bedrock', 'litellm' or None.

            If none, provider will be inferred from available credentials.

        model (str): LLM model to use when running the agent.

        default_context_files (List[str]): List of default context files to load when the agent is initialized.

            Agents have access to a pre-defined set of context files by default; useful for adding key files to perform its tasks.

        read_only (bool): Flag to indicate if the agent is read-only. Read-only agents can't modify the repository.
        repository_interaction (bool): Flag to indicate if the agent have context of the repository. If False, the agent can't interact with the repository due to lack of context.
        is_custom (bool): Flag to indicate if the agent is a custom agent. Custom agents are created by the user and have custom behavior.
        suggestions (List[str]): List of input suggestions to provide to the user when the agent is selected during interactive mode.


    """

    id: str
    name: str
    description: str
    prompt: str
    reminder: Optional[str]
    tools: List[str]
    provider: Optional[str]
    model: str
    default_context_files: List[str]
    read_only: bool = False
    repository_interaction: bool = True
    is_custom: bool = False
    suggestions: Optional[List[str]] = None


OrchestrationState = TypedDict(
    "OrchestrationState",
    {
        "input": str,
        # id of the current conversation
        "chat_id": str,
        # Available agents
        "agents_configs": Dict[str, AgentConfig],
        # agent of the current conversation
        "chat_agent": AgentConfig,
        "max_iterations": int,
        "current_iterations": int,
        "accumulated_token_usage": TokenUsage,
        # Token usage data
        "token_usage": Optional[TokenUsage],
        # Data extracted using extraction tools
        "tool_data": dict,
        # Status of the agent in a conversation
        #   active: Agent is in a active state available for or having a conversation with the caller (no tasks assigned)
        #   delegating: Agent is communicating with another agent to complete and validate the active task.
        "status": Literal["active", "delegating", "summarizing"],
        "return_to_user": bool,
        # Tell is the workflow is being run from task list to avoid user interactions
        "is_task_list_workflow": bool,
        # Max times to additionally delegate same task to an agent to complete it properly
        "max_agent_deflections": int,
        # Current agent deflections count
        "current_agent_deflections": int,
        # List of messages of this agent with the caller
        "messages": Annotated[List[BaseMessage], add_messages],
    },
)


class AgentTask(BaseModel):
    objective: str
    details: str
    agent: Literal["developer"]
    is_finished: bool
    restrictions: str = ""
    outcome: str = ""


class AgentInstructions(BaseModel):
    general_objective: str
    resources: List[str]
    task_list: List[AgentTask]

    def get_task_count(self) -> int:
        return len(self.task_list)

    def get_completed_task_count(self) -> int:
        return sum(1 for task in self.task_list if task.is_finished)

    def get_current_task(self) -> AgentTask:
        return next((task for task in self.task_list if not task.is_finished), None)

    def to_markdown(self) -> str:
        markdown = f"# General Objective\n\n{self.general_objective}\n\n## Task List\n\n"
        for i, task in enumerate(self.task_list, 1):
            status = "✅" if task.is_finished else "⏳"
            markdown += f"{i}. {status} **{task.objective}** (Agent: {task.agent})\n"
            markdown += f"   - Details: {task.details}\n"
            if task.restrictions:
                markdown += f"   - Restrictions: {task.restrictions}\n"
            if task.outcome:
                markdown += f"   - Expected Outcome: {task.outcome}\n"
            markdown += "\n"
        markdown += f"**Resources**: {', '.join(self.resources)}"
        return markdown

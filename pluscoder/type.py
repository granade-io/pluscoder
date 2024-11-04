from operator import add
from typing import Annotated
from typing import List
from typing import Literal

from langchain_core.messages import AnyMessage
from langchain_core.pydantic_v1 import BaseModel
from langgraph.graph import add_messages
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


# TODO: This should be config independent
OrchestrationState = TypedDict(
    "OrchestrationState",
    {
        "max_iterations": int,
        "current_iterations": int,
        "accumulated_token_usage": TokenUsage,
        # Token usage data
        "token_usage": TokenUsage,
        # Data extracted using extraction tools
        "tool_data": dict,
        # Status of the agent in a conversation
        #   active: Agent is in a active state available for or having a conversation with the caller (no tasks assigned)
        #   delegating: Agent is communicating with another agent to complete and validate the active task.
        "status": Literal["active", "delegating", "summarizing"],
        "return_to_user": bool,
        "chat_agent": str,
        # Tell is the workflow is being run from task list to avoid user interactions
        "is_task_list_workflow": bool,
        # Max times to additionally delegate same task to an agent to complete it properly
        "max_agent_deflections": int,
        # Current agent deflections count
        "current_agent_deflections": int,
        # List of messages of this agent with the caller
        "messages": Annotated[List[AnyMessage], add_messages],
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

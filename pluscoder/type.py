from operator import add
from typing import Annotated, List, Literal
from langgraph.graph import add_messages
from typing_extensions import TypedDict
from langchain_core.pydantic_v1 import BaseModel
from langchain_core.messages import AnyMessage


class TokenUsage(TypedDict):
    total_tokens: int
    prompt_tokens: int
    completion_tokens: int
    total_cost: float
    
    @classmethod
    def default(cls):
        return {"total_tokens": 0, "prompt_tokens": 0, "completion_tokens": 0, "total_cost": 0.0}
    
class AgentState(TypedDict, total=False):
    # Token usage data
    token_usage: TokenUsage
    
    # Deprecated: Context for loaded files
    context_files: Annotated[List[str], add] = []
    
    # List of messages of this agent with the caller
    messages: Annotated[List[AnyMessage], add_messages]
    
    # List of messages of this agent with other agent (support only one agent at a time)
    agent_messages: List[AnyMessage]
    
    # Data extracted using extraction tools
    tool_data: dict
    
    # Status of the agent in a conversation
    #   active: Agent is in a active state available for or having a conversation with the caller (no tasks assigned)
    #   delegating: Agent is communicating with another agent to complete and validate the active task.
    status: Literal["active", "delegating", "summarizing"]
    
    # static function with default AgentState values
    @classmethod
    def default(cls):
        return {"messages": [], "agent_messages": [], "tool_data": {}, "status": "active"}

class OrchestrationState(AgentState, total=False):
    accumulated_token_usage: TokenUsage
    orchestrator_state: AgentState
    domain_stakeholder_state: AgentState
    planning_state: AgentState
    developer_state: AgentState
    domain_expert_state: AgentState
    return_to_user: bool
    chat_agent: str
    
    # Max times to additionally delegate same task to an agent to complete it properly
    max_agent_deflections: int = 2
    
    # Current agent deflections count
    current_agent_deflections: int = 0

class AgentTask(BaseModel):
    objective: str
    details: str
    agent: Literal["domain_stakeholder", "planning", "developer", "domain_expert"]
    is_finished: bool

class AgentInstructions(BaseModel):
    general_objective: str
    task_list: List[AgentTask]

    def get_task_count(self) -> int:
        return len(self.task_list)
    
    def get_completed_task_count(self) -> int:
        return sum(1 for task in self.task_list if task.is_finished)
    
    def get_current_task(self) -> AgentTask:
        return next((task for task in self.task_list if not task.is_finished), None)
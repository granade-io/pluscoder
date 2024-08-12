from langgraph.graph import END
from pluscoder import tools
from typing import Annotated, List, Literal
from pluscoder.agents.base import Agent, AgentState
from pluscoder.agents.prompts import combine_prompts, BASE_PROMPT, FILE_OPERATIONS_PROMPT
from pluscoder.io_utils import io
from rich.panel import Panel
from langchain_core.messages import HumanMessage

from pluscoder.type import AgentInstructions


class OrchestratorAgent(Agent):
    id = "orchestrator"
    mode: Annotated[Literal["orchestrate", "direct"],
                    "'Direct' mode means the OrchestratorAgent talks directly to the selected agent in 'direct mode'.\n" +
                    "'Orchestrate' mode means the OrchestratorAgent delegates tasks to the selected agent in 'orchestrate mode'."
                    ]
    current_agent: Annotated[str, "Agent to talk with when in 'direct mode"] = None
    agent_first_instruction: str = None
    
    orchestrator_prompt = """
*SPECIALIZATION INSTRUCTIONS*:
Your role is to understand user requirements to generate a proper list of task to solve those requirements with the help of specialized AI Agents.

Ask any questions to understand the user vision and goals deeply, including technical aspects & non-technical aspects.
Simple requirements requires less (or no) questions than complex ones. Choose key questions that will help you create a comprehensive list of tasks.

Do not propose a list of task until you understand the user requirements deeply through asking detailed questions. *Do not* ask more than 3 questions at once.

*Available Agents*:
- Domain Stakeholder Agent: For discussing project details, maintaining the project overview, roadmap, and brainstorming.
- Planning Agent: For creating detailed, actionable plans for software development tasks.
- Developer Agent: For implementing code to solve complex software development requirements.
- Domain Expert Agent: For validating tasks and providing feedback on alignment with project vision.

*Always* present the list of tasks in a structured, ordered format to the user *before* using a tool
To execute/delegate/complete tasks *use the delegation tool*.

*List task item structure*:

[] <task name>:
   Objective: <task objective>
   Details: <task details> if possible include file path to give more context. Of references to files edited by previous tasks.
   Agent: <agent name> Agent who is responsible for this task.

"""

    validation_system_message = f"""
    An user requested you a task, and you delegated it to an agent to solve it.
    Your work is to tell if a task/instruction solven by the agent was fully executed and if the expected outcome was achieved.
    
    *Instructions*:
    1. If the task/instruction was not fully executed, explain why it was not fully executed, what is missing. End the response with "Not fully executed."
    2. If the task/instruction was fully executed, explain how the agent achieved the expected outcome. End the response with "Fully executed."
    
    *Output Format*:
    Task: [Task Objective]
    Completed: [True/False]
    Feedback: [Feedback or response about task completeness]
    """
    
    summarizing_system_message = """
    Your role is to summarize the outputs of others agent to solve a request given by the user's task.
    The summary should be concise and clear.
    
    *Instructions*:
    1. Summarize all task solved in a message aimed for the user who requested the tasks.
    """

    def __init__(self, llm, tools=[tools.read_files], extraction_tools=[tools.delegate_tasks, tools.is_task_completed]):
        system_message = combine_prompts(BASE_PROMPT, self.orchestrator_prompt, FILE_OPERATIONS_PROMPT)
        super().__init__(llm, system_message, "Orchestrator Agent", tools=tools, extraction_tools=extraction_tools, default_context_files=["PROJECT_OVERVIEW.md"])
    
    def get_system_message(self, state: AgentState) -> str:
        # Default prompt
        if state["status"] == "active":
            return self.system_message
        
        # Default prompt
        if state["status"] == "summarizing":
            return self.summarizing_system_message
        
        # Validation prompt
        return self.validation_system_message
    
    
    def get_tool_choice(self, state: AgentState) -> str:
        """Chooses a the tool to use when calling the llm"""
        if state["status"] == "delegating":
            return tools.is_task_completed.name
        return "auto"
    
    
    def is_agent_response(self, state: AgentState) -> bool:
        """
        Verify if the last message in the state is from an agent.
        
        Args:
            state (AgentState): The current state containing messages.
        
        Returns:
            bool: True if the last message is from an agent, False otherwise.
        """
        if not state["messages"]:
            return False
        
        last_message = state["messages"][-1]
        # Assuming agent messages are not instances of HumanMessage
        return not isinstance(last_message, HumanMessage)

    def get_current_task(self, state: AgentState):
        """
        Get the first task that is not finished from the state.

        Args:
            state (AgentState): The current state containing tasks.

        Returns:
            Task: The first unfinished task, or None if all tasks are finished or no tasks exist.
        """
        if "tool_data" not in state \
            or not state["tool_data"] \
            or tools.delegate_tasks.name not in state["tool_data"] \
            or not state["tool_data"][tools.delegate_tasks.name] \
            or "task_list" not in state["tool_data"][tools.delegate_tasks.name]:
            return None

        task_list = state["tool_data"][tools.delegate_tasks.name]["task_list"]
        return next((task for task in task_list if not task.get('is_finished', False)), None)
    
    def get_task_list(self, state: AgentState) -> List[dict]:
        """
        Get the task list from the state.
        
        Args:
            state (AgentState): The current state containing tasks.
        
        Returns:
            List[dict]: The task list.
        """
        if "tool_data" not in state or not state["tool_data"] or tools.delegate_tasks.name not in state["tool_data"]:
            return []

        return state["tool_data"][tools.delegate_tasks.name]["task_list"]
    
    def remove_task_list_data(self, state: AgentState) -> AgentState:
        """Remove the task list data from the state."""
        return {**state, "tool_data": {**state["tool_data"], tools.delegate_tasks.name: None}}
    
    def get_agent_instructions(self, state: AgentState) -> AgentInstructions:
        return AgentInstructions(**state["tool_data"][tools.delegate_tasks.name])

    
    def get_task_list_objective(self, state: AgentState) -> str:
        return state["tool_data"][tools.delegate_tasks.name]["general_objective"]
    
    def validate_current_task_completed(self, state: AgentState) -> bool:
        """
        Check if the current task is completed based on the state last tool used.

        Args:
            state (AgentState): The current state containing task completion status.

        Returns:
            bool: True if the current task is completed, False otherwise.
        """
        if "tool_data" not in state or not state["tool_data"]:
            return False

        if tools.is_task_completed.name not in state["tool_data"]:
            return False

        return state["tool_data"][tools.is_task_completed.name]["completed"]

    def mark_current_task_as_completed(self, state: AgentState, response: str) -> AgentState:
        """
        Mark the current task as completed and return a new state.
        Adds the llm response to understand in which message the response was marked as completed.

        Args:
            state (AgentState): The current state.
            response (str): The response of the llm that completed the task.

        Returns:
            AgentState: A new state with the current task marked as completed.
        """
        tool_data = state["tool_data"].copy()
        if tools.delegate_tasks.name in tool_data:
            task_list = tool_data[tools.delegate_tasks.name]["task_list"]
            for task in task_list:
                # Mark first unfinished task as completed
                if not task.get('is_finished', False):
                    task['is_finished'] = True
                    task["response"] = response
                    break

        return {**state, "tool_data": tool_data}
    
    def task_to_instruction(self, task: dict) -> str:
        return f"""Complete the following task entirely. \nObjective: {task["objective"]}\nDetails: {task["details"]}\n"""
    
    
    def is_task_list_empty(self, state: AgentState):
        """
        Check if the task list is empty in the state.

        Args:
            state (AgentState): The current state containing tasks.

        Returns:
            bool: True if the task list is empty, False otherwise.
        """
        if "tool_data" not in state or not state["tool_data"]:
            return True

        task_list = state["tool_data"][tools.delegate_tasks.name]["task_list"]
        return not task_list
    
    def is_task_list_complete(self, state: AgentState):
        """
        Check if the task list is complete in the state.

        Args:
            state (AgentState): The current state containing tasks.

        Returns:
            bool: True if the task list is complete, False otherwise.
        """

        task_list = state["tool_data"][tools.delegate_tasks.name]["task_list"]
        return all(task.get('is_finished', False) for task in task_list)
    
    def was_task_validation_tool_used(self, state: AgentState) -> bool:
        """
        Check if the validation tool was used in the last message.

        Args:
            state (AgentState): The current state containing messages.

        Returns:
            bool: True if the validation tool was used, False otherwise.
        """
        
        if "tool_data" not in state or not state["tool_data"]:
            return False

        return tools.is_task_completed.name in state["tool_data"]
    
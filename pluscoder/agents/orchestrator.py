from pluscoder import tools
from typing import Annotated, List, Literal
from pluscoder.agents.base import Agent, AgentState
from pluscoder.agents.prompts import combine_prompts, BASE_PROMPT, FILE_OPERATIONS_PROMPT
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
Your role is to understand user requirements to generate/plan a proper list of task to solve those requirements with the help of specialized AI Agents.

Ask any questions to understand the user vision and goals deeply, including technical aspects & non-technical aspects.
Simple requirements requires less (or no) questions than complex ones. Choose key questions that will help you create a comprehensive list of tasks.

Do not propose a list of task until you understand the user requirements deeply through asking detailed questions. *Do not* ask more than 3 questions at once.

*Available Agents*:
- Domain Stakeholder Agent: For discussing project details, maintaining the project overview, roadmap, and brainstorming.
- Developer Agent: For implementing code to solve complex software development requirements.

*Always* present the list of tasks in a structured, ordered format to the user *before* using the delegation tool.
To execute/delegate/complete tasks *use the delegation tool*.

*List task item structure*:

[] <task name>:
   Objective: <task objective>
   Details: <task details> Details of the task to complete. Always include file paths to give more context, and functions/class/method names. Always include references to files edited by previous tasks to explain how tasks are related.
   Agent: <agent name> Agent who is responsible for this task.
   Restrictions: <task restrictions> Any limitations or constraints for the task.
   Outcome: <expected outcome> The expected result (file updates) of completing this task.
   
   
*Examples of task list*:

Example 1. For features; always speficy files to edit in the details. Include unit test and doc updated

[ ] Implement Weather Data Fetching:
   Objective: Add functionality to fetch current weather data from an API
   Details: Create a new file `code/weather.py`. Implement a `WeatherService` class with a method `get_current_weather(city: str)` that fetches weather data for a given city using an external API (e.g., OpenWeatherMap). Use the `requests` library to make HTTP calls.
   Agent: Developer

[ ] Add Weather Command to CLI:
   Objective: Create a new CLI command to display weather information
   Details: Modify `code/commands.py` to add a new command `weather`. This command should accept a city name as an argument, use the `WeatherService` from `code/weather.py` to fetch weather data, and display it to the user. Update the command parser to include this new weather command.
   Agent: Developer

[ ] Create Unit Tests for Weather Feature:
   Objective: Implement unit tests for the new weather functionality
   Details: Create a new file `tests/test_weather.py`. Write unit tests to verify the correct functioning of the `WeatherService` class and its `get_current_weather()` method. Include tests for successful API calls, error handling, and edge cases. Also, add tests for the new weather command in `pluscoder/commands.py`, mocking the `WeatherService` to avoid actual API calls during testing.
   Agent: Developer

[ ] Document Weather Feature in README and overview:
   Objective: Update project documentation to include information about the new weather feature
   Details: Document new feature in overview file explaining the weather feature. Include information on how to use the new weather command at README, any required API keys or configuration, and an example of the output.
   Agent: Domain Expert
   
Example 2: Another feature

[ ] Implement CSV Data Processing:
   Objective: Add functionality to process CSV files and calculate statistics
   Details: Create a new file `data_processor.py`. Implement a `CSVProcessor` class with a method `calculate_stats(file_path: str)` that reads a CSV file, calculates basic statistics (mean, median, mode) for numeric columns, and returns the results. Use the `pandas` library to read and process the CSV data.
   Agent: Developer

[ ] Add Command-line Interface for CSV Processing:
   Objective: Create a CLI to allow users to process CSV files
   Details: Modify the existing `main.py` file. Add a new command-line argument `--process-csv` that accepts a file path. Update the main function to check for this argument and call the `CSVProcessor.calculate_stats()` method when present. Use the `argparse` library to handle command-line arguments.
   Agent: Developer

[ ] Create Unit Tests for CSV Processing:
   Objective: Implement unit tests for the new CSV processing functionality
   Details: Create a new file `tests/test_csv_processor.py`. Write unit tests to verify the correct functioning of the `CSVProcessor` class and its `calculate_stats()` method. Include tests for various CSV formats, error handling, and edge cases. Create sample CSV files in a `tests/data/` directory to use in these tests. Also, add tests for the new command-line interface in `main.py`, using mock CSV files.
   Agent: Developer

[ ] Document CSV Processing Feature:
   Objective: Update project documentation to include information about the new CSV processing feature
   Details: Edit the existing `README.md` file. Add a new section explaining the CSV processing functionality, including how to use the command-line interface, expected CSV format, and the statistics calculated. Provide an example command and sample output. Reference the new `data_processor.py` file and the changes made to `main.py`.
   Agent: Domain Expert
   
Example 3: Project Analysis and overview

[ ] Analyze Backend Architecture:
   Objective: Read and analyze the main backend components
   Details: Examine `src/server/app.js`, `src/server/models/index.js`, and `src/server/controllers/index.js`. Analyze these files to understand the server setup, database models, and API endpoints. Summarize the findings in a temporary file `temp_backend_analysis.md`.
   Agent: Developer

[ ] Review Frontend Structure:
   Objective: Examine the main frontend components and structure
   Details: Read and analyze `src/client/App.js`, `src/client/components/index.js`, and `src/client/pages/index.js`. Summarize the key React components, routing structure, and overall frontend architecture. Add this information to `temp_frontend_analysis.md`.
   Agent: Developer

[ ] Examine Database and API Integration:
   Objective: Review database schema and API integration
   Details: Analyze `src/server/config/database.js`, `src/server/routes/api.js`, and `src/client/services/api.js`. Summarize the database configuration, API routes on the server, and how the frontend interacts with the API. Append this information to `temp_integration_analysis.md`.
   Agent: Developer

[ ] Generate Structured Overview:
   Objective: Create a comprehensive, structured overview of the e-commerce platform
   Details: Based on the analysis in the temporary files, create a new file `PLATFORM_OVERVIEW.md` in the project root. Organize the information into sections such as "Backend Architecture", "Frontend Structure", "Database Schema", "API Integration", and "Key Features". Include relevant file paths, main components, and brief explanations of their purposes. Ensure the document provides a clear, high-level understanding of the e-commerce platform's structure and functionality.
   Agent: Domain Stakeholder
   
* All previous tasks were examples, do not use them as a reference. Create your own list of tasks and follow the given instructions to complete them *

*Rules for Task List*:
You *must follow* following rules when suggesting a task list:
1. Each task must be an step of an step-by-step solution
2. All editions related to the same file *must be handled by the same task*
3. Task *must* be able to be executed sequentially and reference outcome of previous tasks.
4. Tasks outcome must always be file updates/editions
"""

    validation_system_message = """
    An user requested you a task, and you delegated it to an agent to solve it.
    Your work is to tell if a task/instruction solved by the agent was fully executed and if the expected outcome was achieved.

    Agents can read and write files by themselves, so don't question the agent's actions, just evaluate their procedure and thinking.

    *Instructions*:
    1. If the task/instruction was not fully executed, explain why it was not fully executed, what is missing. Consider any restrictions that were placed on the task. End the response with "Not fully executed."
    2. If the task/instruction was fully executed, explain how the agent achieved the expected outcome. Verify that the outcome matches what was specified for the task. End the response with "Fully executed."

    *Output Format*:
    Task: [Task Objective]
    Completed: [True/False]
    Feedback: [Feedback or response about task completeness, including adherence to restrictions and achievement of the expected outcome]
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
    
    def get_completed_tasks(self, state: AgentState) -> List[dict]:
        """
        Get the list of completed tasks from the state.

        Args:
            state (AgentState): The current state containing tasks.

        Returns:
            List[dict]: A list of completed tasks with their results.
        """
        if "tool_data" not in state \
            or not state["tool_data"] \
            or tools.delegate_tasks.name not in state["tool_data"] \
            or not state["tool_data"][tools.delegate_tasks.name] \
            or "task_list" not in state["tool_data"][tools.delegate_tasks.name]:
            return []

        task_list = state["tool_data"][tools.delegate_tasks.name]["task_list"]
        return [task for task in task_list if task.get('is_finished', False)]
    
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
    
    def task_to_instruction(self, task: dict, state: AgentState) -> str:
        general_objective = state["tool_data"][tools.delegate_tasks.name]["general_objective"]
        
        completed_tasks = self.get_completed_tasks(state)
        completed_tasks_info = "\n".join([
            f"- Completed: {t['objective']}\n  {t['details']}" 
            for t in completed_tasks
        ])
        
        instruction = f"""You are requested to solve a specific task related to the objective: {general_objective}.
        
        These tasks were already completed:

*Context (completed tasks):*
{completed_tasks_info}


*You must execute/complete only the following task:*

Objective: {task["objective"]}
Details: {task["details"]}
Restrictions: {task.get("restrictions", "No specific restrictions.")}
Expected Outcome: {task.get("outcome", "No specific outcome defined.")}

Load relevant files mentioned in your task or the completed ones to help you achieve the objective.

Write you answer step by step, using a <thinking> block for analysis your throughts before giving a response to me and edit files inside a <output> block.

"""
        return instruction
    
    
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
    
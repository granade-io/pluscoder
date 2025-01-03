from typing import List

from pluscoder import tools
from pluscoder.agents.base import Agent
from pluscoder.agents.core import AgentDefinition
from pluscoder.agents.prompts import build_system_prompt
from pluscoder.agents.stream_parser import XMLStreamParser
from pluscoder.config import config
from pluscoder.message_utils import HumanMessage
from pluscoder.model import get_orchestrator_llm
from pluscoder.type import AgentConfig
from pluscoder.type import AgentInstructions
from pluscoder.type import OrchestrationState

ORCHESTRATOR_REMINDER = """
<specialization_reminder>
Remember your role is to understand user requirements to generate/plan a proper list of task to solve those requirements with the help of specialized Pluscoder AI Agents.
1. Each task you generate must be an step of an step-by-step solution
2. All editions related to the same file *must be handled by the same task*
3. Task *must* be able to be executed sequentially and reference outcome of previous tasks.
4. Tasks outcome must always be file updates/editions
5. Specify in agent instructions the resources (links/images) the user gave (including 'img::' if present on images)
</specialization_reminder>
"""


class OrchestratorAgent(Agent, AgentDefinition):
    id = "orchestrator"
    name = "Orchestrator"
    description = "Design and run complex plan delegating it to other agents"
    suggestions = [
        "Plan implementation of SSO with Keycloak and JWT auth",
        "Create roadmap for migrating monolith to microservices",
        "Design implementation of AWS S3 file upload system",
        "Plan Kubernetes deployment with monitoring setup",
    ]
    specialization_prompt = """
*SPECIALIZATION INSTRUCTIONS*:
You are the Orchestrator Agent, your role is to understand user requirements to generate/plan a proper list of task to solve those requirements with the help of specialized Pluscoder AI Agents.

<specialization_context>
1. Other Pluscoder agents are mostly like you. Then know and have access to the same repository and can work over it, creating files, analyzing, summarizing, coding, document, etc
2. They have the same limitations as you. They can't run bash commands for example.
3. They can read files from urls or from user SO/repository
4. They don't have memory, when delegating tasks they will only have access to the task list you provide to them.
5. They can visually read images if these starts with img::<image_path_or_utl>, same as you can do, otherwise they will only see the path
</specialization_context>

<available_agents_to_delegate_tasks>
*Available Agents*:
- Developer Agent: For writing code, documentation, tests, etc.
</available_agents_to_delegate_tasks>

<task_item_structure>
[] '<task name>'
   'Objective': <task objective>
   'Details': <task details> Details of the task to complete. Always include file paths to give more context, and functions/class/method names. Always include references to files edited by previous tasks to explain how tasks are related.
   'Agent': <agent name> Agent who is responsible for this task.
   'Restrictions': <task restrictions> Any limitations or constraints for the task.
   'Outcome': <expected outcome> The expected result (file updates) of completing this task.
</task_item_structure>

<task_list_examples>
* All following tasks are examples, do not use them as a reference. Create your own list of tasks and follow the given instructions to complete them *
    <example requirement="add a cli option to display weather information">
        'General objective': Implement Weather Feature

        [ ] 'Implement Weather Data Fetching and CLI Command'
        'Objective': Add functionality to fetch current weather data from an API and create a CLI command
        'Details': Create a new file `code/weather.py`. Implement a `WeatherService` class with a method `get_current_weather(city: str)` that fetches weather data for a given city using an external API (e.g., OpenWeatherMap). Use the `requests` library for HTTP calls. In the same file, implement a CLI command `weather` that uses this service. Update `code/commands.py` to include the new weather command in the command parser.
        'Agent': Developer
        'Restrictions': Use only the `requests` library for API calls. Ensure proper error handling for API requests.
        'Outcome': New file `code/weather.py` with `WeatherService` class and CLI command implementation. Updated `code/commands.py` with new weather command added to the parser.

        [ ] 'Create Unit Tests for Weather Feature'
        'Objective': Implement unit tests for the new weather functionality
        'Details': Create a new file `tests/test_weather.py`. Write unit tests to verify the correct functioning of the `WeatherService` class, its `get_current_weather()` method, and the CLI command. Include tests for successful API calls, error handling, and edge cases. Use mocking to avoid actual API calls during testing.
        'Agent': Developer
        'Restrictions': Use pytest for writing tests. Ensure all tests are independent and do not rely on external services.
        'Outcome': New file `tests/test_weather.py` with comprehensive unit tests for the weather feature.

        [ ] 'Update Project Documentation'
        'Objective': Document the new weather feature in project files
        'Details': Update `PROJECT_OVERVIEW.md` to include information about the new weather feature. Add a section in `README.md` explaining how to use the new weather command, including any required API keys or configuration, and provide an example of the output.
        'Agent': Developer
        'Restrictions': Ensure documentation is clear and concise. Include any setup steps required for the weather API.
        'Outcome': Updated `PROJECT_OVERVIEW.md` and `README.md` files with new sections detailing the weather feature.
    </example>
    <example requirement="allow client to process csv data">
        'General objective': Implement Data Processing Feature

        [ ] 'Implement CSV Data Processing and CLI Interface'
        'Objective': Add functionality to process CSV files, calculate statistics, and create a CLI interface
        'Details': Create a new file `code/data_processor.py`. Implement a `CSVProcessor` class with a method `calculate_stats(file_path: str)` that reads a CSV file, calculates basic statistics (mean, median, mode) for numeric columns, and returns the results. Use the `pandas` library for data processing. In the same file, implement a CLI command `process-csv` that uses this processor. Update `code/commands.py` to include the new CSV processing command in the command parser.
        'Agent': Developer
        'Restrictions': Use only the `pandas` library for CSV processing. Ensure proper error handling for file operations and data processing.
        'Outcome': New file `code/data_processor.py` with `CSVProcessor` class and CLI command implementation. Updated `code/commands.py` with new CSV processing command added to the parser.

        [ ] 'Create Unit Tests for CSV Processing'
        'Objective': Implement unit tests for the new CSV processing functionality
        'Details': Create a new file `tests/test_csv_processor.py`. Write unit tests to verify the correct functioning of the `CSVProcessor` class, its `calculate_stats()` method, and the CLI command. Include tests for various CSV formats, error handling, and edge cases. Create sample CSV files in a `tests/data/` directory to use in these tests.
        'Agent': Developer
        'Restrictions': Use pytest for writing tests. Ensure all tests are independent and use mock data.
        'Outcome': New file `tests/test_csv_processor.py` with comprehensive unit tests for the CSV processing feature. New directory `tests/data/` with sample CSV files for testing.

        [ ] 'Update Project Documentation for CSV Processing'
        'Objective': Document the new CSV processing feature in project files
        'Details': Update `PROJECT_OVERVIEW.md` to include information about the new CSV processing feature. Add a section in `README.md` explaining how to use the new CSV processing command, including expected CSV format, the statistics calculated, and provide an example command with sample output.
        'Agent': Developer
        'Restrictions': Ensure documentation is clear and concise. Include any dependencies required for the CSV processing feature.
        'Outcome': Updated `PROJECT_OVERVIEW.md` and `README.md` files with new sections detailing the CSV processing feature.
    </example>
    <example requirement="generate an overview documentation of this backend and frontend project at PROJECT_OVERVIEW.md">
        Example 3: Project Analysis and Overview

        [ ] 'Analyze Project Structure and Components'
        'Objective': Examine and summarize the project's backend, frontend, and integration components
        'Details': Analyze the following files:
        - Backend: `src/server/app.js`, `src/server/models/index.js`, `src/server/controllers/index.js`
        - Frontend: `src/client/App.js`, `src/client/components/index.js`, `src/client/pages/index.js`
        - Integration: `src/server/config/database.js`, `src/server/routes/api.js`, `src/client/services/api.js`
        Summarize the findings in a single file `temp_project_analysis.md`, organizing the information into sections for backend, frontend, and integration.
        'Agent': Developer
        'Restrictions': Focus on high-level architecture and key components. Do not include low-level implementation details.
        'Outcome': New file `temp_project_analysis.md` with a comprehensive summary of the project's structure and components.

        [ ] 'Generate Structured Project Overview'
        'Objective': Create a comprehensive, structured overview of the project based on the analysis
        'Details': Using the information from `temp_project_analysis.md`, create a new file `PROJECT_OVERVIEW.md` in the project root. Organize the information into sections such as "Backend Architecture", "Frontend Structure", "Database Schema", "API Integration", and "Key Features". Include relevant file paths, main components, and brief explanations of their purposes. Ensure the document provides a clear, high-level understanding of the project's structure and functionality.
        'Agent': Developer
        'Restrictions': The overview should be concise yet comprehensive. Use clear headings and subheadings for easy navigation.
        'Outcome': New file `PROJECT_OVERVIEW.md` with a structured, comprehensive overview of the project. Deletion of the temporary `temp_project_analysis.md` file.
    </example>
</task_list_examples>

<main_specialization_responsibilities>
    Ask key questions about the requirement to understand the user vision and goals deeply, including technical aspects & non-technical aspects.
    Simple requirements requires less (or no) questions than complex ones. Choose key questions that will help you create a comprehensive list of tasks.

    Do not propose a list of task until you understand the user requirements deeply through asking detailed questions. *Do not* ask more than 3 questions at once.
    *Always* present the list of tasks in a structured, ordered format to the user *before* using the delegation tool.
    To execute/delegate/complete tasks *use the delegation tool*.

    <task_list_proposal_rules>
        You *must follow* following rules when suggesting a task list:
        1. Each task must be an step of an step-by-step solution
        2. All editions related to the same file *must be handled by the same task*
        3. Task *must* be able to be executed sequentially and reference outcome of previous tasks.
        4. Tasks outcome must always be file updates/editions
        5. Specify in agent instructions the resources (links/images) the user gave (including 'img::' if present on images)
    </task_list_proposal_rules>
</main_specialization_responsibilities>
"""

    validation_system_message = """
You are an AI Agent which has to check if an user request was properly accomplished given the work done by another AI Agent
Your work is to tell if a task/instruction solved by the agent was fully executed and if the expected outcome was achieved.

Agents can read and write files by themselves, so don't question the agent's actions, if they reported they did something, assume its done, just evaluate their procedure and thinking.

<main_instructions>
1. If the task/instruction was not fully executed, explain why it was not fully executed, what is missing. Consider any restrictions that were placed on the task. End the response with "Not fully executed."
2. If the task/instruction was fully executed, explain how the agent achieved the expected outcome. Verify that the outcome matches what was specified for the task. End the response with "Fully executed."
Use is_task_completed tool
</main_instructions>

<task_validation_output_format>
Task: [Task Objective]
Completed: [True/False]
Feedback: [Feedback or response about task completeness, including adherence to restrictions and achievement of the expected outcome]
</task_validation_output_format>
    """

    summarizing_system_message = """
Your role is to summarize the outputs of others agent to solve a request given by the user's task.
The summary should be concise and clear.

*Instructions*:
1. Summarize all task solved in a message aimed for the user who requested the tasks.
    """

    orchestrator_reminder_prompt = """
You *must follow* following rules when suggesting a task list:
1. Each task must be an step of an step-by-step solution
2. All editions related to the same file *must be handled by the same task*
3. Task *must* be able to be executed sequentially and reference outcome of previous tasks.
4. Tasks outcome *must always* be file updates/editions
5. Specify in Task Details the resources (links/images) the user gave (including 'img::' if present on images)
    """

    def __init__(
        self,
        agent_config: AgentConfig,
        stream_parser: XMLStreamParser,
        extraction_tools=[tools.delegate_tasks, tools.is_task_completed],
    ):
        super().__init__(
            agent_config,
            stream_parser=stream_parser,
            extraction_tools=extraction_tools,
        )

    def get_system_message(self, state: OrchestrationState) -> str:
        # Default prompt
        if state["status"] == "active":
            system_prompt = self.system_message
        elif state["status"] == "summarizing":
            system_prompt = self.summarizing_system_message
        else:
            system_prompt = self.validation_system_message

        return build_system_prompt(
            system_prompt,
            can_read_files=self.repository_interaction,
            can_edit_files=not self.read_only and not config.read_only and self.repository_interaction,
        )

    def get_reminder_prefill(self, state: OrchestrationState) -> str:
        # Default prompt
        if state["status"] == "active":
            return super().get_reminder_prefill(state)
        return ""

    def get_tool_choice(self, state: OrchestrationState) -> str:
        """Chooses a the tool to use when calling the llm"""
        if state["status"] == "delegating":
            return tools.is_task_completed.name
        return "auto"

    def get_agent_model(self):
        return get_orchestrator_llm()

    @classmethod
    def is_agent_response(cls, state: OrchestrationState) -> bool:
        """
        Verify if the last message in the state is from an agent.

        Args:
            state (OrchestrationState): The current state containing messages.

        Returns:
            bool: True if the last message is from an agent, False otherwise.
        """
        if not state["messages"]:
            return False

        last_message = state["messages"][-1]
        # Assuming agent messages are not instances of HumanMessage
        return not isinstance(last_message, HumanMessage)

    @classmethod
    def get_current_task(cls, state: OrchestrationState):
        """
        Get the first task that is not finished from the state.

        Args:
            state (OrchestrationState): The current state containing tasks.

        Returns:
            Task: The first unfinished task, or None if all tasks are finished or no tasks exist.
        """
        if (
            "tool_data" not in state
            or not state["tool_data"]
            or tools.delegate_tasks.name not in state["tool_data"]
            or not state["tool_data"][tools.delegate_tasks.name]
            or "task_list" not in state["tool_data"][tools.delegate_tasks.name]
        ):
            return None

        task_list = state["tool_data"][tools.delegate_tasks.name]["task_list"]
        return next((task for task in task_list if not task.get("is_finished", False)), None)

    @classmethod
    def get_completed_tasks(cls, state: OrchestrationState) -> List[dict]:
        """
        Get the list of completed tasks from the state.

        Args:
            state (OrchestrationState): The current state containing tasks.

        Returns:
            List[dict]: A list of completed tasks with their results.
        """
        if (
            "tool_data" not in state
            or not state["tool_data"]
            or tools.delegate_tasks.name not in state["tool_data"]
            or not state["tool_data"][tools.delegate_tasks.name]
            or "task_list" not in state["tool_data"][tools.delegate_tasks.name]
        ):
            return []

        task_list = state["tool_data"][tools.delegate_tasks.name]["task_list"]
        return [task for task in task_list if task.get("is_finished", False)]

    @classmethod
    def get_task_list(cls, state: OrchestrationState) -> List[dict]:
        """
        Get the task list from the state.

        Args:
            state (OrchestrationState): The current state containing tasks.

        Returns:
            List[dict]: The task list.
        """
        if "tool_data" not in state or not state["tool_data"] or tools.delegate_tasks.name not in state["tool_data"]:
            return []

        return state["tool_data"][tools.delegate_tasks.name]["task_list"]

    @classmethod
    def remove_task_list_data(cls, state: OrchestrationState) -> OrchestrationState:
        """Remove the task list data from the state."""
        return {
            **state,
            "tool_data": {**state["tool_data"], tools.delegate_tasks.name: None},
        }

    @classmethod
    def get_agent_instructions(cls, state: OrchestrationState) -> AgentInstructions:
        return AgentInstructions(**state["tool_data"][tools.delegate_tasks.name])

    @classmethod
    def validate_current_task_completed(cls, state: OrchestrationState) -> bool:
        """
        Check if the current task is completed based on the state last tool used.

        Args:
            state (OrchestrationState): The current state containing task completion status.

        Returns:
            bool: True if the current task is completed, False otherwise.
        """
        if "tool_data" not in state or not state["tool_data"]:
            return False

        if tools.is_task_completed.name not in state["tool_data"]:
            return False

        return state["tool_data"][tools.is_task_completed.name]["completed"]

    @classmethod
    def mark_current_task_as_completed(cls, state: OrchestrationState, response: str) -> OrchestrationState:
        """
        Mark the current task as completed and return a new state.
        Adds the llm response to understand in which message the response was marked as completed.

        Args:
            state (OrchestrationState): The current state.
            response (str): The response of the llm that completed the task.

        Returns:
            OrchestrationState: A new state with the current task marked as completed.
        """
        tool_data = state["tool_data"].copy()
        if tools.delegate_tasks.name in tool_data:
            task_list = tool_data[tools.delegate_tasks.name]["task_list"]
            for task in task_list:
                # Mark first unfinished task as completed
                if not task.get("is_finished", False):
                    task["is_finished"] = True
                    task["response"] = response
                    break

        return {**state, "tool_data": tool_data}

    @classmethod
    def task_to_instruction(cls, task: dict, state: OrchestrationState) -> str:
        task_list_data = state["tool_data"][tools.delegate_tasks.name]
        general_objective = task_list_data["general_objective"]

        completed_tasks = OrchestratorAgent.get_completed_tasks(state)
        completed_tasks_info = "\n".join([f"- Completed: {t['objective']}\n  {t['details']}" for t in completed_tasks])

        # Get any image for multi-modal llm
        images = list(filter(lambda res: res.startswith("img::"), task_list_data["resources"]))
        other_resources = list(filter(lambda res: not res.startswith("img::"), task_list_data["resources"]))
        images_instruction = ""
        resources_instruction = ""

        if images:
            images_instruction += f"\n*Reference images:* {''.join(images)}"
        if other_resources:
            resources_instruction += f"\n*Other resources:* {''.join(other_resources)}"

        return f"""\
You are requested to solve a specific task related to the objective: {general_objective}.

These tasks were already completed:

*Context (completed tasks):*
{completed_tasks_info}


*You must execute/complete only the following task:*

Objective: {task["objective"]}
Details: {task["details"]}
Restrictions: {task.get("restrictions", "No specific restrictions.")}
Expected Outcome: {task.get("outcome", "No specific outcome defined.")}

*Read all files mentioned in tasks above* for context, then analyze if need to load any else to complete the task.

{images_instruction}
{resources_instruction}

Write you answer step by step, using a <thinking> block for analysis your thoughts before giving a response to me using <step> and edit files using <source> blocks.
"""

    @classmethod
    def is_task_list_empty(cls, state: OrchestrationState):
        """
        Check if the task list is empty in the state.

        Args:
            state (OrchestrationState): The current state containing tasks.

        Returns:
            bool: True if the task list is empty, False otherwise.
        """
        if (
            "tool_data" not in state
            or not state["tool_data"]
            or tools.delegate_tasks.name not in state["tool_data"]
            or not state["tool_data"][tools.delegate_tasks.name]
        ):
            return True

        task_list = state["tool_data"][tools.delegate_tasks.name]["task_list"]
        return not task_list

    @classmethod
    def is_task_list_complete(cls, state: OrchestrationState):
        """
        Check if the task list is complete in the state.

        Args:
            state (OrchestrationState): The current state containing tasks.

        Returns:
            bool: True if the task list is complete, False otherwise.
        """

        task_list = state["tool_data"][tools.delegate_tasks.name]["task_list"]
        return all(task.get("is_finished", False) for task in task_list)

    @classmethod
    def was_task_validation_tool_used(cls, state: OrchestrationState) -> bool:
        """
        Check if the validation tool was used in the last message.

        Args:
            state (OrchestrationState): The current state containing messages.

        Returns:
            bool: True if the validation tool was used, False otherwise.
        """

        if "tool_data" not in state or not state["tool_data"]:
            return False

        return tools.is_task_completed.name in state["tool_data"]

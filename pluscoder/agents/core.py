from pluscoder import tools
from pluscoder.agents.base import Agent
from pluscoder.agents.prompts import (
    BASE_PROMPT,
    FILE_OPERATIONS_PROMPT,
    OUTPUT_STRUCTURE_PROMPT_READ_ONLY,
    OUTPUT_STRUCTURE_PROMPT_WRITE,
    READONLY_MODE_PROMPT,
    combine_prompts,
)
from pluscoder.config import config


class DeveloperAgent(Agent):
    id = "developer"
    description = "Implement code to solve complex software development requirements"
    developer_prompt = """
*SPECIALIZATION INSTRUCTIONS*:
Your role is to implement software development tasks based on detailed plans provided. You should write high-quality, maintainable code that adheres to the project's coding guidelines and integrates seamlessly with the existing codebase.

Key Responsibilities:
1. Review the overview, guidelines and repository files to determine which files to load to solve the user requirements.
2. Review relevant existing code and project files to ensure proper integration.
3. Adhere strictly to the project's coding guidelines and best practices when coding
4. Ensure your implementation aligns with the overall project architecture and goals.

Guidelines:
- Consult PROJECT_OVERVIEW.md for understanding the overall system architecture and goals.
- Always refer to CODING_GUIDELINES.md for project-specific coding standards and practices.
- Follow the project's file structure and naming conventions.

*IMPORTANT*:
1. Always read the relevant project files and existing code before thinking a solution
2. Ensure your code integrates smoothly with the existing codebase and doesn't break any functionality.
3. If you encounter any ambiguities or potential issues with the task description, ask for clarification before proceeding.
"""

    def __init__(
        self,
        tools=[tools.read_files, tools.move_files, tools.read_file_from_url],
        default_context_files=["PROJECT_OVERVIEW.md", "CODING_GUIDELINES.md"],
    ):
        system_message = combine_prompts(
            BASE_PROMPT,
            self.developer_prompt,
            OUTPUT_STRUCTURE_PROMPT_READ_ONLY
            if config.read_only
            else OUTPUT_STRUCTURE_PROMPT_WRITE,
            FILE_OPERATIONS_PROMPT if not config.read_only else READONLY_MODE_PROMPT,
        )
        super().__init__(
            system_message,
            "Developer",
            tools=tools,
            default_context_files=default_context_files,
        )


class DomainStakeholderAgent(Agent):
    id = "domain_stakeholder"
    description = (
        "Discuss project details, maintain project overview, roadmap, and brainstorm"
    )

    domain_prompt = """
*SPECIALIZATION INSTRUCTIONS*:
Your role is to discuss project details with the user, do planning, roadmap generation, brainstorming, design, etc.

Ask any questions to understand the project vision and goals deeply, including technical aspects & non-technical aspects.

*Do not* ask more than 6 questions at once.

*Some Inspiring Key questions*:
These are only example questions to help you understand the project vision and goals. Make your own based on user feedback.
- System Overview: Can you provide a high-level overview of the system and its primary purpose?
- Key Functionalities: What are the main features and functionalities of the system?
- Technology Stack: What technologies and frameworks are used in the system?
- System Architecture: What is the architecture of the system (e.g., monolithic, microservices)?
- User Base: Who are the primary users of the system?
- Deployment: How and where is the system deployed and hosted?
- Security: What are the key security measures and protocols in place?
- Scalability: How does the system handle scaling and high availability?
- Development Workflow: What is the development and deployment workflow like?
- Restrictions: Are there any specific technical or business restrictions that affect the system?
- Challenges: What are the main challenges and constraints faced in maintaining and developing the system?
- Future Roadmap: What are the key upcoming features or changes planned for the system?

*Always* suggest the user how to proceed based on their requirement. You are in charge to lead the discussion and support.
"""

    def __init__(
        self,
        tools=[tools.read_files, tools.move_files, tools.read_file_from_url],
        default_context_files=["PROJECT_OVERVIEW.md"],
    ):
        system_message = combine_prompts(
            BASE_PROMPT,
            self.domain_prompt,
            OUTPUT_STRUCTURE_PROMPT_READ_ONLY
            if config.read_only
            else OUTPUT_STRUCTURE_PROMPT_WRITE,
            FILE_OPERATIONS_PROMPT if not config.read_only else READONLY_MODE_PROMPT,
        )
        super().__init__(
            system_message,
            "Domain Stakeholder",
            tools=tools,
            default_context_files=default_context_files,
        )


class DomainExpertAgent(Agent):
    id = "domain_expert"
    description = "Validate tasks and ensure alignment with project vision"
    domain_prompt = """
*SPECIALIZATION INSTRUCTIONS*:
Your role is to validate the tasks of all other agents, check alignment with the project vision, and provide feedback for task revisions.

You should:
1. Review the work of other agents to ensure it aligns with the project vision and goals.
2. Provide constructive feedback and suggestions for improvements.
3. Help refine and clarify project requirements and specifications.
4. Assist in resolving conflicts or inconsistencies in the project plan or implementation.

*Important instructions*:
1. *always* load relevant files to understand them to give proper feedback
2. ensure the system *will continue working as expected* on proposed work/changes
3. understand clearly each proposed work/change/task will integrate with the current workflow
4. Identify missing parts of the proposal that are needed to allow execute the project properly
5. Identify parts of the project that can be broken or removed due the proposed changes
6. Identify missing files to be modified that are not mentioned in the proposal
7. Be extremely specific with methods names, classes and functions

*Some Inspiring Key questions*:
Adapt them according to the work/tasks you are validating.
1. Which class/methods are involved in an specific proposal?
2. Which files nee
2. How will the main workflow change?
3. Can any feature be broken or removed due to the proposed changes?
4. Which functions/class need to be updated or removed with the proposed change?

Always refer to the `PROJECT_OVERVIEW.md` file for the most up-to-date project vision and goals.

THE PROPOSAL NEVER IS FULLY CORRECT, WAS MADE BY AN IA, FIND THOSE DETAILS TO IMPROVE IT. TAKE A DETAILED LOOK TO PROJECT FILES TO DETECT THOSE .
"""

    def __init__(
        self,
        tools=[tools.read_files, tools.move_files, tools.read_file_from_url],
        default_context_files=["PROJECT_OVERVIEW.md", "CODING_GUIDELINES.md"],
    ):
        system_message = combine_prompts(
            BASE_PROMPT,
            self.domain_prompt,
            OUTPUT_STRUCTURE_PROMPT_READ_ONLY
            if config.read_only
            else OUTPUT_STRUCTURE_PROMPT_WRITE,
            FILE_OPERATIONS_PROMPT if not config.read_only else READONLY_MODE_PROMPT,
        )
        super().__init__(
            system_message,
            "Domain Expert",
            tools=tools,
            default_context_files=default_context_files,
        )


class PlanningAgent(Agent):
    id = "planning"
    description = "Create detailed, actionable plans for software development tasks"
    planning_prompt = """
*SPECIALIZATION INSTRUCTIONS*:
Your role is to create detailed, actionable plans for software development tasks. You should break down high-level requirements into specific, implementable tasks at the class and method level. Your plans will be executed by AI developer agents, so be as clear and specific as possible.

Key Responsibilities:
1. *Read all relevant project files to understand the context and requirements.*
2. Break down high-level requirements into specific, implementable tasks.
3. Define tasks at the class and method level, including clear descriptions of functionality.
4. Order tasks in an iterative manner, ensuring each task can be implemented and tested before proceeding to the next.
5. Consider dependencies between tasks when defining the order of implementation.
6. Provide clear, concise instructions for each task, suitable for junior engineers or AI agents.
7. Ensure that the plan aligns with the project's overall vision and goals.

Guidelines:
- Read and analyze the relevant project files to understand the context and requirements.
- Create plans that are clear, concise, and easy to follow.
- Each task should be self-contained and testable.
- Consider the project's current state and any technical restrictions when creating the plan.
- Do not include time estimates or team-specific constraints.
- Assume that the developers (AI agents) will have access to the PROJECT_OVERVIEW.md and CODING_GUIDELINES.md files.

When creating a plan, follow this structure:
1. Overall objective
2. List of tasks, each containing:
   a. Task name
   b. Description
   c. Specific implementation details (classes, methods, functionality)
   d. Expected outcome or acceptance criteria
3. Any important notes or considerations for the implementation

*EXTREMELY IMPORTANT*:
1. *First of all* read ALL necessary project files to propose a plan
2. *DO NOT* propose a plan without reading all necessary project files first
3. your plans should be detailed enough for implementation by AI agents or junior developers who have read the project overview and coding guidelines.
"""

    def __init__(
        self,
        tools=[tools.read_files, tools.move_files, tools.read_file_from_url],
        default_context_files=["PROJECT_OVERVIEW.md", "CODING_GUIDELINES.md"],
    ):
        system_message = combine_prompts(
            BASE_PROMPT,
            self.planning_prompt,
            OUTPUT_STRUCTURE_PROMPT_READ_ONLY
            if config.read_only
            else OUTPUT_STRUCTURE_PROMPT_WRITE,
            FILE_OPERATIONS_PROMPT if not config.read_only else READONLY_MODE_PROMPT,
        )
        super().__init__(
            system_message,
            "Planning",
            tools=tools,
            default_context_files=default_context_files,
        )

from pluscoder.tools import base_tools
from pluscoder.type import AgentConfig


class AgentDefinition:
    @classmethod
    def to_agent_config(cls, **kwargs):
        """Creates an AgentConfig instance from the AgentDefinition class.

        You can override any AgentConfig value to customize the agent configuration.

        Check the AgentConfig class for more details on the available fields.

        Returns:
            AgentConfig: Agent configuration dict
        """
        return AgentConfig(
            **{
                "id": cls.id,
                "name": cls.name,
                "description": cls.description,
                "suggestions": cls.suggestions,
                "prompt": cls.specialization_prompt,
                "repository_interaction": True,
                "read_only": False,
                "reminder": "",
                "default_context_files": [],
                "tools": [tool.name for tool in base_tools],
                "provider": None,
                **kwargs,
            },
        )


class DeveloperAgent(AgentDefinition):
    id = "developer"
    name = "Developer"
    description = "Agent specialized in development and code generations"
    suggestions = [
        "Create a FastAPI endpoint for user profile with SQLAlchemy models",
        "Implement Redis caching layer for frequently accessed API routes",
        "Add Swagger documentation for the payment processing endpoints",
        "Set up Celery tasks for async email notifications",
    ]
    specialization_prompt = """
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
"""


class DomainStakeholderAgent(AgentDefinition):
    id = "domain_stakeholder"
    name = "Domain Stakeholder"
    description = "Discuss project details, maintain project overview, roadmap, and brainstorm"
    suggestions = [
        "Design a social media feed microservice with MongoDB",
        "Plan integration of Stripe payment processing system",
        "Design WebSocket architecture for real-time chat feature",
        "Plan ElasticSearch implementation for product search",
    ]
    specialization_prompt = """
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

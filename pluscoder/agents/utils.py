from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser

from pluscoder.config import config
from pluscoder.io_utils import io
from pluscoder.model import get_llm


def generate_agent(description: str, repository_interaction: bool) -> dict:
    """Generate a specialized agent prompt based on a description.

    Args:
        description (str): Description of the agent's role and responsibilities

    Returns:
        str: Formatted agent prompt
    """
    prompt_template = """
<instructions>
"""

    if repository_interaction:
        prompt_template += """
Given the following prompt for an programming AI Agent that have access to a repository to assist and work with:

    <prompt>
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
    </prompt>

and given the following description/requirement:

<description>
{description}
</description>

Please generate another equivalent prompt to describe the *BEST POSSIBLE AI AGENT* that can handle that request or match that description:
1. Preserve same structure and key points structure of <prompt>
2. Specify specialized knowledge and specific areas where the desired agent is an expert
3. Keep key points related to the repository management (like read, review files and think step by step) to solve any related request related to the <description>
"""
    else:
        prompt_template += """
Given an agent description or problem to solve:

<description>
{description}
</description>

Generate a prompt to describe the *BEST POSSIBLE AI AGENT ASSISTANT* that can handle that request or matches that description:
1. Specify specialized knowledge and specific areas where the described agent is an expert and its responsibilities to assist an user
2. Start that prompt with "You are..."
"""

    prompt_template += """
<output_format>
Return the only well-formatted json without any tag. With this structure:
- name: Mayus-Camelcase without any spaces, dashes or underscores. Max 2 words. i.e: AgentName, Css6, Security, AuthExpert, DjangoBackend
- description: An small sentence with agent description
- prompt: <Generated prompt>
- system_reminder: Paragraph with system reminder to tell the agent each time the user talk with them to reminds what's their specialized role and responsibilities

    <example_output>
    {{
        "name": "DocExpert",
        "description": "An AI agent specialized in creating comprehensive code documentation in Python following Google Docstring standards.",
        "prompt": <prompt>
        "system_reminder": "Remember, your primary role is to create high-quality documentation in Python using Google Docstring standards, carefully reviewing code and adhering to the project’s guidelines to maintain clarity and consistency across the codebase."
    }}
    </example_output>
</output_format>
<instructions>
"""

    prompt = PromptTemplate(
        input_variables=["description"],
        template=prompt_template,
    )

    model = get_llm(config.provider, config.model)
    if model is None:
        io.print("Error: Language model not found.", style="bold red")
        return ""

    parser = JsonOutputParser()
    chain = prompt | model | parser

    return chain.invoke({"description": description})

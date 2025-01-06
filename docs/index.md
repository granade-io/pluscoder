# Introduction

--8<-- "docs/.partials/header.html"

* **PlusCoder** is an AI-powered tool that accelerates software development by assisting with planning, coding, and management tasks.
* The name ”+ Coder” extends beyond just **“You + Coder”**—it can be paired with other tools, or CI/CD processes, enhancing them with AI.
* PlusCoder is a versatile assistant specialized for integration with other systems for streamlined, effortless development.


## Why to use PlusCoder

1. **It's just Python**: Coding agents are designed to work with large codebases efficiently, and they are fully programmable. You can run them in your development environment or in the cloud, leveraging LLM power in an easy sweep in all your repositories.
2. **Customizable and Standardizable**: You can write custom company-wide specialized agents, instructions and tools. Allowing your entire team to leverage a single centralized configuration of agents.
3. **Chat with agents**: You can chat with PlusCoder agents directly working with them as a coding partner with same company-wide configurations and guidelines.
4. **Task based workflows**: PlusCoder allows you to create customizable and standardizable workflows for automating repetitive coding tasks.
5. **Multiple LLM providers**: Choose your preferred LLM provider, such as OpenAI, Anthropic, or VertexAI, and everything supported by LiteLLM.


## Basic Examples

Instruct agent to work in the current repository:


=== "python"
    ```python
    from pluscoder.agents.core import DeveloperAgent
    from pluscoder.type import AgentConfig
    from pluscoder.workflow import run_agent


    async def main():
        # Select specific agent
        developer_agent: AgentConfig = DeveloperAgent.to_agent_config(model="gpt-4o")

        # Runs agent in the current workdir
        await run_agent(
            agent=developer_agent,
            input="Write a detailed README.md file specifying develop environment setup using commands present in Makefile"
        )
    ```
=== "CLI"
    ```bash
    pluscoder --default_agent developer \
    --auto_confirm yes \
    --input "Write a detailed README.md file specifying develop environment setup using commands present in Makefile"
    ```
=== "In-Chat"
    ```bash
    > You: Write a detailed README.md file specifying develop environment setup using commands present in Makefile
    ```

## Next steps
- [Installation](installation.md)
- [Quick Start](quick_start.md)
- [Examples](examples/index.md)
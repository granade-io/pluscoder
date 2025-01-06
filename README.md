# PlusCoder

--8<-- "docs/.partials/header.html"

* **PlusCoder** is an AI-powered tool that accelerates software development by assisting with planning, coding, and management tasks.
* The name ”+ Coder” extends beyond just **“You + Coder”**—it can be paired with other tools, or CI/CD processes, enhancing them with AI.
* PlusCoder is a versatile assistant specialized for integration with other systems for streamlined, effortless development.

## Basic Usage

You can run PlusCoder in two ways: as a Python library or as a CLI tool.

**Python:**

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

**CLI:**
   ```bash
   pluscoder --default_agent developer \
   --auto_confirm yes \
   --input "Write a detailed README.md file specifying develop environment setup using commands present in Makefile"
   ```


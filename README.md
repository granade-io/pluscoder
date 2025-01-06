# PlusCoder

A Python agents framework intended for working in repositories. In simple words, programmable agents that code.

See full documentation at [https://granade-io.github.io/pluscoder/](https://granade-io.github.io/pluscoder/)

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


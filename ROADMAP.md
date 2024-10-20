# Prioritized Project Roadmap

## Features:
- Alias --user_input --input
- --llm_output_only to display only the output of llms as a clean output mode
- --llm_output_file to write llm output to a file
- GenAI commits messages and descriptions.
- 

- Allow custom prompt command to run in different agents from the current one

## High Priority Features

### Repository Initialization and Enhancement Command
- Implement an 'init' command for first-time pluscoder setup or forced execution via slash command
- Perform repository improvements prior to using pluscoder calling orchestration agent and telling him to:
  - Auto-generate or update overview file by telling the agent to read key files to sumarize them in the overview
  - Detect linting/test commands of the repo telling the agent in the same prompt to also detect those commands
  - Iterate over files and use an agent to improve docstrings
- Implement as both a startup process and a slash command for on-demand execution

### Improve Orchestrator's flexibility and feedback mechanism
- Improve task quality and relevance by:
  - Ensuring each task is clearly defined and actionable
  - Aligning tasks with the overall project vision and its current state
  - Define tasks of a proper complexity
- Task management:
  - Make this feature configurable, allowing users to enable or disable it
  - Enable to restart from first incompleted task
  - Task persistence for restoring task lists
- Agent interruption and context modification:
  - Allow users to interrupt agent execution to provide additional context
  - Preserve current agent output when interrupted
  - Enable editing of the last message sent to the agent
  - Implement a mechanism to resume agent execution with updated context


### Predefined task list
- Develop a set of pre-defined task lists for common use cases, or prompts to generate whem
- Implement logic for the Orchestrator to identify when these task lists are applicable
- Command to execute pre-defined task list
- Examples of pre-defined task lists:
  - Tell the agent to read relevant files of repository and generate README or other documentation files
  - Identify missing tests and add unit testing
  - Mass refactor over multiples files or entire repo

### Token Usage Tracking and Progress Display
- Create a progress bar or similar visual representation to show total token usage instead of a log

### URL Browse Tool for Agents
- Develop a tool that allows agents to access and browse internet resources

### Chain of throughs
- Extends agents workflow to include a COT to;
  - Retrieve Context files/chunks to solve the request
  - Analize code and propose a solution aligned with the vision or the project or using indication of the user request
  - Generate a solution
  - Evaluate / Judge the solution
- Available algorithms to solve code context retrieval and code generation:
  - GraphRAG / RAG / Triplets / Knowledge Graph
  - AST with metadata & comments
  - Improved inline documentation
  - Custom metadata to files

### Voice Communication Interface (High Priority, Medium Complexity)
- Implement speech-to-text functionality for user input
- Integrate voice input with existing command-line interface

## Medium Priority Features

### Advanced Output Filtering System enhancement (Low Complexity)
- Improve the system to filter and present only key points and final results to the user
- Implement context-aware summarization of agent interactions and outputs
- Enhance display of additional information:
  - Links to modified files
  - Diffs of edited files

## Low Priority Features

### Advanced Input System Development (Low Complexity)
- Develop image pasting functionality in the console or from url/path.
- Add conversation history management features (cleaning, switching contexts, etc.)

### Other features
- Regularly review and update the PROJECT_OVERVIEW.md file automatically
- Generate/Convert task list from/into github/gitlab issues
- Chat persistence to resume chat from previous conversation
- Auto-complete configs when using /config command
- Implement structured handling of development and testing dependencies:
  - Create separate requirements files for production, development, and testing
  - Consider using dependency management tools like pip-tools or poetry
  - Update documentation and CI/CD pipelines to reflect the new dependency structure
  - Encourage use of separate virtual environments for different purposes 

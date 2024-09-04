# Prioritized Project Roadmap

## High Priority Features

### 1. Improve Orchestrator's flexibility and feedback mechanism
- Improve task quality and relevance by:
  - Ensuring each task is clearly defined and actionable
  - Aligning tasks with the overall project vision and its current state
  - Define tasks of a proper complexity
- Task management:
  - Make this feature configurable, allowing users to enable or disable it
  - Enable to restart from first incompleted task
  - Task persistence for restoring task lists


### 2. Predefined task list
- Develop a set of pre-defined task lists for common use cases, or prompts to generate whem
- Implement logic for the Orchestrator to identify when these task lists are applicable
- Command to execute pre-defined task list
- Examples of pre-defined task lists:
  - Tell the agent to read relevant files of repository and generate README or other documentation files
  - Identify missing tests and add unit testing
  - Mass refactor over multiples files or entire repo

### 3. Token Usage Tracking and Progress Display
- Create a progress bar or similar visual representation to show total token usage instead of a log

### 4. URL Browse Tool for Agents
- Develop a tool that allows agents to access and browse internet resources

### 5. Chain of throughs
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

### 6. Voice Communication Interface (High Priority, Medium Complexity)
- Implement speech-to-text functionality for user input
- Integrate voice input with existing command-line interface

## Medium Priority Features

### 7. Advanced Output Filtering System enhancement (Low Complexity)
- Improve the system to filter and present only key points and final results to the user
- Implement context-aware summarization of agent interactions and outputs
- Enhance display of additional information:
  - Links to modified files
  - Diffs of edited files

## Low Priority Features

### 8. Advanced Input System Development (Low Complexity)
- Develop image pasting functionality in the console or from url/path.
- Add conversation history management features (cleaning, switching contexts, etc.)

### 9 Other features
- Regularly review and update the PROJECT_OVERVIEW.md file automatically
- Generate/Convert task list from/into github/gitlab issues
- Chat persistence to resume chat from previous conversation

# Prioritized Project Roadmap

## Critical to fix
- "Maximum deflections reached. Stopping" didn't worked and the agent tried to edit the file infinitely.

## High Priority Features

### 1. Improve Orchestrator's flexibility and feedback mechanism (Highest Priority, High Complexity)
- Enhance the Orchestrator's prompt to:
  - Collect feedback with key questions before generating a task list
  - Determine when it has enough information to proceed with task generation
  - Generate tasks that can be completed in 2-3 days of work
  - Ensure tasks are actionable within the current project repository
- Implement adaptive questioning based on requirement complexity:
  - Ask a few key questions to understand the user's requirement
  - Determine if additional questions are necessary before proceeding
  - Balance information gathering with moving forward on task generation
- Improve task quality and relevance by:
  - Ensuring each task is clearly defined and actionable
  - Aligning tasks with the overall project goals and current state
  - Breaking down complex requirements into manageable, discrete tasks
- Add optional confirmation between tasks:
  - Implement a feature to ask for user confirmation before starting each task
  - Make this feature configurable, allowing users to enable or disable it


### 2. Recommended Task List (Coroutines) (High Priority, Medium Complexity)
- Develop a set of pre-defined task lists for common use cases
- Implement logic for the Orchestrator to identify when these task lists are applicable
- Allow for user feedback and customization of recommended task lists
- Examples of pre-defined task lists:
  - Understand repository and document core files
  - Identify missing tests and add unit testing
  - Perform code review and suggest improvements

### 3. Token Usage Tracking and Progress Display
- Create a progress bar or similar visual representation to show token usage instead of a log

### 4. URL Browse Tool for Agents (High Priority, Medium Complexity)
- Develop a tool that allows agents to access and browse internet resources
- Implement safety measures to ensure responsible use of internet access
- Integrate the tool with existing agent workflows

### 5. Repository Understanding Agent (High Priority, High Complexity)
- Develop an agent to fully understand the current repository based on:
  - Augmented context
  - Complex algorithms like GraphRAG
  - AST with metadata
  - Improved documentation

### 6. Voice Communication Interface (High Priority, Medium Complexity)
- Implement speech-to-text functionality for user input
- Integrate voice input with existing command-line interface
- Ensure seamless transition between voice and text inputs

## Medium Priority Features

### 7. Improve inter-agent communication protocols (Low Complexity)
- Enhance the way agents share information and collaborate

### 8. LangGraph Workflow Optimization (Low Complexity)
- Implement advanced state management across multiple agent interactions
- Optimize the flow of information between agents in complex scenarios

### 9. Advanced Output Filtering System enhancement (Low Complexity)
- Improve the system to filter and present only key points and final results to the user
- Implement context-aware summarization of agent interactions and outputs
- Enhance display of additional information:
  - Token usage
  - Links to modified files
  - Diffs of edited files

## Low Priority Features

### 10. Enhanced Testing Framework (Low Complexity)
- Develop comprehensive testing scenarios for the new Orchestrator-centric workflow
- Implement automated testing for core functionalities, focusing on complex, multi-step processes
- Create evaluation metrics for assessing Orchestrator performance and output quality

### 11. Performance Optimization (Low Complexity)
- Analyze and optimize LLM usage across all agents, particularly the Orchestrator
- Implement caching mechanisms for frequently used information
- Optimize the overall system performance and response times for complex workflows

### 12. Advanced Input System Development (Low Complexity)
- Implement a flexible command system with easy addition of new commands
- Develop image pasting functionality in the console
- Create a temp/ folder for saving and managing pasted images
- Implement image encoding for use in LLMs alongside text
- Add conversation history management features (cleaning, switching contexts, etc.)

## Continuous Improvement
- Regularly review and update the PROJECT_OVERVIEW.md file
- Continuously gather user feedback and iterate on features
- Stay updated with advancements in LLM technology and integrate relevant improvements

## Note on Implementation
Each feature should be developed iteratively, focusing on quick deployment of usable functionality that can be easily improved upon. The goal is to unlock the use of each feature as soon as possible, allowing for real-world testing and refinement.
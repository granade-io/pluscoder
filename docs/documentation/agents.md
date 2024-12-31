# Agents

PlusCoder core system relies on agents to perform tasks and provide assistance to the user.

## Features

PlusCoder agents have the following features:

- `Filesystem interaction`: Agents can create/edit files on the repository workspace.
- `File downloading`: Agents can download files from external sources given their raw URLs when instructed to do.
- `Multi-modal support`: Agents can read images passed as input by the user using `img::<img_url>` or pasting an image with Ctrl+V during the conversation.
- `Test and Lint support`: Agents can execute tests and linting commands in the repository workspace and recover from errors.

## Predefined Agents

PlusCoder comes with a set of predefined agents that can be used in your conversations or automated runs.

- `Orchestrator`: Agent that helps you define a task list based plan. It also run the tasks delegating them to other agents until each task is completed.

!!! tip "Using Orchestrator"
    When using the Orchestrator agent, be clear with your intentions. Tell the agent to "create a plan" and to "delegate it" to other agents after reviewing it.


**Example**:
=== "CLI"
    ```bash
    pluscoder \
    --default_agent orchestrator \
    --auto_confirm yes \
    --user_input "I need to refactor main.py into utils.py and config.py; Create a plan with a task to refactor and a second task to add unit tests for new files. Delegate it immediately" 
    ```
=== "In-Chat"
    ```bash
    > You: I need to refactor main.py into utils.py and config.py; Create a plan with a task to refactor and a second task to add unit tests for new files. Show me the plan.
    > Orchestrator: <plan output>
    > You: Delegate it
    ```


- `Developer`: Agent to perform general development tasks through code generation.

!!! tip "Using Developer"
    Developer can read/edit files by itself. You can ask it to generate code, fix errors, or create new files. If you don't want Developer agent to edit files, tell it explicitly.

- `Domain Stakeholder`: Agent useful for discussing project details, design decisions, business requirements, roadmap, etc. It will ask you key questions to help you achieve your goals.

!!! tip "Using Domain Stakeholder"
    Stakeholder can read/edit files the same way as Developer. Talk with it when some inspiration is needed or when you are unsure about how to proceed.

## Custom Agents

Custom agents can be defined using `custom_agents` [configuration](../configuration/#custom-agents) in PlusCoder.

Agents perform better when their instruction are specific to the problem domain we are working on.


### Use Cases
You can use custom agents for:

1. Having custom knowledge and instructions to perform specific tasks:
      1. For example, a `CodeReviewer` agent can be created to review code changes and provide feedback on code quality, best practices, and potential issues.
      2. A `DocstringGenerator` agent can be created to generate docstrings for specified files following a specific format or guidelines.
      3. A `Brainstormer` agent can be created to propose ideas for implementation without editing the codebase.
      4. A `CodeStyleEnforcer` agent can be created to enforce code style guidelines in the codebase.
2. Having experts in different domains:
      1. For example, a `SecurityExpert` agent can be created to review security vulnerabilities in the codebase.
      2. A `VueJsExpert` agent can be created to provide guidance on Vue.js specific problems.
      3. `MyCompanyExpert` agent can be created to provide expert advice on specific aspects of your company's business.
3. Having custom tools and integrations:
      1. For example, a `JiraIntegration` agent can be created to interact with Jira API to create issues, assign tasks, or update issues.
      2. A `SlackIntegration` agent can be created to interact with Slack API to send messages, create channels, or update messages.
      3. A `GithubIssuesIntegration` agent can be created to interact with Github API to create issues, assign tasks, or update issues.

## Related Docs
- [Configuration](configuration.md)
- [CLI Usage](cli.md)

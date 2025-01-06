# Tools

To properly work with a repository, PlusCoder agents have access to a set of tools that help them to perform tasks and instructions. These tools are used to interact with the repository, and more.

## Pre-defined tools

By default all agents have access to the following tools:

| Tool | Description |
|------|-------------|
| read_files | Allows agents to read multiple repository files at once, getting their contents to analyze code and documentation |
| move_files | Enables agents to move multiple files between different locations in the repository structure |
| read_file_from_url | Provides agents capability to read files from external URLs and repository links |
| query_repository | Lets agents search through repository files and code snippets using natural language queries to find relevant information |

Most of the time there is no need to disable these tools, but if you want to do so, you can configure agents to disable some of them:

=== "Python"
    ```python
    from pluscoder.tools import base_tools
    from pluscoder.type import AgentConfig
    from pluscoder.agents.core import DeveloperAgent

    async def main():
        # Override agent default tools
        disabled_tool_names = ['read_files', 'move_files', 'query_repository']
        tool_names = [tool.name for tool in tools.base_tools if tool.name not in disabled_tool_names]
        developer_agent: AgentConfig = DeveloperAgent.to_agent_config(tools=tool_names)
    ```

!!! tip "Specifying tools for custom agents"
    [Custom Agents](configuration.md#custom-agents) can also be configured to use a specific set of tools. By default all pre-defined tools are available.

## Custom tools

In addition to the pre-defined tools, you can create custom tools to extend the capabilities of the agents. Custom tools can be created through Python.

!!! Warning "Custom tools are not available in the interactive mode"
    Custom tools are not available in the interactive mode, but they can be used in the Python API.

Here an example to read open issues and read issue details:

=== "Python"
    ```python
    from langchain_core.tools import tool
    from pluscoder.tools import base_tools
    from pluscoder.type import AgentConfig
    from pluscoder.agents.core import DeveloperAgent
    from pluscoder.workflow import run_agent
    from pluscoder.search.builtin import setup_search_engine

    @tool
    def read_open_repository_issues() -> str:
        "Read most recent open issues from the repository"
        ...
        <logic>
        ...
        return f"Issues: {issues_text}"

    @tool
    def read_issue_details(issue_id: Annotated[int, "Id of the issue to read"] ) -> str:
        "Read details of an issue by its id"
        ...
        <logic>
        ...
        return f"Issue Details: {issue_details}"

    def comment_issue(issue_id: Annotated[int, "Id of the issue to comment"], markdown_comment: Annotated[str, "Markdown comment to add to the issue"]) -> str:
        "Add markdown comments to an specific issue by its id"
        ...
        <logic>
        ...
        return f"Issue with ID {issue_id} has been successfully commented"


    async def main():
        await setup_search_engine(show_progress=True, embedding_model="cohere/embed-english-v3.0")

        # Override agent default tools
        my_tools = tools.base_tools + [read_open_repository_issues, read_issue_details, comment_issue]
        developer_agent: AgentConfig = DeveloperAgent.to_agent_config(tools=my_tools)

        # Run the agent
        await run_agent(
            agent=developer_agent, 
            input="""Read details about last tech debt issue,
        brainstorm about how to solve it and code the proposed solution""",
        )
    ```

## Related Docs
- [Configuration](configuration.md)
- [Agents](agents.md)
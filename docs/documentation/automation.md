# Automation

Automation can be reached in two ways: out-of-the-box using the CLI and through custom python scripts.

## CLI

PlusCoder CLI handles most core functionalities automatically, so you can just give an instruction or task list to agents to work in the repository without any additional code or configuration.

```bash
pluscoder --user_input "List all open issues in the 'pluscoder/pluscoder' repository" --default_agent developer --auto_confirm yes
```

!!! tip
    The `--auto_confirm` flag is used to skip the confirmation steps allowing agents to run freely.

Under the hood:

- CLI reads configuration from different sources
- Repository is indexed using embedding model if its defined
- Detects task list and parses it to run Orchestrator Agent with orchestrated workflow

### Basic examples

#### Basic coding instruction

```bash
pluscoder --user_input "Write unit tests for api/endpoints.py endpoints" --default_agent developer --auto_confirm yes
```

#### Instruction supported with remote guidelines

```bash
pluscoder --user_input "Read the 'Code Style Guide' file at https://github.com/pluscoder/pluscoder/blob/main/docs/CodeStyleGuide.md and apply it to the codebase" --default_agent developer --auto_confirm yes
```

#### Handling multiple repositories

```bash
#!/bin/bash

repositories=("granade-io/pluscoder" "granade-io/pluscoder-docs" "granade-io/pluscoder-cli")

for repo in "${repositories[@]}"; do
    echo "Running PlusCoder for $repo..."
    # PlusCoder will clone the repository
    pluscoder \
        --repository $repo \
        --source_branch develop \
        --user_input "Add README.md file following guidelines at https://github.com/granade-io/pluscoder/blob/main/docs/README-GUIDELINES.md" \
        --default_agent developer \
        --auto_confirm yes \
        --auto_commit false
    cd $repo
    git add README.md
    git commit -m "Add README.md file"
    git push origin develop
    cd ..
done
```

#### Task list for complex instructions

You can define a task list to achieve more complex instructions. Orchestrator agent will handle the task list and delegate tasks to agents until each task is completed.

=== "task_list.json"
```json
{

    "objective": "Update API endpoints documentation",
    "task_list": [
    {
        "objective": "Apply Google Python Style Guide to main app file",
        "details": """
        - Read Python style guide from https://google.github.io/styleguide/pyguide.html
        - Apply formatting rules to app/main.py
        - Fix docstrings format
        - Adjust import order
        - Fix naming conventions
        """,
        "restrictions": "Only modify app/main.py file, keep functionality intact",
        "outcome": "main.py formatted according to Google Python Style Guide",
        "agent": "developer",
        "completed": false,
        "is_finished": false
    },
    {
        "objective": "Update API endpoints documentation",
        "details": """
        - Follow OpenAPI 3.0 spec from https://spec.openapis.org/oas/v3.0.3
        - Update documentation for /users endpoints
        - Update documentation for /auth endpoints
        """,
        "restrictions": "Only modify api/docs/endpoints.yaml file",
        "outcome": "API documentation updated following OpenAPI 3.0 specification",
        "agent": "developer",
        "completed": false,
        "is_finished": false
    }
    ]
}
```

PlusCoder will use the orchestration workflow to delegate tasks to agents:

```bash
pluscoder --task_list task_list.json --auto_confirm yes
```

!!! tip "Task list recommendations"
    Task list are executed sequentially and each agent will work on its task until it's completed. We recommend:
    
    1. Keep tasks simple and focused
    2. Define clear objectives and outcomes
    3. Use restrictions to avoid unwanted changes
    4. Specify involved files and/or guidelines to accomplish the task


## Python

!!! warning
    This feature is still in development.

## Related Docs
- [Configuration](configuration.md)
- [Agents](agents.md)
- [CLI Usage](cli.md)
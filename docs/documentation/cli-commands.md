# Commands

PlusCoder provides several built-in commands to help you manage conversations, repository interactions, and configuration. All commands start with `/`.

## General Commands

| Command&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; | Description |
|:--|:--|
| `/help` | Displays help information for all available commands. |
| `/clear` | Clears the entire chat history with current agent. |
| `/config` | Override any PlusCoder configuration setting.<br><br>**Usage:**<br>`/config <setting_name> <value>`<br><br>**Example:**<br>`/config auto_commits false` |

## Agent Management Commands

| Command&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; | Description |
|:--|:--|
| `/agent` | Start a new conversation with another agent. Can optionally preserve chat history.<br><br>**Usage:**<br>`/agent [agent_name]`<br><br>If no agent name is provided, shows interactive selection. |
| `/agent_create` | Creates a new persistent specialized agent to chat with. Interactive process to define:<br>- Code-base interaction capabilities<br>- File editing permissions<br>- Agent specialization and description |

## Repository Management Commands

| Command&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; | Description |
|:--|:--|
| `/diff` | Shows the diff of the last commit. |
| `/undo` | Reverts last commit and removes messages from history until last user message. |
| `/show_repo` | Displays repository files tree in the current context. |

## Configuration & System Commands

| Command&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; | Description |
|:--|:--|
| `/show_config` | Displays current PlusCoder configuration and config file locations. |
| `/run` | Executes a system command and displays its output.<br><br>**Usage:**<br>`/run <command>`<br><br>**Example:**<br>`/run git status` |

## Custom Prompt Commands

| Command&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; | Description |
|:--|:--|
| `/custom` | Gives the current agent a pre-defined set of instruction including (optional) additional instructions. Check how to define custom instructions at [Custom Prompt Command](configuration.md#custom-prompt-commands) section. <br><br>**Usage:**<br>`/custom <prompt_name> [additional instructions]`<br><br>**Example:**<br>`/custom docstrings files display.py and utils.py` |
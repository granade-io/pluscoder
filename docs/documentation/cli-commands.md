# Commands

PlusCoder provides several built-in commands to help you manage conversations, repository interactions, and configuration. All commands start with `/`.

## Available Commands

### General Commands

#### `/help`

Displays help information for all available commands.

#### `/clear`
Clears the entire chat history with current agent.

#### `/config`
Override any PlusCoder configuration setting.

**Usage:**
```bash
/config <setting_name> <value>
```

**Example:**
```bash
/config auto_commits false
```

### Agent Management

#### `/agent`
Start a new conversation with another agent. Can optionally preserve chat history.

**Usage:**
```bash
/agent [agent_name]
```
If no agent name is provided, shows interactive selection.

#### `/agent_create`
Creates a new persistent specialized agent to chat with. Interactive process to define:
- Code-base interaction capabilities
- File editing permissions
- Agent specialization and description

### Repository Management

#### `/diff`
Shows the diff of the last commit.

#### `/undo`
Reverts last commit and removes messages from history until last user message.

#### `/show_repo`
Displays repository files tree in the current context.

### Configuration & System

#### `/show_config`
Displays current PlusCoder configuration and config file locations.

#### `/run`
Executes a system command and displays its output.

**Usage:**
```bash
/run <command>
```

**Example:**
```bash
/run git status
```

### Custom Commands

#### `/custom`
Executes a custom prompt command defined in configuration.

**Usage:**
```bash
/custom <prompt_name> [additional instructions]
```

**Example:**
```bash
/custom code_review
```
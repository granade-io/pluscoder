import re
import sys
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple
from typing import Type

from pydantic import Field
from pydantic import field_validator
from pydantic_settings import BaseSettings
from pydantic_settings import CliImplicitFlag
from pydantic_settings import PydanticBaseSettingsSource
from pydantic_settings import SettingsConfigDict
from pydantic_settings import YamlConfigSettingsSource
from rich.console import Console


def validate_custom_agents(custom_agents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    console = Console()
    names = set()
    for agent in custom_agents:
        # Check for required fields
        if "name" not in agent:
            console.print("[bold red]Error:[/bold red] Custom agent must have a 'name' field")
            sys.exit(1)
        if "prompt" not in agent:
            console.print(f"[bold red]Error:[/bold red] Custom agent '{agent['name']}' must have a 'prompt' field")
            sys.exit(1)
        if "description" not in agent:
            console.print(f"[bold red]Error:[/bold red] Custom agent '{agent['name']}' must have a 'description' field")
            sys.exit(1)

        # Check for unique names
        if agent["name"] in names:
            console.print(f"[bold red]Error:[/bold red] Duplicate custom agent name: '{agent['name']}'")
            sys.exit(1)
        names.add(agent["name"])

        # Check for non-empty prompt and description
        if not agent["prompt"].strip():
            console.print(f"[bold red]Error:[/bold red] Custom agent '{agent['name']}' has an empty prompt")
            sys.exit(1)
        if not agent["description"].strip():
            console.print(f"[bold red]Error:[/bold red] Custom agent '{agent['name']}' has an empty description")
            sys.exit(1)

        # Check for valid boolean flags
        for flag in ["read_only", "repository_interaction"]:
            if flag in agent and not isinstance(agent[flag], bool):
                console.print(f"[bold red]Error:[/bold red] Custom agent '{agent['name']}': '{flag}' must be a boolean")
                sys.exit(1)

        # Validate other fields
        if "default_context_files" in agent:
            if not isinstance(agent["default_context_files"], list):
                console.print(
                    f"[bold red]Error:[/bold red] Custom agent '{agent['name']}': 'default_context_files' must be a list of repository files"
                )
                sys.exit(1)
            for file in agent["default_context_files"]:
                if not isinstance(file, str):
                    console.print(
                        f"[bold red]Error:[/bold red] Custom agent '{agent['name']}' has an invalid file name in 'default_context_files'"
                    )
                    sys.exit(1)

    return custom_agents


class Settings(BaseSettings):
    def __new__(cls, *args, **kwargs):
        if not hasattr(cls, "_instance"):
            cls._instance = super().__new__(cls)
        return cls._instance

    custom_agents: List[Dict[str, Any]] = Field(
        default=[],
        description="List of custom agents with properties: name, description, prompt, and read_only",
    )

    default_agent: Optional[str] = Field(None, description="Default agent to use")

    @field_validator("custom_agents")
    def validate_custom_agents_field(cls, v):  # noqa: N805
        return validate_custom_agents(v)

    # Application behavior
    init: CliImplicitFlag[bool] = Field(True, description="Enable/disable initial setup")
    initialized: CliImplicitFlag[bool] = Field(False, description="Pluscoder was or not initialized")
    read_only: CliImplicitFlag[bool] = Field(False, description="Enable/disable read-only mode")
    streaming: bool = Field(True, description="Enable/disable LLM streaming")
    user_feedback: bool = Field(True, description="Enable/disable user feedback")
    display_internal_outputs: bool = Field(False, description="Display internal agent outputs")
    auto_confirm: bool = Field(False, description="Enable/disable auto confirmation of pluscoder execution")
    user_input: str = Field("", description="Predefined user input")

    # File paths
    overview_filename: str = Field("PROJECT_OVERVIEW.md", description="Filename for project overview")
    log_filename: str = Field("pluscoder.log", description="Filename for logs")
    overview_file_path: str = Field("PROJECT_OVERVIEW.md", description="Path to the project overview file")
    guidelines_file_path: str = Field("CODING_GUIDELINES.md", description="Path to the coding guidelines file")

    # Model and API settings
    model: Optional[str] = Field(None, description="LLM model to use")
    provider: Optional[str] = Field(
        "openai",
        description="Provider to use. Options: bedrock, openai, anthropic, litellm, null",
    )

    orchestrator_model: Optional[str] = Field(None, description="LLM model to use for orchestrator")
    orchestrator_model_provider: Optional[str] = Field(None, description="Provider to use for orchestrator model")

    weak_model: Optional[str] = Field(None, description="Weaker LLM model to use for less complex tasks")
    weak_model_provider: Optional[str] = Field(None, description="Provider to use for weak model")

    # Providers API keys
    # OpenAI API keys
    openai_api_key: Optional[str] = Field(None, description="OpenAI API key")
    openai_api_base: Optional[str] = Field(None, description="OpenAI API base URL")

    # Anthropic API keys
    anthropic_api_key: Optional[str] = Field(None, description="Anthropic API key")

    # AWS IAM keys
    aws_access_key_id: Optional[str] = Field(None, description="AWS Access Key ID")
    aws_secret_access_key: Optional[str] = Field(None, description="AWS Secret Access Key")
    aws_profile: str = Field("default", description="AWS profile name")

    # Git settings
    auto_commits: bool = Field(False, description="Enable/disable automatic Git commits")
    allow_dirty_commits: bool = Field(False, description="Allow commits in a dirty repository")

    # Test and Lint settings
    run_tests_after_edit: bool = Field(False, description="Run tests after file edits")
    run_lint_after_edit: bool = Field(False, description="Run linter after file edits")
    test_command: Optional[str] = Field(None, description="Command to run tests")
    lint_command: Optional[str] = Field(None, description="Command to run linter")
    auto_run_linter_fix: bool = Field(False, description="Automatically run linter fix before linting")
    lint_fix_command: Optional[str] = Field(None, description="Command to run linter fix")

    # Repomap settings
    use_repomap: bool = Field(False, description="Enable/disable repomap feature")
    repomap_level: int = Field(2, description="Set the level of detail for repomap")
    repomap_exclude_files: List[str] = Field([], description="List of files to exclude from repomap")
    repo_exclude_files: List[str] = Field(
        [], description="List of regex patterns to exclude files from repo operations"
    )

    # Show args
    show_repo: CliImplicitFlag[bool] = Field(False, description="Show repository information")
    show_repomap: CliImplicitFlag[bool] = Field(False, description="Show repository map")
    show_config: CliImplicitFlag[bool] = Field(False, description="Show repository information")
    show_token_usage: CliImplicitFlag[bool] = Field(True, description="Show token usage/cost")

    # Output display settings
    hide_thinking_blocks: CliImplicitFlag[bool] = Field(True, description="Hide thinking blocks in LLM output")
    hide_output_blocks: CliImplicitFlag[bool] = Field(False, description="Hide output blocks in LLM output")
    hide_source_blocks: CliImplicitFlag[bool] = Field(True, description="Hide source blocks in LLM output")

    # Debug mode
    debug: CliImplicitFlag[bool] = Field(False, description="Enable debug mode")

    # Custom prompt commands
    custom_prompt_commands: List[Dict[str, Any]] = Field(
        default=[],
        description="Custom prompt commands with prompt_name, description, and prompt",
    )

    model_config = SettingsConfigDict(
        extra="ignore",
        env_file=".env",
        env_file_encoding="utf-8",
        cli_parse_args=True,
        case_sensitive=False,
        yaml_file=".pluscoder-config.yml",
        yaml_file_encoding="utf-8",
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: Type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> Tuple[PydanticBaseSettingsSource, ...]:
        if not init_settings.init_kwargs.get("ignore_yaml", False):
            yaml_config = YamlConfigSettingsSource(settings_cls)
            return init_settings, dotenv_settings, yaml_config, env_settings
        return init_settings, dotenv_settings, env_settings

    def update(self, persist: bool = False, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

        if persist:
            config_file = ".pluscoder-config.yml"
            with open(config_file) as f:
                config_text = f.read()

            for option, value in kwargs.items():
                config_text = re.sub(
                    rf"^#?\s*{option}:.*$",
                    f"{option}: {value}",
                    config_text,
                    flags=re.MULTILINE,
                )

            with open(config_file, "w") as f:
                f.write(config_text)

        # Re-execute initialization
        new_config = {key: getattr(self, key) for key in self.__fields__}
        self.__init__(**new_config)


def get_settings():
    return Settings()


# Usage
config = get_settings()
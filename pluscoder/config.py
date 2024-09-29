import os
import argparse
import dotenv
from typing import Any, Dict, List

dotenv.load_dotenv(dotenv.find_dotenv(usecwd=True), override=True)

def str2bool(v: Any) -> bool:
    if isinstance(v, bool):
        return v
    if isinstance(v, str):
        return v.lower() in ("yes", "true", "t", "1")
    return bool(v)

def str2list(v: Any) -> List[str]:
    if isinstance(v, list):
        return v
    if isinstance(v, str):
        return [item.strip() for item in v.split(',') if item.strip()]
    return []

class Config:

    def __new__(cls):
        if not hasattr(cls, '_instance'):
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        # Initialize with default values
        # Application behavior
        self.streaming = True
        self.user_feedback = True
        self.display_internal_outputs = False
        self.auto_confirm = False
        self.user_input = ""
        
        # New command line arguments
        self.show_repo = False
        self.show_repomap = False
        self.show_config = False

        # File paths
        self.overview_filename = "PROJECT_OVERVIEW.md"
        self.log_filename = "pluscoder.log"
        self.overview_file_path = "PROJECT_OVERVIEW.md"
        self.guidelines_file_path = "CODING_GUIDELINES.md"

        # Model and API settings
        self.model = "anthropic.claude-3-5-sonnet-20240620-v1:0"
        self.openai_api_key = None
        self.openai_api_base = None
        self.provider = None
        self.anthropic_api_key = None

        # AWS settings
        self.aws_access_key_id = None
        self.aws_secret_access_key = None
        self.aws_profile = "default"

        # Git settings
        self.auto_commits = True
        self.allow_dirty_commits = True

        # Test and Lint settings
        self.run_tests_after_edit = False
        self.run_lint_after_edit = False
        self.test_command = None
        self.lint_command = None
        self.auto_run_linter_fix = False
        self.lint_fix_command = None

        # Repomap settings
        self.use_repomap = False
        self.repomap_level = 2
        self.repomap_exclude_files = []
        self.repomap_include_files = []
        self.repo_exclude_files = []

    def update_from_env(self):
        for key in vars(self):
            env_var = f"{key.upper()}"
            if env_var in os.environ:
                value = os.environ[env_var]
                if isinstance(getattr(self, key), bool):
                    setattr(self, key, str2bool(value))
                elif isinstance(getattr(self, key), list):
                    setattr(self, key, str2list(value))
                else:
                    default = getattr(self, key)
                    setattr(self, key, type(default)(value) if default else value)

    def update_from_args(self, args: Dict[str, Any]):
        for key, value in args.items():
            if value is not None:
                if isinstance(getattr(self, key), bool):
                    setattr(self, key, str2bool(value))
                elif isinstance(getattr(self, key), list):
                    setattr(self, key, str2list(value))
                else:
                    setattr(self, key, value)

    def update_config(self, key: str, value: Any) -> bool:
        if hasattr(self, key):
            current_value = getattr(self, key)
            if isinstance(current_value, bool):
                new_value = str2bool(value)
                setattr(self, key, new_value)
            else:
                new_value = type(current_value)(value)
                setattr(self, key, new_value)
            return new_value
        return False

def parse_args():
    parser = argparse.ArgumentParser(description="PlusCoder Configuration")
    # Application behavior
    parser.add_argument("--streaming", type=str2bool, default=None, help="Enable/disable LLM streaming")
    parser.add_argument("--user-feedback", type=str2bool, default=None, help="Enable/disable user feedback")
    parser.add_argument("--display-internal-outputs", type=str2bool, default=None, help="Display internal agent outputs")
    parser.add_argument("--auto-confirm", type=str2bool, default=None, help="Enable/disable auto confirmation of pluscoder execution")
    parser.add_argument("--user-input", type=str, default="", help="Predefined user input")

    # New command line arguments
    parser.add_argument("--show-repo", action="store_true", help="Show repository information")
    parser.add_argument("--show-repomap", action="store_true", help="Show repository map")
    parser.add_argument("--show-config", action="store_true", help="Show current configuration")

    # File paths
    parser.add_argument("--overview-filename", type=str, default=None, help="Filename for project overview")
    parser.add_argument("--log-filename", type=str, default=None, help="Filename for logs")
    parser.add_argument("--overview-file-path", type=str, default=None, help="Path to the project overview file")
    parser.add_argument("--guidelines-file-path", type=str, default=None, help="Path to the coding guidelines file")

    # Model and API settings
    parser.add_argument("--model", type=str, default=None, help="LLM model to use")
    parser.add_argument("--provider", type=str, default=None, help="Prvider to use. Options: aws_bedrock, openai, litellm, anthropic")
    parser.add_argument("--openai-api-key", type=str, default=None, help="OpenAI API key")
    parser.add_argument("--openai-api-base", type=str, default=None, help="OpenAI API base URL")
    parser.add_argument("--anthropic-api-key", type=str, default=None, help="Anthropic API key")

    # AWS settings
    parser.add_argument("--aws-access-key-id", type=str, default=None, help="AWS Access Key ID")
    parser.add_argument("--aws-secret-access-key", type=str, default=None, help="AWS Secret Access Key")
    parser.add_argument("--aws-profile", type=str, default=None, help="AWS profile name")

    # Git settings
    parser.add_argument("--auto-commits", type=str2bool, default=None, help="Enable/disable automatic Git commits")
    parser.add_argument("--allow-dirty-commits", type=str2bool, default=None, help="Allow commits in a dirty repository")

    # Test and Lint settings
    parser.add_argument("--run-tests-after-edit", type=str2bool, default=None, help="Run tests after file edits")
    parser.add_argument("--run-lint-after-edit", type=str2bool, default=None, help="Run linter after file edits")
    parser.add_argument("--test-command", type=str, default=None, help="Command to run tests")
    parser.add_argument("--lint-command", type=str, default=None, help="Command to run linter")
    parser.add_argument("--auto-run-linter-fix", type=str2bool, default=None, help="Automatically run linter fix before linting")
    parser.add_argument("--lint-fix-command", type=str, default=None, help="Command to run linter fix")

    # Repomap settings
    parser.add_argument("--use-repomap", type=str2bool, default=None, help="Enable/disable repomap feature")
    parser.add_argument("--repomap-level", type=int, default=None, help="Set the level of detail for repomap")
    parser.add_argument("--repomap-exclude-files", type=str2list, default=None, help="Comma-separated list of files to exclude from repomap")
    parser.add_argument("--repo-exclude-files", type=str2list, default=None, help="Comma-separated list of regex patterns to exclude files from repo operations")

    return parser.parse_args()

def get_config(reset=False) -> Config:
    config = Config()
    if reset:
        config._initialize()
    config.update_from_env()
    args = vars(parse_args())
    config.update_from_args(args)
    return config

config = get_config()

# Usage example:
# from pluscoder.config import config
# if config.streaming:
#     # Do something with streaming enabled

if __name__ == "__main__":
    print(f"Current configuration with {dotenv.find_dotenv(usecwd=True)}:")
    for key, value in vars(config).items():
        print(f"{key}: {value}")
import os
import argparse
import dotenv
from typing import Any, Dict

dotenv.load_dotenv(dotenv.find_dotenv(usecwd=True), override=True)

def str2bool(v: Any) -> bool:
    if isinstance(v, bool):
        return v
    if isinstance(v, str):
        return v.lower() in ("yes", "true", "t", "1")
    return bool(v)

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

    def update_from_env(self):
        for key in vars(self):
            env_var = f"{key.upper()}"
            if env_var in os.environ:
                value = os.environ[env_var]
                if isinstance(getattr(self, key), bool):
                    setattr(self, key, str2bool(value))
                else:
                    default = getattr(self, key)
                    setattr(self, key, type(default)(value) if default else value)

    def update_from_args(self, args: Dict[str, Any]):
        for key, value in args.items():
            if value is not None:
                if isinstance(getattr(self, key), bool):
                    setattr(self, key, str2bool(value))
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
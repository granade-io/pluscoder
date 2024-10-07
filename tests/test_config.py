import os
import sys
from unittest.mock import patch
from pluscoder.config import Settings


def test_config_default_values():
    with patch.object(sys, "argv", ["config.py"]):
        config = Settings(_env_file=None, ignore_yaml=True)
        assert config.streaming is True
        assert config.user_feedback is True
        assert config.display_internal_outputs is False
        assert config.overview_filename == "PROJECT_OVERVIEW.md"
        assert config.log_filename == "pluscoder.log"


def test_update_from_env():
    with patch.dict(
        os.environ,
        {
            "MODEL": "my_model",
            "STREAMING": "true",
            "USER_FEEDBACK": "false",
            "DISPLAY_INTERNAL_OUTPUTS": "true",
            "OVERVIEW_FILENAME": "test_overview.md",
            "LOG_FILENAME": "test.log",
        },
        clear=True,
    ):
        with patch.object(sys, "argv", ["config.py"]):
            config = Settings(_env_file=None, ignore_yaml=True)
            assert config.model == "my_model"
            assert config.streaming is True
            assert config.user_feedback is False
            assert config.display_internal_outputs is True
            assert config.overview_filename == "test_overview.md"
            assert config.log_filename == "test.log"


def test_update_from_args():
    test_args = [
        "--streaming=true",
        "--user_feedback=false",
        "--display_internal_outputs=true",
        "--overview_filename=args_overview.md",
        "--log_filename=args.log",
    ]
    with patch.object(sys, "argv", [] + test_args):
        config = Settings(_env_file=None, ignore_yaml=True)
        assert config.streaming is True
        assert config.user_feedback is False
        assert config.display_internal_outputs is True
        assert config.overview_filename == "args_overview.md"
        assert config.log_filename == "args.log"


def test_config_precedence():
    with patch.dict(
        os.environ,
        {
            "STREAMING": "false",
            "USER_FEEDBACK": "false",
            "DISPLAY_INTERNAL_OUTPUTS": "false",
            "OVERVIEW_FILENAME": "env_overview.md",
            "LOG_FILENAME": "env.log",
        },
        clear=True,
    ):
        with patch.object(
            sys,
            "argv",
            ["config.py", "--streaming=true", "--display_internal_outputs=true"],
        ):
            config = Settings(_env_file=None, ignore_yaml=True)

            # Command-line args should take precedence over env vars
            assert config.streaming is True
            # Env vars should take precedence over default values
            assert config.user_feedback is False
            # Command-line args should take precedence over env vars
            assert config.display_internal_outputs is True
            # Env vars should take precedence over default values when not specified in command-line
            assert config.overview_filename == "env_overview.md"
            assert config.log_filename == "env.log"


def test_config_precedence_empty_configs():
    # Test default values when neither env vars nor command-line args are provided
    with patch.dict(os.environ, {}, clear=True):
        with patch.object(sys, "argv", ["config.py"]):
            config = Settings(_env_file=None, ignore_yaml=True)
            assert config.streaming is True
            assert config.user_feedback is True
            assert config.display_internal_outputs is False
            assert config.overview_filename == "PROJECT_OVERVIEW.md"
            assert config.log_filename == "pluscoder.log"

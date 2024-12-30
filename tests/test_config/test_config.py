import os
import sys
from unittest.mock import patch

import pytest

from pluscoder.config import Settings


@pytest.fixture
def clear_env(monkeypatch):
    # Backup the original environment
    original_env = os.environ.copy()
    # Clear all environment variables
    monkeypatch.setattr(os, "environ", {})

    # Restore the environment after the test
    yield
    os.environ.update(original_env)


def test_config_default_values():
    with patch.object(sys, "argv", ["config.py"]):
        config = Settings(_env_file=None, ignore_instances=True)
        assert config.streaming is True
        assert config.user_feedback is True
        assert config.display_internal_outputs is False
        assert config.log_filename == "pluscoder.log"


def test_update_from_env():
    with patch.dict(
        os.environ,
        {
            "MODEL": "my_model",
            "STREAMING": "true",
            "USER_FEEDBACK": "false",
            "DISPLAY_INTERNAL_OUTPUTS": "true",
            "LOG_FILENAME": "test.log",
        },
        clear=True,
    ):
        with patch.object(sys, "argv", ["config.py"]):
            config = Settings(_env_file=None, ignore_instances=True)
            assert config.model == "my_model"
            assert config.streaming is True
            assert config.user_feedback is False
            assert config.display_internal_outputs is True
            assert config.log_filename == "test.log"


def test_update_from_args():
    test_args = [
        "--streaming=true",
        "--user_feedback=false",
        "--display_internal_outputs=true",
        "--log_filename=args.log",
    ]
    with patch.object(sys, "argv", [] + test_args):
        config = Settings(_env_file=None, ignore_instances=True)
        assert config.streaming is True
        assert config.user_feedback is False
        assert config.display_internal_outputs is True
        assert config.log_filename == "args.log"


def test_config_precedence():
    with patch.dict(
        os.environ,
        {
            "STREAMING": "false",
            "USER_FEEDBACK": "false",
            "DISPLAY_INTERNAL_OUTPUTS": "false",
            "LOG_FILENAME": "env.log",
        },
        clear=True,
    ):
        with patch.object(
            sys,
            "argv",
            ["config.py", "--streaming=true", "--display_internal_outputs=true"],
        ):
            config = Settings(_env_file=None, ignore_instances=True)

            # Command-line args should take precedence over env vars
            assert config.streaming is True
            # Env vars should take precedence over default values
            assert config.user_feedback is False
            # Command-line args should take precedence over env vars
            assert config.display_internal_outputs is True
            # Env vars should take precedence over default values when not specified in command-line
            assert config.log_filename == "env.log"


def test_config_precedence_empty_configs(clear_env):
    # Test default values when neither env vars nor command-line args are provided
    with patch.dict(os.environ, {}, clear=True):
        with patch.object(sys, "argv", ["config.py"]):
            config = Settings(_env_file=None, ignore_instances=True)
            assert config.streaming is True
            assert config.user_feedback is True
            assert config.display_internal_outputs is False
            assert config.log_filename == "pluscoder.log"


def test_update_method_non_persisting(clear_env):
    with patch.object(sys, "argv", ["config.py"]):
        config = Settings(_env_file=None, ignore_instances=True)

        # Initial values
        assert config.streaming is True
        assert config.model is None

        # Update without persisting
        config.update(streaming=False, model="new-model", persist=False)

        # Check if values are updated in the instance
        assert config.streaming is False
        assert config.model == "new-model"

        # Ensure YAML file hasn't been modified
        with open(".pluscoder-config.yml", "r") as f:
            yaml_content = f.read()
        assert "streaming: false" not in yaml_content
        assert "model: new-model" not in yaml_content

        # Re-initialize to check if changes persist
        new_config = Settings(_env_file=None, ignore_instances=True)
        assert new_config.streaming is True
        assert new_config.model is None

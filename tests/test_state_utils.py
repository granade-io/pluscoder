from typing import TYPE_CHECKING
from unittest.mock import patch

from pluscoder.state_utils import accumulate_token_usage
from pluscoder.state_utils import sum_token_usage

if TYPE_CHECKING:
    from pluscoder.type import OrchestrationState
    from pluscoder.type import TokenUsage


@patch("pluscoder.state_utils.get_model_token_info")
def test_sum_token_usage(mock_get_model_token_info):
    mock_get_model_token_info.return_value = None
    accumulated: TokenUsage = {
        "prompt_tokens": 100,
        "completion_tokens": 50,
        "total_tokens": 150,
        "total_cost": 0.001,
    }
    new: TokenUsage = {
        "prompt_tokens": 200,
        "completion_tokens": 100,
        "total_tokens": 300,
        "total_cost": 0.002,
    }
    result = sum_token_usage(accumulated, new)
    assert result == {
        "prompt_tokens": 300,
        "completion_tokens": 150,
        "total_tokens": 450,
        "total_cost": 0.003,
    }


@patch("pluscoder.state_utils.get_model_token_info")
def test_accumulate_token_usage(mock_get_model_token_info):
    mock_get_model_token_info.return_value = None
    global_state: OrchestrationState = {
        "accumulated_token_usage": {
            "prompt_tokens": 100,
            "completion_tokens": 50,
            "total_tokens": 150,
            "total_cost": 0.001,
        }
    }
    agent_state: OrchestrationState = {
        "token_usage": {
            "prompt_tokens": 200,
            "completion_tokens": 100,
            "total_tokens": 300,
            "total_cost": 0.002,
        }
    }

    result = accumulate_token_usage(global_state, agent_state)

    assert result == {
        "accumulated_token_usage": {
            "prompt_tokens": 300,
            "completion_tokens": 150,
            "total_tokens": 450,
            "total_cost": 0.003,
        },
        "token_usage": None,
    }


def test_accumulate_token_usage_no_token_usage():
    global_state: OrchestrationState = {}
    agent_state: OrchestrationState = {}

    result = accumulate_token_usage(global_state, agent_state)

    assert result == {}


@patch("pluscoder.state_utils.get_model_token_info")
def test_accumulate_token_usage_empty_global_state(mock_get_model_token_info):
    mock_get_model_token_info.return_value = None
    global_state: OrchestrationState = {}
    agent_state: OrchestrationState = {
        "token_usage": {
            "prompt_tokens": 200,
            "completion_tokens": 100,
            "total_tokens": 300,
            "total_cost": 0.002,
        }
    }

    result = accumulate_token_usage(global_state, agent_state)

    assert result == {
        "accumulated_token_usage": {
            "prompt_tokens": 200,
            "completion_tokens": 100,
            "total_tokens": 300,
            "total_cost": 0.002,
        },
        "token_usage": None,
    }


@patch("pluscoder.state_utils.get_model_token_info")
def test_accumulate_token_usage_with_none_model_info(mock_get_model_token_info):
    mock_get_model_token_info.return_value = None
    global_state: OrchestrationState = {}
    agent_state: OrchestrationState = {
        "token_usage": {
            "prompt_tokens": 200,
            "completion_tokens": 100,
            "total_tokens": 300,
            "total_cost": 0.002,
        }
    }

    result = accumulate_token_usage(global_state, agent_state)

    assert result == {
        "accumulated_token_usage": {
            "prompt_tokens": 200,
            "completion_tokens": 100,
            "total_tokens": 300,
            "total_cost": 0.002,
        },
        "token_usage": None,
    }


@patch("pluscoder.state_utils.get_model_token_info")
def test_accumulate_token_usage_with_model_info(mock_get_model_token_info):
    mock_get_model_token_info.return_value = {
        "input_cost_per_token": 0.00001,
        "output_cost_per_token": 0.00002,
    }
    global_state: OrchestrationState = {}
    agent_state: OrchestrationState = {
        "token_usage": {
            "prompt_tokens": 200,
            "completion_tokens": 100,
            "total_tokens": 300,
        }
    }

    result = accumulate_token_usage(global_state, agent_state)

    expected_cost = 200 * 0.00001 + 100 * 0.00002
    assert result == {
        "accumulated_token_usage": {
            "prompt_tokens": 200,
            "completion_tokens": 100,
            "total_tokens": 300,
            "total_cost": expected_cost,
        },
        "token_usage": None,
    }

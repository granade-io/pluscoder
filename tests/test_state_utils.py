import pytest
from unittest.mock import patch, MagicMock
from pluscoder.state_utils import print_token_usage, sum_token_usage, accumulate_token_usage
from pluscoder.type import TokenUsage, OrchestrationState, AgentState

def test_print_token_usage(capsys):
    token_usage: TokenUsage = {
        "prompt_tokens": 100,
        "completion_tokens": 50,
        "total_tokens": 150,
        "total_cost": 0.00123456
    }
    print_token_usage(token_usage)
    captured = capsys.readouterr()
    assert captured.out.strip() == "Tokens: ↑:100 ↓:50 T:150 $0.00123456"

def test_sum_token_usage():
    accumulated: TokenUsage = {
        "prompt_tokens": 100,
        "completion_tokens": 50,
        "total_tokens": 150,
        "total_cost": 0.001
    }
    new: TokenUsage = {
        "prompt_tokens": 200,
        "completion_tokens": 100,
        "total_tokens": 300,
        "total_cost": 0.002
    }
    result = sum_token_usage(accumulated, new)
    assert result == {
        "prompt_tokens": 300,
        "completion_tokens": 150,
        "total_tokens": 450,
        "total_cost": 0.003
    }

def test_accumulate_token_usage():
    global_state: OrchestrationState = {
        "accumulated_token_usage": {
            "prompt_tokens": 100,
            "completion_tokens": 50,
            "total_tokens": 150,
            "total_cost": 0.001
        }
    }
    agent_state: AgentState = {
        "token_usage": {
            "prompt_tokens": 200,
            "completion_tokens": 100,
            "total_tokens": 300,
            "total_cost": 0.002
        }
    }
    
    with patch('pluscoder.state_utils.print_token_usage') as mock_print:
        result = accumulate_token_usage(global_state, agent_state)
    
    assert result == {
        "accumulated_token_usage": {
            "prompt_tokens": 300,
            "completion_tokens": 150,
            "total_tokens": 450,
            "total_cost": 0.003
        }
    }
    mock_print.assert_called_once_with({
        "prompt_tokens": 300,
        "completion_tokens": 150,
        "total_tokens": 450,
        "total_cost": 0.003
    })

def test_accumulate_token_usage_no_token_usage():
    global_state: OrchestrationState = {}
    agent_state: AgentState = {}
    
    result = accumulate_token_usage(global_state, agent_state)
    
    assert result == {}

def test_accumulate_token_usage_empty_global_state():
    global_state: OrchestrationState = {}
    agent_state: AgentState = {
        "token_usage": {
            "prompt_tokens": 200,
            "completion_tokens": 100,
            "total_tokens": 300,
            "total_cost": 0.002
        }
    }
    
    with patch('pluscoder.state_utils.print_token_usage') as mock_print:
        result = accumulate_token_usage(global_state, agent_state)
    
    assert result == {
        "accumulated_token_usage": {
            "prompt_tokens": 200,
            "completion_tokens": 100,
            "total_tokens": 300,
            "total_cost": 0.002
        }
    }
    mock_print.assert_called_once_with({
        "prompt_tokens": 200,
        "completion_tokens": 100,
        "total_tokens": 300,
        "total_cost": 0.002
    })
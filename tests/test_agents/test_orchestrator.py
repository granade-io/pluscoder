import pytest
from pluscoder.agents.orchestrator import OrchestratorAgent
from pluscoder.agents.base import AgentState
from langchain_core.messages import HumanMessage, AIMessage
from pluscoder import tools

@pytest.fixture
def orchestrator_agent():
    return OrchestratorAgent(llm=None)  # We don't need a real LLM for these tests

def test_is_agent_response_empty_state(orchestrator_agent):
    state = AgentState(messages=[])
    assert not orchestrator_agent.is_agent_response(state)

def test_is_agent_response_human_message(orchestrator_agent):
    state = AgentState(messages=[HumanMessage(content="Hello")])
    assert not orchestrator_agent.is_agent_response(state)

def test_is_agent_response_ai_message(orchestrator_agent):
    state = AgentState(messages=[AIMessage(content="Hello")])
    assert orchestrator_agent.is_agent_response(state)

def test_is_agent_response_mixed_messages(orchestrator_agent):
    state = AgentState(messages=[
        HumanMessage(content="Hello"),
        AIMessage(content="Hi there"),
        HumanMessage(content="How are you?")
    ])
    assert not orchestrator_agent.is_agent_response(state)

def test_get_current_task_no_tool_data(orchestrator_agent):
    state = AgentState()
    assert orchestrator_agent.get_current_task(state) is None

def test_get_current_task_empty_task_list(orchestrator_agent):
    state = AgentState(tool_data={tools.delegate_tasks.name: {"args": {"task_list": []}}})
    assert orchestrator_agent.get_current_task(state) is None

def test_get_current_task_all_finished(orchestrator_agent):
    state = AgentState(tool_data={
        tools.delegate_tasks.name: {
            "task_list": [
                {"is_finished": True},
                {"is_finished": True}
            ]
        }
    })
    assert orchestrator_agent.get_current_task(state) is None

def test_get_current_task_unfinished_task(orchestrator_agent):
    unfinished_task = {"is_finished": False, "description": "Unfinished task"}
    state = AgentState(tool_data={
        tools.delegate_tasks.name: {
            "task_list": [
                {"is_finished": True},
                unfinished_task,
                {"is_finished": False}
            ]
        }
    })
    assert orchestrator_agent.get_current_task(state) == unfinished_task
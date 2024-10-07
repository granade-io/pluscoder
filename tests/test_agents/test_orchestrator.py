import pytest
from pluscoder.agents.orchestrator import OrchestratorAgent
from pluscoder.agents.base import AgentState
from langchain_core.messages import AIMessage
from pluscoder.message_utils import HumanMessage
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
    state = AgentState(
        messages=[
            HumanMessage(content="Hello"),
            AIMessage(content="Hi there"),
            HumanMessage(content="How are you?"),
        ]
    )
    assert not orchestrator_agent.is_agent_response(state)


def test_get_current_task_no_tool_data(orchestrator_agent):
    state = AgentState()
    assert orchestrator_agent.get_current_task(state) is None


def test_get_current_task_empty_task_list(orchestrator_agent):
    state = AgentState(
        tool_data={
            tools.delegate_tasks.name: {"args": {"task_list": [], "resources": []}}
        }
    )
    assert orchestrator_agent.get_current_task(state) is None


def test_get_current_task_all_finished(orchestrator_agent):
    state = AgentState(
        tool_data={
            tools.delegate_tasks.name: {
                "task_list": [{"is_finished": True}, {"is_finished": True}]
            }
        }
    )
    assert orchestrator_agent.get_current_task(state) is None


def test_get_current_task_unfinished_task(orchestrator_agent):
    unfinished_task = {"is_finished": False, "description": "Unfinished task"}
    state = AgentState(
        tool_data={
            tools.delegate_tasks.name: {
                "task_list": [
                    {"is_finished": True},
                    unfinished_task,
                    {"is_finished": False},
                ]
            }
        }
    )
    assert orchestrator_agent.get_current_task(state) == unfinished_task


def test_get_completed_tasks_no_tool_data(orchestrator_agent):
    state = AgentState()
    assert orchestrator_agent.get_completed_tasks(state) == []


def test_get_completed_tasks_empty_task_list(orchestrator_agent):
    state = AgentState(tool_data={tools.delegate_tasks.name: {"task_list": []}})
    assert orchestrator_agent.get_completed_tasks(state) == []


def test_get_completed_tasks_mixed(orchestrator_agent):
    state = AgentState(
        tool_data={
            tools.delegate_tasks.name: {
                "task_list": [
                    {"is_finished": True, "objective": "Task 1"},
                    {"is_finished": False, "objective": "Task 2"},
                    {"is_finished": True, "objective": "Task 3"},
                ]
            }
        }
    )
    completed_tasks = orchestrator_agent.get_completed_tasks(state)
    assert len(completed_tasks) == 2
    assert completed_tasks[0]["objective"] == "Task 1"
    assert completed_tasks[1]["objective"] == "Task 3"


def test_task_to_instruction_no_completed_tasks(orchestrator_agent):
    task = {"objective": "Current task", "details": "Task details"}
    state = AgentState(
        tool_data={
            tools.delegate_tasks.name: {
                "general_objective": "Objective",
                "task_list": [],
                "resources": [],
            }
        }
    )
    instruction = orchestrator_agent.task_to_instruction(task, state)
    assert "Current task" in instruction
    assert "Task details" in instruction
    assert "Context (completed tasks):" in instruction
    assert "Completed:" not in instruction


def test_task_to_instruction_with_completed_tasks(orchestrator_agent):
    task = {"objective": "Current task", "details": "Task details"}
    state = AgentState(
        tool_data={
            tools.delegate_tasks.name: {
                "general_objective": "Objective",
                "task_list": [
                    {
                        "is_finished": True,
                        "objective": "Completed task 1",
                        "details": "Details 1",
                    },
                    {
                        "is_finished": True,
                        "objective": "Completed task 2",
                        "details": "Details 2",
                    },
                    {
                        "is_finished": False,
                        "objective": "Current task",
                        "details": "Task details",
                    },
                ],
                "resources": [],
            }
        }
    )
    instruction = orchestrator_agent.task_to_instruction(task, state)
    assert "Current task" in instruction
    assert "Task details" in instruction
    assert "Context (completed tasks):" in instruction
    assert "Completed: Completed task 1" in instruction
    assert "Details 1" in instruction
    assert "Completed: Completed task 2" in instruction
    assert "Details 2" in instruction

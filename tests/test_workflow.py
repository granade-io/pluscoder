from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from langchain_core.messages import AIMessage
from langchain_core.messages import ToolMessage
from langgraph.prebuilt import ToolNode

from pluscoder import tools
from pluscoder.agents.base import Agent
from pluscoder.agents.orchestrator import OrchestratorAgent
from pluscoder.agents.stream_parser import XMLStreamParser
from pluscoder.config import config
from pluscoder.message_utils import HumanMessage
from pluscoder.type import AgentConfig
from pluscoder.type import OrchestrationState
from pluscoder.type import TokenUsage
from pluscoder.workflow import build_workflow
from pluscoder.workflow import run_workflow


@pytest.fixture
def mock_agents_config():
    return {
        "orchestrator": AgentConfig(
            id=OrchestratorAgent.id,
            name="Orchestrator",
            description="Design and run complex plan delegating it to other agents",
            prompt=OrchestratorAgent.specialization_prompt,
            reminder="",
            tools=[],
            default_context_files=[],
            repository_interaction=True,
            provider="openai",
            model="gpt-4o",
        ),
        "developer": AgentConfig(
            id="developer",
            name="Developer",
            description="Test developer",
            prompt="Test prompt",
            reminder="",
            tools=[],
            default_context_files=[],
            repository_interaction=True,
            provider="openai",
            model="gpt-4o",
        ),
    }


@pytest.fixture
def agent():
    return Agent(
        AgentConfig(
            prompt="You are a helpful assistant.",
            name="TestAgent",
            id="developer",
            description="Description",
            reminder="",
            tools=[],
            default_context_files=["test_file.txt"],
            repository_interaction=True,
            provider="openai",
            model="gpt-4o",
        ),
        stream_parser=XMLStreamParser(),
    )


@pytest.fixture
def orchestrator_agent(mock_agents_config):
    return OrchestratorAgent(
        mock_agents_config["orchestrator"],
        extraction_tools=[tools.delegate_tasks, tools.is_task_completed],
        stream_parser=XMLStreamParser(),
    )


@pytest.mark.asyncio
@patch("pluscoder.model.get_llm")
@patch("pluscoder.workflow.accumulate_token_usage")
@patch.object(Agent, "_invoke_llm_chain")
async def test_workflow_with_mocked_llm(
    mock_invoke_llm_chain, mock_accumulate_token_usage, mock_get_llm, orchestrator_agent, agent, mock_agents_config
):
    # Mock the LLM response
    mock_llm = MagicMock()
    mock_get_llm.return_value = mock_llm

    # Mock _invoke_llm_chain to return a mocked AIMessage
    mock_invoke_llm_chain.return_value = AIMessage(content="Mocked LLM response")

    # Mock accumulate_token_usage to return the state unchanged
    mock_accumulate_token_usage.side_effect = lambda state, _: state

    # Set up the initial state
    initial_state = OrchestrationState(
        max_iterations=1,
        current_iterations=0,
        return_to_user=False,
        messages=[],
        context_files=[],
        chat_agent=mock_agents_config["developer"],
        is_task_list_workflow=False,
        accumulated_token_usage=TokenUsage(prompt_tokens=0, completion_tokens=0, total_tokens=0, total_cost=0.0),
        agents_configs=mock_agents_config,
    )

    # Set user input for testing
    config.user_input = "Test input"

    # Build workflow
    app = build_workflow({"orchestrator": mock_agents_config["orchestrator"], "developer": agent})

    # Run the workflow
    state = await run_workflow(app, initial_state)

    # Check if _invoke_llm_chain was called
    assert mock_invoke_llm_chain.called

    # Check if the orchestrator state has been updated with the mocked AIMessage
    assert len(state["messages"]) == 2
    assert isinstance(state["messages"][0], HumanMessage)
    assert isinstance(state["messages"][1], AIMessage)
    assert "Test input" in state["messages"][0].content
    assert "Mocked LLM response" in state["messages"][-1].content
    assert agent.id in state["messages"][0].tags
    assert agent.id in state["messages"][1].tags


@pytest.mark.asyncio
@patch.object(ToolNode, "invoke")
@patch("pluscoder.model.get_llm")
@patch("pluscoder.workflow.accumulate_token_usage")
@patch.object(Agent, "_invoke_llm_chain")
async def test_workflow_with_mocked_llm_with_tool(
    mock_invoke_llm_chain,
    mock_accumulate_token_usage,
    mock_get_llm,
    mock_tool_node_invoke,
    orchestrator_agent,
    agent,
    mock_agents_config,
):
    # Mock the LLM response
    mock_llm = MagicMock()
    mock_get_llm.return_value = mock_llm

    # Mock _invoke_llm_chain to return a mocked AIMessage
    ai_message = AIMessage(content="Mocked LLM response")
    ai_message.tool_calls = [{"name": "test_tool"}]
    ai_message_2 = AIMessage(content="2nd Mocked LLM response")
    mock_invoke_llm_chain.side_effect = [ai_message, ai_message_2]

    # Mock accumulate_token_usage to return the state unchanged
    mock_accumulate_token_usage.side_effect = lambda state, _: state

    # Tool node mock
    mock_tool_node_invoke.return_value = {
        "messages": [ai_message, ToolMessage(content="Tool message content", tool_call_id="id")]
    }

    # Set up the initial state
    initial_state = OrchestrationState(
        max_iterations=1,
        current_iterations=0,
        return_to_user=False,
        messages=[],
        context_files=[],
        chat_agent=mock_agents_config["developer"],
        is_task_list_workflow=False,
        accumulated_token_usage=TokenUsage(prompt_tokens=0, completion_tokens=0, total_tokens=0, total_cost=0.0),
        agents_configs=mock_agents_config,
    )

    # Set user input for testing
    config.user_input = "Test input"

    # Build workflow
    app = build_workflow(
        {"orchestrator": mock_agents_config["orchestrator"], "developer": mock_agents_config["developer"]}
    )

    # Run the workflow
    state = await run_workflow(app, initial_state)

    # Check if _invoke_llm_chain was called
    assert mock_invoke_llm_chain.called_twice

    # Check if the orchestrator state has been updated with the mocked AIMessage
    assert len(state["messages"]) == 4
    assert isinstance(state["messages"][1], AIMessage)
    assert isinstance(state["messages"][2], ToolMessage)
    assert isinstance(state["messages"][3], AIMessage)
    assert "Mocked LLM response" in state["messages"][1].content
    assert "2nd Mocked LLM response" in state["messages"][3].content

    assert agent.id in state["messages"][0].tags
    assert agent.id in state["messages"][2].tags
    assert agent.id in state["messages"][1].tags


@pytest.mark.asyncio
@patch.object(ToolNode, "invoke")
@patch("pluscoder.workflow.io.input")
@patch("pluscoder.model.get_llm")
@patch("pluscoder.workflow.accumulate_token_usage")
@patch.object(Agent, "_invoke_llm_chain")
async def test_orchestrator_basic(
    mock_invoke_llm_chain,
    mock_accumulate_token_usage,
    mock_get_llm,
    mock_io,
    mock_tool_node_invoke,
    orchestrator_agent,
    agent,
    mock_agents_config,
):
    # Mock the LLM response
    mock_llm = MagicMock()
    mock_get_llm.return_value = mock_llm

    mock_io.side_effect = ["some user input"]
    # mock_io.return_value = "some user input"

    # Mock _invoke_llm_chain to return a mocked AIMessage
    ai_message = AIMessage(content="Mocked LLM response")
    mock_invoke_llm_chain.side_effect = [ai_message]

    # Mock accumulate_token_usage to return the state unchanged
    mock_accumulate_token_usage.side_effect = lambda state, _: state

    # Set up the initial state
    initial_state = OrchestrationState(
        max_iterations=1,
        current_iterations=0,
        return_to_user=False,
        messages=[],
        context_files=[],
        chat_agent=mock_agents_config["orchestrator"],
        is_task_list_workflow=False,
        accumulated_token_usage=TokenUsage(prompt_tokens=0, completion_tokens=0, total_tokens=0, total_cost=0.0),
        status="active",
        agents_configs=mock_agents_config,
    )

    # Set user input for testing
    config.user_input = None

    # Build workflow
    app = build_workflow(
        {"orchestrator": mock_agents_config["orchestrator"], "developer": mock_agents_config["developer"]}
    )

    # Run the workflow
    state = await run_workflow(app, initial_state)

    # Check if _invoke_llm_chain was called
    assert mock_invoke_llm_chain.called_twice

    # Check if the orchestrator state has been updated with the mocked AIMessage
    assert len(state["messages"]) == 2
    assert isinstance(state["messages"][0], HumanMessage)
    assert isinstance(state["messages"][1], AIMessage)

    assert orchestrator_agent.id in state["messages"][0].tags
    assert orchestrator_agent.id in state["messages"][1].tags


@pytest.mark.asyncio
# @patch.object(ToolNode, 'invoke')
@patch("pluscoder.workflow.io.confirm")
@patch("pluscoder.workflow.io.input")
@patch("pluscoder.model.get_llm")
@patch("pluscoder.workflow.accumulate_token_usage")
@patch.object(Agent, "_invoke_llm_chain")
async def test_orchestrator_task_list_run(
    mock_invoke_llm_chain,
    mock_accumulate_token_usage,
    mock_get_llm,
    mock_io,
    mock_io_confirm,
    orchestrator_agent,
    agent,
    mock_agents_config,
):
    # Mock the LLM response
    mock_llm = MagicMock()
    mock_get_llm.return_value = mock_llm

    mock_io.side_effect = ["some user input"]
    # mock_io.return_value = "some user input"

    # Mock confirm
    mock_io_confirm.return_value = True

    # Mock _invoke_llm_chain to return a mocked AIMessage
    ai_message = AIMessage(content="Mocked LLM response")
    ai_message.tool_calls = [
        {
            "name": tools.delegate_tasks.name,
            "id": "delegation_1",
            "args": {
                "general_objective": "Objective",
                "task_list": [
                    {"is_finished": False, "objective": "Task 1", "details": "Details 1", "agent": "developer"},
                    {"is_finished": False, "objective": "CTask 2", "details": "Details 2", "agent": "developer"},
                ],
                "resources": [],
            },
        }
    ]

    # Developer response
    ai_message_dev = AIMessage(content="Developer response")

    # Orch validation response
    ai_message_orc = AIMessage(content="Orch validation")
    ai_message_orc.tool_calls = [
        {
            "name": tools.is_task_completed.name,
            "id": "task_completed_1",
            "args": {"completed": True, "feedback": "some feedback"},
        }
    ]

    # Developer response
    ai_message_dev2 = AIMessage(content="Developer response")

    # Orch validation response
    ai_message_orc2 = AIMessage(content="Orch validation")
    ai_message_orc2.tool_calls = [
        {
            "name": tools.is_task_completed.name,
            "id": "task_completed_1",
            "args": {"completed": True, "feedback": "some feedback"},
        }
    ]

    # Orch Summarization Response
    ai_message_orc3 = AIMessage(content="Summary")

    mock_invoke_llm_chain.side_effect = [
        ai_message,
        ai_message_dev,
        ai_message_orc,
        ai_message_dev2,
        ai_message_orc2,
        ai_message_orc3,
    ]

    # Mock accumulate_token_usage to return the state unchanged
    mock_accumulate_token_usage.side_effect = lambda state, _: state

    # Set up the initial state
    initial_state = OrchestrationState(
        max_iterations=1,
        current_iterations=0,
        return_to_user=False,
        messages=[],
        context_files=[],
        chat_agent=mock_agents_config["orchestrator"],
        is_task_list_workflow=False,
        accumulated_token_usage=TokenUsage(prompt_tokens=0, completion_tokens=0, total_tokens=0, total_cost=0.0),
        status="active",
        agents_configs=mock_agents_config,
    )

    # Set user input for testing
    config.user_input = None

    # Build workflow
    app = build_workflow(
        {"orchestrator": mock_agents_config["orchestrator"], "developer": mock_agents_config["developer"]}
    )

    # Run the workflow
    state = await run_workflow(app, initial_state)

    # Check if _invoke_llm_chain was called
    assert mock_invoke_llm_chain.call_count == 6

    # Check if llm input messages are correct
    # First call must be only with one message made by the user
    assert len(mock_invoke_llm_chain.call_args_list[0][0][0]["messages"]) == 1
    assert isinstance(mock_invoke_llm_chain.call_args_list[0][0][0]["messages"][0], HumanMessage)
    assert "orchestrator" in mock_invoke_llm_chain.call_args_list[0][0][0]["messages"][0].tags

    # Second call must be developer agent with its task to solve
    assert len(mock_invoke_llm_chain.call_args_list[1][0][0]["messages"]) == 1
    assert isinstance(mock_invoke_llm_chain.call_args_list[1][0][0]["messages"][0], HumanMessage)
    assert "developer" in mock_invoke_llm_chain.call_args_list[1][0][0]["messages"][0].tags

    # Third call must be orchestrator for validating developer answer
    assert len(mock_invoke_llm_chain.call_args_list[2][0][0]["messages"]) == 1
    assert isinstance(mock_invoke_llm_chain.call_args_list[2][0][0]["messages"][0], HumanMessage)
    assert "orchestrator-developer" in mock_invoke_llm_chain.call_args_list[2][0][0]["messages"][0].tags

    # Fourth call must be developer agent with its second task to solve
    assert len(mock_invoke_llm_chain.call_args_list[3][0][0]["messages"]) == 1
    assert isinstance(mock_invoke_llm_chain.call_args_list[3][0][0]["messages"][0], HumanMessage)
    assert "developer" in mock_invoke_llm_chain.call_args_list[3][0][0]["messages"][0].tags

    # fifth call must be orchestrator for validating developer answer
    assert len(mock_invoke_llm_chain.call_args_list[4][0][0]["messages"]) == 1
    assert isinstance(mock_invoke_llm_chain.call_args_list[4][0][0]["messages"][0], HumanMessage)
    assert "orchestrator-developer" in mock_invoke_llm_chain.call_args_list[4][0][0]["messages"][0].tags

    # sixth call must be orchestrator for summarizing
    assert len(mock_invoke_llm_chain.call_args_list[5][0][0]["messages"]) == 1
    assert isinstance(mock_invoke_llm_chain.call_args_list[5][0][0]["messages"][0], HumanMessage)
    assert "orchestrator-orchestrator" in mock_invoke_llm_chain.call_args_list[5][0][0]["messages"][0].tags

    # Check if the orchestrator state has been updated with the mocked AIMessage
    assert len(state["messages"]) == 4
    assert isinstance(state["messages"][0], HumanMessage)
    assert isinstance(state["messages"][1], AIMessage)
    assert isinstance(state["messages"][2], ToolMessage)
    assert isinstance(state["messages"][3], AIMessage)

    assert orchestrator_agent.id in state["messages"][0].tags
    assert orchestrator_agent.id in state["messages"][1].tags
    assert orchestrator_agent.id in state["messages"][2].tags
    assert orchestrator_agent.id in state["messages"][3].tags

    assert tools.delegate_tasks.name not in state["tool_data"]


@pytest.mark.asyncio
# @patch.object(ToolNode, 'invoke')
@patch("pluscoder.workflow.io.confirm")
@patch("pluscoder.workflow.io.input")
@patch("pluscoder.model.get_llm")
@patch("pluscoder.workflow.accumulate_token_usage")
@patch.object(Agent, "_invoke_llm_chain")
async def test_orchestrator_task_list_cancel(
    mock_invoke_llm_chain,
    mock_accumulate_token_usage,
    mock_get_llm,
    mock_io,
    mock_io_confirm,
    orchestrator_agent,
    agent,
    mock_agents_config,
):
    # Mock the LLM response
    mock_llm = MagicMock()
    mock_get_llm.return_value = mock_llm

    mock_io.side_effect = ["some user input"]
    # mock_io.return_value = "some user input"

    # Mock confirm
    mock_io_confirm.return_value = False

    # Mock _invoke_llm_chain to return a mocked AIMessage
    ai_message = AIMessage(content="Mocked LLM response")
    ai_message.tool_calls = [
        {
            "name": tools.delegate_tasks.name,
            "id": "delegation_1",
            "args": {
                "general_objective": "Objective",
                "task_list": [
                    {"is_finished": False, "objective": "Task 1", "details": "Details 1", "agent": "developer"},
                    {"is_finished": False, "objective": "CTask 2", "details": "Details 2", "agent": "developer"},
                ],
                "resources": [],
            },
        }
    ]

    mock_invoke_llm_chain.side_effect = [ai_message]

    # Mock accumulate_token_usage to return the state unchanged
    mock_accumulate_token_usage.side_effect = lambda state, _: state

    # Set up the initial state
    initial_state = OrchestrationState(
        max_iterations=1,
        current_iterations=0,
        return_to_user=False,
        messages=[],
        context_files=[],
        chat_agent=mock_agents_config["orchestrator"],
        is_task_list_workflow=False,
        accumulated_token_usage=TokenUsage(prompt_tokens=0, completion_tokens=0, total_tokens=0, total_cost=0.0),
        status="active",
        agents_configs=mock_agents_config,
    )

    # Set user input for testing
    config.user_input = None

    # Build workflow
    app = build_workflow(
        {"orchestrator": mock_agents_config["orchestrator"], "developer": mock_agents_config["developer"]}
    )

    # Run the workflow
    state = await run_workflow(app, initial_state)

    # Check if _invoke_llm_chain was called
    assert mock_invoke_llm_chain.call_count == 1

    # Check if llm input messages are correct
    # First call must be only with one message made by the user
    assert len(mock_invoke_llm_chain.call_args_list[0][0][0]["messages"]) == 1
    assert isinstance(mock_invoke_llm_chain.call_args_list[0][0][0]["messages"][0], HumanMessage)
    assert "orchestrator" in mock_invoke_llm_chain.call_args_list[0][0][0]["messages"][0].tags

    # Check if the orchestrator state has been updated with the mocked AIMessage
    assert len(state["messages"]) == 3
    assert isinstance(state["messages"][0], HumanMessage)
    assert isinstance(state["messages"][1], AIMessage)
    assert isinstance(state["messages"][2], ToolMessage)

    assert orchestrator_agent.id in state["messages"][0].tags
    assert orchestrator_agent.id in state["messages"][1].tags
    assert orchestrator_agent.id in state["messages"][2].tags

    assert state["tool_data"][tools.delegate_tasks.name] is None


@pytest.mark.asyncio
# @patch.object(ToolNode, 'invoke')
@patch("pluscoder.workflow.io.confirm")
@patch("pluscoder.workflow.io.input")
@patch("pluscoder.model.get_llm")
@patch("pluscoder.workflow.accumulate_token_usage")
@patch.object(Agent, "_invoke_llm_chain")
async def test_orchestrator_task_list_partial_run(
    mock_invoke_llm_chain,
    mock_accumulate_token_usage,
    mock_get_llm,
    mock_io,
    mock_io_confirm,
    orchestrator_agent,
    agent,
    mock_agents_config,
):
    # Mock the LLM response
    mock_llm = MagicMock()
    mock_get_llm.return_value = mock_llm

    mock_io.side_effect = ["some user input"]
    # mock_io.return_value = "some user input"

    # Mock confirm
    mock_io_confirm.side_effect = [True, False]

    # Mock _invoke_llm_chain to return a mocked AIMessage
    ai_message = AIMessage(content="Mocked LLM response")
    ai_message.tool_calls = [
        {
            "name": tools.delegate_tasks.name,
            "id": "delegation_1",
            "args": {
                "general_objective": "Objective",
                "task_list": [
                    {"is_finished": False, "objective": "Task 1", "details": "Details 1", "agent": "developer"},
                    {"is_finished": False, "objective": "CTask 2", "details": "Details 2", "agent": "developer"},
                ],
                "resources": [],
            },
        }
    ]

    # Developer response
    ai_message_dev = AIMessage(content="Developer response")

    # Orch validation response
    ai_message_orc = AIMessage(content="Orch validation")
    ai_message_orc.tool_calls = [
        {
            "name": tools.is_task_completed.name,
            "id": "task_completed_1",
            "args": {"completed": True, "feedback": "some feedback"},
        }
    ]

    mock_invoke_llm_chain.side_effect = [ai_message, ai_message_dev, ai_message_orc]

    # Mock accumulate_token_usage to return the state unchanged
    mock_accumulate_token_usage.side_effect = lambda state, _: state

    # Set up the initial state
    initial_state = OrchestrationState(
        max_iterations=1,
        current_iterations=0,
        return_to_user=False,
        messages=[],
        context_files=[],
        chat_agent=mock_agents_config["orchestrator"],
        is_task_list_workflow=False,
        accumulated_token_usage=TokenUsage(prompt_tokens=0, completion_tokens=0, total_tokens=0, total_cost=0.0),
        status="active",
        agents_configs=mock_agents_config,
    )

    # Set user input for testing
    config.user_input = None

    # Build workflow
    app = build_workflow(
        {"orchestrator": mock_agents_config["orchestrator"], "developer": mock_agents_config["developer"]}
    )

    # Run the workflow
    state = await run_workflow(app, initial_state)

    # Check if _invoke_llm_chain was called
    assert mock_invoke_llm_chain.call_count == 3

    # Check if llm input messages are correct
    # First call must be only with one message made by the user
    assert len(mock_invoke_llm_chain.call_args_list[0][0][0]["messages"]) == 1
    assert isinstance(mock_invoke_llm_chain.call_args_list[0][0][0]["messages"][0], HumanMessage)
    assert "orchestrator" in mock_invoke_llm_chain.call_args_list[0][0][0]["messages"][0].tags

    # Second call must be developer agent with its task to solve
    assert len(mock_invoke_llm_chain.call_args_list[1][0][0]["messages"]) == 1
    assert isinstance(mock_invoke_llm_chain.call_args_list[1][0][0]["messages"][0], HumanMessage)
    assert "developer" in mock_invoke_llm_chain.call_args_list[1][0][0]["messages"][0].tags

    # Third call must be orchestrator for validating developer answer
    assert len(mock_invoke_llm_chain.call_args_list[2][0][0]["messages"]) == 1
    assert isinstance(mock_invoke_llm_chain.call_args_list[2][0][0]["messages"][0], HumanMessage)
    assert "orchestrator-developer" in mock_invoke_llm_chain.call_args_list[2][0][0]["messages"][0].tags

    # Check if the orchestrator state has been updated with the mocked AIMessage
    assert len(state["messages"]) == 4
    assert isinstance(state["messages"][0], HumanMessage)
    assert isinstance(state["messages"][1], AIMessage)
    assert isinstance(state["messages"][2], ToolMessage)
    assert isinstance(state["messages"][3], AIMessage)

    assert orchestrator_agent.id in state["messages"][0].tags
    assert orchestrator_agent.id in state["messages"][1].tags
    assert orchestrator_agent.id in state["messages"][2].tags
    assert orchestrator_agent.id in state["messages"][3].tags

    assert tools.delegate_tasks.name not in state["tool_data"]


@pytest.mark.skip(reason="validate")
@pytest.mark.asyncio
@patch("pluscoder.main.parse_task_list")
@patch("pluscoder.workflow.io.confirm")
@patch("pluscoder.model.get_llm")
@patch("pluscoder.workflow.accumulate_token_usage")
@patch.object(Agent, "_invoke_llm_chain")
async def test_task_list_workflow_execution(
    mock_invoke_llm_chain,
    mock_accumulate_token_usage,
    mock_get_llm,
    mock_io_confirm,
    mock_parse_task_list,
    orchestrator_agent,
    agent,
    mock_agents_config,
):
    """Test successful execution of task list workflow from JSON string input"""
    # Mock task list as JSON string (simulating CLI input)
    tasks = [
        {
            "objective": "Test task 1",
            "details": "Details 1",
            "restrictions": "None",
            "outcome": "Outcome 1",
            "agent": "developer",
            "completed": False,
            "is_finished": False,
        }
    ]
    # Simulate JSON string from command line
    mock_parse_task_list.return_value = tasks
    mock_io_confirm.return_value = True

    # Mock LLM responses
    ai_message = AIMessage(content="Task delegated")
    ai_message.tool_calls = [{"name": tools.delegate_tasks.name, "id": "1", "args": {"tasks": tasks}}]

    dev_response = AIMessage(content="Task completed")
    validation_response = AIMessage(content="Task validated")
    validation_response.tool_calls = [
        {"name": tools.is_task_completed.name, "id": "2", "args": {"completed": True, "feedback": "Done"}}
    ]
    summary = AIMessage(content="All tasks completed successfully")

    mock_invoke_llm_chain.side_effect = [ai_message, dev_response, validation_response, summary]
    mock_accumulate_token_usage.side_effect = lambda state, _: state
    mock_get_llm.return_value = MagicMock()

    # Set initial state with task list workflow flag
    initial_state = {
        "agents_configs": mock_agents_config,
        "chat_agent": mock_agents_config["orchestrator"],
        "status": "active",
        "max_iterations": 1,
        "current_iterations": 0,
        "messages": [],
        "tool_data": {},
        "return_to_user": False,
        "accumulated_token_usage": TokenUsage.default(),
        "token_usage": None,
        "is_task_list_workflow": True,
        "max_agent_deflections": 2,
        "current_agent_deflections": 0,
    }

    app = build_workflow(
        {"orchestrator": mock_agents_config["orchestrator"], "developer": mock_agents_config["developer"]}
    )
    final_state = await run_workflow(app, initial_state)

    # Verify workflow executed task list correctly
    assert mock_invoke_llm_chain.call_count == 4
    assert final_state["status"] == "active"
    assert isinstance(final_state["messages"][-1], AIMessage)
    assert "All tasks completed successfully" in final_state["messages"][-1].content


@pytest.mark.skip(reason="validate")
@pytest.mark.asyncio
@patch("pluscoder.main.parse_task_list")
@patch("pluscoder.workflow.io.confirm")
@patch("pluscoder.model.get_llm")
@patch("pluscoder.workflow.accumulate_token_usage")
@patch.object(Agent, "_invoke_llm_chain")
async def test_task_list_workflow_errors(
    mock_invoke_llm_chain,
    mock_accumulate_token_usage,
    mock_get_llm,
    mock_io_confirm,
    mock_parse_task_list,
    orchestrator_agent,
    agent,
    mock_agents_config,
):
    """Test error handling in task list workflow"""
    # Mock LLM to avoid actual calls
    mock_get_llm.return_value = MagicMock()
    mock_invoke_llm_chain.return_value = AIMessage(content="Mock response")
    mock_accumulate_token_usage.side_effect = lambda state, _: state

    error_test_cases = [
        (ValueError("Invalid JSON"), "Invalid JSON"),
        (IOError("File not found"), "File not found"),
        (ValueError("Task missing required fields"), "Task missing required fields"),
    ]

    for error, error_msg in error_test_cases:
        mock_parse_task_list.side_effect = error

        with pytest.raises(type(error), match=error_msg):  # noqa: PT012
            initial_state = {
                "agents_configs": mock_agents_config,
                "chat_agent": mock_agents_config["orchestrator"],
                "status": "active",
                "max_iterations": 1,
                "current_iterations": 0,
                "messages": [],
                "tool_data": {},
                "return_to_user": False,
                "accumulated_token_usage": TokenUsage.default(),
                "token_usage": None,
                "is_task_list_workflow": True,
                "max_agent_deflections": 2,
                "current_agent_deflections": 0,
            }

            app = build_workflow({"orchestrator": mock_agents_config["orchestrator"]})
            await run_workflow(app, initial_state)

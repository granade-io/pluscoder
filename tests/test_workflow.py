from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from langchain_core.messages import AIMessage
from langchain_core.messages import HumanMessage

from pluscoder.agents.base import Agent
from pluscoder.agents.orchestrator import OrchestratorAgent
from pluscoder.config import config
from pluscoder.type import AgentState
from pluscoder.type import OrchestrationState
from pluscoder.type import TokenUsage
from pluscoder.workflow import build_workflow
from pluscoder.workflow import run_workflow


@pytest.fixture
def agent():
    agent = Agent(
        system_message="You are a helpful assistant.",
        name="TestAgent",
        tools=[],
        default_context_files=["test_file.txt"],
    )
    agent.id = "developer"
    return agent


@pytest.fixture
def orchestrator_agent():
    return OrchestratorAgent(
        tools=[],
        extraction_tools=[],
    )


@pytest.mark.asyncio
@patch("pluscoder.model.get_llm")
@patch("pluscoder.workflow.accumulate_token_usage")
@patch.object(Agent, "_invoke_llm_chain")
async def test_workflow_with_mocked_llm(
    mock_invoke_llm_chain, mock_accumulate_token_usage, mock_get_llm, orchestrator_agent, agent
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
        return_to_user=False,
        messages=[],
        context_files=[],
        orchestrator_state=AgentState(
            messages=[HumanMessage(content="Test input")],
            token_usage=TokenUsage(prompt_tokens=0, completion_tokens=0, total_tokens=0, total_cost=0.0),
            status="active",
            agent_messages=[],
            tool_data={},
        ),
        domain_stakeholder_state=AgentState.default(),
        planning_state=AgentState.default(),
        developer_state=AgentState.default(),
        domain_expert_state=AgentState.default(),
        chat_agent="orchestrator",
        is_task_list_workflow=False,
        accumulated_token_usage=TokenUsage(prompt_tokens=0, completion_tokens=0, total_tokens=0, total_cost=0.0),
    )

    # Set user input for testing
    config.user_input = "Test input"

    # Build workflow
    app = build_workflow({"orchestrator": orchestrator_agent, "developer": agent})

    # Run the workflow
    state = await run_workflow(app, initial_state)

    # Check if _invoke_llm_chain was called
    assert mock_invoke_llm_chain.called

    # Check if the orchestrator state has been updated with the mocked AIMessage
    assert any(isinstance(msg, AIMessage) for msg in state["orchestrator_state"]["messages"])
    assert "Mocked LLM response" in state["orchestrator_state"]["messages"][-1].content

from unittest.mock import Mock
from unittest.mock import patch

import pytest
from langchain_core.messages import AIMessage

from pluscoder.agents.base import Agent
from pluscoder.agents.base import parse_block
from pluscoder.agents.base import parse_mentioned_files
from pluscoder.agents.stream_parser import XMLStreamParser
from pluscoder.exceptions import AgentException
from pluscoder.message_utils import HumanMessage
from pluscoder.repo import Repository
from pluscoder.type import AgentConfig
from pluscoder.type import OrchestrationState


def test_parse_block():
    test_input = """
`file1.py`
<source>
def hello():
    print("Hello, World!")
</source>

`file2.txt`
<source>
This is some plain text content.
Multiple lines are supported.
</source>
"""

    expected_output = [
        {
            "file_path": "file1.py",
            "content": 'def hello():\n    print("Hello, World!")',
        },
        {
            "file_path": "file2.txt",
            "content": "This is some plain text content.\nMultiple lines are supported.",
        },
    ]

    assert parse_block(test_input) == expected_output


def test_parse_block_no_blocks():
    test_input = """
`file1.py`
    <source>
    def hello():
        print("Hello, World!")
    </source>

<source>
This is some plain text content.
Multiple lines are supported.
</source>
"""
    assert parse_block(test_input) == []


def test_parse_block_merge():
    test_input = """
`file1.py`
<source>
def hello():
    print("Hello, World!")
</source>

<source>
This is some plain text content.
Multiple lines are supported.
</source>

`file2.py`
<source>
1st source
</source>

Modify this other file:
<source>
2nd source
</source>

<source>
3rd source
</source>
"""

    expected_output = [
        {
            "file_path": "file1.py",
            "content": 'def hello():\n    print("Hello, World!")\n\nThis is some plain text content.\nMultiple lines are supported.',
        },
        {
            "file_path": "file2.py",
            "content": "1st source\n\n2nd source\n\n3rd source",
        },
    ]

    assert parse_block(test_input) == expected_output


def test_parse_mentioned_files():
    test_input = "This text mentions `file1.py` and `file2.txt` as well as `another_file.md`."
    expected_output = list(set(["file1.py", "file2.txt", "another_file.md"]))

    assert parse_mentioned_files(test_input) == expected_output


def test_parse_mentioned_files_no_duplicates():
    test_input = "This text mentions `file1.py` twice: `file1.py` and also `file2.txt`."
    expected_output = list(set(["file1.py", "file2.txt"]))

    assert parse_mentioned_files(test_input) == expected_output


def test_parse_mentioned_files_empty():
    test_input = "This text doesn't mention any files."
    expected_output = []

    assert parse_mentioned_files(test_input) == expected_output


@pytest.fixture
def mock_llm():
    return Mock()


@pytest.fixture
def agent():
    return Agent(
        agent_config=AgentConfig(
            prompt="You are a helpful assistant.",
            name="TestAgent",
            id="test_agent",
            description="Description",
            reminder="",
            tools=[],
            default_context_files=["test_file.txt"],
            repository_interaction=True,
        ),
        stream_parser=XMLStreamParser(),
    )


def test_agent_initialization(agent):
    assert agent.name == "TestAgent"
    assert agent.system_message == "You are a helpful assistant."
    assert agent.tools == []
    assert agent.default_context_files == ["test_file.txt"]


# TODO: Comented, context files will be removed in the future
# def test_get_context_files(agent):
#     state = OrchestrationState(context_files=["new_file.txt"])
#     context_files = agent.get_context_files(state)
#     assert set(context_files) == set(["test_file.txt", "new_file.txt"])


def test_get_context_files_panel(agent):
    files = ["file1.txt", "file2.txt", "file3.txt"]
    panel = agent.get_context_files_panel(files)
    assert "file1.txt file2.txt file3.txt" in panel


@patch.object(Repository, "generate_repomap")
@patch("pluscoder.agents.base.get_formatted_files_content")
def test_build_assistant_prompt(mock_get_formatted_files_content, mock_generate_repomap, agent):
    mock_generate_repomap.return_value = "My Repomap"
    mock_get_formatted_files_content.return_value = "file content"
    state = OrchestrationState(messages=[HumanMessage(content="Hello")], context_files=["test_file.txt"])
    prompt = agent.build_assistant_prompt(state, [])
    assert isinstance(prompt, object)  # Check if it returns a RunnableMap object


# @patch.object(Repository, 'generate_repomap')
@patch.object(Agent, "_invoke_llm_chain")
@patch("pluscoder.agents.base.get_formatted_files_content")
@patch("pluscoder.agents.base.io")
@patch("pluscoder.agents.base.file_callback")
def test_call_agent(
    mock_file_callback, mock_io, mock_get_formatted_files_content, mock_invoke_llm_chain, agent
) -> None:
    # mock_generate_repomap.return_value = "My Repomap"
    mock_invoke_llm_chain.return_value = AIMessage(content="Mocked LLM response")
    # mock_get_formatted_files_content.return_value = "Mocked file content"
    state = OrchestrationState(messages=[HumanMessage(content="Hello")], context_files=[])

    result = agent.call_agent(state)
    assert "messages" in result

    # Just IA Message is present in state updates
    assert len(result["messages"]) == 1

    # Last message
    last_message = result["messages"][-1]
    assert len(last_message.tags) == 1
    assert agent.id in last_message.tags
    assert isinstance(last_message, AIMessage)


def test_process_agent_response(agent):
    state = OrchestrationState(context_files=[])
    response = AIMessage(content="Check `new_file.txt`")
    result = agent.process_agent_response(state, response)
    assert result == {}


def test_agent_router_return_tools(agent):
    message = AIMessage(content="")
    message.tool_calls = True  # Just to simulate a tool call message
    state = OrchestrationState(messages=[message])
    result = agent.agent_router(state)
    assert result == "tools"


def test_agent_router_return_end_on_max_deflections(agent):
    agent.current_deflection = agent.max_deflections + 1
    message = AIMessage(content="")
    message.tool_calls = True  # Just to simulate a tool call message
    state = OrchestrationState(messages=[message])
    result = agent.agent_router(state)
    assert result == "__end__"


def test_agent_router_no_tools(agent):
    state = OrchestrationState(messages=[AIMessage(content="")])
    result = agent.agent_router(state)
    assert result == "__end__"


@patch.object(Agent, "_invoke_llm_chain")
@pytest.mark.asyncio
async def test_graph_node_normal_response(mock_invoke_llm_chain, agent):
    # Mock the graph.invoke method to return a normal response
    mock_invoke_llm_chain.return_value = AIMessage(content="Normal response")

    initial_state = OrchestrationState(messages=[HumanMessage(content="Hello")])
    result = await agent.graph_node(initial_state)

    assert len(result["messages"]) == 2
    assert "Normal response" in result["messages"][-1].content
    assert agent.current_deflection == 0


@patch.object(Agent, "_invoke_llm_chain")
@pytest.mark.asyncio
async def test_graph_node_one_deflection_and_recover(mock_invoke_llm_chain, agent):
    # Mock the graph.invoke method to raise an exception once, then return a normal response
    mock_invoke_llm_chain.side_effect = [
        AgentException("Test error"),
        AIMessage(content="Recovered response"),
    ]

    initial_state = OrchestrationState(messages=[HumanMessage(content="Hello")])
    result = await agent.graph_node(initial_state)

    assert len(result["messages"]) == 3
    assert "Recovered response" in result["messages"][-1].content
    assert agent.current_deflection == 1


@patch.object(Agent, "process_agent_response")
@patch.object(Agent, "_invoke_llm_chain")
@pytest.mark.asyncio
async def test_graph_node_max_deflections_no_recover(mock_invoke_llm_chain, mock_process_agent_response, agent):
    # Mock the graph.invoke method to always raise an exception
    mock_process_agent_response.side_effect = AgentException("Persistent error")
    mock_invoke_llm_chain.return_value = AIMessage(content="Edit response")

    initial_state = OrchestrationState(messages=[HumanMessage(content="Hello")])
    result = await agent.graph_node(initial_state)

    # Last message should be the persistent error
    assert "Persistent error" in str(result["messages"][-1].content)
    # 1 deflection means 1 more try, so more tries occurs at max_deflections + 1
    assert agent.current_deflection == agent.max_deflections + 1
    assert len(result["messages"]) == 9

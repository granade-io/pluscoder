import pytest
from unittest.mock import Mock, patch
from langchain_core.messages import HumanMessage, AIMessage
from pluscoder.agents.base import Agent, AgentState, parse_block, parse_mentioned_files
from pluscoder.exceptions import AgentException
from pluscoder.repo import Repository

def test_parse_block():
    test_input = """
`file1.py`
```python
def hello():
    print("Hello, World!")
```

`file2.txt`
```
This is some plain text content.
Multiple lines are supported.
```
"""
    
    expected_output = [
        {
            'file_path': 'file1.py',
            'language': 'python',
            'content': 'def hello():\n    print("Hello, World!")'
        },
        {
            'file_path': 'file2.txt',
            'language': '',
            'content': 'This is some plain text content.\nMultiple lines are supported.'
        }
    ]
    
    assert parse_block(test_input) == expected_output
    
def test_parse_block_no_blocks():
    test_input = """
`file1.py`
    ```python
    def hello():
        print("Hello, World!")
    ```

```
This is some plain text content.
Multiple lines are supported.
```
"""
    assert parse_block(test_input) == []


def test_parse_mentioned_files():
    test_input = "This text mentions `file1.py` and `file2.txt` as well as `another_file.md`."
    expected_output = list(set(['file1.py', 'file2.txt', 'another_file.md']))
    
    assert parse_mentioned_files(test_input) == expected_output

def test_parse_mentioned_files_no_duplicates():
    test_input = "This text mentions `file1.py` twice: `file1.py` and also `file2.txt`."
    expected_output = list(set(['file1.py', 'file2.txt']))
    
    assert parse_mentioned_files(test_input) == expected_output

def test_parse_mentioned_files_empty():
    test_input = "This text doesn't mention any files."
    expected_output = []
    
    assert parse_mentioned_files(test_input) == expected_output
    

@pytest.fixture
def mock_llm():
    return Mock()

@pytest.fixture
def agent(mock_llm):
    return Agent(
        llm=mock_llm,
        system_message="You are a helpful assistant.",
        name="TestAgent",
        tools=[],
        default_context_files=["test_file.txt"]
    )

def test_agent_initialization(agent):
    assert agent.name == "TestAgent"
    assert agent.system_message == "You are a helpful assistant."
    assert agent.tools == []
    assert agent.default_context_files == ["test_file.txt"]
    assert agent.max_deflections == 3

# TODO: Comented, context files will be removed in the future
# def test_get_context_files(agent):
#     state = AgentState(context_files=["new_file.txt"])
#     context_files = agent.get_context_files(state)
#     assert set(context_files) == set(["test_file.txt", "new_file.txt"])

def test_get_context_files_panel(agent):
    files = ["file1.txt", "file2.txt", "file3.txt"]
    panel = agent.get_context_files_panel(files)
    assert "file1.txt file2.txt file3.txt" in panel

@patch.object(Repository, 'generate_repomap')
@patch('pluscoder.agents.base.get_formatted_files_content')
def test_build_assistant_prompt(mock_get_formatted_files_content, mock_generate_repomap, agent):
    mock_generate_repomap.return_value = "My Repomap"
    mock_get_formatted_files_content.return_value = "file content"
    state = AgentState(
        messages=[HumanMessage(content="Hello")],
        context_files=["test_file.txt"]
    )
    prompt = agent.build_assistant_prompt(state, [])
    assert isinstance(prompt, object)  # Check if it returns a RunnableMap object

# @patch.object(Repository, 'generate_repomap')
@patch('pluscoder.agents.base.get_formatted_files_content')
@patch('pluscoder.agents.base.io')
@patch('pluscoder.agents.base.file_callback')
def test_call_agent(mock_file_callback, mock_io, mock_get_formatted_files_content, agent, mock_llm) -> None:
    # mock_generate_repomap.return_value = "My Repomap"
    mock_llm.bind_tools.return_value.return_value = AIMessage(content="AI response with file mention `some_file.txt`")
    # mock_get_formatted_files_content.return_value = "Mocked file content"
    state = AgentState(messages=[HumanMessage(content="Hello")], context_files=[])
    
    result = agent.call_agent(state)
    print(result)
    assert "messages" in result
    
    # Just IA Message is present in state updates
    assert len(result["messages"]) == 1



def test_process_agent_response(agent):
    state = AgentState(context_files=[])
    response = AIMessage(content="Check `new_file.txt`")
    result = agent.process_agent_response(state, response)
    assert result == {}

@patch.object(Repository, 'run_lint')
@patch.object(Repository, 'run_test')
@patch('pluscoder.agents.event.config.event_emitter.emit')
@patch('pluscoder.agents.base.apply_block_update')
def test_process_blocks_success(mock_apply_block_update, mock_event_emitter, mock_run_test, mock_run_lint, agent):
    mock_run_test.return_value = False  # Indicates success
    mock_run_lint.return_value = False  # Indicates success
    mock_apply_block_update.return_value = False  # Indicates success
    blocks = [
        {"file_path": "test.py", "content": "print('Hello')", "language": "python"}
    ]
    agent.process_blocks(blocks)
    mock_apply_block_update.assert_called_once_with("test.py", "print('Hello')")
    mock_event_emitter.assert_called_once()

@patch('pluscoder.agents.event.config.event_emitter.emit')
@patch('pluscoder.agents.base.apply_block_update')
def test_process_blocks_with_errors(mock_apply_block_update, mock_event_emitter, agent):
    mock_apply_block_update.return_value = "Error in file `test.py`"  # Indicates error message
    blocks = [
        {"file_path": "test.py", "content": "print('Hello')", "language": "python"},
        {"file_path": "test2.py", "content": "print('World')", "language": "python"}
    ]
    with pytest.raises(AgentException) as excinfo:
        agent.process_blocks(blocks)
    
    assert "Some files couldn't be updated:" in str(excinfo.value)
    assert "Error in file `test.py`" in str(excinfo.value)
    mock_event_emitter.assert_not_called()

def test_agent_router_return_tools(agent):
    message = AIMessage(content="")
    message.tool_calls = True  # Just to simulate a tool call message
    state = AgentState(messages=[message])
    result = agent.agent_router(state)
    assert result == "tools"

def test_agent_router_return_end_on_max_deflections(agent):
    agent.current_deflection = agent.max_deflections + 1
    message = AIMessage(content="")
    message.tool_calls = True  # Just to simulate a tool call message
    state = AgentState(messages=[message])
    result = agent.agent_router(state)
    assert result == "__end__"
    
def test_agent_router_no_tools(agent):
    state = AgentState(messages=[AIMessage(content="")])
    result = agent.agent_router(state)
    assert result == "__end__"

@patch.object(Agent, '_invoke_llm_chain')
@pytest.mark.asyncio
async def test_graph_node_normal_response(mock_invoke_llm_chain, agent):
    # Mock the graph.invoke method to return a normal response
    mock_invoke_llm_chain.return_value = AIMessage(content="Normal response")

        
    initial_state = AgentState(messages=[HumanMessage(content="Hello")])
    result = await agent.graph_node(initial_state)
    
    assert "Normal response" in result["messages"][-1].content
    assert agent.current_deflection == 0

@patch.object(Agent, '_invoke_llm_chain')
@pytest.mark.asyncio
async def test_graph_node_one_deflection_and_recover(mock_invoke_llm_chain, agent):
    # Mock the graph.invoke method to raise an exception once, then return a normal response
    mock_invoke_llm_chain.side_effect = [
        AgentException("Test error"),
        AIMessage(content="Recovered response")
    ]
        
    initial_state = AgentState(messages=[HumanMessage(content="Hello")])
    result = await agent.graph_node(initial_state)
    
    assert "Recovered response" in result["messages"][-1].content
    assert agent.current_deflection == 1


@patch.object(Agent, 'process_agent_response')
@patch.object(Agent, '_invoke_llm_chain')
@pytest.mark.asyncio
async def test_graph_node_max_deflections_no_recover(mock_invoke_llm_chain, mock_process_agent_response, agent):
    # Mock the graph.invoke method to always raise an exception
    mock_process_agent_response.side_effect = AgentException("Persistent error")
    mock_invoke_llm_chain.return_value = AIMessage(content="Edit response")
    
    initial_state = AgentState(messages=[HumanMessage(content="Hello")])
    result = await agent.graph_node(initial_state)
    
    # Last message should be the persistent error
    assert "Persistent error" in str(result["messages"][-1].content)
    # 1 deflection means 1 more try, so more tries occurs at max_deflections + 1
    assert agent.current_deflection == agent.max_deflections + 1
    assert len(result["messages"]) == 8
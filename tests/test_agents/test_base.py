import pytest
from unittest.mock import Mock, patch, mock_open
from langchain_core.messages import HumanMessage, AIMessage
from pluscoder.agents.base import Agent, AgentState, parse_block, parse_mentioned_files
from pluscoder.exceptions import AgentException

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

@patch('pluscoder.agents.base.get_formatted_files_content')
def test_build_assistant_prompt(mock_get_formatted_files_content, agent):
    mock_get_formatted_files_content.return_value = "file content"
    state = AgentState(
        messages=[HumanMessage(content="Hello")],
        context_files=["test_file.txt"]
    )
    prompt = agent.build_assistant_prompt(state, [])
    assert isinstance(prompt, object)  # Check if it returns a RunnableMap object

@patch('pluscoder.agents.base.get_formatted_files_content')
@patch('pluscoder.agents.base.io')
@patch('pluscoder.agents.base.file_callback')
def test_call_agent(mock_file_callback, mock_io, mock_get_formatted_files_content, agent, mock_llm):
    mock_llm.bind_tools.return_value.return_value = AIMessage(content="AI response with file mention `some_file.txt`")
    mock_get_formatted_files_content.return_value = "Mocked file content"
    state = AgentState(messages=[HumanMessage(content="Hello")], context_files=[])
    
    # mock the file existence to allow file mention
    with patch('pluscoder.agents.base.Path.is_file', return_value=True):
        result = agent.call_agent(state)
    assert "messages" in result
    assert "context_files" in result
    assert "some_file.txt" in result["context_files"]



def test_process_agent_response(agent):
    state = AgentState(context_files=[])
    response = AIMessage(content="Check `new_file.txt`")
    with patch('pluscoder.agents.base.Path.is_file', return_value=True):
        result = agent.process_agent_response(state, response)
    assert "new_file.txt" in result["context_files"]

@patch('pluscoder.agents.event.config.event_emitter.emit')
@patch('pluscoder.agents.base.apply_block_update')
def test_process_blocks_success(mock_apply_block_update, mock_event_emitter, agent):
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

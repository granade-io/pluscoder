import sys
from unittest.mock import patch
import pytest
import os

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

@pytest.fixture(autouse=True)
def mock_sys_argv():
    with patch.object(sys, 'argv', ['config.py']):
        yield
        
def pytest_configure(config):
    sys.argv = ['--auto-commits=False']
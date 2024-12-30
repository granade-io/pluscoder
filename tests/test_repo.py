import subprocess
from unittest.mock import ANY
from unittest.mock import Mock
from unittest.mock import call
from unittest.mock import patch

import pytest
from git import GitCommandError

from pluscoder.io_utils import io
from pluscoder.repo import Repository


@pytest.fixture
def mock_repo():
    with patch("pluscoder.repo.Repo") as mock_repo:
        yield mock_repo


def test_commit_clean_repo(mock_repo):
    mock_repo_instance = Mock()
    mock_repo.return_value = mock_repo_instance
    mock_repo_instance.is_dirty.return_value = False

    repo = Repository(io=io)
    result = repo.commit("Test commit")

    assert result is True
    mock_repo_instance.git.add.assert_called_once_with(A=True)
    mock_repo_instance.index.commit.assert_called_once_with("Test commit", author=ANY, committer=ANY)


def test_commit_dirty_repo_allowed(mock_repo):
    mock_repo_instance = Mock()
    mock_repo.return_value = mock_repo_instance
    mock_repo_instance.is_dirty.return_value = True

    with patch("pluscoder.repo.config") as mock_config:
        mock_config.allow_dirty_commits = True
        repo = Repository(io=io)
        result = repo.commit("Test commit")

        assert result is True
        mock_repo_instance.git.add.assert_called_once_with(A=True)
        mock_repo_instance.index.commit.assert_called_once_with("Test commit", author=ANY, committer=ANY)


def test_commit_dirty_repo_not_allowed(mock_repo):
    mock_repo_instance = Mock()
    mock_repo.return_value = mock_repo_instance
    mock_repo_instance.is_dirty.return_value = True

    with patch("pluscoder.repo.config") as mock_config:
        mock_config.allow_dirty_commits = False
        repo = Repository(io=io)
        result = repo.commit("Test commit")

        assert result is False
        mock_repo_instance.git.add.assert_not_called()
        mock_repo_instance.index.commit.assert_not_called()


def test_commit_git_error(mock_repo):
    mock_repo_instance = Mock()
    mock_repo.return_value = mock_repo_instance
    mock_repo_instance.git.add.side_effect = GitCommandError("git add", "error")

    repo = Repository(io=io)
    result = repo.commit("Test commit")

    assert result is False


def test_undo_successful(mock_repo):
    mock_repo_instance = Mock()
    mock_repo.return_value = mock_repo_instance

    # Set up the mock commit
    mock_commit = Mock()
    mock_commit.author.name = "Test User (pluscoder)"
    mock_repo_instance.head.commit = mock_commit

    repo = Repository(io=io)
    result = repo.undo()

    assert result is True
    mock_repo_instance.git.reset.assert_called_once_with("--hard", "HEAD~1")


def test_undo_git_error(mock_repo):
    mock_repo_instance = Mock()
    mock_repo.return_value = mock_repo_instance

    # Set up the mock commit
    mock_commit = Mock()
    mock_commit.author.name = "Test User (pluscoder)"
    mock_repo_instance.head.commit = mock_commit

    # Set up the GitCommandError
    mock_repo_instance.git.reset.side_effect = GitCommandError("git reset", "error")

    repo = Repository(io=io)
    result = repo.undo()

    assert result is False


def test_diff_successful(mock_repo):
    mock_repo_instance = Mock()
    mock_repo.return_value = mock_repo_instance
    mock_repo_instance.git.show.return_value = "Test diff"

    repo = Repository(io=io)
    result = repo.diff()

    assert result == "Test diff"
    mock_repo_instance.git.show.assert_called_once()


def test_diff_git_error(mock_repo):
    mock_repo_instance = Mock()
    mock_repo.return_value = mock_repo_instance
    mock_repo_instance.git.show.side_effect = GitCommandError("git show", "error")

    repo = Repository(io=io)
    result = repo.diff()

    assert result == ""


def test_get_tracked_files_successful(mock_repo):
    mock_repo_instance = Mock()
    mock_repo.return_value = mock_repo_instance
    mock_repo_instance.git.ls_files.return_value = "file1.py\nfile2.py"

    repo = Repository(io=io)
    result = repo.get_tracked_files()

    assert result == ["file1.py", "file2.py"]


def test_get_tracked_files_git_error(mock_repo):
    mock_repo_instance = Mock()
    mock_repo.return_value = mock_repo_instance
    mock_repo_instance.git.ls_files.side_effect = GitCommandError("git ls-files", "error")

    repo = Repository(io=io)
    result = repo.get_tracked_files()

    assert result == []


@patch("pluscoder.repo.config")
def test_get_tracked_files_with_exclude_patterns(mock_config, mock_repo):
    mock_repo_instance = Mock()
    mock_repo.return_value = mock_repo_instance
    mock_repo_instance.git.ls_files.return_value = "file1.py\nfile2.txt\ntest.py"
    mock_repo_instance.git.ls_files.side_effect = [
        "file1.py\nfile2.txt\ntest.py",  # tracked files
        "",  # untracked files (none in this case)
    ]

    mock_config.repo_include_only_files = []
    mock_config.repo_exclude_files = [r".*\.txt$", r"test\..*"]

    repo = Repository(io=io)
    result = repo.get_tracked_files()

    assert result == ["file1.py"]


@patch("pluscoder.repo.config")
def test_get_tracked_files_with_include_only_patterns(mock_config, mock_repo):
    mock_repo_instance = Mock()
    mock_repo.return_value = mock_repo_instance
    mock_repo_instance.git.ls_files.side_effect = [
        "file1.py\nfile2.txt\ntest.py\nsetup.py",  # tracked files
        "",  # untracked files
    ]

    mock_config.repo_include_only_files = [r".*\.py$"]
    mock_config.repo_exclude_files = []

    repo = Repository(io=io)
    result = repo.get_tracked_files()

    assert result == ["file1.py", "setup.py", "test.py"]


@patch("pluscoder.repo.config")
def test_get_tracked_files_with_include_and_exclude_patterns(mock_config, mock_repo):
    mock_repo_instance = Mock()
    mock_repo.return_value = mock_repo_instance
    mock_repo_instance.git.ls_files.side_effect = [
        "file1.py\nfile2.txt\ntest.py\nsetup.py",  # tracked files
        "",  # untracked files
    ]

    mock_config.repo_include_only_files = [r".*\.py$"]
    mock_config.repo_exclude_files = [r"test\..*"]

    repo = Repository(io=io)
    result = repo.get_tracked_files()

    assert result == ["file1.py", "setup.py"]


def test_commit_with_custom_committer(mock_repo):
    mock_repo_instance = Mock()
    mock_repo.return_value = mock_repo_instance
    mock_repo_instance.is_dirty.return_value = False
    mock_config_reader = Mock()
    mock_repo_instance.config_reader.return_value = mock_config_reader
    mock_config_reader.get_value.side_effect = ["Test User", "test@example.com"]

    repo = Repository(io=io)
    result = repo.commit("Test commit")

    assert result is True
    mock_repo_instance.git.add.assert_called_once_with(A=True)
    mock_repo_instance.index.commit.assert_called_once_with("Test commit", author=ANY, committer=ANY)
    # Check if the author and committer are set correctly
    _args, kwargs = mock_repo_instance.index.commit.call_args
    assert kwargs["author"].name == "Test User (pluscoder)"
    assert kwargs["author"].email == "test@example.com"
    assert kwargs["committer"].name == "Test User (pluscoder)"
    assert kwargs["committer"].email == "test@example.com"


def test_commit_with_specific_files(mock_repo):
    mock_repo_instance = Mock()
    mock_repo.return_value = mock_repo_instance
    mock_repo_instance.is_dirty.return_value = False
    mock_config_reader = Mock()
    mock_repo_instance.config_reader.return_value = mock_config_reader
    mock_config_reader.get_value.side_effect = ["Test User", "test@example.com"]

    repo = Repository(io=io)
    updated_files = ["file1.py", "file2.py", "file3.py"]
    result = repo.commit("Test commit with specific files", updated_files=updated_files)

    assert result is True
    mock_repo_instance.git.add.assert_has_calls([call(file) for file in updated_files])
    mock_repo_instance.index.commit.assert_called_once_with(
        "Test commit with specific files", author=ANY, committer=ANY
    )
    # Check if the author and committer are set correctly
    _args, kwargs = mock_repo_instance.index.commit.call_args
    assert kwargs["author"].name == "Test User (pluscoder)"
    assert kwargs["author"].email == "test@example.com"
    assert kwargs["committer"].name == "Test User (pluscoder)"
    assert kwargs["committer"].email == "test@example.com"


def test_undo_pluscoder_commit(mock_repo):
    mock_repo_instance = Mock()
    mock_repo.return_value = mock_repo_instance
    mock_last_commit = Mock()
    mock_last_commit.author.name = "Test User (pluscoder)"
    mock_repo_instance.head.commit = mock_last_commit

    repo = Repository(io=io)
    result = repo.undo()

    assert result is True
    mock_repo_instance.git.reset.assert_called_once_with("--hard", "HEAD~1")


def test_undo_non_pluscoder_commit(mock_repo):
    mock_repo_instance = Mock()
    mock_repo.return_value = mock_repo_instance
    mock_last_commit = Mock()
    mock_last_commit.author.name = "Regular User"
    mock_repo_instance.head.commit = mock_last_commit

    repo = Repository(io=io)
    result = repo.undo()

    assert result is False
    mock_repo_instance.git.reset.assert_not_called()


@patch("pluscoder.repo.subprocess.run")
@patch("pluscoder.repo.config")
def test_run_lint_success(mock_config, mock_subprocess_run):
    mock_config.lint_command = "pylint ."
    mock_subprocess_run.return_value.returncode = 0

    repo = Repository(io=io)
    result = repo.run_lint()

    assert result is None
    mock_subprocess_run.assert_called_with("pylint .", shell=True, check=True, capture_output=True, text=True)


@patch("pluscoder.repo.subprocess.run")
@patch("pluscoder.repo.config")
def test_run_lint_failure(mock_config, mock_subprocess_run):
    mock_config.lint_command = "pylint ."
    mock_subprocess_run.side_effect = [
        True,
        subprocess.CalledProcessError(1, "pylint .", stderr="Linting errors found"),
    ]

    repo = Repository(io=io)
    result = repo.run_lint()

    assert result == "Linting failed:\n\nLinting errors found"


@patch("pluscoder.repo.subprocess.run")
@patch("pluscoder.repo.config")
def test_run_test_success(mock_config, mock_subprocess_run):
    mock_config.test_command = "pytest"
    mock_subprocess_run.return_value.returncode = 0

    repo = Repository(io=io)
    result = repo.run_test()

    assert result is None
    mock_subprocess_run.assert_called_once_with("pytest", shell=True, check=True, capture_output=True, text=True)


@patch("pluscoder.repo.subprocess.run")
@patch("pluscoder.repo.config")
def test_run_test_failure(mock_config, mock_subprocess_run):
    mock_config.test_command = "pytest"
    mock_subprocess_run.side_effect = subprocess.CalledProcessError(1, "pytest", stderr="Test failures found")

    repo = Repository(io=io)
    result = repo.run_test()

    assert result == "Tests failed:\n\nTest failures found"

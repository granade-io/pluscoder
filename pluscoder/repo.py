import os
import pprint
import re
import subprocess
import tempfile
import traceback
from typing import List
from typing import Optional

from git import Actor
from git import GitCommandError
from git import Repo
from git.exc import HookExecutionError

from pluscoder.config import config
from pluscoder.exceptions import GitCloneException
from pluscoder.exceptions import NotGitRepositoryException


class Repository:
    def __init__(self, io=None, repository_path=None, validate=False):
        self.repository_path = repository_path or os.getcwd()
        self.io = io
        self.validate = validate
        self._init_repository()

    def _init_repository(self):
        if self.is_git_url(self.repository_path):
            self.repository_path = self.clone_repository(self.repository_path)

        self.repository_path = os.path.abspath(self.repository_path)
        self.repository_path = os.path.abspath(self.repository_path)
        if not os.path.isdir(self.repository_path):
            msg = f"Invalid repository path: {self.repository_path}"
            if self.validate:
                raise ValueError(msg)
            return
        if not os.path.isdir(os.path.join(self.repository_path, ".git")):
            if self.validate:
                raise NotGitRepositoryException(self.repository_path)
            return
        os.chdir(self.repository_path)
        self.repo = Repo(self.repository_path, search_parent_directories=True)

    @staticmethod
    def is_git_url(url: str) -> bool:
        """Validate if the given string is a git repository URL.
        Supports formats:
        - HTTPS: https://github.com/user/repo.git
        - SSH: git@github.com:user/repo.git
        - Git: git://github.com/user/repo.git"""
        patterns = [r"^https?://.*\.git$", r"^git@.*:.*\.git$", r"^git://.*\.git$"]
        return any(re.match(pattern, url) for pattern in patterns)

    def clone_repository(self, url: str) -> str:
        """Clone a git repository from URL into a temporary directory.
        Args:
            url: Git repository URL
        Returns:
            str: Path to the cloned repository
        Raises:
            GitCommandError: If cloning fails"""
        try:
            # Create temporary directory
            temp_dir = tempfile.mkdtemp(prefix="pluscoder_")

            # Clone repository
            if self.io:
                self.io.event(f"> Cloning repository from {url}...")

            repo = Repo.clone_from(url, temp_dir)

            if config.source_branch:
                if self.io:
                    self.io.event(f"> Checking out branch {config.source_branch}...")
                repo.git.checkout(config.source_branch)

            if self.io:
                self.io.event(f"> Repository cloned to {temp_dir}")

            return temp_dir

        except GitCommandError as e:
            if self.io:
                self.io.console.print(f"Error cloning repository: {e}", style="bold red")
            raise GitCloneException(url, str(e)) from e

    def commit(self, message="Auto-commit", updated_files=None):
        """Create a new commit from specified updated files."""
        if not config.allow_dirty_commits and self.repo.is_dirty():
            self.io.console.print(
                "Warn: Repository is dirty and allow_dirty_commits is set to False. No new commit created.",
                style="bold dark_goldenrod",
            )
            return False

        try:
            if updated_files:
                # Stage only the specified files
                for file in updated_files:
                    self.repo.git.add(file)
            else:
                # If no specific files are provided, stage all changes
                self.repo.git.add(A=True)

            # Get current git user
            config_reader = self.repo.config_reader()
            current_name = config_reader.get_value("user", "name", "Pluscoder")
            current_email = config_reader.get_value("user", "email", "unknown@pluscoder.com")
            # Create custom committer
            committer = Actor(f"{current_name} (pluscoder)", current_email)
            # Use the custom committer for the commit
            self.repo.index.commit(message, author=committer, committer=committer)

            return True
        except GitCommandError as e:
            self.io.console.print(f"Error creating commit: {e}", style="bold red")
            return False
        except HookExecutionError:
            if config.debug:
                self.io.console.print(traceback.format_exc())
            self.io.console.print("WARN: Pre-commit hook didn't pass", style="bold dark_goldenrod")
            # Return true event when the commit failed
            return True

    def undo(self):
        """Revert the last commit if made by pluscoder, without preserving changes."""
        try:
            last_commit = self.repo.head.commit
            if "(pluscoder)" in last_commit.author.name:
                self.repo.git.reset("--hard", "HEAD~1")
                return True
            self.io.console.print(
                "Last commit was not made by pluscoder, can't be reverted.",
                style="bold dark_goldenrod",
            )
            return False
        except GitCommandError as e:
            self.io.console.print(f"Error undoing last commit: {e}", style="bold red")
            return False

    def diff(self):
        """Return a string with the diff of the last commit."""
        try:
            last_commit = self.repo.head.commit
            return self.repo.git.show(last_commit.hexsha)
        except GitCommandError as e:
            self.io.console.print(f"Error getting diff: {e}", style="bold red")
            return ""

    def get_tracked_files(self) -> List[str]:
        try:
            # Open the repository
            repo = Repo(os.getcwd(), search_parent_directories=True)

            # Get all tracked files
            tracked_files = set(repo.git.ls_files().splitlines())

            # Get untracked files (excluding ignored ones)
            untracked_files = set(repo.git.ls_files(others=True, exclude_standard=True).splitlines())

            # Combine and sort the results
            all_files = sorted(tracked_files.union(untracked_files))

            # Filter out files based on repo_exclude_files patterns
            exclude_patterns = [re.compile(pattern) for pattern in config.repo_exclude_files]
            return [file for file in all_files if not any(pattern.match(file) for pattern in exclude_patterns)]

        except Exception as e:
            self.io.console.print(f"An error occurred: {e}", style="bold red")
            return []

    def create_default_files(self):
        if not os.path.isfile(config.overview_file_path):
            with open(config.overview_file_path, "w") as f:
                f.write("")

        if not os.path.isfile(config.guidelines_file_path):
            with open(config.guidelines_file_path, "w") as f:
                f.write("")

    def setup(self):
        """Validates if repository meets requirements to use pluscoder"""
        missing_files = []

        # Check overview file
        if not os.path.isfile(config.overview_file_path):
            missing_files.append(config.overview_file_path)

        if not os.path.isfile(config.guidelines_file_path):
            missing_files.append(config.guidelines_file_path)

        if missing_files:
            self.io.console.print("The following files are required:", style="bold red")
            for file in missing_files:
                self.io.console.print(f"- {file}", style="bold red")

        # Ask y/n to create the files if missing
        if missing_files:
            if self.io.confirm("To proceed, create the missing files?"):
                self.create_default_files()

                # allow to continue using pluscoder

            else:
                # otherwise, stop using pluscoder
                return False
        return True

    def run_lint(self) -> Optional[str]:
        """
        Execute the configured lint command, with optional auto-fix.

        Returns:
            Optional[str]: None if linting was successful or not configured,
                           error message string if it failed.
        """
        if not config.run_lint_after_edit:
            return None  # Return None as there's no error, just not configured
        if config.run_lint_after_edit and not config.lint_command:
            self.io.console.print(
                "No lint command configured. Skipping linting.",
                style="bold dark_goldenrod",
            )
            return None  # Return None as there's no error, just not configured

        # Run linter fix if configured
        if config.auto_run_linter_fix and config.lint_fix_command:
            subprocess.run(config.lint_fix_command, shell=True, check=False, capture_output=True)

        try:
            subprocess.run(
                config.lint_command,
                shell=True,
                check=True,
                capture_output=True,
                text=True,
            )
            return None  # Linting successful
        except subprocess.CalledProcessError as e:
            # Both stdout and stderr returned because stderr not showing
            error_message = e.stdout if e.stdout else ""
            error_message += e.stderr if e.stderr else ""  # Append stderr to error message
            return f"Linting failed:\n\n{error_message}"  # Return error message

    def run_test(self) -> Optional[str]:
        """
        Execute the configured test command.

        Returns:
            Optional[str]: None if tests were successful or not configured,
                           error message string if they failed.
        """

        if not config.run_tests_after_edit:
            return None  # Return None as there's no error, just not configured
        if config.run_tests_after_edit and not config.test_command:
            self.io.console.print(
                "No test command configured. Skipping tests.",
                style="bold dark_goldenrod",
            )
            return None  # Return None as there's no error, just not configured

        try:
            subprocess.run(
                config.test_command,
                shell=True,
                check=True,
                capture_output=True,
                text=True,
            )
            return None  # Tests successful
        except subprocess.CalledProcessError as e:
            # Both stdout and stderr returned because stderr not showing
            error_message = e.stdout if e.stdout else ""
            error_message += e.stderr if e.stderr else ""  # Append stderr to error message
            return f"Tests failed:\n\n{error_message}"

    def change_repository(self, path: str) -> None:
        """Change the current repository path or clone if URL is provided.
        Args:
            path: Repository path or git URL
        Raises:
            ValueError: If path is invalid
            GitCloneException: If clone operation fails
            NotGitRepositoryException: If path is not a git repository"""
        self.repository_path = os.path.abspath(path)
        self._init_repository()

    def generate_repomap(self) -> Optional[str]:
        """Generate a repository map.
        Returns:
            Optional[str]: Generated repomap string if use_repomap is True, None otherwise"""
        if not config.use_repomap:
            return None

        from pluscoder.repomap import LANGUAGE_MAP
        from pluscoder.repomap import generate_tree

        include_patterns = config.repomap_include_files or [r".*\.(" + "|".join(LANGUAGE_MAP.keys()) + ")$"]
        exclude_patterns = config.repomap_exclude_files
        level = config.repomap_level

        tracked_files = self.get_tracked_files()
        return generate_tree(
            self.repo.working_tree_dir,
            include_patterns,
            exclude_patterns,
            level,
            tracked_files,
            self.io,
        )


if __name__ == "__main__":
    repo = Repository()
    print("Tree:")
    pprint.pprint(repo.get_tracked_files())
    repo.run_test()

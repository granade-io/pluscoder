import os
import pprint
import subprocess
from typing import Optional
from git import Actor, Repo
from git import GitCommandError
from pluscoder.config import config

from pluscoder.repomap import LANGUAGE_MAP, generate_tree

class Repository:
    def __init__(self, io=None):
        self.repo = Repo(os.getcwd(), search_parent_directories=True)
        self.io = io

    def commit(self, message="Auto-commit"):
        """Create a new commit from all changed files."""
        if not config.allow_dirty_commits and self.repo.is_dirty():
            self.io.console.print("Warn: Repository is dirty and allow_dirty_commits is set to False. No new commit created.", style="bold dark_goldenrod")
            return False

        try:
            self.repo.git.add(A=True)  # Stage all changes
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

    def undo(self):
        """Revert the last commit if made by pluscoder, without preserving changes."""
        try:
            last_commit = self.repo.head.commit
            if "(pluscoder)" in last_commit.author.name:
                self.repo.git.reset('--hard', 'HEAD~1')
                return True
            else:
                self.io.console.print("Last commit was not made by pluscoder, can't be reverted.", style="bold dark_goldenrod")
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
    def get_tracked_files(self):
        try:
            # Open the repository
            repo = Repo(os.getcwd(), search_parent_directories=True)
            
            # Get the root directory of the repository
            
            # Get all tracked files
            tracked_files = set(repo.git.ls_files().splitlines())
            
            # Get untracked files (excluding ignored ones)
            untracked_files = set(repo.git.ls_files(others=True, exclude_standard=True).splitlines())

            # Combine and sort the results
            all_files = sorted(tracked_files.union(untracked_files))

            
            return all_files
        
        except Exception as e:
            self.io.console.print(f"An error occurred: {e}", style="bold red")
            return []
    
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
            if input("To proceed, create the missing files? (y/n):").lower().strip() == 'y':
                with open(config.overview_file_path, "w") as f:
                    f.write("")
                
                with open(config.guidelines_file_path, "w") as f:
                    f.write("# Coding Guidelines\n\n")
            
                # allow to continue using pluscoder
            
            else:
                # otherwise, stop using pluscoder
                return False
        
        # Ask to add .plus_coder* to gitignore. Reads the file or create it if it doesn't exist
        if not os.path.isfile(".gitignore"):
            if input("Create the missing .gitignore file? (y/n):").lower().strip() == 'y':
                with open(".gitignore", "a") as f:
                    f.write("\n# Pluscoder\n")
                    f.write(".plus_coder*\n")
        else:
            with open(".gitignore", "r+") as f:
                if ".plus_coder*" not in f.read() and input("Add pluscoder files to gitignore (recommended)? (y/n):").lower().strip() == 'y':
                    f.write("\n# Pluscoder\n")
                    f.write(".plus_coder*\n")
        
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
        elif config.run_lint_after_edit and not config.lint_command:
            self.io.console.print("No lint command configured. Skipping linting.", style="bold dark_goldenrod")
            return None  # Return None as there's no error, just not configured
        
        # Run linter fix if configured
        if config.auto_run_linter_fix and config.lint_fix_command:
            subprocess.run(config.lint_fix_command, shell=True, check=False)
        
        try:
            subprocess.run(config.lint_command, shell=True, check=True, capture_output=True, text=True)
            return None  # Linting successful
        except subprocess.CalledProcessError as e:
            # Both stdout and stderr returned because stderr not showing 
            error_message = e.stdout if e.stdout else ''
            error_message += e.stderr if e.stderr else ''  # Append stderr to error message
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
        elif config.run_tests_after_edit and not config.test_command:
            self.io.console.print("No test command configured. Skipping tests.", style="bold dark_goldenrod")
            return None  # Return None as there's no error, just not configured
        
        try:
            subprocess.run(config.test_command, shell=True, check=True, capture_output=True, text=True)
            return None  # Tests successful
        except subprocess.CalledProcessError as e:
            # Both stdout and stderr returned because stderr not showing 
            error_message = e.stdout if e.stdout else ''
            error_message += e.stderr if e.stderr else ''  # Append stderr to error message
            return f"Tests failed:\n\n{error_message}"

    def generate_repomap(self) -> Optional[str]:
        """
        Generate a repository map using the logic from repomap2.py.
        
        Returns:
            Optional[str]: The generated repomap as a string if use_repomap is True,
                           None otherwise.
        """
        if not config.use_repomap:
            return None

        include_patterns = config.repomap_include_files or [r'.*\.(' + '|'.join(LANGUAGE_MAP.keys()) + ')$']
        exclude_patterns = config.repomap_exclude_files
        level = config.repomap_level

        tracked_files = self.get_tracked_files()
        return generate_tree(self.repo.working_tree_dir, include_patterns, exclude_patterns, level, tracked_files, self.io)


if __name__ == "__main__":
    repo = Repository()
    print("Tree:")
    pprint.pprint(repo.get_tracked_files())
    
    print("\n\nRepomap:")
    print(repo.generate_repomap())
    
    repo.run_test()
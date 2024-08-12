import os
import pprint
from click import style
from git import Actor, Repo
from pathlib import Path
from git import GitCommandError
from pluscoder.config import config

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
            repo_root = repo.working_tree_dir
            
            # Get all tracked files
            tracked_files = repo.git.ls_files().split('\n')
            
            return tracked_files
        
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
                    f.write("# Project Overview\n\n")
                
                with open(config.guidelines_file_path, "w") as f:
                    f.write("# Coding Guidelines\n\n")
            
                # allow to continue using pluscoder
                return True
            
            # otherwise, stop using pluscoder
            return False
        
        return True

        
if __name__ == "__main__":
    repo = Repository()
    pprint.pprint(repo.get_tracked_files())
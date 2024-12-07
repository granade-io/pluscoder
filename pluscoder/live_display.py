"""Live display system for rich console output with component management."""

import re
from abc import ABC
from abc import abstractmethod
from typing import Any
from typing import Dict
from typing import Optional

from rich.console import ConsoleRenderable
from rich.console import Group
from rich.console import RenderableType
from rich.console import RichCast
from rich.live import Live
from rich.progress import Progress
from rich.progress import SpinnerColumn
from rich.progress import TextColumn
from rich.text import Text

from pluscoder.display_utils import get_cost_usage_display
from pluscoder.type import TokenUsage


class BaseComponent(ABC):
    """Base class for live display components."""

    console = None
    show = True

    @abstractmethod
    def render(self) -> RenderableType:
        """Render the component.

        Returns:
            RenderableType: A rich-compatible renderable object
        """

    @abstractmethod
    def update(self, data: Any) -> None:
        """Update component with new data.

        Args:
            data: New data to update the component state
        """

    def start(self) -> None:
        """Starts a component. Many times this does nothing"""
        return

    def stop(self) -> None:
        """Stops a component. Many times this does nothing"""
        return


class FlexibleProgress(Live):
    """Custom live display with component management."""

    def __init__(self, *args, **kwargs):
        """Initialize custom live display.

        Args:
            refresh_per_second: Number of screen refreshes per second
        """
        self.components: Dict[str, BaseComponent] = {}
        super().__init__(*args, **kwargs)

    def register_component(self, name: str, component: BaseComponent) -> None:
        """Register a new component.

        Args:
            name: Unique identifier for the component
            component: Component instance to register
        """
        self.components[name] = component
        self.refresh()

    def update_component(self, name: str, data: Any, **kwargs) -> None:
        """Update a registered component with new data.

        Args:
            name: Component identifier
            data: New data for the component
        """
        if component := self.components.get(name):
            component.update(data, **kwargs)
            self.refresh()

    def get_component(self, name: str) -> Optional[BaseComponent]:
        """Get a registered component by name.

        Args:
            name: Component identifier

        Returns:
            Optional[BaseComponent]: The component if found, None otherwise
        """
        return self.components.get(name)

    # def refresh(self) -> None:
    #     """Refresh the display with current component states."""
    #     renderable = Group(*[comp.render() for comp in self.components.values()])
    #     self.update(renderable)
    #     super().refresh()

    def start(self, refresh: bool = False) -> None:
        for comp in self.components.values():
            comp.start()
        return super().start(refresh)

    def stop(self) -> None:
        for comp in self.components.values():
            comp.stop()
        return super().stop()

    def get_renderable(self) -> ConsoleRenderable | RichCast | str:
        return Group(*[comp.render() for comp in self.components.values()])


class TokenUsageComponent(BaseComponent):
    """Component for displaying token usage metrics."""

    def __init__(self):
        self.token_usage = TokenUsage()

    def render(self):
        text = get_cost_usage_display(self.token_usage)
        # Use regex to find numbers and surround them with [cyan]{number}[/cyan]
        text = re.sub(r"(\d+(?:\.\d+)?)", lambda m: f"[cyan]{m.group(1)}[/cyan]", text)
        return "[yellow]" + text + "[/yellow]"

    def update(self, token_usage):
        self.token_usage = token_usage


class IndexingComponent(BaseComponent):
    """Component for displaying indexing progress."""

    def __init__(self):
        self.indexing = False
        self.progress = Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"))

    def render(self):
        if not self.show:
            return Text("", end="")
        if not self.indexing:
            return Text("", end="")
        return self.progress

    def update(self, indexing):
        self.indexing = indexing
        if self.indexing:
            self.progress.add_task("[yellow]Still indexing repository for better suggestions...[/yellow]", start=True)
            self.progress.refresh()

    def start(self):
        self.show = True

    def stop(self):
        self.show = False


class TaskListComponent(BaseComponent):
    """Component for displaying task list progress."""

    def __init__(self):
        self.tasks = []
        self.progress = None
        self.task_progress_ids = {}
        self._current_action = None
        self._current_task_index = None
        self._live = None

    def render(self):
        if not self.tasks or not self.progress:
            return Text("", end="")
        return self.progress

    def update(self, data, action=None, task_index=None):
        """Update task list data.
        Args:
            data: List of AgentTask objects or dict with tasks list
            action: Optional action type ('new_task_list', 'delegate', 'validate', 'complete')
            task_index: Index of task being acted upon
        """
        if action in ["list_complete", "list_interrupted"]:
            self.progress.stop()
            self.progress = None
            self.task_progress_ids = {}
            return

        if isinstance(data, dict) and "task_list" in data:
            self.tasks = data["task_list"]
        elif isinstance(data, list):
            self.tasks = data
        else:
            self.tasks = []

        self._current_action = action
        self._current_task_index = task_index

        # Handle new task list creation
        if action == "new_task_list":
            self.progress = Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                auto_refresh=False,
            )
            self.task_progress_ids = {}
            for idx, task in enumerate(self.tasks):
                try:
                    description = (
                        f"[yellow][ ] {task.objective} - {task.agent}: Delegating..."
                        if idx == 0
                        else f"[ ] {task.objective} - {task.agent}"
                    )
                    task_id = self.progress.add_task(description, start=False, total=1)
                    self.task_progress_ids[idx] = task_id
                except AttributeError:
                    continue
            return

        # Update task descriptions based on state
        if self.progress and self.tasks:
            for idx, task in enumerate(self.tasks):
                try:
                    if idx not in self.task_progress_ids:
                        continue

                    description = task.objective
                    task_id = self.task_progress_ids[idx]

                    if idx < self._current_task_index:
                        # Completed tasks
                        self.progress.update(task_id, description=f"[green][✓] {description}")
                    elif idx == self._current_task_index and action:
                        # Current task with action
                        if action == "delegate":
                            self.progress.update(
                                task_id, description=f"[yellow][ ] {description} - {task.agent}: Delegating..."
                            )
                        elif action == "validate":
                            self.progress.update(
                                task_id, description=f"[yellow][ ] {description} - {task.agent}: Validating..."
                            )
                        elif action == "complete":
                            self.progress.update(task_id, description=f"[green][✓] {description}")
                    else:
                        # Pending tasks
                        self.progress.update(task_id, description=f"[ ] {description} - {task.agent}")
                except AttributeError:
                    continue

    def _get_or_create_progress_id(self, task_index):
        """Get existing progress ID or create new one for task index."""
        if task_index not in self.task_progress_ids:
            task_id = self.progress.add_task("", start=True)
            self.task_progress_ids[task_index] = task_id
        return self.task_progress_ids[task_index]

    def start(self):
        """Start progress display."""
        super().start()

    def stop(self):
        """Stop progress display."""
        super().stop()

import asyncio
from typing import Any
from typing import List

from pluscoder.agents.event.base import AgentEventBaseHandler
from pluscoder.config import config
from pluscoder.io_utils import IO
from pluscoder.live_display import IndexingComponent
from pluscoder.live_display import TaskListComponent
from pluscoder.live_display import TokenUsageComponent
from pluscoder.type import AgentInstructions
from pluscoder.type import AgentTask
from pluscoder.type import TokenUsage


class ConsoleAgentEventHandler(AgentEventBaseHandler):
    agent_instructions: AgentInstructions = None
    task_ids: List[int] = None
    token_usage: TokenUsage = {}

    def __init__(self, io: IO = None) -> None:
        """Initialize console event handler.
        Args:
            io: IO instance for console interactions
        """
        super().__init__()
        self.io = io
        self.progress = None
        self.usage_task_id = None
        self._initialized = False

        if self.io:
            self._initialize_components()

    def _initialize_components(self) -> None:
        """Initialize and register live display components."""
        if self._initialized:
            return

        try:
            # Register core components
            self.io.register_live_component("tasks", TaskListComponent())
            self.io.register_live_component("tokens", TokenUsageComponent())
            self.io.register_live_component("indexing", IndexingComponent())
            self._initialized = True
        except Exception as e:
            print(f"Error initializing components: {e}")
            self._initialized = False

    async def on_indexing_started(self, chunks: int = 0):
        """Display spinner when indexing starts."""
        self.io.update_live_component("indexing", {"total_chunks": chunks})

    async def on_indexing_progress(self, data):
        """Display spinner when indexing starts."""
        self.io.update_live_component("indexing", data)

    async def on_indexing_completed(self):
        """Update progress when indexing completes."""
        self.io.update_live_component("indexing", False)

    async def on_cost_update(self, token_usage: TokenUsage = {}):
        """Handle token usage updates with both live display and progress.
        Args:
            token_usage: Token usage information to display
        """
        if not config.show_token_usage or not self._initialized:
            return

        try:
            # Update live component
            self.io.update_live_component("tokens", token_usage)

            # Maintain progress support for backwards compatibility
            # text = get_cost_usage_display(token_usage)
            # if self.progress:
            #     if self.usage_task_id is None:
            #         self.usage_task_id = self.progress.add_task(text, start=True, completed=1, total=1)
            #     else:
            #         try:
            #             self.progress.update(self.usage_task_id, description=f"[yellow]{text}[/yellow]")
            #         except Exception:
            #             self.io.print(text, style="yellow")
        except Exception as e:
            print(f"Error updating token usage: {e}")

    async def on_new_agent_instructions(self, agent_instructions: AgentInstructions = None):
        """Initialize task display with both live components and progress."""
        self.agent_instructions = agent_instructions

        # Initialize task list with new_task_list action
        if self.agent_instructions and self.agent_instructions.task_list:
            self.io.update_live_component("tasks", self.agent_instructions.task_list, action="new_task_list")

    async def on_task_delegated(self, agent_instructions: AgentInstructions):
        """Handle task delegation with both live display and progress."""
        self.agent_instructions = agent_instructions

        # Update live component with latest task list
        if self.agent_instructions and self.agent_instructions.task_list:
            current_task = self.agent_instructions.get_current_task()
            if current_task:
                task_index = self.agent_instructions.task_list.index(current_task)
                self.io.update_live_component(
                    "tasks", self.agent_instructions.task_list, action="delegate", task_index=task_index
                )

    async def on_task_validation_start(self, agent_instructions: AgentInstructions):
        """Handle task validation with both live display and progress."""
        self.agent_instructions = agent_instructions

        # Update live component with latest task list
        if self.agent_instructions and self.agent_instructions.task_list:
            current_task = self.agent_instructions.get_current_task()
            if current_task:
                task_index = self.agent_instructions.task_list.index(current_task)
                self.io.update_live_component(
                    "tasks", self.agent_instructions.task_list, action="validate", task_index=task_index
                )

    async def on_task_completed(self, agent_instructions: AgentInstructions = None):
        """Handle task completion event."""
        self.agent_instructions = agent_instructions

        if self.agent_instructions and self.agent_instructions.task_list:
            current_task = self.agent_instructions.get_current_task()
            if current_task:
                task_index = self.agent_instructions.task_list.index(current_task) - 1

            else:
                task_index = len(self.agent_instructions.task_list) - 1
            self.io.update_live_component(
                "tasks", self.agent_instructions.task_list, action="complete", task_index=task_index
            )

    async def on_task_list_completed(self, agent_instructions: AgentInstructions = None):
        """Handle task list completion."""
        self.io.update_live_component("tasks", self.agent_instructions.task_list, action="list_complete")

    async def on_task_list_interrumpted(self, agent_instructions: AgentInstructions = None):
        """Handle task list interruption."""
        self.io.update_live_component("tasks", self.agent_instructions.task_list, action="list_interrupted")

    async def on_live_display_update(self, component_name: str, data: Any) -> None:
        """Handle generic live display updates.
        Args:
            component_name: Name of component to update
            data: New data for component
        """
        if not self._initialized:
            return

        try:
            self.io.update_live_component(component_name, data)
        except Exception as e:
            print(f"Error updating component {component_name}: {e}")

    def get_instructions_progress_text(self) -> str:
        objective = self.agent_instructions.general_objective
        total_tasks = self.agent_instructions.get_task_count()
        completed = self.agent_instructions.get_completed_task_count()
        color = "green" if completed == total_tasks else "yellow"

        if completed == total_tasks:
            return f"[{color}] ¡Completed! `{objective}` were successfully completed!"
        return f"[{color}]Completing `{objective}` {completed}/{total_tasks}..."


if __name__ == "__main__":
    import asyncio

    from pluscoder.io_utils import io

    async def main():
        handler = ConsoleAgentEventHandler(io=io)
        await handler.on_new_agent_instructions(
            AgentInstructions(
                general_objective="Complete tasks",
                resources=[],
                task_list=[
                    AgentTask(
                        objective="Task 1",
                        details="Task 1 details",
                        agent="domain_expert",
                        is_finished=False,
                    ),
                    AgentTask(
                        objective="Task 2",
                        details="Task 2 details",
                        agent="planning",
                        is_finished=False,
                    ),
                    AgentTask(
                        objective="Task 3",
                        details="Task 3 details",
                        agent="developer",
                        is_finished=False,
                    ),
                ],
            )
        )

        await asyncio.sleep(2)  # Simulate agent validation and delegation
        await handler.on_task_delegated(
            AgentInstructions(
                general_objective="Complete tasks",
                resources=[],
                task_list=[
                    AgentTask(
                        objective="Task 1",
                        details="Task 1 details",
                        agent="domain_expert",
                        is_finished=False,
                    ),
                    AgentTask(
                        objective="Task 2",
                        details="Task 2 details",
                        agent="planning",
                        is_finished=False,
                    ),
                    AgentTask(
                        objective="Task 3",
                        details="Task 3 details",
                        agent="developer",
                        is_finished=False,
                    ),
                ],
            )
        )
        await asyncio.sleep(2)  # Simulate agent validation and delegation
        await handler.on_task_validation_start(
            AgentInstructions(
                general_objective="Complete tasks",
                resources=[],
                task_list=[
                    AgentTask(
                        objective="Task 1",
                        details="Task 1 details",
                        agent="domain_expert",
                        is_finished=False,
                    ),
                    AgentTask(
                        objective="Task 2",
                        details="Task 2 details",
                        agent="planning",
                        is_finished=False,
                    ),
                    AgentTask(
                        objective="Task 3",
                        details="Task 3 details",
                        agent="developer",
                        is_finished=False,
                    ),
                ],
            )
        )
        await asyncio.sleep(2)
        await handler.on_task_completed(
            AgentInstructions(
                general_objective="Complete tasks",
                resources=[],
                task_list=[
                    AgentTask(
                        objective="Task 1",
                        details="Task 1 details",
                        agent="domain_expert",
                        is_finished=True,
                    ),
                    AgentTask(
                        objective="Task 2",
                        details="Task 2 details",
                        agent="planning",
                        is_finished=False,
                    ),
                    AgentTask(
                        objective="Task 3",
                        details="Task 3 details",
                        agent="developer",
                        is_finished=False,
                    ),
                ],
            )
        )
        await asyncio.sleep(2)  # Simulate agent completion
        await handler.on_task_delegated(
            AgentInstructions(
                general_objective="Complete tasks",
                resources=[],
                task_list=[
                    AgentTask(
                        objective="Task 1",
                        details="Task 1 details",
                        agent="domain_expert",
                        is_finished=True,
                    ),
                    AgentTask(
                        objective="Task 2",
                        details="Task 2 details",
                        agent="planning",
                        is_finished=False,
                    ),
                    AgentTask(
                        objective="Task 3",
                        details="Task 3 details",
                        agent="developer",
                        is_finished=False,
                    ),
                ],
            )
        )
        await asyncio.sleep(2)  # Simulate agent completion
        await handler.on_task_completed(
            AgentInstructions(
                general_objective="Complete tasks",
                resources=[],
                task_list=[
                    AgentTask(
                        objective="Task 1",
                        details="Task 1 details",
                        agent="domain_expert",
                        is_finished=True,
                    ),
                    AgentTask(
                        objective="Task 2",
                        details="Task 2 details",
                        agent="planning",
                        is_finished=True,
                    ),
                    AgentTask(
                        objective="Task 3",
                        details="Task 3 details",
                        agent="developer",
                        is_finished=False,
                    ),
                ],
            )
        )
        await asyncio.sleep(2)  # Simulate agent completion
        await handler.on_task_delegated(
            AgentInstructions(
                general_objective="Complete tasks",
                resources=[],
                task_list=[
                    AgentTask(
                        objective="Task 1",
                        details="Task 1 details",
                        agent="domain_expert",
                        is_finished=True,
                    ),
                    AgentTask(
                        objective="Task 2",
                        details="Task 2 details",
                        agent="planning",
                        is_finished=True,
                    ),
                    AgentTask(
                        objective="Task 3",
                        details="Task 3 details",
                        agent="developer",
                        is_finished=False,
                    ),
                ],
            )
        )
        await asyncio.sleep(2)  # Simulate agent completion
        await handler.on_task_completed(
            AgentInstructions(
                general_objective="Complete tasks",
                resources=[],
                task_list=[
                    AgentTask(
                        objective="Task 1",
                        details="Task 1 details",
                        agent="domain_expert",
                        is_finished=True,
                    ),
                    AgentTask(
                        objective="Task 2",
                        details="Task 2 details",
                        agent="planning",
                        is_finished=True,
                    ),
                    AgentTask(
                        objective="Task 3",
                        details="Task 3 details",
                        agent="developer",
                        is_finished=True,
                    ),
                ],
            )
        )
        await asyncio.sleep(2)  # Simulate agent completion

    asyncio.run(main())

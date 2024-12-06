import asyncio
import re
from typing import List

from rich.progress import SpinnerColumn
from rich.progress import TextColumn

from pluscoder.agents.event.base import AgentEventBaseHandler
from pluscoder.config import config
from pluscoder.display_utils import get_cost_usage_display
from pluscoder.io_utils import IO
from pluscoder.io_utils import CustomProgress
from pluscoder.type import AgentInstructions
from pluscoder.type import AgentTask
from pluscoder.type import TokenUsage


class ConsoleAgentEventHandler(AgentEventBaseHandler):
    agent_instructions: AgentInstructions = None
    task_ids: List[int] = None
    token_usage: TokenUsage = {}

    def __init__(self, io: IO = None) -> None:
        super().__init__()
        self.io = io

    def on_cost_update(self, token_usage: TokenUsage = {}):
        if not config.show_token_usage:
            return
        text = get_cost_usage_display(token_usage)
        if self.io.progress:
            # Use regex to find numbers and surround them with [cyan]{number}[/cyan]
            text = re.sub(r"(\d+(?:\.\d+)?)", lambda m: f"[cyan]{m.group(1)}[/cyan]", text)
            description = "[yellow]" + text + "[/yellow]"
            self.io.progress.update(self.usage_task_id, description=description)
        else:
            # Use regex to find numbers and surround them with [cyan]{number}[/cyan]
            self.io.console.print(text, style="yellow")

    async def on_new_agent_instructions(self, agent_instructions: AgentInstructions = None):
        self.agent_instructions = agent_instructions
        self.progress = CustomProgress(
            SpinnerColumn(),
            TextColumn("[white]{task.description}"),
            console=self.io.console,
            transient=False,
            auto_refresh=True,
        )
        self.io.set_progress(self.progress)
        self.task_ids = []
        for task in self.agent_instructions.task_list:
            task_id = self.progress.add_task(
                f"[ ] {task.objective} - {task.agent} agent"
                if not task.is_finished
                else f"[green][✓] {task.objective}",
                total=1,
                completed=1 if task.is_finished else 0,
            )
            self.task_ids.append(task_id)

        total_tasks = self.agent_instructions.get_task_count()
        self.task_id = self.progress.add_task(self.get_instructions_progress_text(), total=total_tasks)

        if config.show_token_usage:
            # Display token usage
            self.usage_task_id = self.progress.add_task(get_cost_usage_display({}), start=True, completed=1, total=1)

        self.progress.start()

    async def on_task_delegated(self, agent_instructions: AgentInstructions):
        self.agent_instructions = agent_instructions
        current_task = self.agent_instructions.get_current_task()
        if current_task:
            task_index = self.agent_instructions.task_list.index(current_task)
            self.progress.update(
                self.task_ids[task_index],
                description=f"[yellow][ ] {current_task.objective} - {current_task.agent}: Delegating...",
            )
            self.progress.update(self.task_id, description=self.get_instructions_progress_text())

    async def on_task_validation_start(self, agent_instructions: AgentInstructions):
        self.agent_instructions = agent_instructions
        current_task = self.agent_instructions.get_current_task()
        if current_task:
            task_index = self.agent_instructions.task_list.index(current_task)
            self.progress.update(
                self.task_ids[task_index],
                description=f"[yellow][ ] {current_task.objective} - {current_task.agent}: Validating...",
            )
            self.progress.update(self.task_id, description=self.get_instructions_progress_text())

    async def on_task_completed(self, agent_instructions: AgentInstructions = None):
        self.agent_instructions = agent_instructions
        completed_task = next(
            (
                task
                for task in self.agent_instructions.task_list
                if task.is_finished
                and not self.progress.tasks[self.task_ids[self.agent_instructions.task_list.index(task)]].completed
            ),
            None,
        )
        if completed_task:
            task_index = self.agent_instructions.task_list.index(completed_task)
            self.progress.update(
                self.task_ids[task_index],
                advance=1,
                description=f"[green][✓] {completed_task.objective}",
            )

        self.progress.update(self.task_id, advance=1, description=self.get_instructions_progress_text())
        self.progress.refresh()

    async def on_task_list_completed(self, agent_instructions: AgentInstructions = None):
        self.progress.refresh()
        self.io.set_progress(None)
        self.progress.stop()

    async def on_task_list_interrumpted(self, agent_instructions: AgentInstructions = None):
        self.io.set_progress(None)
        self.progress.stop()

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

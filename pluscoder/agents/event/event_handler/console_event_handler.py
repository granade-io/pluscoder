from time import sleep
import asyncio
from typing import List
from pluscoder.agents.event.base import AgentEventBaseHandler
from rich.progress import Progress, SpinnerColumn, TextColumn, TaskProgressColumn, BarColumn

from pluscoder.io_utils import IO, CustomProgress
from pluscoder.type import AgentInstructions, AgentTask


class ConsoleAgentEventHandler(AgentEventBaseHandler):
    agent_instructions: AgentInstructions = None
    task_ids: List[int] = None
    
    def __init__(self, io: IO=None) -> None:
        super().__init__()
        self.io = io
    
    async def on_new_agent_instructions(self, agent_instructions: AgentInstructions = None):
        self.agent_instructions = agent_instructions
        self.progress = CustomProgress(SpinnerColumn(), TextColumn("[white]{task.description}"), console=self.io.console, transient=False)
        self.io.set_progress(self.progress)
        self.task_ids = []
        first_incomplete = True
        for task in self.agent_instructions.task_list:
            task_id = self.progress.add_task(f"[ ] {task.objective} - {task.agent} agent", total=1)
            self.task_ids.append(task_id)

        total_tasks = self.agent_instructions.get_task_count()
        self.task_id = self.progress.add_task(self.get_instructions_progress_text(), total=total_tasks)

        self.progress.start()

    async def on_task_delegated(self, agent_instructions: AgentInstructions):
        self.agent_instructions = agent_instructions
        current_task = self.agent_instructions.get_current_task()
        if current_task:
            task_index = self.agent_instructions.task_list.index(current_task)
            self.progress.update(self.task_ids[task_index], description=f"[yellow][ ] {current_task.objective} - {current_task.agent}: Delegating...")
            self.progress.update(self.task_id, description=self.get_instructions_progress_text())

    async def on_task_validation_start(self, agent_instructions: AgentInstructions):
        self.agent_instructions = agent_instructions
        current_task = self.agent_instructions.get_current_task()
        if current_task:
            task_index = self.agent_instructions.task_list.index(current_task)
            self.progress.update(self.task_ids[task_index], description=f"[yellow][ ] {current_task.objective} - {current_task.agent}: Validating...")
            self.progress.update(self.task_id, description=self.get_instructions_progress_text())

    async def on_task_completed(self, agent_instructions: AgentInstructions = None):
        self.agent_instructions = agent_instructions
        completed_task = next((task for task in self.agent_instructions.task_list if task.is_finished and not self.progress.tasks[self.task_ids[self.agent_instructions.task_list.index(task)]].completed), None)
        if completed_task:
            task_index = self.agent_instructions.task_list.index(completed_task)
            self.progress.update(self.task_ids[task_index], advance=1, description=f"[green][✓] {completed_task.objective}")
        
        self.progress.update(self.task_id, advance=1, description=self.get_instructions_progress_text())


    async def on_task_list_completed(self, agent_instructions: AgentInstructions = None):
        asyncio.sleep(1)
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
    import time
    from io_utils import io

    async def main():
        handler = ConsoleAgentEventHandler(io=io)
        await handler.on_new_agent_instructions(AgentInstructions(general_objective="Complete tasks", task_list=[
            AgentTask(objective="Task 1", details="Task 1 details", agent="domain_expert", is_finished=False),
            AgentTask(objective="Task 2", details="Task 2 details", agent="planning", is_finished=False),
            AgentTask(objective="Task 3", details="Task 3 details", agent="developer", is_finished=False),
        ]))

        await asyncio.sleep(2)  # Simulate agent validation and delegation
        await handler.on_task_delegated(AgentInstructions(general_objective="Complete tasks", task_list=[
            AgentTask(objective="Task 1", details="Task 1 details", agent="domain_expert", is_finished=False),
            AgentTask(objective="Task 2", details="Task 2 details", agent="planning", is_finished=False),
            AgentTask(objective="Task 3", details="Task 3 details", agent="developer", is_finished=False),
        ]))
        await asyncio.sleep(2)  # Simulate agent validation and delegation
        await handler.on_task_validation_start(AgentInstructions(general_objective="Complete tasks", task_list=[
            AgentTask(objective="Task 1", details="Task 1 details", agent="domain_expert", is_finished=False),
            AgentTask(objective="Task 2", details="Task 2 details", agent="planning", is_finished=False),
            AgentTask(objective="Task 3", details="Task 3 details", agent="developer", is_finished=False),
        ]))
        await asyncio.sleep(2)
        await handler.on_task_completed(AgentInstructions(general_objective="Complete tasks", task_list=[
            AgentTask(objective="Task 1", details="Task 1 details", agent="domain_expert", is_finished=True),
            AgentTask(objective="Task 2", details="Task 2 details", agent="planning", is_finished=False),
            AgentTask(objective="Task 3", details="Task 3 details", agent="developer", is_finished=False),
        ]))
        await asyncio.sleep(2)  # Simulate agent completion
        await handler.on_task_delegated(AgentInstructions(general_objective="Complete tasks", task_list=[
            AgentTask(objective="Task 1", details="Task 1 details", agent="domain_expert", is_finished=True),
            AgentTask(objective="Task 2", details="Task 2 details", agent="planning", is_finished=False),
            AgentTask(objective="Task 3", details="Task 3 details", agent="developer", is_finished=False),
        ]))
        await asyncio.sleep(2)  # Simulate agent completion
        await handler.on_task_completed(AgentInstructions(general_objective="Complete tasks", task_list=[
            AgentTask(objective="Task 1", details="Task 1 details", agent="domain_expert", is_finished=True),
            AgentTask(objective="Task 2", details="Task 2 details", agent="planning", is_finished=True),
            AgentTask(objective="Task 3", details="Task 3 details", agent="developer", is_finished=False),
        ]))
        await asyncio.sleep(2)  # Simulate agent completion
        await handler.on_task_delegated(AgentInstructions(general_objective="Complete tasks", task_list=[
            AgentTask(objective="Task 1", details="Task 1 details", agent="domain_expert", is_finished=True),
            AgentTask(objective="Task 2", details="Task 2 details", agent="planning", is_finished=True),
            AgentTask(objective="Task 3", details="Task 3 details", agent="developer", is_finished=False),
        ]))
        await asyncio.sleep(2)  # Simulate agent completion
        await handler.on_task_completed(AgentInstructions(general_objective="Complete tasks", task_list=[
            AgentTask(objective="Task 1", details="Task 1 details", agent="domain_expert", is_finished=True),
            AgentTask(objective="Task 2", details="Task 2 details", agent="planning", is_finished=True),
            AgentTask(objective="Task 3", details="Task 3 details", agent="developer", is_finished=True),
        ]))
        await asyncio.sleep(2)  # Simulate agent completion
    asyncio.run(main())
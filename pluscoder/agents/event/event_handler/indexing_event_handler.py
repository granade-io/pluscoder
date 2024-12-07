"""Handler for search index building events."""

import logging

from pluscoder.agents.event.base import AgentEventBaseHandler
from pluscoder.io_utils import IO

logger = logging.getLogger(__name__)


class IndexingEventHandler(AgentEventBaseHandler):
    """Handler for displaying search indexing progress."""

    def __init__(self, io: IO | None = None) -> None:
        """Initialize handler with IO instance."""
        super().__init__()
        self.io = io
        self.progress = None
        self.task_id = None

    async def on_indexing_started(self, files=[]):
        """Display spinner when indexing starts."""
        # Safely stop any existing progress
        # if self.io.progress:
        #     with contextlib.suppress(Exception):
        #         self.io.progress.stop()
        #         self.io.set_progress(None)

        # try:
        #     self.progress = CustomProgress(
        #         SpinnerColumn(),
        #         TextColumn("[white]{task.description}"),
        #         console=self.io.console,
        #         transient=True,
        #         auto_refresh=True,
        #     )
        #     self.io.set_progress(self.progress)
        #     self.task_id = self.progress.add_task("[yellow]Building search index...", total=1)
        #     self.progress.start()
        # except Exception as e:
        #     logger.error("Failed to start indexing progress: %s", str(e))

    async def on_indexing_completed(self):
        """Update progress when indexing completes."""
        # if self.progress:
        #     try:
        #         self.progress.update(self.task_id, advance=1, description="[green]Search index built successfully!")
        #         self.progress.refresh()
        #     except Exception as e:
        #         logger.error("Failed to complete indexing progress: %s", str(e))
        #     finally:
        #         with contextlib.suppress(Exception):
        #             self.io.set_progress(None)
        #             self.progress.stop()

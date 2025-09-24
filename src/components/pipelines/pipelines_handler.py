"""Minimal pipeline handler for Cycloid MCP server."""

from src.base_handler import BaseHandler
from src.cli_mixin import CLIMixin
from src.types import JSONList


class PipelineHandler(BaseHandler):
    """Minimal pipeline handler."""

    def __init__(self, cli: CLIMixin):
        """Initialize pipeline handler with CLI mixin."""
        super().__init__(cli)

    async def get_pipelines(self) -> JSONList:
        """Get pipelines from CLI - minimal implementation."""
        try:
            # Try to get actual pipeline data
            pipelines_data = await self.cli.execute_cli(
                "pipeline", ["list"], output_format="json"
            )

            processed_data = self.cli.process_cli_response(pipelines_data)

            return processed_data
        except Exception as e:
            self.logger.error(f"Error getting pipelines: {e}")
            return []

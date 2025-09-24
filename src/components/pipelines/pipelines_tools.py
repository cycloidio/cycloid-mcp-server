"""Minimal pipeline MCP tools."""

from typing import Any, Dict

from fastmcp.contrib.mcp_mixin import MCPMixin, mcp_tool
from fastmcp.utilities.logging import get_logger

from src.cli_mixin import CLIMixin

from .pipelines_handler import PipelineHandler

logger = get_logger(__name__)


class PipelineTools(MCPMixin):
    """Minimal tools for working with Cycloid Pipelines."""

    def __init__(self, cli: CLIMixin):
        """Initialize pipeline tools with CLI mixin."""
        super().__init__()
        self.handler = PipelineHandler(cli)

    @mcp_tool(
        name="CYCLOID_PIPELINE_LIST",
        description="List all pipelines from Cycloid.",
        enabled=True,
    )
    async def list_pipelines(self, format: str = "summary") -> str | Dict[str, Any]:
        """List all pipelines.

        Args:
            format: Output format ("summary" or "json")
        """
        try:
            pipelines = await self.handler.get_pipelines()

            if format == "json":
                return {
                    "pipelines": pipelines,
                    "count": len(pipelines)
                }
            else:
                return f"🚀 Pipelines\n\nFound {len(pipelines)} pipelines."

        except Exception as e:
            error_msg = f"❌ Error listing pipelines: {str(e)}"
            logger.error("Error listing pipelines", extra={"error": str(e)})
            return error_msg

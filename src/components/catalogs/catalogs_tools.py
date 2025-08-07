"""Catalog MCP tools."""

from typing import Any, Dict

from fastmcp.contrib.mcp_mixin import MCPMixin, mcp_tool
from fastmcp.utilities.logging import get_logger

from src.cli_mixin import CLIMixin
from src.error_handling import handle_errors

from .catalogs_handler import CatalogHandler

logger = get_logger(__name__)


class CatalogTools(MCPMixin):
    """Catalog MCP tools."""

    def __init__(self, cli: CLIMixin):
        """Initialize catalog tools with CLI mixin."""
        super().__init__()
        self.handler = CatalogHandler(cli)

    @mcp_tool(
        name="CYCLOID_CATALOG_REPO_LIST",
        description=(
            "List all available service catalog repositories with their details. "
            "The LLM can filter the results based on user requirements."
        ),
        enabled=True,
    )
    @handle_errors(
        action="list catalog repositories",
        return_on_error=(
            "❌ Failed to retrieve catalog repositories. Please check your configuration."
        ),
        suggestions=[
            "Verify your Cycloid CLI is properly configured",
            "Check your API credentials and organization access",
            "Ensure you have permission to view catalog repositories",
        ],
    )
    async def list_catalog_repositories(self, format: str = "table") -> str | Dict[str, Any]:
        """List all available service catalog repositories.

        This tool provides access to all catalog repositories with their details.
        The LLM can filter the results based on user requirements.

        Args:
            format: Output format ("table" or "json")
        """
        # Get repositories using shared logic
        repositories = await self.handler.get_catalog_repositories()

        # Format output
        if format == "json":
            result = {"repositories": repositories, "count": len(repositories)}
            return result
        else:
            table_result = self.handler.format_table_output(repositories, "")
            return table_result

"""Catalog MCP resources."""

import json

from fastmcp.contrib.mcp_mixin import MCPMixin, mcp_resource
from fastmcp.utilities.logging import get_logger

from src.cli_mixin import CLIMixin
from src.exceptions import CycloidCLIError

from .catalogs_handler import CatalogHandler

logger = get_logger(__name__)


class CatalogResources(MCPMixin):
    """Catalog MCP resources."""

    def __init__(self, cli: CLIMixin):
        """Initialize catalog resources with CLI mixin."""
        super().__init__()
        self.handler = CatalogHandler(cli)

    @mcp_resource("cycloid://service-catalogs-repositories")
    async def get_service_catalogs_resource(self) -> str:
        """Get all available service catalog repositories as a resource."""
        try:
            # Get repositories using shared logic
            repositories = await self.handler.get_catalog_repositories()

            # Format as JSON with both raw data and formatted table
            result = {
                "repositories": repositories,
                "count": len(repositories),
                "formatted_table": self.handler.format_table_output(repositories, ""),
            }

            return json.dumps(result, indent=2)

        except CycloidCLIError as e:
            logger.error(f"Failed to read service catalogs resource: {str(e)}")
            return json.dumps(
                {
                    "error": f"Failed to load service catalog repositories: {str(e)}",
                    "repositories": [],
                    "count": 0,
                },
                indent=2,
            )

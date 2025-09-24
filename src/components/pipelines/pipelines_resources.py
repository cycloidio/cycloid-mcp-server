"""Pipeline MCP resources."""

import json

from fastmcp.contrib.mcp_mixin import MCPMixin, mcp_resource
from fastmcp.utilities.logging import get_logger

from src.cli_mixin import CLIMixin

from .pipelines_handler import PipelineHandler

logger = get_logger(__name__)


class PipelineResources(MCPMixin):
    """Pipeline MCP resources."""

    def __init__(self, cli: CLIMixin):
        """Initialize pipeline resources with CLI mixin."""
        super().__init__()
        self.handler = PipelineHandler(cli)

    @mcp_resource("cycloid://pipelines")
    async def get_pipelines_resource(self) -> str:
        """Get all pipelines as a resource."""
        try:
            result = {
                "message": "Pipeline resources are working!"
            }

            return json.dumps(result, indent=2)

        except Exception as e:
            error_str = str(e)
            error_msg = (
                f"Failed to read pipelines resource: {error_str}"
            )
            logger.error(error_msg)
            return json.dumps(
                {
                    "error": f"Failed to load pipelines: {error_str}",
                    "pipelines": [],
                    "count": 0,
                },
                indent=2,
            )

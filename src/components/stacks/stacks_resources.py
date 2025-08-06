"""Stack MCP resources."""

import json

from fastmcp.contrib.mcp_mixin import MCPMixin, mcp_resource
from fastmcp.utilities.logging import get_logger

from src.cli_mixin import CLIMixin
from src.exceptions import CycloidCLIError

from .stacks_handler import StackHandler

logger = get_logger(__name__)


class StackResources(MCPMixin):
    """Stack MCP resources."""

    def __init__(self, cli: CLIMixin):
        """Initialize stack resources with CLI mixin."""
        super().__init__()
        self.handler = StackHandler(cli)

    @mcp_resource("cycloid://blueprints")
    async def get_blueprints_resource(self) -> str:
        """Get all available blueprints as a resource."""
        try:
            # Get blueprints using shared logic
            blueprints = await self.handler.get_blueprints()

            # Format as JSON with both raw data and formatted table
            result = {
                "blueprints": blueprints,
                "count": len(blueprints),
                "formatted_table": self.handler.format_blueprint_table_output(
                    blueprints, ""
                ),  # noqa: E501
            }

            return json.dumps(result, indent=2)

        except CycloidCLIError as e:
            error_str = str(e)
            error_msg = f"Failed to read blueprints resource: {error_str}"  # noqa: E501
            logger.error(error_msg)
            return json.dumps(
                {
                    "error": f"Failed to load blueprints: {error_str}",
                    "blueprints": [],
                    "count": 0,
                },
                indent=2,
            )

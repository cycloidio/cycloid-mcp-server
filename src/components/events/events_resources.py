"""Event MCP resources."""

# Standard library imports
import json

# Third-party imports
from fastmcp.contrib.mcp_mixin import MCPMixin, mcp_resource
from fastmcp.utilities.logging import get_logger

# Local imports
from src.cli_mixin import CLIMixin
from .events_handler import EventHandler

logger = get_logger(__name__)


class EventResources(MCPMixin):
    """Event MCP resources."""

    def __init__(self, cli: CLIMixin):
        """Initialize event resources with CLI mixin."""
        super().__init__()
        self.handler = EventHandler(cli)

    @mcp_resource("cycloid://events")
    async def get_events_resource(self) -> str:
        """Get all events as a resource with minimal formatting."""
        try:
            events = await self.handler.list_events()
            result = {
                "events": events,
                "count": len(events),
            }
            return json.dumps(result, indent=2)
        except Exception as e:
            logger.error("Failed to fetch events resource", extra={"error": str(e)})
            return json.dumps({"error": str(e), "events": [], "count": 0}, indent=2)

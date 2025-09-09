"""Event MCP tools."""

# Standard library imports
import json

# Third-party imports
from fastmcp.contrib.mcp_mixin import MCPMixin, mcp_tool
from fastmcp.utilities.logging import get_logger

# Local imports
from src.cli_mixin import CLIMixin
from src.types import OptionalString, OptionalStringList
from .events_handler import EventHandler

logger = get_logger(__name__)


class EventTools(MCPMixin):
    """Tools for working with Cycloid Events."""

    def __init__(self, cli: CLIMixin):
        """Initialize event tools with CLI mixin."""
        super().__init__()
        self.handler = EventHandler(cli)

    @mcp_tool(
        name="CYCLOID_EVENT_LIST",
        description=(
            "List organization events with optional filters (begin, end, severity, type)."
        ),
        enabled=True,
    )
    async def list_events(
        self,
        format: str = "json",
        begin: OptionalString = None,
        end: OptionalString = None,
        severity: OptionalStringList = None,
        type: OptionalStringList = None,
    ) -> str:
        """List events from Cycloid.

        Args:
            format: Output format ("json" or "table"). Defaults to "json".
            begin: Unix timestamp (string) start date.
            end: Unix timestamp (string) end date.
            severity: List of severities to include.
            type: List of event types to include.
        """
        try:
            events = await self.handler.list_events(
                begin=begin, end=end, severity=severity, type=type
            )

            if format == "json":
                return json.dumps({"events": events, "count": len(events)}, indent=2)

            # Fallback simple table formatting
            if not events:
                return "📋 Events\n\nNo events found."

            header = "| ID | Timestamp | Severity | Type | Title |"
            sep = "|----|-----------|----------|------|-------|"
            lines = ["# Events", "", f"Found {len(events)} events", "", header, sep]
            for ev in events:
                ev_id = ev.get("id", "")
                ts = ev.get("timestamp", "")
                sev = ev.get("severity", "")
                ev_type = ev.get("type", "")
                title = ev.get("title", "")
                lines.append(f"| {ev_id} | {ts} | {sev} | {ev_type} | {title} |")
            return "\n".join(lines)

        except Exception as e:
            logger.error("Error listing events", extra={"error": str(e)})
            return f"❌ Error listing events: {str(e)}"

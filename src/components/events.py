"""Event tools and resources for Cycloid MCP server."""

import json
from typing import Any, Dict, List

from fastmcp.dependencies import Depends  # type: ignore[reportAttributeAccessIssue]
from fastmcp.exceptions import ToolError
from fastmcp.resources import resource
from fastmcp.tools import tool
from fastmcp.utilities.logging import get_logger

from src.cli import CLIMixin
from src.dependencies import get_cli
from src.display_hints import build_display_hints
from src.exceptions import CycloidCLIError
from src.types import JSONDict, JSONList, OptionalString, OptionalStringList

logger = get_logger(__name__)


async def _list_events(
    cli: CLIMixin,
    begin: OptionalString = None,
    end: OptionalString = None,
    severity: OptionalStringList = None,
    type: OptionalStringList = None,
) -> JSONList:
    """List events using `cy event list` with optional filters."""
    args: List[str] = ["list"]

    flags: JSONDict = {}
    if begin:
        flags["begin"] = begin
    if end:
        flags["end"] = end
    if severity:
        flags["severity"] = ",".join(severity)
    if type:
        flags["type"] = ",".join(type)

    events_data = await cli.execute_cli("event", args, flags=flags)
    return cli.process_cli_response(events_data, list_key=None)


@tool(
    name="CYCLOID_EVENT_LIST",
    description=(
        "List organization events with optional filters (begin, end, severity, type). "
        "DISPLAY GUIDANCE: Present as a markdown table. Key fields: title (Title), "
        "severity (Severity), type (Type), timestamp (Timestamp). "
        "Full JSON details available on request."
    ),
    annotations={"readOnlyHint": True},
)
async def list_events(
    begin: OptionalString = None,
    end: OptionalString = None,
    severity: OptionalStringList = None,
    type: OptionalStringList = None,
    cli: CLIMixin = Depends(get_cli),  # type: ignore[reportCallInDefaultInitializer]
) -> Dict[str, Any]:
    """List events from Cycloid.

    Args:
        begin: Unix timestamp (string) start date.
        end: Unix timestamp (string) end date.
        severity: List of severities to include.
        type: List of event types to include.
    """
    try:
        events = await _list_events(cli, begin=begin, end=end, severity=severity, type=type)
        return {
            "events": events,
            "count": len(events),
            "_display_hints": build_display_hints(
                key_fields=["title", "severity", "type", "timestamp"],
                display_format="table",
                columns={
                    "title": "Title",
                    "severity": "Severity",
                    "type": "Type",
                    "timestamp": "Timestamp",
                },
                sort_by="timestamp",
            ),
        }
    except CycloidCLIError as e:
        raise ToolError(f"Failed to list events: {str(e)}")
    except Exception as e:
        raise ToolError(f"Error listing events: {str(e)}")


@resource("cycloid://events")
async def get_events_resource(
    cli: CLIMixin = Depends(get_cli),  # type: ignore[reportCallInDefaultInitializer]
) -> str:
    """Get all events as a resource."""
    try:
        events = await _list_events(cli)
        result = {
            "events": events,
            "count": len(events),
        }
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error("Failed to fetch events resource", extra={"error": str(e)})
        return json.dumps({"error": str(e), "events": [], "count": 0}, indent=2)

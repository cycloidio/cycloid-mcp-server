"""Member tools for Cycloid MCP server."""

from typing import Any, Dict

from fastmcp.dependencies import Depends  # type: ignore[reportAttributeAccessIssue]
from fastmcp.exceptions import ToolError
from fastmcp.tools import tool
from fastmcp.utilities.logging import get_logger

from src.cli import CLIMixin
from src.dependencies import get_cli
from src.display_hints import build_display_hints
from src.exceptions import CycloidCLIError
from src.types import JSONList

logger = get_logger(__name__)


async def _list_members(cli: CLIMixin) -> JSONList:
    """List organization members via `cy members list`."""
    members_data = await cli.execute_cli("members", ["list"])
    return cli.process_cli_response(members_data, list_key=None)


@tool(
    name="CYCLOID_MEMBER_LIST",
    description=(
        "List all members of the organization. "
        "Use this to look up a member's numeric `id` from their `username`. "
        "The `id` field is required to build member URLs: "
        "/organizations/<org>/members/<id>. "
        "DISPLAY GUIDANCE: Present as a markdown table. Key fields: username (Username), "
        "full_name (Full Name), role (Role). Full JSON details available on request."
    ),
    annotations={"readOnlyHint": True},
)
async def list_members(
    cli: CLIMixin = Depends(get_cli),  # type: ignore[reportCallInDefaultInitializer]
) -> Dict[str, Any]:
    """List all organization members.

    Returns members with id, username, full_name, email, and role fields
    for cross-referencing event actor usernames to numeric member ids.
    """
    try:
        members = await _list_members(cli)
        return {
            "members": members,
            "count": len(members),
            "_display_hints": build_display_hints(
                key_fields=["username", "full_name", "role"],
                display_format="table",
                columns={
                    "username": "Username",
                    "full_name": "Full Name",
                    "role": "Role",
                },
                sort_by="username",
            ),
        }
    except CycloidCLIError as e:
        raise ToolError(f"Failed to list members: {str(e)}")
    except Exception as e:
        raise ToolError(f"Error listing members: {str(e)}")

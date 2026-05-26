"""Component tools for Cycloid MCP server.

Wraps the `cy components` CLI subcommand (project-scoped infrastructure components).
"""

from typing import Any, Dict, List

from fastmcp.dependencies import Depends  # type: ignore[reportAttributeAccessIssue]
from fastmcp.exceptions import ToolError
from fastmcp.tools import tool
from fastmcp.utilities.logging import get_logger

from src.cli import CLIMixin
from src.dependencies import get_cli
from src.display_hints import build_display_hints
from src.exceptions import CycloidCLIError
from src.types import JSONList, StringList

logger = get_logger(__name__)


async def _list_components(cli: CLIMixin, project: str, env: str) -> JSONList:
    """List components in a project environment."""
    components_data = await cli.execute_cli(
        "components", ["list"], flags={"project": project, "env": env}
    )
    return cli.process_cli_response(components_data, list_key=None)


async def _get_components(
    cli: CLIMixin, project: str, env: str, canonicals: StringList
) -> JSONList:
    """Get one or more components by canonical."""
    args: List[str] = ["get", *canonicals]
    components_data = await cli.execute_cli(
        "components", args, flags={"project": project, "env": env}
    )

    if isinstance(components_data, dict):
        return [components_data]
    return cli.process_cli_response(components_data, list_key=None)


@tool(
    name="CYCLOID_COMPONENT_LIST",
    description=(
        "List components in a project environment. "
        "DISPLAY GUIDANCE: Present as a markdown table. Key fields: name (Component), "
        "canonical (Canonical), status (Status), service_catalog_ref (Stack). "
        "Full JSON details available on request."
    ),
    annotations={"readOnlyHint": True},
)
async def list_components(
    project: str,
    env: str,
    cli: CLIMixin = Depends(get_cli),  # type: ignore[reportCallInDefaultInitializer]
) -> Dict[str, Any]:
    """List components in a project environment.

    Args:
        project: The project canonical.
        env: The environment canonical.
    """
    if not project:
        raise ToolError("Project canonical is required")
    if not env:
        raise ToolError("Environment canonical is required")

    try:
        components = await _list_components(cli, project, env)
        return {
            "components": components,
            "count": len(components),
            "_display_hints": build_display_hints(
                key_fields=["name", "canonical", "status", "service_catalog_ref"],
                display_format="table",
                columns={
                    "name": "Component",
                    "canonical": "Canonical",
                    "status": "Status",
                    "service_catalog_ref": "Stack",
                },
                sort_by="name",
            ),
        }
    except CycloidCLIError as e:
        raise ToolError(f"Failed to list components: {str(e)}")
    except Exception as e:
        raise ToolError(f"Error listing components: {str(e)}")


@tool(
    name="CYCLOID_COMPONENT_GET",
    description=(
        "Get the state of one or more components in a project environment. "
        "DISPLAY GUIDANCE: Present as a markdown table when multiple, "
        "or a detail block when single. Key fields: name (Component), "
        "canonical (Canonical), status (Status), service_catalog_ref (Stack). "
        "Full JSON details available on request."
    ),
    annotations={"readOnlyHint": True},
)
async def get_components(
    project: str,
    env: str,
    canonicals: StringList,
    cli: CLIMixin = Depends(get_cli),  # type: ignore[reportCallInDefaultInitializer]
) -> Dict[str, Any]:
    """Get one or more components by canonical.

    Args:
        project: The project canonical.
        env: The environment canonical.
        canonicals: List of component canonicals to fetch.
    """
    if not project:
        raise ToolError("Project canonical is required")
    if not env:
        raise ToolError("Environment canonical is required")
    if not canonicals:
        raise ToolError("At least one component canonical is required")

    try:
        components = await _get_components(cli, project, env, canonicals)
        return {
            "components": components,
            "count": len(components),
        }
    except CycloidCLIError as e:
        raise ToolError(f"Failed to get components: {str(e)}")
    except Exception as e:
        raise ToolError(f"Error getting components: {str(e)}")

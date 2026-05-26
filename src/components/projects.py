"""Project tools and resources for Cycloid MCP server."""

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
from src.types import JSONList, StringList

logger = get_logger(__name__)


async def _list_projects(cli: CLIMixin) -> JSONList:
    """List projects from CLI."""
    projects_data = await cli.execute_cli("project", ["list"])
    return cli.process_cli_response(projects_data, list_key=None)


async def _get_projects(cli: CLIMixin, canonicals: StringList) -> JSONList:
    """Get one or more projects by canonical."""
    args: List[str] = ["get", *canonicals]
    projects_data = await cli.execute_cli("project", args)

    if isinstance(projects_data, dict):
        return [projects_data]
    return cli.process_cli_response(projects_data, list_key=None)


async def _list_project_envs(cli: CLIMixin, project: str) -> JSONList:
    """List environments in a project."""
    envs_data = await cli.execute_cli(
        "project", ["list-env"], flags={"project": project}
    )
    return cli.process_cli_response(envs_data, list_key=None)


@tool(
    name="CYCLOID_PROJECT_LIST",
    description=(
        "List all projects in the organization. "
        "DISPLAY GUIDANCE: Present as a markdown table. Key fields: name (Project), "
        "canonical (Canonical), description (Description), owner (Owner). "
        "Full JSON details available on request."
    ),
    annotations={"readOnlyHint": True},
)
async def list_projects(
    cli: CLIMixin = Depends(get_cli),  # type: ignore[reportCallInDefaultInitializer]
) -> Dict[str, Any]:
    """List all projects.

    Returns a dict with projects list and count.
    """
    try:
        projects = await _list_projects(cli)
        return {
            "projects": projects,
            "count": len(projects),
            "_display_hints": build_display_hints(
                key_fields=["name", "canonical", "description", "owner"],
                display_format="table",
                columns={
                    "name": "Project",
                    "canonical": "Canonical",
                    "description": "Description",
                    "owner": "Owner",
                },
                sort_by="name",
            ),
        }
    except CycloidCLIError as e:
        raise ToolError(f"Failed to list projects: {str(e)}")
    except Exception as e:
        raise ToolError(f"Error listing projects: {str(e)}")


@tool(
    name="CYCLOID_PROJECT_GET",
    description=(
        "Get one or more projects by canonical. "
        "DISPLAY GUIDANCE: Present as a markdown table when multiple, "
        "or a detail block when single. Key fields: name (Project), "
        "canonical (Canonical), description (Description), owner (Owner). "
        "Full JSON details available on request."
    ),
    annotations={"readOnlyHint": True},
)
async def get_projects(
    canonicals: StringList,
    cli: CLIMixin = Depends(get_cli),  # type: ignore[reportCallInDefaultInitializer]
) -> Dict[str, Any]:
    """Get one or more projects by canonical.

    Args:
        canonicals: List of project canonicals to fetch.
    """
    if not canonicals:
        raise ToolError("At least one project canonical is required")

    try:
        projects = await _get_projects(cli, canonicals)
        return {
            "projects": projects,
            "count": len(projects),
        }
    except CycloidCLIError as e:
        raise ToolError(f"Failed to get projects: {str(e)}")
    except Exception as e:
        raise ToolError(f"Error getting projects: {str(e)}")


@tool(
    name="CYCLOID_PROJECT_LIST_ENV",
    description=(
        "List environments in a project. "
        "DISPLAY GUIDANCE: Present as a markdown table. Key fields: canonical (Environment), "
        "color (Color), icon (Icon). "
        "Full JSON details available on request."
    ),
    annotations={"readOnlyHint": True},
)
async def list_project_envs(
    project: str,
    cli: CLIMixin = Depends(get_cli),  # type: ignore[reportCallInDefaultInitializer]
) -> Dict[str, Any]:
    """List environments in a project.

    Args:
        project: The project canonical.
    """
    if not project:
        raise ToolError("Project canonical is required")

    try:
        environments = await _list_project_envs(cli, project)
        return {
            "environments": environments,
            "count": len(environments),
            "_display_hints": build_display_hints(
                key_fields=["canonical", "color", "icon"],
                display_format="table",
                columns={
                    "canonical": "Environment",
                    "color": "Color",
                    "icon": "Icon",
                },
                sort_by="canonical",
            ),
        }
    except CycloidCLIError as e:
        raise ToolError(f"Failed to list project environments: {str(e)}")
    except Exception as e:
        raise ToolError(f"Error listing project environments: {str(e)}")


@resource("cycloid://projects")
async def get_projects_resource(
    cli: CLIMixin = Depends(get_cli),  # type: ignore[reportCallInDefaultInitializer]
) -> str:
    """Get all projects as a resource."""
    try:
        projects = await _list_projects(cli)
        result: Dict[str, Any] = {
            "projects": projects,
            "count": len(projects),
        }
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Failed to read projects resource: {str(e)}")
        return json.dumps(
            {
                "error": f"Failed to load projects: {str(e)}",
                "projects": [],
                "count": 0,
            },
            indent=2,
        )

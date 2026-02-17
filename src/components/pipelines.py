"""Pipeline tools and resources for Cycloid MCP server."""

import json
from typing import Any, Dict

from fastmcp.dependencies import Depends  # type: ignore[reportAttributeAccessIssue]
from fastmcp.exceptions import ToolError
from fastmcp.resources import resource
from fastmcp.tools import tool
from fastmcp.utilities.logging import get_logger

from src.cli import CLIMixin
from src.dependencies import get_cli
from src.display_hints import build_display_hints
from src.types import JSONList

logger = get_logger(__name__)


async def _get_pipelines(cli: CLIMixin) -> JSONList:
    """Get pipelines from CLI."""
    try:
        pipelines_data = await cli.execute_cli("pipeline", ["list"])
        return cli.process_cli_response(pipelines_data)
    except Exception as e:
        logger.error(f"Error getting pipelines: {e}")
        return []


@tool(
    name="CYCLOID_PIPELINE_LIST",
    description=(
        "List all pipelines from Cycloid. "
        "DISPLAY GUIDANCE: Present as a markdown table. Key fields: name (Pipeline), "
        "status (Status), project name from component.project.name (Project), "
        "environment name from component.environment.name (Environment). "
        "Full JSON details available on request."
    ),
    annotations={"readOnlyHint": True},
)
async def list_pipelines(
    cli: CLIMixin = Depends(get_cli),  # type: ignore[reportCallInDefaultInitializer]
) -> Dict[str, Any]:
    """List all pipelines.

    Returns a dict with pipelines list and count.
    """
    try:
        pipelines = await _get_pipelines(cli)
        return {
            "pipelines": pipelines,
            "count": len(pipelines),
            "_display_hints": build_display_hints(
                key_fields=[
                    "name",
                    "status",
                    "component.project.name",
                    "component.environment.name",
                ],
                display_format="table",
                columns={
                    "name": "Pipeline",
                    "status": "Status",
                    "component.project.name": "Project",
                    "component.environment.name": "Environment",
                },
                sort_by="name",
            ),
        }
    except Exception as e:
        raise ToolError(f"Error listing pipelines: {str(e)}")


@resource("cycloid://pipelines")
async def get_pipelines_resource(
    cli: CLIMixin = Depends(get_cli),  # type: ignore[reportCallInDefaultInitializer]
) -> str:
    """Get all pipelines as a resource."""
    try:
        pipelines = await _get_pipelines(cli)
        result: Dict[str, Any] = {
            "pipelines": pipelines,
            "count": len(pipelines),
        }
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.error(f"Failed to read pipelines resource: {str(e)}")
        return json.dumps(
            {
                "error": f"Failed to load pipelines: {str(e)}",
                "pipelines": [],
                "count": 0,
            },
            indent=2,
        )

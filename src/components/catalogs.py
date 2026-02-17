"""Catalog tools and resources for Cycloid MCP server."""

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
from src.exceptions import CycloidCLIError
from src.types import JSONList

logger = get_logger(__name__)


async def _get_catalog_repositories(cli: CLIMixin) -> JSONList:
    """Get catalog repositories from CLI."""
    repositories_data = await cli.execute_cli("catalog-repository", ["list"])
    return cli.process_cli_response(repositories_data, list_key=None)


@tool(
    name="CYCLOID_CATALOG_REPO_LIST",
    description=(
        "List all available service catalog repositories with their details. "
        "The LLM can filter the results based on user requirements. "
        "DISPLAY GUIDANCE: Present as a markdown table. Key fields: canonical (Name), "
        "url (URL), branch (Branch), stack_count (Stacks). "
        "Full JSON details available on request."
    ),
    annotations={"readOnlyHint": True},
)
async def list_catalog_repositories(
    cli: CLIMixin = Depends(get_cli),  # type: ignore[reportCallInDefaultInitializer]
) -> Dict[str, Any]:
    """List all available service catalog repositories.

    Returns a dict with repositories list and count.
    """
    try:
        repositories = await _get_catalog_repositories(cli)
        return {
            "repositories": repositories,
            "count": len(repositories),
            "_display_hints": build_display_hints(
                key_fields=["canonical", "url", "branch", "stack_count"],
                display_format="table",
                columns={
                    "canonical": "Name",
                    "url": "URL",
                    "branch": "Branch",
                    "stack_count": "Stacks",
                },
                sort_by="canonical",
            ),
        }
    except CycloidCLIError as e:
        raise ToolError(f"Failed to list catalog repositories: {str(e)}")
    except Exception as e:
        raise ToolError(f"Error listing catalog repositories: {str(e)}")


@resource("cycloid://service-catalogs-repositories")
async def get_service_catalogs_resource(
    cli: CLIMixin = Depends(get_cli),  # type: ignore[reportCallInDefaultInitializer]
) -> str:
    """Get all available service catalog repositories as a resource."""
    try:
        repositories = await _get_catalog_repositories(cli)
        result = {
            "repositories": repositories,
            "count": len(repositories),
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

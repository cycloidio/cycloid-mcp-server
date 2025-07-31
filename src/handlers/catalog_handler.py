"""Catalog handler for Cycloid MCP server."""

import json
from typing import Any, Dict, List, Optional

import structlog
from mcp.types import Resource, TextContent

from ..cli_mixin import CLIMixin
from ..exceptions import CycloidCLIError

logger = structlog.get_logger(__name__)


class CatalogHandler(CLIMixin):
    """Handler for service catalog operations."""

    def __init__(self):
        """Initialize the catalog handler."""
        super().__init__()

    def get_resources(self) -> List[Resource]:
        """Get available resources."""
        return [
            Resource(
                uri="cycloid://service-catalogs",
                name="service-catalogs",
                title="Service Catalog Repositories",
                description="List of all available service catalog repositories",
                mimeType="application/json",
            )
        ]

    async def read_resource(self, uri: str) -> Optional[Resource]:
        """Read a specific resource."""
        if uri == "cycloid://service-catalogs":
        try:
            # Get repositories from CLI
            repositories_data = await self.execute_cli_json(
                    "catalog-repository", ["list"]
            )

            repositories = repositories_data.get("service_catalog_repositories", [])
                
                # Format as JSON with both raw data and formatted table
                result = {
                    "service_catalog_repositories": repositories,
                    "count": len(repositories),
                    "formatted_table": self._format_table_output(repositories, "")
                }

                return Resource(
                    uri=uri,
                    name="service-catalogs",
                    title="Service Catalog Repositories",
                    description=f"Found {len(repositories)} service catalog repositories",
                    mimeType="application/json",
                content=[
                    TextContent(
                        type="text",
                            text=json.dumps(result, indent=2)
                    )
                ]
            )

        except CycloidCLIError as e:
            logger.error(
                    "Failed to read service catalogs resource",
                error=str(e),
            )
                return Resource(
                    uri=uri,
                    name="service-catalogs",
                    title="Service Catalog Repositories",
                    description="Error loading service catalog repositories",
                    mimeType="application/json",
                content=[
                    TextContent(
                        type="text",
                            text=json.dumps({
                                "error": f"Failed to load service catalog repositories: {str(e)}",
                                "service_catalog_repositories": [],
                                "count": 0
                            }, indent=2)
                        )
                    ]
                )

        return None

    def _format_table_output(
        self, repositories: List[Dict[str, Any]], filter_text: str
    ) -> str:
        """Format repositories as table output."""
        if not repositories:
            return "📚 Service Catalog Repositories\n\nNo repositories found."

        # Build table
        table_lines = [
            "# Service Catalog Repositories",
            "",
            f"Found {len(repositories)} service catalog repositories",
            "",
            "| Canonical | Name | URL | Branch | Stack Count |",
            "|-----------|------|-----|--------|-------------|",
        ]

        for repo in repositories:
            canonical = repo.get("canonical", "")
            name = repo.get("name", "")
            url = repo.get("url", "")
            branch = repo.get("branch", "")
            stack_count = repo.get("stack_count", "")

            table_lines.append(
                f"| {canonical} | {name} | {url} | {branch} | {stack_count} |"
            )

        table_lines.extend([
            "",
            f"Total repositories: {len(repositories)}",
            "",
            "💡 Popular choices:",
            "• cycloid-stacks - Main Cycloid stacks repository",
            "• cycloid-demo-stacks - Demo stacks repository",
            "• stack-getting-started - Getting started examples",
            "• terraform-runner - Terraform automation templates",
        ])

        return "\n".join(table_lines)
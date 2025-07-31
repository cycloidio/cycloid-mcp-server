"""Catalog handler utilities and core logic."""

from typing import Any, Dict, List

from fastmcp.utilities.logging import get_logger

from src.cli_mixin import CLIMixin

logger = get_logger(__name__)

CATALOG_TABLE_HEADER = "| Canonical | Branch | URL | Stack Count |"  # noqa: E501
CATALOG_TABLE_SEPARATOR = "|-----------|--------|-----|-------------|"  # noqa: E501


class CatalogHandler:
    """Core catalog operations and utilities."""

    def __init__(self, cli: CLIMixin):  # type: ignore[reportMissingSuperCall]
        """Initialize catalog handler with CLI mixin."""
        self.cli = cli

    async def get_catalog_repositories(self) -> List[Dict[str, Any]]:
        """
        Get catalog repositories from CLI.
        Shared logic for both tool and resource.
        """
        try:
            repositories_data = await self.cli.execute_cli_json(
                "catalog-repository", ["list"]
            )

            # CLI returns a list directly, not a dictionary
            if isinstance(repositories_data, list):
                return repositories_data
            else:
                return repositories_data.get("service_catalog_repositories", [])
        except Exception as e:
            error_str = str(e)
            error_msg = (  # noqa: E501
                f"Failed to fetch catalog repositories: {error_str}"
            )
            logger.error(error_msg)
            raise

    def format_table_output(
        self, repositories: List[Dict[str, Any]], filter_text: str
    ) -> str:  # noqa: E501
        """Format repositories as table output."""
        if not repositories:
            return "📋 Service Catalog Repositories\n\nNo repositories found."

        # Build table
        filter_suffix = f" matching '{filter_text}'" if filter_text else ""
        table_lines = [
            "# Service Catalog Repositories",
            "",
            f"Found {len(repositories)} repositories{filter_suffix}",
            "",
            CATALOG_TABLE_HEADER,
            CATALOG_TABLE_SEPARATOR,
        ]

        for repo in repositories:
            canonical = repo.get("canonical", "N/A")
            branch = repo.get("branch", "N/A")
            url = repo.get("url", "N/A")
            stack_count = repo.get("stack_count", 0)

            # Truncate long URLs
            if url and len(url) > 50:
                url = url[:47] + "..."

            table_lines.append(f"| {canonical} | {branch} | {url} | {stack_count} |")

        return "\n".join(table_lines)

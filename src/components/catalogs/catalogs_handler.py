"""Catalog handler utilities and core logic."""

from src.base_handler import BaseHandler
from src.cli_mixin import CLIMixin
from src.error_handling import handle_errors
from src.types import JSONList

CATALOG_TABLE_HEADER = "| Canonical | Branch | URL | Stack Count |"  # noqa: E501
CATALOG_TABLE_SEPARATOR = "|-----------|--------|-----|-------------|"  # noqa: E501


class CatalogHandler(BaseHandler):
    """Core catalog operations and utilities."""

    def __init__(self, cli: CLIMixin):
        """Initialize catalog handler with CLI mixin."""
        super().__init__(cli)

    @handle_errors(
        action="fetch catalog repositories",
        suggestions=[
            "Check your Cycloid CLI configuration",
            "Verify API credentials and organization settings",
            "Ensure you have access to catalog repositories",
        ],
    )
    async def get_catalog_repositories(self) -> JSONList:
        """
        Get catalog repositories from CLI.
        Shared logic for both tool and resource.
        """
        repositories_data = await self.cli.execute_cli(
            "catalog-repository", ["list"], output_format="json"
        )

        return self.cli.process_cli_response(repositories_data, list_key=None)

    def format_table_output(self, repositories: JSONList, filter_text: str) -> str:
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

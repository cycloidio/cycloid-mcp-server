"""Stack handler utilities and core logic."""

import re

from fastmcp.utilities.logging import get_logger

from src.base_handler import BaseHandler
from src.cli_mixin import CLIMixin
from src.error_handling import handle_errors
from src.types import Any, Dict, JSONList, List

from .constants import BLUEPRINT_TABLE_HEADER, BLUEPRINT_TABLE_SEPARATOR

logger = get_logger(__name__)


class StackHandler(BaseHandler):
    """Core stack operations and utilities."""

    def __init__(self, cli: CLIMixin):
        """Initialize stack handler with CLI mixin."""
        super().__init__(cli)

    @handle_errors(
        action="fetch blueprints",
        suggestions=[
            "Check your Cycloid CLI configuration",
            "Verify API credentials and organization settings",
            "Ensure you have access to stack blueprints",
        ],
    )
    async def get_blueprints(self) -> JSONList:
        """Get blueprints from CLI - shared logic for both tool and resource."""
        blueprints_data = await self.cli.execute_cli(
            "stacks", ["list", "--blueprint"], output_format="json"
        )

        # If CLI returned a string, it's probably an error message
        if isinstance(blueprints_data, str):
            logger.error(f"CLI returned error string: {blueprints_data}")
            return []  # Return empty list for error cases

        return self.cli.process_cli_response(blueprints_data, list_key="service_catalogs")

    def format_blueprint_table_output(self, blueprints: JSONList, filter_text: str) -> str:
        """Format blueprints as table output."""
        if not blueprints:
            return "📋 Blueprints\n\nNo blueprints found."

        filter_suffix = f" matching '{filter_text}'" if filter_text else ""
        blueprint_count = len(blueprints)
        table_lines = [
            "# Blueprints",
            "",
            f"Found {blueprint_count} blueprints{filter_suffix}",
            "",
            BLUEPRINT_TABLE_HEADER,
            BLUEPRINT_TABLE_SEPARATOR,
        ]

        for bp in blueprints:
            # Handle case where bp might be a string (error message) instead of dict
            if isinstance(bp, str):
                table_lines.append(f"| ERROR | {bp} | N/A | N/A | N/A |")
                continue

            if not isinstance(bp, dict):  # type: ignore[reportUnnecessaryIsInstance]
                continue

            name = bp.get("name", "N/A")
            ref = bp.get("ref", "N/A")
            version = bp.get("version", "N/A")
            usecases_list = bp.get("use_cases", [])
            usecases = ", ".join(usecases_list) if usecases_list else "N/A"
            description = bp.get("description", "N/A")
            row = f"| {name} | {ref} | {version} | {usecases} | {description} |"
            table_lines.append(row)

        return "\n".join(table_lines)

    def get_blueprint_by_ref(
        self, blueprints: List[Dict[str, Any]], ref: str
    ) -> Dict[str, Any] | None:
        """Find a specific blueprint by reference."""
        for bp in blueprints:
            # Handle case where bp might be a string (error message) instead of dict
            if isinstance(bp, str):
                continue

            if not isinstance(bp, dict):  # type: ignore[reportUnnecessaryIsInstance]
                continue

            if bp.get("ref") == ref:
                return bp
        return None

    async def get_catalog_repositories(self) -> List[Dict[str, Any]]:
        """Get catalog repositories for validation."""
        try:
            catalog_repositories = await self.cli.execute_cli(
                "catalog-repository", ["list"], output_format="json"
            )
            if isinstance(catalog_repositories, list):
                return catalog_repositories
            elif isinstance(catalog_repositories, dict):
                return catalog_repositories.get("catalog_repositories", [])
            else:
                return []
        except Exception as e:
            logger.error(f"Failed to fetch catalog repositories: {str(e)}")  # noqa: E501
            raise

    def get_available_canonicals(self, catalog_repositories: List[Dict[str, Any]]) -> List[str]:
        """Extract canonical values from catalog repositories."""
        available_canonicals: List[str] = []
        for repo in catalog_repositories:
            canonical = repo.get("canonical")
            if canonical:
                available_canonicals.append(str(canonical))
        return available_canonicals

    def validate_use_case(
        self, use_case: str, available_use_cases: List[str]
    ) -> str | None:  # noqa: E501
        """Validate the provided use case."""
        if use_case not in available_use_cases:
            available_str = ", ".join(available_use_cases)
            msg = (
                f"❌ Invalid use case '{use_case}'. "
                f"Available use cases for this blueprint are: {available_str}"
            )
            return msg
        return None

    def validate_canonical(
        self, service_catalog_source_canonical: str, available_canonicals: List[str]
    ) -> str | None:
        """Validate the provided canonical."""
        if service_catalog_source_canonical not in available_canonicals:
            available_str = ", ".join(available_canonicals)
            canonical_name = service_catalog_source_canonical
            msg = (
                f"❌ Invalid service catalog source '{canonical_name}'. "
                f"Available options are: {available_str}"
            )
            return msg
        return None

    def generate_canonical_from_name(self, name: str) -> str:
        """Generate canonical (slug) from name."""
        canonical = re.sub(r"[^a-zA-Z0-9-]", "-", name.lower()).strip("-")
        # Replace multiple dashes with single dash
        canonical = re.sub(r"-+", "-", canonical)
        return canonical

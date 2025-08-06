"""Stack handler utilities and core logic."""

import re

from src.base_handler import BaseHandler
from src.cli_mixin import CLIMixin
from src.error_handling import handle_errors
from src.template_loader import get_elicitation_fallback, get_stack_creation_guidance
from src.types import Any, Dict, JSONList, List

from .constants import BLUEPRINT_TABLE_HEADER, BLUEPRINT_TABLE_SEPARATOR


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
            self.logger.error(f"Failed to fetch catalog repositories: {str(e)}")  # noqa: E501
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

    async def create_stack_directly(
        self,
        ref: str,
        name: str,
        use_case: str,
        service_catalog_source_canonical: str,
        available_use_cases: List[str],
    ) -> str:
        """Create a stack directly with provided parameters."""
        try:
            # Validate the provided use case
            use_case_error = self.validate_use_case(use_case, available_use_cases)
            if use_case_error:
                return use_case_error

            # Get available catalog repositories to fetch valid canonical options
            self.logger.info("Fetching catalog repositories to get valid canonical options")
            try:
                catalog_repositories = await self.get_catalog_repositories()
            except Exception as e:
                return f"❌ Failed to fetch catalog repositories: {str(e)}"

            # Extract canonical values from catalog repositories
            available_canonicals = self.get_available_canonicals(catalog_repositories)

            if not available_canonicals:
                return "❌ No catalog repositories found. Please check your configuration."

            self.logger.info(f"Found catalog repositories with canonicals: {available_canonicals}")

            # Validate the provided canonical
            canonical_error = self.validate_canonical(
                service_catalog_source_canonical, available_canonicals
            )
            if canonical_error:
                return canonical_error

            # Generate canonical (slug) from name
            canonical = self.generate_canonical_from_name(name)

            # Execute CLI command to create the stack
            cli_args = [
                "create",
                "--blueprint-ref",
                ref,
                "--name",
                name,
                "--stack",
                canonical,
                "--use-case",
                use_case,
                "--catalog-repository",
                service_catalog_source_canonical,
            ]
            result = await self.cli.execute_cli_command("stack", cli_args, auto_parse=False)

            # Type guard to ensure we have a CLIResult-like object
            from src.cli_mixin import CLIResult

            if not isinstance(result, CLIResult) and not hasattr(result, "success"):
                raise RuntimeError("Expected CLIResult from execute_cli_command")

            # Type cast for better type checking (we know it has CLI attributes after the guard)
            cli_result = result  # type: ignore[reportUnknownMemberType]

            if cli_result.exit_code == 0:  # type: ignore[reportUnknownMemberType]
                return (
                    f"✅ Stack '{name}' created successfully!\n"
                    f"{cli_result.stdout}"  # type: ignore[reportUnknownMemberType]
                )
            else:
                return (
                    f"❌ Failed to create stack: "
                    f"{cli_result.stderr}"  # type: ignore[reportUnknownMemberType]
                )

        except Exception as e:
            self.logger.error(f"Error during direct stack creation: {str(e)}")
            return f"❌ An unexpected error occurred during stack creation: {str(e)}"

    def create_guidance_message(self, ref: str, blueprint: Dict[str, Any]) -> str:
        """Create guidance message for stack creation."""
        available_use_cases = blueprint.get("use_cases", [])
        use_cases_str = ", ".join(available_use_cases)

        return f"📋 **{get_stack_creation_guidance(ref, use_cases_str)}"

    def create_fallback_info(
        self, ref: str, blueprint: Dict[str, Any], available_canonicals: List[str]
    ) -> str:
        """Create fallback information when elicitation is not supported."""
        available_use_cases = blueprint.get("use_cases", [])
        use_cases_str = ", ".join(available_use_cases)
        canonicals_str = ", ".join(available_canonicals)
        # Remove unused variables

        return get_elicitation_fallback(
            name=blueprint.get("name", "N/A"),
            description=blueprint.get("description", "N/A"),
            version=blueprint.get("version", "N/A"),
            use_cases=use_cases_str,
            canonicals=canonicals_str,
            ref=ref,
        )

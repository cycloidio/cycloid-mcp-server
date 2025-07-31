"""Stack handler utilities and core logic."""

import re
from typing import Any, Dict, List

from fastmcp.utilities.logging import get_logger

from src.cli_mixin import CLIMixin

logger = get_logger(__name__)

BLUEPRINT_TABLE_HEADER = (
    "| Name | Ref | Version | Use Cases | Description |"  # noqa: E501
)
BLUEPRINT_TABLE_SEPARATOR = (
    "|------|-----|---------|-----------|-------------|"  # noqa: E501
)

# Long documentation strings for better readability
STACK_CREATION_GUIDANCE_INTRO = (
    "📋 **Stack Creation Guidance**\n\n"
    "🚨 **CRITICAL**: Interactive elicitation is not available. "
    "You must explicitly provide ALL parameters. The LLM should NEVER guess or assume values.\n\n"
    "⚠️ **LLM INSTRUCTIONS**: Do NOT provide default values, suggestions, or examples. "
    "Let the user make their own choices. Do NOT call this tool with guessed parameters.\n\n"
    "To create a stack from blueprint '{ref}', you need to provide the following parameters:\n\n"
    "**Required Parameters:**\n"
    "- `name`: The name for your new stack (YOU must choose this)\n"
    "- `use_case`: Choose from available use cases: **{use_cases}** (YOU must choose this)\n"
    "- `service_catalog_source_canonical`: The service catalog source to use (YOU must choose this)\n\n"
    "**To get available service catalog sources:**\n"
    "Use the `CYCLOID_CATALOG_REPO_LIST` tool to see all available catalog "
    "repositories and their canonicals.\n\n"
    "**⚠️ IMPORTANT FOR LLM**:\n"
    "- Do NOT provide example values in your response\n"
    "- Do NOT suggest specific use cases or catalog sources\n"
    "- Do NOT call this tool with guessed parameters\n"
    "- Let the user provide their own choices\n"
    "- Only call this tool when the user explicitly provides ALL required parameters\n\n"
    "**Available use cases for this blueprint:** {use_cases}\n\n"
    "**Next Steps:**\n"
    "1. Choose your preferred use case from the list above\n"
    "2. Use `CYCLOID_CATALOG_REPO_LIST` to see available catalog repositories\n"
    "3. Choose your preferred catalog repository\n"
    "4. Decide on a name for your stack\n"
    "5. Call this tool again with ALL the required parameters\n\n"
    "**🚨 REMINDER**: The LLM should NEVER guess or provide default values!"
)

FALLBACK_INFO_INTRO = (
    "# Interactive Elicitation Not Supported\n\n"
    "🚨 **CRITICAL**: The client doesn't support interactive elicitation. "
    "The LLM should NEVER guess or assume parameter values. "
    "ALL parameters must be explicitly provided by the user.\n\n"
    "⚠️ **LLM INSTRUCTIONS**: Do NOT provide default values, suggestions, or examples. "
    "Let the user make their own choices. Do NOT call this tool with guessed parameters.\n\n"
    "## Blueprint Details\n"
    "- **Name**: {name}\n"
    "- **Description**: {description}\n"
    "- **Version**: {version}\n\n"
    "## Available Use Cases\n"
    "{use_cases}\n\n"
    "## Available Service Catalog Sources\n"
    "{canonicals}\n\n"
    "## How to Create the Stack\n\n"
    "Since interactive elicitation is not supported, you'll need to provide all "
    "parameters when calling this tool again. Here are the required parameters:\n\n"
    "**Required Parameters:**\n"
    "- `ref`: {ref} (already provided)\n"
    "- `name`: Choose a name for your stack (YOU must choose this)\n"
    "- `use_case`: Choose one from: {use_cases} (YOU must choose this)\n"
    "- `service_catalog_source_canonical`: Choose from: {canonicals} (YOU must choose this)\n\n"
    "**⚠️ IMPORTANT FOR LLM**:\n"
    "- Do NOT provide example values in your response\n"
    "- Do NOT suggest specific use cases or catalog sources\n"
    "- Do NOT call this tool with guessed parameters\n"
    "- Let the user provide their own choices\n"
    "- Only call this tool when the user explicitly provides ALL required parameters\n\n"
    "**Next Steps:**\n"
    "1. Choose your preferred use case from the list above\n"
    "2. Choose your preferred service catalog source from the list above\n"
    "3. Decide on a name for your stack\n"
    "4. Call this tool again with all the required parameters\n\n"
    "**🚨 REMINDER**: The LLM should NEVER guess or provide default values!"
)


class StackHandler:
    """Core stack operations and utilities."""

    def __init__(self, cli: CLIMixin):  # type: ignore[reportMissingSuperCall]
        """Initialize stack handler with CLI mixin."""
        self.cli = cli

    async def get_blueprints(self) -> List[Dict[str, Any]]:
        """Get blueprints from CLI - shared logic for both tool and resource."""
        try:
            blueprints_data = await self.cli.execute_cli_json(
                "stacks", ["list", "--blueprint"]
            )
            if isinstance(blueprints_data, list):
                return blueprints_data
            else:
                return blueprints_data.get("service_catalogs", [])
        except Exception as e:
            logger.error(f"Failed to fetch blueprints: {str(e)}")
            raise

    def format_blueprint_table_output(
        self, blueprints: List[Dict[str, Any]], filter_text: str
    ) -> str:
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
            catalog_repositories = await self.cli.execute_cli_json(
                "catalog-repository", ["list"]
            )
            if isinstance(catalog_repositories, list):
                return catalog_repositories
            else:
                return catalog_repositories.get("catalog_repositories", [])
        except Exception as e:
            logger.error(
                f"Failed to fetch catalog repositories: {str(e)}"  # noqa: E501
            )
            raise

    def get_available_canonicals(
        self, catalog_repositories: List[Dict[str, Any]]
    ) -> List[str]:
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
            logger.info("Fetching catalog repositories to get valid canonical options")
            try:
                catalog_repositories = await self.get_catalog_repositories()
            except Exception as e:
                return f"❌ Failed to fetch catalog repositories: {str(e)}"

            # Extract canonical values from catalog repositories
            available_canonicals = self.get_available_canonicals(catalog_repositories)

            if not available_canonicals:
                return (
                    "❌ No catalog repositories found. "
                    "Please check your configuration."
                )

            logger.info(
                f"Found catalog repositories with canonicals: {available_canonicals}"
            )

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
            result = await self.cli.execute_cli_command("stack", cli_args)

            if result.exit_code == 0:
                return f"✅ Stack '{name}' created successfully!\n{result.stdout}"
            else:
                return f"❌ Failed to create stack: {result.stderr}"

        except Exception as e:
            logger.error(f"Error during direct stack creation: {str(e)}")
            return f"❌ An unexpected error occurred during stack creation: {str(e)}"

    def create_guidance_message(
        self, ref: str, blueprint: Dict[str, Any], available_canonicals: List[str]
    ) -> str:
        """Create guidance message for stack creation."""
        available_use_cases = blueprint.get("use_cases", [])
        use_cases_str = ", ".join(available_use_cases)

        return STACK_CREATION_GUIDANCE_INTRO.format(ref=ref, use_cases=use_cases_str)

    def create_fallback_info(
        self, ref: str, blueprint: Dict[str, Any], available_canonicals: List[str]
    ) -> str:
        """Create fallback information when elicitation is not supported."""
        available_use_cases = blueprint.get("use_cases", [])
        use_cases_str = ", ".join(available_use_cases)
        canonicals_str = ", ".join(available_canonicals)
        first_use_case = available_use_cases[0] if available_use_cases else "N/A"
        first_canonical = available_canonicals[0] if available_canonicals else "N/A"

        return FALLBACK_INFO_INTRO.format(
            ref=ref,
            name=blueprint.get("name", "N/A"),
            description=blueprint.get("description", "N/A"),
            version=blueprint.get("version", "N/A"),
            use_cases=use_cases_str,
            canonicals=canonicals_str,
            first_use_case=first_use_case,
            first_canonical=first_canonical,
        )

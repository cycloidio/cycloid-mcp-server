"""StackForms validation tool for Cycloid MCP server."""

import tempfile

from fastmcp.dependencies import Depends  # type: ignore[reportAttributeAccessIssue]
from fastmcp.exceptions import ToolError
from fastmcp.tools import tool
from fastmcp.utilities.logging import get_logger

from src.cli import CLIMixin, CLIResult
from src.dependencies import get_cli

logger = get_logger(__name__)


@tool(
    name="CYCLOID_STACKFORMS_VALIDATE",
    description=(
        "Validate a StackForms (.forms.yml) file using the Cycloid CLI. "
        "This tool can validate StackForms configuration and provide detailed "
        "feedback for fixing issues."
    ),
)
async def validate_stackforms(
    forms_content: str,
    cli: CLIMixin = Depends(get_cli),  # type: ignore[reportCallInDefaultInitializer]
) -> str:
    """Validate a StackForms (.forms.yml) file.

    Args:
        forms_content: The content of the .forms.yml file to validate
    """
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=True) as temp_file:
        temp_file.write(forms_content)
        temp_file.flush()

        logger.info("Validating StackForms file: %s", temp_file.name)
        result = await cli.execute_cli_command(
            "stacks", ["forms", "validate", temp_file.name], auto_parse=False
        )

        if not isinstance(result, CLIResult) and not hasattr(result, "success"):
            raise ToolError("Unexpected result from CLI command")

        cli_result = result  # type: ignore[reportUnknownMemberType]

        if cli_result.success:  # type: ignore[reportUnknownMemberType]
            if cli_result.stdout.strip():  # type: ignore[reportUnknownMemberType]
                return (
                    "**StackForms Validation Successful**\n\n"
                    f"{cli_result.stdout}"  # type: ignore[reportUnknownMemberType]
                )
            else:
                return (
                    "**StackForms Validation Successful**\n\n"
                    "The StackForms file is valid and follows Cycloid best practices."
                )
        else:
            raise ToolError(
                "Validation failed with exit code "
                f"{cli_result.exit_code}: "  # type: ignore[reportUnknownMemberType]
                f"{cli_result.stderr}"  # type: ignore[reportUnknownMemberType]
            )

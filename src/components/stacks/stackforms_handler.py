"""StackForms handler utilities and core logic."""

import tempfile

from src.base_handler import BaseHandler
from src.cli_mixin import CLIMixin
from src.error_handling import handle_errors


class StackFormsHandler(BaseHandler):
    """Core StackForms operations and utilities."""

    def __init__(self, cli: CLIMixin):
        """Initialize StackForms handler with CLI mixin."""
        super().__init__(cli)

    @handle_errors(
        action="validate StackForms",
        return_on_error="",
        suggestions=[
            "Check YAML syntax and formatting",
            "Verify widget configurations are correct",
            "Ensure proper technology injection",
            "Validate variable naming conventions",
        ],
    )
    async def validate_stackforms(self, forms_content: str) -> str:
        """Validate a StackForms (.forms.yml) file.

        This method validates StackForms configuration and provides detailed feedback
        for fixing any issues found. It's useful for ensuring StackForms files are
        correctly formatted and follow Cycloid best practices.

        Args:
            forms_content: The content of the .forms.yml file to validate
        """
        # Use a context manager for better resource management
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=True) as temp_file:
            temp_file.write(forms_content)
            temp_file.flush()  # Ensure content is written

            # Execute the CLI validation command
            self.logger.info("Validating StackForms file: %s", temp_file.name)
            result = await self.cli.execute_cli_command(
                "stacks", ["forms", "validate", temp_file.name], auto_parse=False
            )

            # Type guard to ensure we have a CLIResult-like object
            from src.cli_mixin import CLIResult

            if not isinstance(result, CLIResult) and not hasattr(result, "success"):
                raise RuntimeError("Expected CLIResult from execute_cli_command")

            # Type cast for better type checking (we know it has CLI attributes after the guard)
            cli_result = result  # type: ignore[reportUnknownMemberType]

            # Check if validation was successful
            if cli_result.success:  # type: ignore[reportUnknownMemberType]
                if cli_result.stdout.strip():  # type: ignore[reportUnknownMemberType]
                    return (
                        f"✅ **StackForms Validation Successful**\n\n"
                        f"{cli_result.stdout}"  # type: ignore[reportUnknownMemberType]
                    )
                else:
                    return (
                        "✅ **StackForms Validation Successful**\n\n"
                        "The StackForms file is valid and follows Cycloid best practices."
                    )
            else:
                # Let the error handling decorator handle CLI failures
                # Let the error handling decorator handle CLI failures
                raise RuntimeError(
                    f"Validation failed with exit code "
                    f"{cli_result.exit_code}: "  # type: ignore[reportUnknownMemberType]
                    f"{cli_result.stderr}"  # type: ignore[reportUnknownMemberType]
                )
                # File automatically deleted when exiting context manager


# Old error handling methods removed - now using unified error handling system

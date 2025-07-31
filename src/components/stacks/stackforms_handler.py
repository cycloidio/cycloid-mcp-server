"""StackForms handler utilities and core logic."""

import os
import tempfile

from fastmcp.utilities.logging import get_logger

from src.cli_mixin import CLIMixin

logger = get_logger(__name__)


class StackFormsHandler:
    """Core StackForms operations and utilities."""

    def __init__(self, cli: CLIMixin):  # type: ignore[reportMissingSuperCall]
        """Initialize StackForms handler with CLI mixin."""
        self.cli = cli

    async def validate_stackforms(self, forms_content: str) -> str:
        """Validate a StackForms (.forms.yml) file.

        This method validates StackForms configuration and provides detailed feedback
        for fixing any issues found. It's useful for ensuring StackForms files are
        correctly formatted and follow Cycloid best practices.

        Args:
            forms_content: The content of the .forms.yml file to validate
        """
        try:
            # Write the forms content to a temporary file
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".yml", delete=False
            ) as temp_file:
                temp_file.write(forms_content)
                temp_file_path = temp_file.name

            try:
                # Execute the CLI validation command
                log_msg = f"Validating StackForms file: {temp_file_path}"  # noqa: E501
                logger.info(log_msg)
                result = await self.cli.execute_cli_command(
                    "stacks", ["forms", "validate", temp_file_path]
                )

                # Clean up the temporary file
                _ = os.unlink(temp_file_path)  # type: ignore[reportUnusedCallResult]  # noqa: E501

                # Check if validation was successful
                if result.success:
                    if result.stdout.strip():
                        return (
                            f"✅ **StackForms Validation Successful**\n\n"
                            f"{result.stdout}"  # noqa: E501
                        )
                    else:
                        return (
                            "✅ **StackForms Validation Successful**\n\n"
                            "The StackForms file is valid and follows Cycloid best practices."  # noqa: E501
                        )
                else:
                    return self._format_validation_error(
                        result.exit_code, result.stderr
                    )  # noqa: E501

            except Exception as cli_error:
                # Clean up the temporary file even if validation fails
                try:
                    _ = os.unlink(temp_file_path)  # type: ignore[reportUnusedCallResult]  # noqa: E501
                except OSError:
                    pass

                return self._handle_validation_exception(cli_error)

        except Exception as e:
            logger.error(f"Error during StackForms validation: {str(e)}")
            return (
                f"❌ **Unexpected Error**\n\n"
                f"Failed to validate StackForms file: {str(e)}"
            )

    def _format_validation_error(self, exit_code: int, stderr: str) -> str:
        """Format validation error output."""
        return (
            f"❌ **StackForms Validation Failed**\n\n"
            f"Exit code: {exit_code}\n\n"
            f"**Error output:**\n{stderr}\n\n"
            f"**Suggestions:**\n"
            f"- Check YAML syntax\n"
            f"- Verify widget configurations\n"
            f"- Ensure proper technology injection\n"
            f"- Validate variable naming conventions"
        )

    def _handle_validation_exception(self, cli_error: Exception) -> str:
        """Handle different types of validation exceptions."""
        if hasattr(cli_error, "stderr") and hasattr(cli_error, "exit_code"):
            # This is a CLIResult or CycloidCLIError
            return self._format_validation_error(
                cli_error.exit_code,  # type: ignore[reportUnknownMemberType, reportAttributeAccessIssue]  # noqa: E501
                cli_error.stderr,  # type: ignore[reportUnknownMemberType, reportAttributeAccessIssue]  # noqa: E501
            )
        else:
            # This is a regular exception
            error_msg = str(cli_error)
            if "validation failed" in error_msg.lower() or "error" in error_msg.lower():
                return (
                    f"❌ **StackForms Validation Failed**\n\n"
                    f"{error_msg}\n\n"
                    f"**Suggestions:**\n"
                    f"- Check YAML syntax\n"
                    f"- Verify widget configurations\n"
                    f"- Ensure proper technology injection\n"
                    f"- Validate variable naming conventions"  # noqa: E501
                )
            else:
                return f"❌ **Validation Error**\n\n{error_msg}"  # noqa: E501

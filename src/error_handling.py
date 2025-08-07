"""Unified error handling utilities for Cycloid MCP Server."""

import functools
import inspect
from typing import Any, Callable, Optional, TypeVar, Union

from fastmcp.utilities.logging import get_logger

from .exceptions import CycloidCLIError

logger = get_logger(__name__)

# Type variable for decorated functions
F = TypeVar("F", bound=Callable[..., Any])


class ErrorFormatter:
    """Standardized error message formatting."""

    # Consistent emoji patterns
    ERROR_EMOJI = "❌"

    @classmethod
    def format_error(
        cls,
        action: str,
        error: Union[str, Exception],
        suggestions: Optional[list[str]] = None,
    ) -> str:
        """Format a standardized error message.

        Args:
            action: The action that failed (e.g., "validate StackForms", "list blueprints")
            error: The error message or exception
            suggestions: Optional list of suggestions to help the user

        Returns:
            Formatted error message string
        """
        error_msg = str(error)

        # Build the formatted message
        message_parts = [
            f"{cls.ERROR_EMOJI} **Failed to {action}**",
            "",
            f"**Error:** {error_msg}",
        ]

        if suggestions:
            message_parts.extend(
                [
                    "",
                    "**Suggestions:**",
                    *[f"- {suggestion}" for suggestion in suggestions],
                ]
            )

        return "\n".join(message_parts)

    @classmethod
    def format_cli_error(cls, cli_error: CycloidCLIError) -> str:
        """Format a CLI-specific error message."""
        suggestions = [
            "Check your Cycloid CLI configuration",
            "Verify API credentials and organization settings",
            "Ensure the CLI command syntax is correct",
        ]

        return cls.format_error(
            f"execute CLI command: {cli_error.command}",
            f"Exit code {cli_error.exit_code}: {cli_error.stderr}",
            suggestions,
        )

    @classmethod
    def format_validation_error(cls, content_type: str, error: str) -> str:
        """Format validation error messages."""
        suggestions = [
            "Check YAML syntax and formatting",
            "Verify all required fields are present",
            "Ensure proper indentation and structure",
        ]

        return cls.format_error(f"validate {content_type}", error, suggestions)


def handle_errors(  # noqa: C901  # Acceptable complexity for error handling decorator
    action: str,
    return_on_error: Optional[str] = None,
    suggestions: Optional[list[str]] = None,
    log_level: str = "error",
) -> Callable[[F], F]:
    """Decorator to handle errors with consistent logging and formatting.

    Args:
        action: Description of the action being performed
        return_on_error: Value to return on error (if None, re-raises)
        suggestions: List of suggestions to include in error message
        log_level: Logging level for errors ("error", "warning", "info")

    Returns:
        Decorated function with error handling
    """

    def _handle_error(error: Exception) -> str:
        """Common error handling logic."""
        if isinstance(error, CycloidCLIError):
            error_msg = ErrorFormatter.format_cli_error(error)
            getattr(logger, log_level)(
                f"CLI error during {action}",
                extra={
                    "action": action,
                    "command": error.command,
                    "exit_code": error.exit_code,
                    "stderr": error.stderr,
                },
            )
        else:
            error_msg = ErrorFormatter.format_error(action, error, suggestions)
            getattr(logger, log_level)(
                f"Error during {action}: {str(error)}",
                extra={"action": action, "error": str(error)},
            )

        if return_on_error is not None:
            return error_msg
        raise

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                return _handle_error(e)

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                return _handle_error(e)

        # Return the appropriate wrapper based on function type
        if inspect.iscoroutinefunction(func):
            return async_wrapper  # type: ignore
        else:
            return sync_wrapper  # type: ignore

    return decorator


# Utility functions removed - only the @handle_errors decorator is used

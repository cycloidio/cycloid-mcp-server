"""Unified error handling utilities for Cycloid MCP Server."""

import asyncio
import functools
import inspect
import uuid
from contextlib import contextmanager
from typing import Any, Callable, Dict, Optional, TypeVar, Union

from fastmcp.utilities.logging import get_logger

from .exceptions import CycloidCLIError, CycloidAPIError

logger = get_logger(__name__)

# Type variable for decorated functions
F = TypeVar("F", bound=Callable[..., Any])

# Global correlation ID storage
_correlation_ids: Dict[str, str] = {}


class CorrelationContext:
    """Context manager for correlation IDs in error handling."""

    def __init__(self, correlation_id: Optional[str] = None) -> None:  # type: ignore[reportMissingSuperCall]  # noqa: E501
        """Initialize correlation context."""
        self.correlation_id = correlation_id or str(uuid.uuid4())
        self.previous_id: Optional[str] = None

    def __enter__(self) -> str:
        """Enter correlation context."""
        # Store previous correlation ID if any
        self.previous_id = _correlation_ids.get("current")
        _correlation_ids["current"] = self.correlation_id
        return self.correlation_id

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit correlation context."""
        if self.previous_id:
            _correlation_ids["current"] = self.previous_id
        else:
            _correlation_ids.pop("current", None)


def get_correlation_id() -> Optional[str]:
    """Get current correlation ID."""
    return _correlation_ids.get("current")


def set_correlation_id(correlation_id: str) -> None:
    """Set current correlation ID."""
    _correlation_ids["current"] = correlation_id


@contextmanager
def error_context(action: str, correlation_id: Optional[str] = None):
    """Context manager for error handling with correlation ID."""
    with CorrelationContext(correlation_id) as ctx_id:
        try:
            logger.info(f"Starting {action}", extra={"correlation_id": ctx_id, "action": action})
            yield ctx_id
            logger.info(f"Completed {action}", extra={"correlation_id": ctx_id, "action": action})
        except Exception as e:
            logger.error(
                f"Failed {action}: {str(e)}",
                extra={
                    "correlation_id": ctx_id,
                    "action": action,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                },
            )
            raise


class ErrorFormatter:
    """Standardized error message formatting with enhanced categorization."""

    # Consistent emoji patterns
    ERROR_EMOJI = "❌"
    WARNING_EMOJI = "⚠️"
    INFO_EMOJI = "ℹ️"

    # Error categories and their default suggestions
    ERROR_CATEGORIES = {
        "authentication": [
            "Verify your API credentials are correct",
            "Check if your API key has expired",
            "Ensure you have the necessary permissions",
        ],
        "network": [
            "Check your internet connection",
            "Verify the API endpoint is accessible",
            "Try again in a few moments",
        ],
        "configuration": [
            "Check your configuration settings",
            "Verify environment variables are set correctly",
            "Review the configuration file format",
        ],
        "validation": [
            "Check the input format and syntax",
            "Verify all required fields are present",
            "Ensure proper data types and values",
        ],
        "resource": [
            "Verify the resource exists",
            "Check if you have access to the resource",
            "Ensure the resource identifier is correct",
        ],
        "rate_limit": [
            "Wait before retrying the request",
            "Consider reducing request frequency",
            "Check if you have exceeded API limits",
        ],
    }

    @classmethod
    def categorize_error(cls, error: Exception) -> str:  # noqa: C901
        """Categorize error based on type and message."""
        error_str = str(error).lower()

        if isinstance(error, CycloidCLIError):
            if error.exit_code == 1:
                return "authentication"
            elif "timeout" in error_str or "connection" in error_str:
                return "network"
            else:
                return "configuration"
        elif isinstance(error, CycloidAPIError):
            if error.status_code == 401:
                return "authentication"
            elif error.status_code == 429:
                return "rate_limit"
            elif error.status_code == 404:
                return "resource"
            elif error.status_code and error.status_code >= 500:  # noqa: E501
                return "network"
            else:
                return "configuration"
        elif "validation" in error_str or "invalid" in error_str:
            return "validation"
        elif "not found" in error_str or "missing" in error_str:
            return "resource"
        else:
            return "configuration"

    @classmethod
    def format_error(
        cls,
        action: str,
        error: Union[str, Exception],
        suggestions: Optional[list[str]] = None,
        correlation_id: Optional[str] = None,
    ) -> str:
        """Format a standardized error message with enhanced context.

        Args:
            action: The action that failed (e.g., "validate StackForms", "list blueprints")
            error: The error message or exception
            suggestions: Optional list of suggestions to help the user
            correlation_id: Optional correlation ID for tracking

        Returns:
            Formatted error message string
        """
        error_msg = str(error)
        error_category = (
            cls.categorize_error(error) if isinstance(error, Exception) else "configuration"
        )

        # Use default suggestions if none provided
        if not suggestions:
            suggestions = cls.ERROR_CATEGORIES.get(
                error_category,
                [
                    "Check your configuration and try again",
                    "Contact support if the issue persists",
                ],
            )

        # Build the formatted message
        message_parts = [
            f"{cls.ERROR_EMOJI} **Failed to {action}**",
            "",
            f"**Error:** {error_msg}",
        ]

        if correlation_id:
            message_parts.extend([
                "",
                f"**Correlation ID:** `{correlation_id}`",
            ])

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
    def format_cli_error(cls, cli_error: CycloidCLIError, correlation_id: Optional[str] = None) -> str:  # noqa: E501
        """Format a CLI-specific error message with enhanced context."""
        error_category = cls.categorize_error(cli_error)
        suggestions = cls.ERROR_CATEGORIES.get(
            error_category,
            [
                "Check your Cycloid CLI configuration",
                "Verify API credentials and organization settings",
                "Ensure the CLI command syntax is correct",
            ],
        )

        return cls.format_error(
            f"execute CLI command: {cli_error.command}",
            f"Exit code {cli_error.exit_code}: {cli_error.stderr}",
            suggestions,
            correlation_id,
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


class GracefulDegradation:
    """Handles graceful degradation for API failures."""

    @staticmethod
    def handle_api_failure(  # noqa: E501
        error: Exception,
        fallback_data: Any = None,
        fallback_message: str = "Using cached data",
    ) -> Any:
        """Handle API failure with graceful degradation.

        Args:
            error: The exception that occurred
            fallback_data: Data to return if available
            fallback_message: Message to log when using fallback

        Returns:
            Fallback data if available, otherwise raises the error
        """
        correlation_id = get_correlation_id()

        if fallback_data is not None:
            logger.warning(
                f"API failure, using fallback: {fallback_message}",
                extra={
                    "correlation_id": correlation_id,
                    "error_type": type(error).__name__,
                    "error_message": str(error),
                    "fallback_used": True,
                },
            )
            return fallback_data

        logger.error(
            f"API failure with no fallback available: {str(error)}",
            extra={
                "correlation_id": correlation_id,
                "error_type": type(error).__name__,
                "error_message": str(error),
                "fallback_used": False,
            },
        )
        raise error


class RetryMechanism:
    """Handles retry logic for transient failures."""

    @staticmethod
    def should_retry(error: Exception, attempt: int, max_attempts: int = 3) -> bool:  # noqa: E501
        """Determine if an error should be retried.

        Args:
            error: The exception that occurred
            attempt: Current attempt number (1-based)
            max_attempts: Maximum number of attempts

        Returns:
            True if the error should be retried
        """
        if attempt >= max_attempts:
            return False

        # Retry on network errors and rate limits
        if isinstance(error, CycloidAPIError):
            return error.status_code in [429, 500, 502, 503, 504]
        elif isinstance(error, CycloidCLIError):
            return "timeout" in str(error).lower() or "connection" in str(error).lower()

        return False

    @staticmethod
    def get_retry_delay(attempt: int, base_delay: float = 1.0) -> float:  # noqa: E501
        """Calculate retry delay with exponential backoff.

        Args:
            attempt: Current attempt number (1-based)
            base_delay: Base delay in seconds

        Returns:
            Delay in seconds before next retry
        """
        return base_delay * (2 ** (attempt - 1))


def handle_errors(  # noqa: C901  # Acceptable complexity for error handling decorator
    action: str,
    return_on_error: Optional[str] = None,
    suggestions: Optional[list[str]] = None,
    log_level: str = "error",
    enable_retry: bool = False,
    max_retries: int = 3,
) -> Callable[[F], F]:
    """Enhanced decorator to handle errors with correlation IDs and retry logic.

    Args:
        action: Description of the action being performed
        return_on_error: Value to return on error (if None, re-raises)
        suggestions: List of suggestions to include in error message
        log_level: Logging level for errors ("error", "warning", "info")
        enable_retry: Whether to enable retry logic for transient failures
        max_retries: Maximum number of retry attempts

    Returns:
        Decorated function with enhanced error handling
    """

    def _handle_error(error: Exception, correlation_id: Optional[str] = None) -> str:
        """Enhanced error handling logic with correlation ID."""
        if isinstance(error, CycloidCLIError):
            error_msg = ErrorFormatter.format_cli_error(error, correlation_id)
            getattr(logger, log_level)(
                f"CLI error during {action}",
                extra={
                    "correlation_id": correlation_id,
                    "action": action,
                    "command": error.command,
                    "exit_code": error.exit_code,
                    "stderr": error.stderr,
                    "error_type": type(error).__name__,
                },
            )
        else:
            error_msg = ErrorFormatter.format_error(action, error, suggestions, correlation_id)
            getattr(logger, log_level)(
                f"Error during {action}: {str(error)}",
                extra={
                    "correlation_id": correlation_id,
                    "action": action,
                    "error": str(error),
                    "error_type": type(error).__name__,
                },
            )

        if return_on_error is not None:
            return return_on_error
        else:
            return error_msg

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            correlation_id = get_correlation_id()

            if enable_retry:
                for attempt in range(1, max_retries + 1):
                    try:
                        return await func(*args, **kwargs)
                    except Exception as e:
                        if RetryMechanism.should_retry(e, attempt, max_retries):
                            delay = RetryMechanism.get_retry_delay(attempt)
                            logger.warning(
                                f"Retrying {action} (attempt {attempt}/{max_retries}) after {delay}s",  # noqa: E501
                                extra={
                                    "correlation_id": correlation_id,
                                    "action": action,
                                    "attempt": attempt,
                                    "max_retries": max_retries,
                                    "retry_delay": delay,
                                    "error_type": type(e).__name__,
                                },
                            )
                            await asyncio.sleep(delay)
                            continue
                        else:
                            return _handle_error(e, correlation_id)
                # This should never be reached, but just in case
                return _handle_error(Exception("Max retries exceeded"), correlation_id)
            else:
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    return _handle_error(e, correlation_id)

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            correlation_id = get_correlation_id()

            if enable_retry:
                for attempt in range(1, max_retries + 1):
                    try:
                        return func(*args, **kwargs)
                    except Exception as e:
                        if RetryMechanism.should_retry(e, attempt, max_retries):
                            delay = RetryMechanism.get_retry_delay(attempt)
                            logger.warning(
                                f"Retrying {action} (attempt {attempt}/{max_retries}) after {delay}s",  # noqa: E501
                                extra={
                                    "correlation_id": correlation_id,
                                    "action": action,
                                    "attempt": attempt,
                                    "max_retries": max_retries,
                                    "retry_delay": delay,
                                    "error_type": type(e).__name__,
                                },
                            )
                            import time
                            time.sleep(delay)
                            continue
                        else:
                            return _handle_error(e, correlation_id)
                # This should never be reached, but just in case
                return _handle_error(Exception("Max retries exceeded"), correlation_id)
            else:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    return _handle_error(e, correlation_id)

        # Return the appropriate wrapper based on function type
        if inspect.iscoroutinefunction(func):
            return async_wrapper  # type: ignore
        else:
            return sync_wrapper  # type: ignore

    return decorator


# Utility functions removed - only the @handle_errors decorator is used

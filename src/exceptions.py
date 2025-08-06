"""Custom exceptions for Cycloid MCP Server."""


class CycloidMCPError(Exception):
    """Base exception for Cycloid MCP Server."""

    pass


class CycloidConfigError(CycloidMCPError):
    """Configuration error."""

    pass


class CycloidCLIError(CycloidMCPError):
    """Cycloid CLI execution error."""

    def __init__(self, message: str, command: str, exit_code: int, stderr: str = ""):
        """Initialize CLI error."""
        super().__init__(message)
        self.command = command
        self.exit_code = exit_code
        self.stderr = stderr


class CycloidAPIError(CycloidMCPError):
    """Cycloid API error."""

    def __init__(self, message: str, status_code: int | None = None, response: str = ""):
        """Initialize API error."""
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class CycloidValidationError(CycloidMCPError):
    """Validation error."""

    pass


class CycloidResourceNotFoundError(CycloidMCPError):
    """Resource not found error."""

    pass

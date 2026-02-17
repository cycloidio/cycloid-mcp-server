"""Dependency injection providers for FastMCP tools and resources."""

from src.cli import CLIMixin

_cli_instance: CLIMixin | None = None


def get_cli() -> CLIMixin:
    """Provide a CLIMixin instance for dependency injection."""
    global _cli_instance
    if _cli_instance is None:
        _cli_instance = CLIMixin()
    return _cli_instance

"""Cycloid MCP Server - A Model Context Protocol server for Cycloid platform."""

from .version import get_project_info, get_version

__version__ = get_version()
__author__ = "Cycloid Team"
__email__ = "team@cycloid.io"

# Export version utilities for external use
__all__ = ["__version__", "__author__", "__email__", "get_version", "get_project_info"]

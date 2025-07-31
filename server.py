#!/usr/bin/env python3
"""Main entry point for the Cycloid MCP server."""

import json
import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from fastmcp import FastMCP  # noqa: E402
from fastmcp.utilities.logging import get_logger  # noqa: E402
from src.cli_mixin import CLIMixin  # noqa: E402
from src.component_registry import ComponentRegistry  # noqa: E402
from src.version import get_project_info  # noqa: E402

logger = get_logger(__name__)


def global_tool_serializer(value):
    """Global serializer that handles JSON strings properly."""
    if isinstance(value, str):
        # If it's already a string, return it as-is
        return value
    # Otherwise, serialize to JSON
    return json.dumps(value, indent=2)


# Create FastMCP server at module level for CLI detection
mcp = FastMCP("Cycloid MCP Server", tool_serializer=global_tool_serializer)


def main():
    """Main entry point."""
    # Log server startup with version information
    project_info = get_project_info()
    logger.info(f"🚀 Starting Cycloid MCP Server {project_info["version"]}")

    cli = CLIMixin()

    # Initialize component registry and register all components automatically
    # This will discover and register all MCP components using MCPMixin's register_all method
    registry = ComponentRegistry(cli)
    registry.register_components(mcp)

    # Get registered components for logging
    registered_components = registry.get_registered_components()
    logger.info("✅ Automatically registered components", extra={"count": len(registered_components)})
    


    # Run the server
    mcp.run()


if __name__ == "__main__":
    main()

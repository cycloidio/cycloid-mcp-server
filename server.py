#!/usr/bin/env python3
"""Main entry point for the Cycloid MCP server."""

import json
import sys
from pathlib import Path
from typing import Any

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from fastmcp import FastMCP  # noqa: E402
from fastmcp.utilities.logging import get_logger  # noqa: E402
from starlette.middleware.cors import CORSMiddleware  # noqa: E402
from starlette.requests import Request  # noqa: E402
from starlette.responses import JSONResponse  # noqa: E402

from src.cli_mixin import CLIMixin  # noqa: E402
from src.component_registry import ComponentRegistry  # noqa: E402
from src.http_config import get_http_config, HTTPCycloidConfig  # noqa: E402
from src.version import get_project_info  # noqa: E402

logger = get_logger(__name__)


def global_tool_serializer(value: str | dict[str, Any] | list[Any]) -> str:
    """Global serializer that handles JSON strings properly."""
    if isinstance(value, str):
        # If it's already a string, return it as-is
        return value
    # Otherwise, serialize to JSON
    return json.dumps(value, indent=2)






def create_mcp_server() -> tuple[FastMCP[Any], CLIMixin]:
    """Create MCP server with HTTP CLI mixin."""
    project_info = get_project_info()

    cli = CLIMixin()
    server_name = f"Cycloid MCP Server HTTP {project_info['version']}"

    mcp: FastMCP[Any] = FastMCP(server_name, tool_serializer=global_tool_serializer)

    # Initialize component registry and register all components
    registry = ComponentRegistry(cli)
    registry.register_components(mcp)

    # Get registered components for logging
    registered_components = registry.get_registered_components()
    logger.info("✅ Automatically registered components", extra={"count": len(registered_components)})

    return mcp, cli




def create_http_app() -> tuple[Any, HTTPCycloidConfig]:
    """Create HTTP application with Starlette."""
    project_info = get_project_info()
    logger.info(f"🚀 Creating Cycloid MCP Server HTTP {project_info['version']}")

    config = get_http_config()
    mcp, _ = create_mcp_server()


    # Add custom routes for health check and info
    @mcp.custom_route("/health", methods=["GET"])
    async def health_check(request: Request) -> JSONResponse:
        """Health check endpoint."""
        return JSONResponse({"status": "healthy", "transport": "http"})

    @mcp.custom_route("/info", methods=["GET"])
    async def info(request: Request) -> JSONResponse:
        """Server information endpoint."""
        return JSONResponse({
            "name": "Cycloid MCP Server HTTP",
            "version": project_info["version"],
            "transport": "http",
            "config": {
                "cli_path": config.cli_path,
                "api_url": config.api_url,
                "host": config.host,
                "port": config.port,
            },
        })


    # Create the Starlette HTTP app
    http_app = mcp.http_app()

    # Add CORS middleware
    http_app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return http_app, config


def main():
    """Main entry point."""
    import uvicorn

    http_app, config = create_http_app()

    logger.info(f"🚀 Starting Cycloid MCP Server HTTP on {config.host}:{config.port}")

    uvicorn.run(
        http_app,
        host=config.host,
        port=config.port,
        log_level="info",
    )


if __name__ == "__main__":
    main()

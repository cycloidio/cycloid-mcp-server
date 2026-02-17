#!/usr/bin/env python3
"""Main entry point for the Cycloid MCP server."""

import sys
from pathlib import Path
from typing import Any

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from fastmcp import FastMCP  # noqa: E402
from fastmcp.server.providers import FileSystemProvider  # noqa: E402
from fastmcp.utilities.logging import get_logger  # noqa: E402
from starlette.requests import Request  # noqa: E402
from starlette.responses import JSONResponse  # noqa: E402

from src.config import get_http_config, HTTPCycloidConfig  # noqa: E402
from src.version import get_project_info  # noqa: E402

logger = get_logger(__name__)


def create_mcp_server() -> FastMCP[Any]:
    """Create MCP server with FileSystemProvider for auto-discovery."""
    project_info = get_project_info()

    server_name = f"Cycloid MCP Server HTTP {project_info['version']}"

    components_path = Path(__file__).parent / "src" / "components"

    mcp: FastMCP[Any] = FastMCP(
        server_name,
        instructions=(
            "MCP server for Cycloid infrastructure platform. "
            "Provides tools for managing blueprints, stacks, service catalogs, "
            "pipelines, and events."
        ),
        providers=[FileSystemProvider(components_path)],
    )

    logger.info("Registered components via FileSystemProvider")

    return mcp


def create_http_app() -> tuple[Any, HTTPCycloidConfig]:
    """Create HTTP application with Starlette."""
    project_info = get_project_info()
    logger.info(f"Creating Cycloid MCP Server HTTP {project_info['version']}")

    config = get_http_config()
    mcp = create_mcp_server()

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

    from starlette.middleware import Middleware
    from starlette.middleware.cors import CORSMiddleware

    middleware = [
        Middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_methods=["*"],
            allow_headers=["*"],
        )
    ]

    http_app = mcp.http_app(middleware=middleware)

    return http_app, config


def main():
    """Main entry point."""
    import uvicorn

    http_app, config = create_http_app()

    logger.info(f"Starting Cycloid MCP Server HTTP on {config.host}:{config.port}")

    uvicorn.run(
        http_app,
        host=config.host,
        port=config.port,
        log_level="info",
    )


if __name__ == "__main__":
    main()

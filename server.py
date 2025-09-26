#!/usr/bin/env python3
"""Main entry point for the Cycloid MCP server."""

import json
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from fastmcp import FastMCP  # noqa: E402
from fastmcp.utilities.logging import get_logger  # noqa: E402

from src.cli_mixin import CLIMixin  # noqa: E402
from src.component_registry import ComponentRegistry  # noqa: E402
from src.http_config import get_http_config  # noqa: E402
from src.version import get_project_info  # noqa: E402

logger = get_logger(__name__)


def global_tool_serializer(value):
    """Global serializer that handles JSON strings properly."""
    if isinstance(value, str):
        # If it's already a string, return it as-is
        return value
    # Otherwise, serialize to JSON
    return json.dumps(value, indent=2)


def extract_headers(request_headers: dict) -> tuple[str, str]:
    """
    Extract organization and API key from request headers.

    Args:
        request_headers: Dictionary of request headers

    Returns:
        Tuple of (organization, api_key)

    Raises:
        HTTPException: If required headers are missing
    """
    from fastapi import HTTPException  # noqa: E402

    organization = request_headers.get("X-CY-ORG")
    api_key = request_headers.get("X-CY-API-KEY")

    if not organization:
        raise HTTPException(
            status_code=400,
            detail="Missing required header: X-CY-ORG",
        )

    if not api_key:
        raise HTTPException(
            status_code=400,
            detail="Missing required header: X-CY-API-KEY",
        )

    return organization, api_key


class HTTPCLIMixin(CLIMixin):
    """HTTP-aware CLI mixin that extracts org and API key from headers."""

    def __init__(self):
        """Initialize HTTP CLI mixin."""
        # Initialize with HTTP config instead of regular config
        from src.http_config import get_http_config
        self.config = get_http_config()
        self._current_org: str | None = None
        self._current_api_key: str | None = None

        # Debug: log the CLI path being used
        logger.info(f"HTTPCLIMixin initialized with CLI path: {self.config.cli_path}")

    def set_request_context(self, organization: str, api_key: str):
        """Set the current request context for CLI operations."""
        self._current_org = organization
        self._current_api_key = api_key

    async def execute_cli_command(
        self,
        subcommand: str,
        args=None,
        flags=None,
        output_format: str = "json",
        timeout: int = 30,
        auto_parse: bool = False,
    ):
        """Execute CLI command with current request context."""
        return await super().execute_cli_command(
            subcommand=subcommand,
            args=args,
            flags=flags,
            output_format=output_format,
            timeout=timeout,
            auto_parse=auto_parse,
            organization=self._current_org,
            api_key=self._current_api_key,
        )

    async def execute_cli(
        self,
        subcommand: str,
        args=None,
        flags=None,
        output_format: str = "json",
        timeout: int = 30,
    ):
        """Execute CLI command with current request context (alias for execute_cli_command)."""
        return await self.execute_cli_command(
            subcommand=subcommand,
            args=args,
            flags=flags,
            output_format=output_format,
            timeout=timeout,
            auto_parse=True,  # Handlers expect parsed data
        )


def create_mcp_server(transport: str) -> tuple[FastMCP, CLIMixin]:
    """Create MCP server with appropriate CLI mixin based on transport."""
    project_info = get_project_info()

    if transport == "http":
        cli = HTTPCLIMixin()
        server_name = f"Cycloid MCP Server HTTP {project_info['version']}"
    else:
        cli = CLIMixin()
        server_name = f"Cycloid MCP Server {project_info['version']}"

    mcp = FastMCP(server_name, tool_serializer=global_tool_serializer)

    # Initialize component registry and register all components
    registry = ComponentRegistry(cli)
    registry.register_components(mcp)

    # Get registered components for logging
    registered_components = registry.get_registered_components()
    logger.info("✅ Automatically registered components", extra={"count": len(registered_components)})

    return mcp, cli


def run_stdio_server():
    """Run STDIO transport server."""
    project_info = get_project_info()
    logger.info(f"🚀 Starting Cycloid MCP Server STDIO {project_info['version']}")

    mcp, _ = create_mcp_server("stdio")
    mcp.run()


def run_http_server():
    """Run HTTP transport server."""
    try:
        import asyncio  # noqa: E402
        from starlette.requests import Request  # noqa: E402
        from starlette.responses import JSONResponse  # noqa: E402
    except ImportError as e:
        logger.error(f"HTTP transport requires additional dependencies: {e}")
        logger.error("Please install FastAPI and uvicorn: pip install fastapi uvicorn")
        sys.exit(1)

    project_info = get_project_info()
    logger.info(f"🚀 Starting Cycloid MCP Server HTTP {project_info['version']}")

    config = get_http_config()
    mcp, http_cli = create_mcp_server("http")

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

    # Add middleware to inject headers into CLI mixin
    async def inject_headers_middleware(request: Request, call_next):
        """Inject organization and API key from headers into CLI mixin."""
        try:
            organization, api_key = extract_headers(dict(request.headers))
            http_cli.set_request_context(organization, api_key)
        except Exception:
            # Let the error propagate - don't set context for invalid requests
            pass

        response = await call_next(request)
        return response

    # Add the middleware to the MCP server
    mcp.add_middleware(inject_headers_middleware)

    async def run_server():
        """Run the MCP server asynchronously."""
        await mcp.run_async(
            transport="http",
            host=config.host,
            port=config.port,
        )

    # Run the async server
    asyncio.run(run_server())


def main():
    """Main entry point."""
    transport = os.environ.get("TRANSPORT", "stdio").lower()

    if transport not in ["stdio", "http"]:
        logger.error(f"Invalid transport '{transport}'. Must be 'stdio' or 'http'")
        logger.error("Set TRANSPORT environment variable to 'stdio' or 'http'")
        sys.exit(1)

    logger.info(f"Using transport: {transport}")

    if transport == "http":
        run_http_server()
    else:
        run_stdio_server()


if __name__ == "__main__":
    main()

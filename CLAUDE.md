# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Cycloid MCP Server is a Model Context Protocol (MCP) server that bridges AI assistants with the Cycloid infrastructure automation platform. It wraps the Cycloid CLI (`cy` binary) to expose blueprints, stacks, service catalogs, pipelines, and events as MCP tools and resources over HTTP.

## Common Commands

```bash
make setup              # First-time dev environment setup (installs uv + deps)
make dev-server         # Run development server
make test               # Run all tests with pytest
make type-check         # Pyright strict mode type checking
make lint               # flake8 linting
make format             # Format with black + isort
make quality-check      # All checks: test + type-check + lint
make simulate-ci        # Full local CI simulation (validates Python 3.13, runs all checks)
make build              # Build Docker image
make prod-server        # Run production Docker container
```

Run a single test file:
```bash
uv run pytest tests/test_stack_component.py -v
```

## Architecture

### Request Flow

```
HTTP Request → FastMCP 3.0 (Starlette/Uvicorn) → @tool/@resource function
  → CLIMixin (via Depends) → Cycloid CLI binary → Cycloid API
```

The server is HTTP-only and multi-tenant: org and API key come from request headers (`X-CY-ORG`, `X-CY-API-KEY`), not environment variables.

### Component System (FastMCP 3.0)

Components are **plain async functions** in `src/components/`, auto-discovered by `FileSystemProvider`. No registry, no base classes — just `@tool()` and `@resource()` decorators with `Depends(get_cli)` for CLI injection.

Each component file contains:
- Private helper functions (prefixed `_`)
- `@tool` decorated async functions — MCP tools
- `@resource` decorated async functions — MCP resources

Current component files: `catalogs.py`, `events.py`, `pipelines.py`, `stacks.py` (includes elicitation), `stackforms.py`.

**Pattern for new tools:**
```python
from fastmcp.dependencies import Depends
from fastmcp.exceptions import ToolError
from fastmcp.tools import tool
from src.cli import CLIMixin
from src.dependencies import get_cli

@tool(name="CYCLOID_THING_LIST", description="...", annotations={"readOnlyHint": True})
async def list_things(cli: CLIMixin = Depends(get_cli)) -> Dict[str, Any]:
    data = await cli.execute_cli("thing", ["list"])
    return {"things": cli.process_cli_response(data), "count": ...}
```

### Key Source Files

- `server.py` — HTTP server entry point, FileSystemProvider setup, custom routes
- `src/cli.py` — CLIMixin: async CLI execution, JSON-only output, response processing
- `src/dependencies.py` — `get_cli()` provider for `Depends()` injection
- `src/config.py` — HTTPCycloidConfig for server configuration
- `src/types.py` — Type aliases (`JSONDict`, `JSONList`, `CliFlags`, etc.)
- `src/exceptions.py` — Custom exceptions (`CycloidCLIError`, `CycloidAPIError`)

### Error Handling

Use `ToolError` from `fastmcp.exceptions` for tool-level errors (validation failures, not-found, etc.). Use `CycloidCLIError` for CLI execution failures. Log with `get_logger` from `fastmcp.utilities.logging`.

## Code Conventions

- **Python 3.12+** (CI runs 3.13, Docker uses 3.12-alpine)
- **Import order**: stdlib → third-party → local (`src.`) → relative (`.`)
- **Types**: Import from `src.types` (`JSONDict`, `JSONList`, `OptionalString`, etc.) instead of using `Dict[str, Any]` or `Any`
- **Formatting**: black (88 char line length), isort (black profile), flake8 (100 char max)
- **Type checking**: Pyright in strict mode (`pyrightconfig.json`). FastMCP's `Depends` import needs `# type: ignore[reportAttributeAccessIssue]` and defaults need `# type: ignore[reportCallInDefaultInitializer]`.
- **Output format**: JSON-only (hardcoded `--output json` in CLI commands). No table formatting.
- **CLI calls**: Use `execute_cli_command` with `auto_parse` parameter; use `process_cli_response` for standardized output

## Testing

Tests use pytest + pytest-asyncio with FastMCP's `Client` for integration testing. Mock `CLIMixin` with `@patch` and `AsyncMock`. Test fixtures create a `FastMCP` server instance, register component functions via `server.add_tool()`/`server.add_resource()`, then test through the MCP client interface. Tool errors raise `ToolError` exceptions in the client.

## Commit Messages

Follow conventional commits: `type(scope): description` where type is `feat`, `fix`, `docs`, `style`, `refactor`, `test`, or `chore`.

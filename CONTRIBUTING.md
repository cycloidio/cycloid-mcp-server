# Contributing to Cycloid MCP Server

Thank you for your interest in contributing to the Cycloid MCP Server! This document provides guidelines for setting up your development environment and contributing to the project.

## Development Environment Setup

### Prerequisites

- Python 3.12 or higher
- [uv](https://github.com/astral-sh/uv) package manager (recommended) or pip
- Git
- Valid Cycloid API credentials

### Quick Start

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd cycloid-mcp-server
   ```

2. **Set up the development environment with uv (recommended)**
   ```bash
   # Install uv if you haven't already
   curl -LsSf https://astral.sh/uv/install.sh | sh

   # Setup development environment
   make setup
   ```

3. **Alternative: Set up with pip**
   ```bash
   # Create virtual environment
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate

   # Install dependencies
   pip install -e .
   ```

4. **Configure MCP client**

   Set up your MCP client (like Cursor) to use the development server. See [MCP Configuration Examples](mcp-examples.md) for detailed instructions.

## Development Workflow

### Running the Server

#### Development Server (Python Virtual Environment)
```bash
# Run the development server
make dev-server

# Or manually:
uv run python server.py
```

#### Production Server (Docker)
```bash
# Build the production image
make build

# Run the production server
make prod-server

# Or manually:
docker run --rm -i \
  -e CY_ORG=your-organization \
  -e CY_API_KEY=your-api-key \
  -e CY_API_URL=https://http-api.cycloid.io \
  cycloid-mcp-server:latest
```

### Code Quality Checks

The project uses several tools to maintain code quality. Run these before committing:

```bash
# Run all quality checks (tests + type checking + linting)
make quality-check

# Individual checks:
make test           # Run all tests
make type-check     # Type checking with Pyright
make lint           # Linting with flake8
make format         # Format code with Black and isort
```

### Testing

```bash
# Run all tests
make test

# Run specific test file
uv run pytest tests/test_stack_component.py -v

# Run with coverage
uv run pytest tests/ --cov=src --cov-report=html
```

## Project Structure

### Component Architecture with BaseHandler Pattern

The server uses an optimized dynamic component registration system with BaseHandler inheritance and centralized utilities:

```
src/
├── base_handler.py        # Base class for all handlers
├── types.py              # Centralized type definitions
├── error_handling.py     # Unified error handling system
├── components/
│   ├── catalogs/         # Catalog management components
│   │   ├── catalogs_tools.py
│   │   ├── catalogs_resources.py
│   │   └── catalogs_handler.py    # Inherits from BaseHandler
│   └── stacks/          # Stack management components
│       ├── stacks_tools.py
│       ├── stacks_resources.py
│       ├── stacks_handler.py      # Inherits from BaseHandler
│       ├── stackforms_tools.py
│       ├── stackforms_handler.py  # Inherits from BaseHandler
│       └── constants.py           # Minimal constants only
├── cli_mixin.py         # CLI execution utilities
├── component_registry.py # Automatic component discovery
├── config.py           # Configuration management
└── exceptions.py       # Custom exceptions
```

### Key Architectural Improvements

1. **BaseHandler Pattern**: All handlers inherit from `BaseHandler` for consistent CLI access and logging
2. **Centralized Types**: Common types defined in `src.types` for better type safety
3. **Unified Error Handling**: `@handle_errors` decorator for consistent error management
4. **Template Externalization**: Large templates moved to separate `.md` files with caching
5. **Memory Optimization**: Conditional debug logging and proper resource management
6. **Import Organization**: Standardized import order across all files

### Component Patterns

Each component follows an optimized consistent pattern:

- **`*_handlers.py`**: Core utilities and private functions
  - **MUST inherit from `BaseHandler`** (gets `self.cli` and `self.logger` automatically)
  - Use `@handle_errors` decorator for consistent error handling
  - Import types from `src.types` (JSONDict, JSONList, etc.)
  - Use proper import organization (stdlib → third-party → local → relative)

- **`*_tools.py`**: MCP tools (`@mcp_tool` decorated functions)
  - Inherits from `MCPMixin`
  - Uses handler for core logic
  - Proper type annotations from `src.types`

- **`*_resources.py`**: MCP resources (`@mcp_resource` decorated functions)
  - Inherits from `MCPMixin`
  - Uses handler for core logic
  - Proper type annotations from `src.types`

- **`*_prompts.py`**: MCP prompts (`@mcp_prompt` decorated functions) (if needed)

### Automatic Registration

Components are automatically discovered and registered by the `ComponentRegistry`:

1. **Discovery**: Scans `src/components/` for files matching the patterns
2. **Loading**: Imports modules and finds classes inheriting from `MCPMixin`
3. **Registration**: Uses FastMCP's `register_all()` method to register tools/resources
4. **Logging**: Provides detailed logging of the registration process

## Adding New Components

### 1. Create Component Files

Create a new directory in `src/components/` for your feature:

```bash
mkdir src/components/your-feature/
```

### 2. Implement Handler Class

```python
# src/components/your-feature/your_feature_handler.py
"""Your feature handler utilities and core logic."""

# Standard library imports
import asyncio
from typing import Optional

# Third-party imports
from fastmcp.utilities.logging import get_logger

# Local imports
from src.base_handler import BaseHandler
from src.cli_mixin import CLIMixin
from src.error_handling import handle_errors
from src.types import JSONDict, JSONList, OptionalString

class YourFeatureHandler(BaseHandler):
    """Core your feature operations and utilities."""

    def __init__(self, cli: CLIMixin):
        """Initialize handler with BaseHandler."""
        super().__init__(cli)  # Provides self.cli and self.logger automatically

    @handle_errors(
        action="fetch your feature data",
        suggestions=["Check API connectivity", "Verify permissions", "Review CLI configuration"]
    )
    async def get_data(self) -> JSONList:
        """Get data from CLI with unified error handling."""
        data = await self.cli.execute_cli("your-command", ["args"])
        return self.cli.process_cli_response(data, list_key="items")
```

### 3. Implement Tools Class (OPTIMIZED)

```python
# src/components/your-feature/your_feature_tools.py
"""Your feature MCP tools."""

# Standard library imports
import json

# Third-party imports
from fastmcp.contrib.mcp_mixin import MCPMixin, mcp_tool

# Local imports
from src.cli_mixin import CLIMixin
from src.types import JSONList, OptionalString
from .your_feature_handler import YourFeatureHandler

class YourFeatureTools(MCPMixin):
    """Your feature MCP tools with optimized patterns."""

    def __init__(self, cli: CLIMixin):
        """Initialize tools with CLI mixin."""
        super().__init__()
        self.handler = YourFeatureHandler(cli)

    @mcp_tool(
        name="your_tool_name",
        description="Description of what this tool does",
        enabled=True,
    )
    async def your_tool_method(self, param: str) -> str:
        """Your tool implementation."""
        # Error handling is done by @handle_errors in handler
        data = await self.handler.get_data()

        # Process and return data
        return json.dumps(data, indent=2)
```

### 4. Implement Resources Class

```python
# src/components/your-feature/your_feature_resources.py
"""Your feature MCP resources."""

# Standard library imports
import json

# Third-party imports
from fastmcp.contrib.mcp_mixin import MCPMixin, mcp_resource

# Local imports
from src.cli_mixin import CLIMixin
from src.types import JSONDict
from .your_feature_handler import YourFeatureHandler

class YourFeatureResources(MCPMixin):
    """Your feature MCP resources with optimized patterns."""

    def __init__(self, cli: CLIMixin):
        """Initialize resources with CLI mixin."""
        super().__init__()
        self.handler = YourFeatureHandler(cli)

    @mcp_resource("cycloid://your-resource")
    async def get_your_resource(self) -> str:
        """Get your resource data."""
        # Error handling is done by @handle_errors in handler
        data = await self.handler.get_data()

        result = {
            "items": data,
            "count": len(data)
        }
        return json.dumps(result, indent=2)
```

### 5. Add Tests

Create comprehensive test files using the optimized patterns:

```python
# tests/test_your_feature_component.py
"""Tests for YourFeature component using optimized patterns."""

# Standard library imports
import pytest
from unittest.mock import AsyncMock, patch

# Third-party imports
from fastmcp import FastMCP, Client

# Local imports
from src.components.your_feature.your_feature_tools import YourFeatureTools
from src.components.your_feature.your_feature_resources import YourFeatureResources
from src.components.your_feature.your_feature_handler import YourFeatureHandler
from src.cli_mixin import CLIMixin

@pytest.fixture
def your_feature_server():
    """Create a test MCP server with your feature components."""
    server = FastMCP("TestYourFeatureServer")

    # Initialize CLI mixin
    cli = CLIMixin()

    # Create and register components
    tools = YourFeatureTools(cli)
    resources = YourFeatureResources(cli)

    tools.register_all(server)
    resources.register_all(server)

    return server

class TestYourFeatureHandler:
    """Test YourFeatureHandler with BaseHandler inheritance."""

    @pytest.fixture
    def handler(self):
        """Create handler instance."""
        cli = CLIMixin()
        return YourFeatureHandler(cli)

    def test_handler_inherits_from_base_handler(self, handler):
        """Test that handler inherits from BaseHandler."""
        from src.base_handler import BaseHandler
        assert isinstance(handler, BaseHandler)
        assert hasattr(handler, 'cli')
        assert hasattr(handler, 'logger')

@patch('src.components.your_feature.your_feature_handler.CLIMixin')
async def test_your_feature_tools(mock_cli_class, your_feature_server):
    """Test YourFeature tools functionality."""
    # Mock setup
    mock_cli = AsyncMock()
    mock_cli_class.return_value = mock_cli
    mock_cli.execute_cli.return_value = [{"test": "data"}]
    mock_cli.process_cli_response.return_value = [{"test": "data"}]

    # Test using FastMCP Client
    async with Client(your_feature_server) as client:
        result = await client.call_tool("your_tool_name", {"param": "test"})
        assert "data" in result.data
```

### 4. No Manual Registration Required

The component will be automatically discovered and registered - no changes to `server.py` needed!

## Code Style Guidelines

### Python Code Style

- Follow [PEP 8](https://pep8.org/) guidelines with optimized import organization
- Use type hints from `src.types` for all function parameters and return values
- Keep functions focused and under 50 lines when possible
- Use meaningful variable and function names
- Apply proper import organization: stdlib → third-party → local → relative

### Architecture Patterns

- **BaseHandler Inheritance**: All handlers MUST inherit from `src.base_handler.BaseHandler`
- **Centralized Types**: Import types from `src.types` instead of `typing` directly
- **Unified Error Handling**: Use `@handle_errors` decorator for consistent error management

- **Memory Optimization**: Use conditional debug logging and proper resource management

### Error Handling

- Use `@handle_errors` decorator from `src.error_handling` for consistent error handling
- Provide descriptive action names and helpful suggestions
- Let the decorator handle `CycloidCLIError` vs `Exception` automatically
- Use `self.logger` (provided by `BaseHandler`) for consistent logging
- Return user-friendly error messages with consistent formatting

### Type Safety

- Import common types from `src.types`: `JSONDict`, `JSONList`, `CliFlags`, etc.
- Avoid `Any` usage - prefer specific type aliases
- Use `ElicitationResult`, `StackCreationParams` for complex operations
- Maintain comprehensive type annotations throughout

### Performance & Memory

- Use conditional debug logging: `if logger.isEnabledFor(logger.DEBUG): logger.debug(...)`
- Apply `@lru_cache` only for static data (templates, file discovery)
- NEVER cache CLI API responses (dynamic data)
- Use `tempfile.NamedTemporaryFile(delete=True)` for automatic resource cleanup
- Use `execute_cli_command` with `auto_parse` parameter to avoid duplication

### Testing

- Write unit tests for all new functionality using optimized patterns
- Test `BaseHandler` inheritance and `@handle_errors` decorator usage
- Include integration tests for complex workflows
- Test edge cases and error conditions with new error handling system
- Maintain test coverage with proper mocking of CLI operations

## Commit Guidelines

### Commit Message Format

```
type(scope): description

[optional body]

[optional footer]
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

### Examples

```
feat(stacks): add blueprint validation tool

Add new MCP tool for validating blueprint configurations
before stack creation.

Closes #123
```

```
fix(catalogs): handle empty repository list

Return empty table instead of error when no repositories
are found.
```

## Pull Request Process

1. **Create a feature branch** from `main`
2. **Make your changes** following the guidelines above
3. **Add tests** for new functionality
4. **Run quality checks** to ensure code quality
5. **Update documentation** if needed
6. **Submit a pull request** with a clear description

### PR Checklist

- [ ] Code follows style guidelines
- [ ] Tests pass (`make test`)
- [ ] Type checking passes (`make type-check`)
- [ ] Linting passes (`make lint`)
- [ ] Documentation updated
- [ ] Commit messages follow guidelines

## Getting Help

- **Issues**: Use GitHub issues for bug reports and feature requests
- **Discussions**: Use GitHub discussions for questions and general discussion
- **Documentation**: Check the [README.md](README.md) and [MCP Configuration Examples](mcp-examples.md)

## License

By contributing to this project, you agree that your contributions will be licensed under the MIT License.

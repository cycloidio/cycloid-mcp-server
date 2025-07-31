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

### Component Architecture

The server uses a dynamic component registration system based on FastMCP's MCPMixin:

```
src/
├── components/
│   ├── catalogs/           # Catalog management components
│   │   ├── catalogs_tools.py
│   │   ├── catalogs_resources.py
│   │   └── catalogs_handler.py
│   └── stacks/            # Stack management components
│       ├── blueprints_tools.py
│       ├── blueprints_resources.py
│       ├── blueprints_handler.py
│       ├── stackforms_tools.py
│       └── stackforms_handler.py
├── cli_mixin.py           # CLI execution utilities
├── component_registry.py  # Automatic component discovery
├── config.py             # Configuration management
└── exceptions.py         # Custom exceptions
```

### Component Patterns

Each component follows a consistent pattern:

- **`*_tools.py`**: MCP tools (`@mcp_tool` decorated functions)
- **`*_resources.py`**: MCP resources (`@mcp_resource` decorated functions)
- **`*_handlers.py`**: Core utilities and private functions
- **`*_prompts.py`**: MCP prompts (`@mcp_prompt` decorated functions)

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

### 2. Implement Component Classes

Create the component files following the naming conventions:

```python
# src/components/your-feature/your_feature_tools.py
from fastmcp.contrib.mcp_mixin import MCPMixin, mcp_tool
from src.cli_mixin import CLIMixin

class YourFeatureTools(MCPMixin):
    def __init__(self, cli: CLIMixin):
        self.cli = cli
    
    @mcp_tool(
        name="your_tool_name",
        description="Description of what this tool does",
        enabled=True,
    )
    async def your_tool_method(self, param: str) -> str:
        # Your tool implementation
        return "Tool result"
```

```python
# src/components/your-feature/your_feature_resources.py
from fastmcp.contrib.mcp_mixin import MCPMixin, mcp_resource
from src.cli_mixin import CLIMixin

class YourFeatureResources(MCPMixin):
    def __init__(self, cli: CLIMixin):
        self.cli = cli
    
    @mcp_resource("cycloid://your-resource")
    async def get_your_resource(self) -> str:
        # Your resource implementation
        return "Resource data"
```

### 3. Add Tests

Create corresponding test files:

```python
# tests/test_your_feature_component.py
import pytest
from src.components.your_feature.your_feature_tools import YourFeatureTools
from src.components.your_feature.your_feature_resources import YourFeatureResources

class TestYourFeatureComponent:
    def test_your_feature_tools_registered(self):
        # Test that tools are properly registered
        pass
    
    def test_your_feature_resources_registered(self):
        # Test that resources are properly registered
        pass
```

### 4. No Manual Registration Required

The component will be automatically discovered and registered - no changes to `server.py` needed!

## Code Style Guidelines

### Python Code Style

- Follow [PEP 8](https://pep8.org/) guidelines
- Use type hints for all function parameters and return values
- Keep functions focused and under 50 lines when possible
- Use meaningful variable and function names

### Error Handling

- Use custom exceptions from `src.exceptions`
- Implement proper error recovery
- Provide meaningful error messages
- Log errors appropriately using `structlog`

### Testing

- Write unit tests for all new functionality
- Include integration tests for complex workflows
- Test edge cases and error conditions
- Maintain test coverage

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
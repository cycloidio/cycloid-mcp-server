---
description: Rules for developing Cycloid MCP components using the modular architecture pattern
globs: src/components/**/*.py,tests/test_*_component.py
---

# Cycloid MCP Component Development Rules

## Component Architecture Overview

The Cycloid MCP Server uses a modular component architecture with automatic registration. Each component follows a consistent pattern that separates concerns and enables automatic discovery.

## Component Structure

### Directory Organization
```
src/components/[feature_name]/
├── __init__.py              # Export all classes
├── [feature]_handler.py     # Core utilities and private functions
├── [feature]_tools.py       # MCP tools (@mcp_tool decorated functions)
└── [feature]_resources.py   # MCP resources (@mcp_resource decorated functions)
```

### File Responsibilities

1. **`[feature]_handler.py`**: Core business logic and utilities
   - Does NOT inherit from `MCPMixin`
   - Contains private utility methods
   - Handles CLI interactions via `CLIMixin`
   - Shared logic between tools and resources

2. **`[feature]_tools.py`**: MCP Tools
   - Inherits from `MCPMixin`
   - Contains `@mcp_tool` decorated methods
   - Uses handler for core logic
   - Exposes functionality to MCP clients

3. **`[feature]_resources.py`**: MCP Resources
   - Inherits from `MCPMixin`
   - Contains `@mcp_resource` decorated methods
   - Uses handler for core logic
   - Provides data resources to MCP clients

## Component Implementation Patterns

### Handler Class Template
```python
"""Feature handler utilities and core logic."""

from typing import Any, Dict, List
from src.cli_mixin import CLIMixin
import structlog

logger = structlog.get_logger()

class FeatureHandler:
    """Core feature operations and utilities."""
    
    def __init__(self, cli: CLIMixin):
        """Initialize handler with CLI mixin."""
        self.cli = cli
    
    async def _get_data(self) -> List[Dict[str, Any]]:
        """Get data from CLI - shared logic."""
        try:
            data = await self.cli.execute_cli_json("command", ["args"])
            return data if isinstance(data, list) else data.get("key", [])
        except Exception as e:
            logger.error(f"Failed to fetch data: {str(e)}")
            raise
```

### Tools Class Template
```python
"""Feature MCP tools."""

from typing import Any
from fastmcp.contrib.mcp_mixin import MCPMixin, mcp_tool
from src.cli_mixin import CLIMixin
from .[feature]_handler import FeatureHandler

class FeatureTools(MCPMixin):
    """Feature MCP tools."""
    
    def __init__(self, cli: CLIMixin):
        """Initialize tools with CLI mixin."""
        super().__init__()
        self.handler = FeatureHandler(cli)
    
    @mcp_tool(
        name="list_items",
        description="List all available items with their details.",
        enabled=True
    )
    async def list_items(self, format: str = "table") -> str:
        """List items in specified format."""
        try:
            data = await self.handler._get_data()
            # Format and return data
            return self._format_output(data, format)
        except Exception as e:
            return f"❌ Error listing items: {str(e)}"
```

### Resources Class Template
```python
"""Feature MCP resources."""

import json
from fastmcp.contrib.mcp_mixin import MCPMixin, mcp_resource
from src.cli_mixin import CLIMixin
from src.exceptions import CycloidCLIError
from .[feature]_handler import FeatureHandler

class FeatureResources(MCPMixin):
    """Feature MCP resources."""
    
    def __init__(self, cli: CLIMixin):
        """Initialize resources with CLI mixin."""
        super().__init__()
        self.handler = FeatureHandler(cli)
    
    @mcp_resource("cycloid://feature-resource")
    async def get_feature_resource(self) -> str:
        """Get feature data as a resource."""
        try:
            data = await self.handler._get_data()
            result = {
                "items": data,
                "count": len(data)
            }
            return json.dumps(result, indent=2)
        except CycloidCLIError as e:
            return json.dumps({
                "error": f"Failed to load feature data: {str(e)}",
                "items": [],
                "count": 0
            }, indent=2)
```

## Component Development Workflow

### Creating New Components

1. **Create Directory Structure**
   ```bash
   mkdir -p src/components/[feature_name]
   ```

2. **Create Required Files**
   - `__init__.py` - Export classes
   - `[feature]_handler.py` - Core logic
   - `[feature]_tools.py` - MCP tools
   - `[feature]_resources.py` - MCP resources

3. **Follow Naming Conventions**
   - Use lowercase with underscores for file names
   - Use PascalCase for class names
   - Use descriptive names that reflect functionality

4. **No Server.py Changes Needed**
   - Components are automatically discovered and registered
   - The `ComponentRegistry` handles all registration

### Component Registration

- **Automatic Discovery**: Components are found by scanning `*_tools.py` and `*_resources.py` files
- **MCPMixin Detection**: Only classes inheriting from `MCPMixin` are registered
- **CLI Integration**: All components receive `CLIMixin` instance automatically
- **Error Handling**: Failed registrations are logged but don't stop the server

## Testing Patterns

### Test File Structure
```python
"""Tests for [Feature]Component using FastMCP Client pattern."""

import pytest
from unittest.mock import AsyncMock, patch
from fastmcp import FastMCP, Client
from src.components.[feature] import FeatureTools, FeatureResources
from src.cli_mixin import CLIMixin

@pytest.fixture
def [feature]_server():
    """Create a test MCP server with [feature] components."""
    server = FastMCP("Test[Feature]Server")
    
    # Initialize CLI mixin
    cli = CLIMixin()
    
    # Create and register components
    tools = FeatureTools(cli)
    resources = FeatureResources(cli)
    
    tools.register_all(server)
    resources.register_all(server)
    
    return server

@patch('src.components.[feature].[feature]_handler.CLIMixin')
async def test_list_items(mock_cli_class, [feature]_server):
    """Test list_items tool functionality."""
    # Mock setup
    mock_cli = AsyncMock()
    mock_cli_class.return_value = mock_cli
    mock_cli.execute_cli_json.return_value = [{"test": "data"}]
    
    # Test using FastMCP Client
    async with Client([feature]_server) as client:
        result = await client.call_tool("list_items", {"format": "json"})
        assert "data" in result.data
```

### Testing Guidelines

1. **Test Both Tools and Resources**
   - Test all `@mcp_tool` decorated methods
   - Test all `@mcp_resource` decorated methods
   - Verify proper error handling

2. **Mock CLI Interactions**
   - Use `@patch` to mock `CLIMixin`
   - Test both success and failure scenarios
   - Verify CLI commands are called correctly

3. **Use FastMCP Client**
   - Test components through the MCP interface
   - Verify tool names and resource URIs
   - Test parameter validation

## Best Practices

### Error Handling
- Always wrap CLI calls in try/except blocks
- Use custom exceptions from `src.exceptions`
- Provide meaningful error messages
- Log errors with appropriate context

### Type Hints
- Use comprehensive type hints throughout
- Import types from `typing` module
- Avoid using `Any` - prefer specific types
- Document complex type structures

### Code Organization
- Keep handler methods focused and small
- Use descriptive method names
- Group related functionality together
- Follow single responsibility principle

### Documentation
- Use clear docstrings for all public methods
- Document complex business logic
- Include usage examples in docstrings
- Keep comments up-to-date

## Quality Checklist

### Before Creating Components
- [ ] Understand the feature requirements
- [ ] Plan the component structure
- [ ] Identify shared logic for handler
- [ ] Design tool and resource interfaces

### During Development
- [ ] Follow naming conventions
- [ ] Implement comprehensive error handling
- [ ] Add type hints to all functions
- [ ] Write tests for all functionality
- [ ] Use meaningful variable names

### Before Committing
- [ ] All tests pass
- [ ] Type checking passes (pyright)
- [ ] Code follows PEP 8
- [ ] Documentation is complete
- [ ] Error handling is robust

## Common Patterns

### Data Fetching Pattern
```python
async def _get_data(self) -> List[Dict[str, Any]]:
    """Get data from CLI with proper error handling."""
    try:
        data = await self.cli.execute_cli_json("command", ["args"])
        return data if isinstance(data, list) else data.get("key", [])
    except Exception as e:
        logger.error(f"Failed to fetch data: {str(e)}")
        raise
```

### Output Formatting Pattern
```python
def _format_output(self, data: List[Dict[str, Any]], format: str) -> str:
    """Format data for different output types."""
    if format == "json":
        return json.dumps(data, indent=2)
    else:
        return self._format_table(data)
```

### Resource Error Handling Pattern
```python
@mcp_resource("cycloid://resource")
async def get_resource(self) -> str:
    """Get resource with error handling."""
    try:
        data = await self.handler._get_data()
        return json.dumps({"data": data}, indent=2)
    except CycloidCLIError as e:
        return json.dumps({
            "error": str(e),
            "data": []
        }, indent=2)
``` 
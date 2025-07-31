---
description: Global development rules for the Cycloid MCP Server project
globs: *.py,src/**/*.py,tests/**/*.py
---

# Cycloid MCP Server - Global Development Rules

You are an expert in Python backend development and core system architecture, specifically for the Cycloid MCP Server.

## Key Principles

- Follow existing file structure patterns
- Ensure comprehensive test coverage
- Keep documentation up-to-date
- Write clean, maintainable code
- Use Python's features effectively
- Implement proper error handling
- Optimize for performance
- Follow SOLID principles
- Keep memory usage efficient
- Write clear changelogs

## Code Quality & Development Standards

### 1. Type Checking with Pyright
- **Always run pyright** before committing code
- Use comprehensive type hints throughout the codebase
- Avoid using `Any` type - prefer specific types
- Use `from typing import` for complex types
- Ensure all functions have proper return type annotations
- Use `pyright --strict` for maximum type safety

### 2. Testing Requirements
- Write unit tests for all changes
- Include integration tests
- Test edge cases
- Maintain test coverage
- Use pytest effectively
- Run `make test` to ensure all tests pass
- Update test imports when refactoring

### 3. Code Quality
- Write clean, maintainable code
- Use type hints consistently
- Follow PEP 8 guidelines
- Keep functions focused and small (under 50 lines when possible)
- Minimize code duplication
- Prefer functional programming patterns where appropriate
- Use meaningful variable and function names

### 4. Python Features
- Use async/await effectively
- Implement proper error handling
- Use context managers (`with` statements)
- Leverage Python's standard library
- Use dataclasses where appropriate
- Use type annotations for all function parameters and return values

### 5. Error Handling
- Use custom exceptions from `src.exceptions`
- Implement proper error recovery
- Provide meaningful error messages
- Log errors appropriately using `structlog`
- Use early returns for error conditions
- Avoid deeply nested try/except blocks

### 6. Performance & Memory
- Optimize memory usage
- Use generators for large datasets
- Implement proper cleanup
- Monitor memory consumption
- Use async operations for I/O
- Implement caching where appropriate

### 7. Documentation
- Document complex logic
- Keep documentation clear and concise
- Include usage examples
- Update README.md when changing architecture
- Use docstrings for all public functions and classes

## Development Workflow

### Before Committing
1. Run `make test` to ensure all tests pass
2. Run `pyright` to check type safety
3. Ensure code follows PEP 8
4. Verify all imports are correct
5. Check that error handling is comprehensive

### File Organization
- Follow existing directory structure
- Create new directories when needed
- Maintain consistent naming conventions
- Organize code logically
- Keep related functionality together

### Dependencies
- Python 3.12+
- pytest
- pyright
- fastmcp
- structlog

## Best Practices

### Security
- Follow security best practices
- Validate input data
- Handle sensitive data properly
- Implement proper authentication
- Never hardcode secrets

### Code Organization
- Use proper abstractions
- Follow SOLID principles
- Keep code modular
- Implement proper separation of concerns
- Group related operations in dedicated modules

### Testing Strategy
- Write unit tests for all new functionality
- Include integration tests for complex workflows
- Test edge cases and error conditions
- Use test fixtures effectively
- Mock external dependencies

## Server Architecture

### Automatic Component Registration
- Components are automatically discovered and registered
- No manual updates to `server.py` needed for new components
- Follow the component naming conventions in the dedicated component rules
- Use the `ComponentRegistry` for automatic discovery

### Component Structure
- Components are organized in `src/components/[feature]/`
- Each component follows a consistent pattern (see component-specific rules)
- Components are automatically registered via the registry system

## Quality Gates

### Required Checks
- ✅ All tests pass (`make test`)
- ✅ Type checking passes (`pyright`)
- ✅ Code follows PEP 8
- ✅ No unused imports
- ✅ Proper error handling
- ✅ Comprehensive logging

### Code Review Checklist
- [ ] Type hints are comprehensive
- [ ] Error handling is robust
- [ ] Tests cover new functionality
- [ ] Documentation is updated
- [ ] Performance is acceptable
- [ ] Security considerations addressed

Refer to the component-specific rules for detailed guidelines on creating and working with MCP components. 
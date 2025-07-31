# Cycloid MCP Server Documentation

This directory contains detailed documentation for the Cycloid MCP Server.

## Available Documentation

### [stack_create_from_blueprint.md](stack_create_from_blueprint.md)
Comprehensive documentation for the guided workflow used when creating Cycloid Terraform stacks from blueprints. This document explains:

- Step-by-step workflow process
- User validation requirements
- Parameter descriptions and usage
- Examples and best practices
- Error handling and troubleshooting

## File Organization

Documentation files are named to match their corresponding Go handler files for easy navigation:

- `stack_create_from_blueprint.md` ↔ `internal/handlers/stack_create_from_blueprint.go`
- Future documentation files will follow the same naming convention

## Contributing

When adding new handlers or features, please:

1. Create corresponding documentation in this folder
2. Name the file to match the Go handler file
3. Update this README.md to include the new documentation
4. Update the main README.md to reference the new documentation 
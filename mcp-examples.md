# MCP Configuration Examples

This document provides examples of how to configure the Cycloid MCP Server for different environments.

## Development Environment (Python Virtual Environment)

For development, use the Python virtual environment with `uv`:

```json
{
  "mcpServers": {
    "Cycloid MCP Server (Dev)": {
      "command": "uv",
      "args": [
        "run",
        "--project",
        "/path/to/cycloid-mcp-server",
        "--with",
        "pydantic",
        "--with",
        "python-dotenv",
        "python",
        "/path/to/cycloid-mcp-server/server.py"
      ],
      "env": {
        "PYTHONPATH": "/path/to/cycloid-mcp-server",
        "PYTHONUNBUFFERED": "1",
        "CY_ORG": "your-organization",
        "CY_API_KEY": "your-api-key-here",
        "CY_API_URL": "https://http-api.cycloid.io",
        "CY_CLI_PATH": "/usr/local/bin/cy"
      },
      "cwd": "/path/to/cycloid-mcp-server"
    }
  }
}
```

## Production Environment (Docker)

For production, use the Docker container. **Note**: Environment variables are passed using the `env` block and referenced in the command:

```json
{
  "mcpServers": {
    "Cycloid MCP Server (Prod)": {
      "command": "docker run --rm -i -e CY_ORG -e CY_API_KEY -e CY_API_URL -e CY_CLI_PATH cycloid-mcp-server:latest",
      "env": {
        "CY_ORG": "your-organization",
        "CY_API_KEY": "your-api-key-here",
        "CY_API_URL": "https://http-api.cycloid.io",
        "CY_CLI_PATH": "/usr/local/bin/cy"
      }
    }
  }
}
```

## Configuration Parameters

### Required Environment Variables

- `CY_ORG`: Your Cycloid organization canonical name
- `CY_API_KEY`: Your Cycloid API key
- `CY_API_URL`: Cycloid API URL (default: `https://http-api.cycloid.io`)

### Optional Environment Variables

- `PYTHONPATH`: Python path for development (set automatically)
- `PYTHONUNBUFFERED`: Set to "1" for unbuffered output (recommended)
- `CY_CLI_PATH`: Path to the Cycloid CLI binary (default: `/usr/local/bin/cy`)

## Setup Instructions

### Development Setup

1. Clone the repository
2. Run `make setup` to create the virtual environment
3. Update the MCP configuration with your paths and credentials
4. Restart your MCP client (Cursor, etc.)

### Production Setup

1. Build the Docker image: `make build`
2. Update the MCP configuration with your credentials
3. Restart your MCP client

## Available Tools

The server provides the following MCP tools:

- `list_blueprints`: List all available blueprints
- `create_stack_from_blueprint_smart`: Create stacks with interactive elicitation
- `validate_stackforms`: Validate StackForms configuration files
- `list_catalog_repositories`: List service catalog repositories

## Available Resources

- `cycloid://blueprints`: Access to blueprint information
- `cycloid://service-catalogs-repositories`: Access to service catalog repositories information

## Troubleshooting

### Docker Environment Variables Not Working

If you see errors like `KeyError: 'CY_ORG'` when using Docker, ensure you're using the correct format with environment variables in the `env` block and referenced in the command:

```json
{
  "command": "docker run --rm -i -e CY_ORG -e CY_API_KEY -e CY_API_URL -e CY_CLI_PATH cycloid-mcp-server:latest",
  "env": {
    "CY_ORG": "your-organization",
    "CY_API_KEY": "your-api-key",
    "CY_API_URL": "https://http-api.cycloid.io",
    "CY_CLI_PATH": "/usr/local/bin/cy"
  }
}
```

**Use the `"env"` block for Docker** - the environment variables are referenced in the command using `-e` flags.

### Testing Docker Configuration

You can test your Docker configuration directly:

```bash
docker run --rm -i \
  -e CY_ORG=your-organization \
  -e CY_API_KEY=your-api-key \
  -e CY_API_URL=https://http-api.cycloid.io \
  -e CY_CLI_PATH=/usr/local/bin/cy \
  cycloid-mcp-server:latest
```

### Common Issues

1. **"No module named 'structlog'"**: Ensure you're using the `--with` flags in development
2. **"Tool already exists"**: This is normal during development - tools are registered multiple times
3. **"0 tools" in client**: Check that the server is starting correctly and environment variables are set
4. **"No such file or directory: 'cy'"**: Set `CY_CLI_PATH` to the correct path where the Cycloid CLI is installed (e.g., `/usr/local/bin/cy`)

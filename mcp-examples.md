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
      "command": "docker",
      "args": [
        "run",
        "-i",
        "--rm",
        "-e",
        "CY_ORG",
        "-e",
        "CY_API_KEY",
        "cycloid/cycloid-mcp-server:latest"
      ],
      "env": {
        "CY_ORG": "your-organization",
        "CY_API_KEY": "your-api-key-here",
      }
    }
  }
}
```

## HTTP Transport

The HTTP transport allows you to run the MCP server as a web service, with organization and API key provided via HTTP headers for each request.

For production with HTTP transport:

```json
{
  "mcpServers": {
    "Cycloid HTTP MCP Server (Prod)": {
      "url": "http://mcp.cycloid.io/mcp/",
      "headers": {
        "X-CY-API-KEY": "your-organization",
        "X-CY-ORG": "your-api-key-here",
      }
    }
  }
}
```

## Configuration Parameters

### STDIO Transport (Default)

#### Required Environment Variables

- `CY_ORG`: Your Cycloid organization canonical name
- `CY_API_KEY`: Your Cycloid API key
- `CY_API_URL`: Cycloid API URL (default: `https://http-api.cycloid.io`)

#### Optional Environment Variables

- `PYTHONPATH`: Python path for development (set automatically)
- `PYTHONUNBUFFERED`: Set to "1" for unbuffered output (recommended)
- `CY_CLI_PATH`: Path to the Cycloid CLI binary (default: `/usr/local/bin/cy`)

### HTTP Transport

#### Required Environment Variables

- `TRANSPORT`: Set to `http` to enable HTTP transport (default: `stdio`)
- `CY_HTTP_CLI_PATH` or `CY_CLI_PATH`: Path to the Cycloid CLI binary (default: `/usr/local/bin/cy`)
- `CY_HTTP_API_URL` or `CY_API_URL`: Cycloid API URL (default: `https://http-api.cycloid.io`)

#### Optional Environment Variables

- `CY_HTTP_HOST`: Host to bind the HTTP server (default: `0.0.0.0`)
- `CY_HTTP_PORT`: Port to bind the HTTP server (default: `8000`)

#### Required Headers (per request)

- `X-CY-ORG`: Your Cycloid organization canonical name
- `X-CY-API-KEY`: Your Cycloid API key

## Setup Instructions

### Development Setup

1. Clone the repository
2. Run `make setup` to create the virtual environment
3. Update the MCP configuration with your paths and credentials
4. Restart your MCP client (Cursor, etc.)

### Production Setup

1. Pull the Docker image: `docker pull cycloid/cycloid-mcp-server:latest`
2. Update the MCP configuration with your credentials
3. Restart your MCP client

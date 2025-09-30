# MCP Configuration Examples

This document provides examples of how to configure the Cycloid MCP Server for different environments.

## Development Environment (Python Virtual Environment)

For development, use the Python virtual environment with `uv`:
```bash
uv run python server.py --host 127.0.0.1 --port 8000
```
And then configure your local MCP server
```json
{
  "mcpServers": {
    "Cycloid HTTP MCP Server (Dev)": {
      "url": "http://127.0.0.1:8000/mcp/",
      "headers": {
        "X-CY-API-KEY": "your-organization",
        "X-CY-ORG": "your-api-key-here",
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
      "url": "https://mcp.cycloid.io/mcp/",
      "headers": {
        "X-CY-API-KEY": "your-organization",
        "X-CY-ORG": "your-api-key-here",
      }
    }
  }
}
```

## Configuration Parameters
### HTTP Transport

#### Optional Environment Variables

- `CY_HTTP_CLI_PATH` or `CY_CLI_PATH`: Path to the Cycloid CLI binary (default: `/usr/local/bin/cy`)
- `CY_HTTP_API_URL` or `CY_API_URL`: Cycloid API URL (default: `https://http-api.cycloid.io`)
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

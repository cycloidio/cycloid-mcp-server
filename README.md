# Cycloid MCP Server

A Model Context Protocol (MCP) server for Cycloid platform integration, providing tools for managing service catalogs and stack creation workflows.

## Features

### 🔧 Tools

#### Service Catalog Management
- **`cycloid_catalog_repository_list`** - List all available service catalog repositories
  - Optional filtering by name, canonical, or description
  - Multiple output formats (table, JSON)
  - Repository metadata including canonical names, URLs, and stack counts

#### Stack Creation Workflow
- **`cycloid_stack_create_from_blueprint`** - Guided workflow for creating stacks from blueprints
  - Step-by-step guided experience
  - Blueprint selection with examples
  - Use case selection (AWS, Azure, GCP, vanilla)
  - Service catalog repository selection
  - Confirmation workflow

## Installation

### Prerequisites

- Docker (for containerized deployment)
- Valid Cycloid API credentials

**Note**: The Cycloid CLI is automatically installed in Docker containers - no manual installation required!

### Quick Setup

```bash
# Clone the repository
git clone <repository-url>
cd cycloid-mcp-server

# Setup everything with one command
make setup

# Or manually:
make setup-env      # Create .env file
make docker-build   # Build Docker image
make setup-cursor   # Configure Cursor MCP
# Restart Cursor
```

### Docker Setup

#### Development Environment

```bash
# Build development image
make docker-build

# Run with auto-reload (source code mounted)
make dev

# Or use docker-compose for development
make docker-dev
```

#### Production Environment

```bash
# Build production image
make docker-prod

# Run production container
make prod
```

## Configuration

### Environment Variables

The server requires the following environment variables:

```bash
export CY_ORG="your-organization"
export CY_API_KEY="your-api-key"
export CY_API_URL="https://api.cycloid.io"  # Optional, defaults to this value
```

**Note**: `CY_CLI_PATH` is automatically set in Docker containers to `/usr/local/bin/cy`.

### MCP Configuration

#### Docker-based (Recommended)

```json
{
  "mcpServers": {
    "cycloid": {
      "command": "docker",
      "args": [
        "run",
        "--rm",
        "-i",
        "--env-file", "/path/to/your/.env",
        "cycloid-mcp-server:dev"
      ]
    }
  }
}
```

## Usage

### Running the Server

#### Docker (Recommended)

```bash
# Development with auto-reload
make dev

# Production
make prod

# Using docker-compose
make docker-dev
```

#### Local Development (Optional)

```bash
# Using uv (if you prefer local development)
uv sync
uv run python server.py

# Or using the entry point
uv run cycloid-mcp-server
```

### Using Tools

#### List Service Catalog Repositories

```bash
# List all repositories
cycloid_catalog_repository_list

# Filter repositories
cycloid_catalog_repository_list filter="terraform"

# Get JSON output
cycloid_catalog_repository_list format="json"
```

This returns structured data including:
- Raw repository information in JSON format
- Formatted table for easy reading
- Repository metadata and statistics

#### Create Stack from Blueprint

```bash
# Start the guided workflow
cycloid_stack_create_from_blueprint

# Or provide all parameters
cycloid_stack_create_from_blueprint \
  blueprint_ref="cycloid-io:terraform-sample" \
  name="my-stack" \
  use_case="aws" \
  service_catalog_source_canonical="cycloid-stacks" \
  confirm="true"
```

This provides a comprehensive guide for:
- Selecting blueprints from available repositories
- Choosing use cases (AWS, Azure, GCP, vanilla)
- Providing stack details and configuration
- Confirming stack creation

## Architecture

The server follows MCP best practices:

### Tools
- **Data Access**: Service catalog repositories are exposed as tools
- **Structured Data**: Both raw JSON and formatted output available
- **Guided Workflows**: Step-by-step assistance for complex operations
- **Interactive Experience**: Natural language guidance through workflows

## Development

### Project Structure

```
cycloid-mcp-server/
├── src/
│   ├── handlers/
│   │   ├── catalog_handler.py    # Service catalog operations
│   │   └── stack_handler.py      # Stack creation workflows
│   ├── cli_mixin.py              # CLI execution utilities
│   ├── config.py                 # Configuration management
│   └── exceptions.py             # Custom exceptions
├── scripts/
│   └── install_cli.sh            # CLI installation script
├── server.py                     # FastMCP server entry point
├── Dockerfile                    # Production Docker image
├── Dockerfile.dev                # Development Docker image
├── docker-compose.yml            # Production compose
├── docker-compose.dev.yml        # Development compose
├── mcp.json                      # MCP configuration
└── README.md                     # This file
```

### Testing

```bash
# Run tests
make test

# Test the server
make test-server

# Run linting
make lint

# Format code
make format
```

### Docker Commands

```bash
# Development
make docker-build    # Build development image
make docker-dev      # Run with docker-compose
make dev             # Quick development run

# Production
make docker-prod     # Build production image
make prod            # Run production container

# Cleanup
make docker-clean    # Clean Docker resources
```

### Local Development (Optional)

If you prefer local development without Docker:

```bash
# Install dependencies
make install

# Run tests
make test

# Format code
make format

# Run server locally
uv run python server.py
```

## CLI Installation

The Cycloid CLI is automatically installed in Docker containers using the `scripts/install_cli.sh` script:

1. **Local Binary Priority**: First checks for local binaries in `/app/bin/`
2. **Fallback Download**: Downloads the official binary if no local version is found
3. **Automatic Setup**: Sets `CY_CLI_PATH` environment variable
4. **Version Verification**: Displays installed version for confirmation

## Error Handling

The server provides comprehensive error handling:

- **Configuration Errors**: Clear messages for missing environment variables
- **CLI Errors**: Detailed error reporting for Cycloid CLI failures
- **API Errors**: Proper handling of Cycloid API authentication and request errors
- **Validation Errors**: Input validation with helpful error messages

## Logging

The server uses structured logging with `structlog`:

- **JSON Format**: Machine-readable log output
- **Contextual Information**: Request details and error context
- **Configurable Levels**: Adjustable logging verbosity

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

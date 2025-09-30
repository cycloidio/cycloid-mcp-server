# Cycloid MCP Server

[![PR Quality Check](https://github.com/cycloidio/cycloid-mcp-server/workflows/PR%20Quality%20Check/badge.svg)](https://github.com/cycloidio/cycloid-mcp-server/actions/workflows/pr-quality-check.yml)

A Model Context Protocol (MCP) server that provides seamless integration with the Cycloid platform, enabling AI assistants to interact with Cycloid's infrastructure management capabilities through natural language.

## Overview

The Cycloid MCP Server bridges the gap between AI assistants and Cycloid's powerful infrastructure automation platform. It enables users to:

- **Discover and explore** available blueprints and service catalogs
- **Create and manage** infrastructure stacks using Cycloid's blueprints
- **Interact naturally** with complex infrastructure workflows through AI assistants
- **Leverage Cycloid's expertise** in infrastructure as code and automation


## Available Tools

- **`CYCLOID_BLUEPRINT_LIST`**: List all available blueprints with their details
- **`CYCLOID_BLUEPRINT_STACK_CREATE`**: Create stacks from blueprints with interactive elicitation
- **`CYCLOID_STACKFORMS_VALIDATE`**: Validate StackForms configuration files
- **`CYCLOID_CATALOG_REPO_LIST`**: List service catalog repositories
- **`CYCLOID_EVENT_LIST`**: List organization events with optional filters (`begin`, `end`, `severity`, `type`)
- **`CYCLOID_PIPELINE_LIST`**: List all pipelines from Cycloid

## Available Resources

- **`cycloid://blueprints`**: Access to blueprint information
- **`cycloid://service-catalogs-repositories`**: Access to service catalog repositories information
- **`cycloid://events`**: Access to recent organization events as JSON
- **`cycloid://pipelines`**: Access to pipeline information

### Event Filters
- **begin/end**: Unix timestamps (strings) delimiting the time window
- **severity**: One or more of `info`, `warn`, `err`, `crit`
- **type**: One or more of `Cycloid`, `AWS`, `Monitoring`, `Custom`

## Architecture

The server uses a dynamic component registration system based on FastMCP's MCPMixin:

- **Automatic Discovery**: Components are automatically discovered from `src/components/`
- **File-based Organization**: Components are organized by feature (`catalogs/`, `stacks/`)
- **Standard Patterns**: Each component follows the pattern `*_tools.py`, `*_resources.py`, `*_handlers.py`, `*_prompts.py`
- **MCPMixin Integration**: Uses FastMCP's built-in `register_all()` method for proper tool/resource registration

## HTTP Transport

The Cycloid MCP Server runs as a web service using HTTP transport. Organization and API key are provided via HTTP headers (`X-CY-ORG` and `X-CY-API-KEY`) for each request, enabling multi-tenant usage.

**Usage:** `python server.py`

## Quick Start

### Prerequisites

- Python 3.12 or higher
- [uv](https://github.com/astral-sh/uv) package manager (recommended)
- Docker (for production deployment)
- Valid Cycloid API credentials

### Development Setup

```bash
# Clone and setup
git clone <repository-url>
cd cycloid-mcp-server
make setup

# Run development server
make dev-server
```

### Production Setup

#### Using Pre-built Docker Images

The project provides pre-built Docker images via Docker Hub:

```bash
# Pull the latest image
docker pull cycloid/cycloid-mcp-server:latest

# Run the server
docker run -p 8000:8000 cycloid/cycloid-mcp-server:latest
```

#### Building Locally

```bash
# Build Docker image
make build

# Run production server
make prod-server
```

## MCP Configuration

For detailed MCP server configuration examples, see [mcp-examples.md](mcp-examples.md).

## Available Commands

```bash
# Development Environment
make setup          # Setup development environment with uv
make install        # Install dependencies
make help           # Show all available commands
make validate-env   # Validate local environment matches CI

# Development Server
make dev-server     # Run development server using Python virtual environment

# HTTP Server
python server.py  # Run HTTP server

# Production
make build          # Build Docker image
make prod-server    # Run production server using Docker

# Testing and Quality
make test           # Run all tests
make type-check     # Run pyright type checking
make lint           # Run PEP 8 linting with flake8
make format         # Format code with black and isort
make quality-check  # Run all quality checks (tests + type checking + linting)
make simulate-ci    # Validate environment and run quality checks

# Cleanup
make clean          # Clean up development artifacts
make clean-docker   # Clean up Docker artifacts
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed development guidelines.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

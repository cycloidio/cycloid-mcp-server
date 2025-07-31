#!/usr/bin/env python3
"""
MCP Server entry point for Cycloid integration.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from mcp.server.fastmcp import FastMCP
from src.handlers import CatalogHandler, StackHandler

# Create FastMCP server
mcp = FastMCP("cycloid-mcp-server")

# Create handlers
catalog_handler = CatalogHandler()
stack_handler = StackHandler()

# Register tools
@mcp.tool()
async def cycloid_catalog_repository_list(filter: str = "", format: str = "table") -> str:
    """List all available service catalog repositories with optional filtering and formatting options.
    
    This tool provides access to service catalog repositories as structured data.
    You can use this to explore available repositories for stack creation.
    """
    try:
        # Get repositories from CLI with correct command
        repositories_data = await catalog_handler.execute_cli_json(
            "catalog-repository", ["list"]
        )
        
        repositories = repositories_data.get("service_catalog_repositories", [])
        
        # Apply filter if provided
        if filter:
            filter_lower = filter.lower()
            filtered_repositories = []
            for repo in repositories:
                if (
                    filter_lower in repo.get("canonical", "").lower()
                    or filter_lower in repo.get("name", "").lower()
                    or filter_lower in repo.get("description", "").lower()
                ):
                    filtered_repositories.append(repo)
            repositories = filtered_repositories
        
        # Format output based on requested format
        if format == "json":
            import json
            result = {
                "service_catalog_repositories": repositories,
                "count": len(repositories),
            }
            if filter:
                result["filter"] = filter
            return json.dumps(result, indent=2)
        else:
            return catalog_handler._format_table_output(repositories, filter)
            
    except Exception as e:
        return f"❌ Error listing catalog repositories: {str(e)}"

@mcp.tool()
async def cycloid_stack_create_from_blueprint(
    blueprint_ref: str = "",
    name: str = "",
    use_case: str = "",
    service_catalog_source_canonical: str = "",
    confirm: str = ""
) -> str:
    """Create a new Cycloid Terraform stack from a blueprint using a guided workflow.
    
    This tool provides a guided workflow for creating stacks from blueprints.
    It will help you through each step of the process.
    """
    return await stack_handler.execute_stack_creation(
        blueprint_ref=blueprint_ref,
        name=name,
        use_case=use_case,
        service_catalog_source_canonical=service_catalog_source_canonical,
        confirm=confirm
    )

# Export for MCP CLI
if __name__ == "__main__":
    mcp.run(transport='stdio') 
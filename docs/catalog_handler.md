# Catalog Handler

This document describes the catalog handler that manages service catalog repository operations in the Cycloid MCP server.

## Overview

The `CatalogHandler` is responsible for managing service catalog repositories, providing tools and resources to list, filter, and access catalog information. This handler is separate from the stack handler to maintain proper domain separation.

## Tools

### cycloid_catalog_repository_list

Lists all available service catalog repositories with optional filtering and formatting options.

**Parameters:**
- `filter` (optional): Filter repositories by name, canonical, or description
- `format` (optional): Output format - "json" or "table" (default: "table")

**Usage Examples:**

```bash
# List all repositories in table format
cycloid_catalog_repository_list

# List repositories in JSON format
cycloid_catalog_repository_list --format "json"

# Filter repositories containing "terraform"
cycloid_catalog_repository_list --filter "terraform"

# Filter and output as JSON
cycloid_catalog_repository_list --filter "demo" --format "json"
```

**Output Formats:**

**Table Format:**
```
📚 Service Catalog Repositories

Found 23 service catalog repositories

| Canonical | Name | URL | Branch | Stack Count |
|-----------|------|-----|--------|-------------|
| cycloid-stacks | cycloid-stacks | git@github.com:cycloidio/cycloid-stacks.git | stacks | 29 |
| cycloid-demo-stacks | Cycloid Demo Stacks | git@github.com:cycloidio/cycloid-demo-stacks.git | master | 15 |

Total repositories: 23

💡 Popular choices:
• cycloid-stacks - Main Cycloid stacks repository
• cycloid-demo-stacks - Demo stacks repository
• stack-getting-started - Getting started examples
• terraform-runner - Terraform automation templates

💡 Tip: Use format: json parameter to get the complete list in JSON format.
```

**JSON Format:**
```json
{
  "service_catalog_repositories": [
    {
      "canonical": "cycloid-stacks",
      "name": "cycloid-stacks",
      "url": "git@github.com:cycloidio/cycloid-stacks.git",
      "branch": "stacks",
      "stack_count": "29"
    }
  ],
  "count": 23,
  "filter": "terraform"
}
```

## Resources

### cycloid://service-catalogs

Provides access to service catalog repositories as a resource, returning data in JSON format with both raw data and formatted table.

**Usage:**
```
cycloid://service-catalogs
```

**Response Format:**
```json
{
  "service_catalog_repositories": [...],
  "count": 23,
  "formatted_table": "# Service Catalog Repositories\n\n| Canonical | Name | URL | Branch | Stack Count |\n..."
}
```

## Features

### Filtering
- Search by repository canonical name
- Search by repository display name
- Search by repository description
- Case-insensitive matching

### Popular Choices
The handler highlights popular service catalog repositories:
- `cycloid-stacks-test` - Main Cycloid stacks repository for creating test stacks
- `cycloid-demo-stacks` - Demo stacks repository
- `stack-getting-started` - Getting started examples

### Error Handling
- Graceful handling of missing Cycloid CLI configuration
- Clear setup instructions when configuration is required
- Proper error messages for API failures

## Configuration Requirements

Before using catalog operations, ensure you have:
- Cycloid CLI installed and configured
- Valid API credentials set up
- Proper organization access

**Required Environment Variables:**
```bash
export CY_ORG="your-organization"
export CY_API_KEY="your-api-key"
# Optional: export CY_API_URL="https://api.cycloid.io"
```

## Integration with Stack Creation

The catalog handler works seamlessly with the stack creation workflow:
- Stack creation workflow can reference the `cycloid://service-catalogs` resource
- Users can use `cycloid_catalog_repository_list` to explore available repositories
- Popular choices are highlighted to help users make informed decisions

## Best Practices

1. **Use the tool for exploration**: Use `cycloid_catalog_repository_list` to explore available repositories
2. **Use the resource for programmatic access**: Use `cycloid://service-catalogs` when you need structured data
3. **Filter when needed**: Use the filter parameter to narrow down results
4. **Choose appropriate format**: Use table format for human reading, JSON for programmatic use 
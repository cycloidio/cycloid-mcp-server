"""Tests for CatalogComponent using FastMCP Client pattern."""

import json
from typing import Any
from unittest.mock import patch

import pytest
from fastmcp import Client, FastMCP

from src.cli_mixin import CLIMixin
from src.components.catalogs import CatalogResources, CatalogTools


@pytest.fixture
def catalog_server():
    """Create a test MCP server with catalog components."""
    server = FastMCP("TestCatalogServer")

    # Initialize CLI mixin
    cli = CLIMixin()

    # Create and register catalog components
    catalog_tools = CatalogTools(cli)
    catalog_resources = CatalogResources(cli)

    catalog_tools.register_all(server)
    catalog_resources.register_all(server)

    return server


class TestCatalogComponent:
    """Test catalog component functionality."""

    @patch("src.cli_mixin.CLIMixin.execute_cli_json")
    async def test_list_catalog_repositories_table(
        self, mock_execute_cli_json: Any, catalog_server: FastMCP
    ):
        """Test catalog repository listing in table format."""
        # Mock the CLI response
        mock_execute_cli_json.return_value = [
            {
                "canonical": "test-repo",
                "branch": "main",
                "url": "https://github.com/test/repo",
                "stack_count": 5,
            }
        ]

        async with Client(catalog_server) as client:
            result = await client.call_tool(
                "CYCLOID_CATALOG_REPO_LIST", {"format": "table"}
            )

            # Extract the actual text content
            result_text: str = (
                result.content[0].text if hasattr(result, "content") else str(result)
            )  # type: ignore[reportUnknownMemberType, reportAttributeAccessIssue]

            assert "test-repo" in result_text
            assert "main" in result_text
            assert "https://github.com/test/repo" in result_text
            assert "5" in result_text

    @patch("src.cli_mixin.CLIMixin.execute_cli_json")
    async def test_list_catalog_repositories_json(
        self, mock_execute_cli_json: Any, catalog_server: FastMCP
    ):
        """Test catalog repository listing in JSON format."""
        # Mock the CLI response
        mock_execute_cli_json.return_value = [
            {
                "canonical": "test-repo",
                "branch": "main",
                "url": "https://github.com/test/repo",
                "stack_count": 5,
            }
        ]

        async with Client(catalog_server) as client:
            result = await client.call_tool(
                "CYCLOID_CATALOG_REPO_LIST", {"format": "json"}
            )

            # Extract the actual text content
            result_text: str = (
                result.content[0].text if hasattr(result, "content")
                else str(result)
            )  # type: ignore[reportUnknownMemberType, reportAttributeAccessIssue]
            data = json.loads(str(result_text))

            assert "repositories" in data
            assert "count" in data
            assert data["count"] == 1
            assert data["repositories"][0]["canonical"] == "test-repo"

    @patch("src.cli_mixin.CLIMixin.execute_cli_json")
    async def test_get_service_catalogs_resource(
        self, mock_execute_cli_json: Any, catalog_server: FastMCP
    ):
        """Test service catalogs resource."""
        # Mock the CLI response
        mock_execute_cli_json.return_value = [
            {
                "canonical": "test-repo",
                "branch": "main",
                "url": "https://github.com/test/repo",
                "stack_count": 5,
            }
        ]

        async with Client(catalog_server) as client:
            result = await client.read_resource(
                "cycloid://service-catalogs-repositories"
            )

            # Handle different response formats from FastMCP Client
            if hasattr(result, "content") and result.content:
                # List of content items
                text_content: str = result.content[0].text
            elif hasattr(result, "__iter__") and len(result) > 0:
                # Direct list response
                text_content: str = result[0].text
            else:
                # Direct text response
                text_content: str = str(result)

            data = json.loads(str(text_content))  # type: ignore[reportUnknownArgumentType]
            assert "repositories" in data
            assert "count" in data
            assert "formatted_table" in data
            assert data["count"] == 1

    async def test_catalog_tools_registered(self, catalog_server: FastMCP):
        """Test that catalog tools are properly registered."""
        async with Client(catalog_server) as client:
            tools = await client.list_tools()
            tool_names = [tool.name for tool in tools]
            assert "CYCLOID_CATALOG_REPO_LIST" in tool_names

    async def test_catalog_resources_registered(self, catalog_server: FastMCP):
        """Test that catalog resources are properly registered."""
        async with Client(catalog_server) as client:
            resources = await client.list_resources()
            # Convert AnyUrl objects to strings for comparison
            resource_uris = [str(resource.uri) for resource in resources]
            assert "cycloid://service-catalogs-repositories" in resource_uris

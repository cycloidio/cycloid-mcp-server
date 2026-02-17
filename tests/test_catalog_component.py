"""Tests for Catalog component using FastMCP Client pattern."""

import json
from typing import List
from unittest.mock import MagicMock, patch

import pytest
from fastmcp import Client, FastMCP

from src.components.catalogs import (
    get_service_catalogs_resource,
    list_catalog_repositories,
)


@pytest.fixture
def catalog_server() -> FastMCP:
    """Create a test MCP server with catalog components."""
    server: FastMCP = FastMCP("TestCatalogServer")
    server.add_tool(list_catalog_repositories)
    server.add_resource(get_service_catalogs_resource)
    return server


class TestCatalogComponent:
    """Test catalog component functionality."""

    @patch("src.cli.CLIMixin.execute_cli")
    async def test_list_catalog_repositories_json(
        self, mock_execute_cli: MagicMock, catalog_server: FastMCP
    ) -> None:
        """Test catalog repository listing returns JSON dict."""
        mock_execute_cli.return_value = [
            {
                "canonical": "test-repo",
                "branch": "main",
                "url": "https://github.com/test/repo",
                "stack_count": 5,
            }
        ]

        async with Client(catalog_server) as client:
            result = await client.call_tool("CYCLOID_CATALOG_REPO_LIST", {})

            result_text: str = (
                result.content[0].text if hasattr(result, "content") else str(result)
            )  # type: ignore[reportUnknownMemberType, reportAttributeAccessIssue]
            data = json.loads(str(result_text))

            assert "repositories" in data
            assert "count" in data
            assert data["count"] == 1
            assert data["repositories"][0]["canonical"] == "test-repo"
            assert "_display_hints" in data
            assert data["_display_hints"]["display_format"] == "table"
            assert "key_fields" in data["_display_hints"]

    @patch("src.cli.CLIMixin.execute_cli")
    async def test_get_service_catalogs_resource(
        self, mock_execute_cli: MagicMock, catalog_server: FastMCP
    ) -> None:
        """Test service catalogs resource."""
        mock_execute_cli.return_value = [
            {
                "canonical": "test-repo",
                "branch": "main",
                "url": "https://github.com/test/repo",
                "stack_count": 5,
            }
        ]

        async with Client(catalog_server) as client:
            result = await client.read_resource("cycloid://service-catalogs-repositories")

            if hasattr(result, "content") and result.content:
                text_content: str = result.content[0].text
            elif hasattr(result, "__iter__") and len(result) > 0:
                text_content: str = result[0].text
            else:
                text_content: str = str(result)

            data = json.loads(str(text_content))  # type: ignore[reportUnknownArgumentType]
            assert "repositories" in data
            assert "count" in data
            assert data["count"] == 1
            # No more formatted_table key
            assert "formatted_table" not in data

    async def test_catalog_tools_registered(self, catalog_server: FastMCP) -> None:
        """Test that catalog tools are properly registered."""
        async with Client(catalog_server) as client:
            tools = await client.list_tools()
            tool_names: List[str] = [tool.name for tool in tools]
            assert "CYCLOID_CATALOG_REPO_LIST" in tool_names

    async def test_catalog_resources_registered(self, catalog_server: FastMCP) -> None:
        """Test that catalog resources are properly registered."""
        async with Client(catalog_server) as client:
            resources = await client.list_resources()
            resource_uris: List[str] = [str(resource.uri) for resource in resources]
            assert "cycloid://service-catalogs-repositories" in resource_uris

"""Tests for Component (cy components) using FastMCP Client pattern."""

import json
from typing import Any, Dict, List
from unittest.mock import MagicMock, patch

import pytest
from fastmcp import Client, FastMCP

from src.components.components import get_components, list_components


@pytest.fixture
def component_server() -> FastMCP:
    """Create a test MCP server with component tools."""
    server: FastMCP = FastMCP("TestComponentServer")
    server.add_tool(list_components)
    server.add_tool(get_components)
    return server


@pytest.fixture
def sample_components_data() -> List[Dict[str, Any]]:
    """Sample component data for testing."""
    return [
        {
            "name": "Web App",
            "canonical": "web-app",
            "status": "running",
            "service_catalog_ref": "my-catalog:web-stack",
        },
        {
            "name": "Database",
            "canonical": "database",
            "status": "running",
            "service_catalog_ref": "my-catalog:postgres-stack",
        },
    ]


class TestComponentComponent:
    """Test components (cy components) tool functionality."""

    @patch("src.cli.CLIMixin.execute_cli")
    async def test_list_components_json(
        self,
        mock_execute_cli: MagicMock,
        component_server: FastMCP,
        sample_components_data: List[Dict[str, Any]],
    ) -> None:
        """Test component listing returns JSON dict."""
        mock_execute_cli.return_value = sample_components_data

        async with Client(component_server) as client:
            result = await client.call_tool(
                "CYCLOID_COMPONENT_LIST",
                {"project": "demo-project", "env": "prod"},
            )

            result_text: str = (
                result.content[0].text if hasattr(result, "content") else str(result)
            )
            data = json.loads(result_text)

            assert "components" in data
            assert data["count"] == 2
            assert data["components"][0]["canonical"] == "web-app"
            assert "_display_hints" in data
            assert data["_display_hints"]["display_format"] == "table"

    @patch("src.cli.CLIMixin.execute_cli")
    async def test_list_components_empty(
        self, mock_execute_cli: MagicMock, component_server: FastMCP
    ) -> None:
        """Test component listing with empty result."""
        mock_execute_cli.return_value = []

        async with Client(component_server) as client:
            result = await client.call_tool(
                "CYCLOID_COMPONENT_LIST",
                {"project": "demo-project", "env": "prod"},
            )

            result_text: str = (
                result.content[0].text if hasattr(result, "content") else str(result)
            )
            data = json.loads(result_text)

            assert data["count"] == 0
            assert data["components"] == []

    async def test_list_components_missing_project_raises(
        self, component_server: FastMCP
    ) -> None:
        """Test that missing project canonical raises an error."""
        async with Client(component_server) as client:
            with pytest.raises(Exception):
                await client.call_tool(
                    "CYCLOID_COMPONENT_LIST", {"project": "", "env": "prod"}
                )

    async def test_list_components_missing_env_raises(
        self, component_server: FastMCP
    ) -> None:
        """Test that missing env canonical raises an error."""
        async with Client(component_server) as client:
            with pytest.raises(Exception):
                await client.call_tool(
                    "CYCLOID_COMPONENT_LIST",
                    {"project": "demo-project", "env": ""},
                )

    @patch("src.cli.CLIMixin.execute_cli")
    async def test_get_components_multiple(
        self,
        mock_execute_cli: MagicMock,
        component_server: FastMCP,
        sample_components_data: List[Dict[str, Any]],
    ) -> None:
        """Test getting multiple components."""
        mock_execute_cli.return_value = sample_components_data

        async with Client(component_server) as client:
            result = await client.call_tool(
                "CYCLOID_COMPONENT_GET",
                {
                    "project": "demo-project",
                    "env": "prod",
                    "canonicals": ["web-app", "database"],
                },
            )

            result_text: str = (
                result.content[0].text if hasattr(result, "content") else str(result)
            )
            data = json.loads(result_text)

            assert data["count"] == 2
            assert data["components"][0]["canonical"] == "web-app"

    @patch("src.cli.CLIMixin.execute_cli")
    async def test_get_components_single_returns_dict(
        self,
        mock_execute_cli: MagicMock,
        component_server: FastMCP,
        sample_components_data: List[Dict[str, Any]],
    ) -> None:
        """Test getting a single component where CLI may return a dict."""
        mock_execute_cli.return_value = sample_components_data[0]

        async with Client(component_server) as client:
            result = await client.call_tool(
                "CYCLOID_COMPONENT_GET",
                {
                    "project": "demo-project",
                    "env": "prod",
                    "canonicals": ["web-app"],
                },
            )

            result_text: str = (
                result.content[0].text if hasattr(result, "content") else str(result)
            )
            data = json.loads(result_text)

            assert data["count"] == 1
            assert data["components"][0]["canonical"] == "web-app"

    async def test_get_components_empty_canonicals_raises(
        self, component_server: FastMCP
    ) -> None:
        """Test that empty canonicals list raises an error."""
        async with Client(component_server) as client:
            with pytest.raises(Exception):
                await client.call_tool(
                    "CYCLOID_COMPONENT_GET",
                    {
                        "project": "demo-project",
                        "env": "prod",
                        "canonicals": [],
                    },
                )

    async def test_component_tools_registered(self, component_server: FastMCP) -> None:
        """Test that component tools are registered."""
        async with Client(component_server) as client:
            tools = await client.list_tools()
            tool_names: List[str] = [tool.name for tool in tools]
            assert "CYCLOID_COMPONENT_LIST" in tool_names
            assert "CYCLOID_COMPONENT_GET" in tool_names

"""Tests for Project component using FastMCP Client pattern."""

import json
from typing import Any, Dict, List
from unittest.mock import MagicMock, patch

import pytest
from fastmcp import Client, FastMCP

from src.components.projects import (
    get_projects,
    get_projects_resource,
    list_project_envs,
    list_projects,
)


@pytest.fixture
def project_server() -> FastMCP:
    """Create a test MCP server with project components."""
    server: FastMCP = FastMCP("TestProjectServer")
    server.add_tool(list_projects)
    server.add_tool(get_projects)
    server.add_tool(list_project_envs)
    server.add_resource(get_projects_resource)
    return server


@pytest.fixture
def sample_projects_data() -> List[Dict[str, Any]]:
    """Sample project data for testing."""
    return [
        {
            "name": "Demo Project",
            "canonical": "demo-project",
            "description": "A demo project",
            "owner": {"username": "alice"},
        },
        {
            "name": "Other Project",
            "canonical": "other-project",
            "description": "Another project",
            "owner": {"username": "bob"},
        },
    ]


@pytest.fixture
def sample_envs_data() -> List[Dict[str, Any]]:
    """Sample environment data for testing."""
    return [
        {"canonical": "prod", "color": "red", "icon": "server"},
        {"canonical": "staging", "color": "yellow", "icon": "server"},
    ]


class TestProjectComponent:
    """Test project component functionality."""

    @patch("src.cli.CLIMixin.execute_cli")
    async def test_list_projects_json(
        self,
        mock_execute_cli: MagicMock,
        project_server: FastMCP,
        sample_projects_data: List[Dict[str, Any]],
    ) -> None:
        """Test project listing returns JSON dict."""
        mock_execute_cli.return_value = sample_projects_data

        async with Client(project_server) as client:
            result = await client.call_tool("CYCLOID_PROJECT_LIST", {})

            result_text: str = (
                result.content[0].text if hasattr(result, "content") else str(result)
            )
            data = json.loads(result_text)

            assert "projects" in data
            assert "count" in data
            assert data["count"] == 2
            assert data["projects"][0]["canonical"] == "demo-project"
            assert "_display_hints" in data
            assert data["_display_hints"]["display_format"] == "table"
            assert "key_fields" in data["_display_hints"]

    @patch("src.cli.CLIMixin.execute_cli")
    async def test_list_projects_empty(
        self, mock_execute_cli: MagicMock, project_server: FastMCP
    ) -> None:
        """Test project listing with empty result."""
        mock_execute_cli.return_value = []

        async with Client(project_server) as client:
            result = await client.call_tool("CYCLOID_PROJECT_LIST", {})

            result_text: str = (
                result.content[0].text if hasattr(result, "content") else str(result)
            )
            data = json.loads(result_text)

            assert data["count"] == 0
            assert data["projects"] == []

    @patch("src.cli.CLIMixin.execute_cli")
    async def test_get_projects_multiple(
        self,
        mock_execute_cli: MagicMock,
        project_server: FastMCP,
        sample_projects_data: List[Dict[str, Any]],
    ) -> None:
        """Test getting multiple projects."""
        mock_execute_cli.return_value = sample_projects_data

        async with Client(project_server) as client:
            result = await client.call_tool(
                "CYCLOID_PROJECT_GET",
                {"canonicals": ["demo-project", "other-project"]},
            )

            result_text: str = (
                result.content[0].text if hasattr(result, "content") else str(result)
            )
            data = json.loads(result_text)

            assert data["count"] == 2
            assert data["projects"][0]["canonical"] == "demo-project"

    @patch("src.cli.CLIMixin.execute_cli")
    async def test_get_projects_single_returns_dict(
        self,
        mock_execute_cli: MagicMock,
        project_server: FastMCP,
        sample_projects_data: List[Dict[str, Any]],
    ) -> None:
        """Test getting a single project where CLI may return a dict (not list)."""
        mock_execute_cli.return_value = sample_projects_data[0]

        async with Client(project_server) as client:
            result = await client.call_tool(
                "CYCLOID_PROJECT_GET", {"canonicals": ["demo-project"]}
            )

            result_text: str = (
                result.content[0].text if hasattr(result, "content") else str(result)
            )
            data = json.loads(result_text)

            assert data["count"] == 1
            assert data["projects"][0]["canonical"] == "demo-project"

    async def test_get_projects_empty_canonicals_raises(
        self, project_server: FastMCP
    ) -> None:
        """Test that empty canonicals list raises an error."""
        async with Client(project_server) as client:
            with pytest.raises(Exception):
                await client.call_tool("CYCLOID_PROJECT_GET", {"canonicals": []})

    @patch("src.cli.CLIMixin.execute_cli")
    async def test_list_project_envs_json(
        self,
        mock_execute_cli: MagicMock,
        project_server: FastMCP,
        sample_envs_data: List[Dict[str, Any]],
    ) -> None:
        """Test listing environments for a project."""
        mock_execute_cli.return_value = sample_envs_data

        async with Client(project_server) as client:
            result = await client.call_tool(
                "CYCLOID_PROJECT_LIST_ENV", {"project": "demo-project"}
            )

            result_text: str = (
                result.content[0].text if hasattr(result, "content") else str(result)
            )
            data = json.loads(result_text)

            assert "environments" in data
            assert data["count"] == 2
            assert data["environments"][0]["canonical"] == "prod"
            assert "_display_hints" in data

    async def test_list_project_envs_empty_project_raises(
        self, project_server: FastMCP
    ) -> None:
        """Test that empty project canonical raises an error."""
        async with Client(project_server) as client:
            with pytest.raises(Exception):
                await client.call_tool("CYCLOID_PROJECT_LIST_ENV", {"project": ""})

    @patch("src.cli.CLIMixin.execute_cli")
    async def test_get_projects_resource(
        self,
        mock_execute_cli: MagicMock,
        project_server: FastMCP,
        sample_projects_data: List[Dict[str, Any]],
    ) -> None:
        """Test projects resource retrieval."""
        mock_execute_cli.return_value = sample_projects_data

        async with Client(project_server) as client:
            result = await client.read_resource("cycloid://projects")

            if hasattr(result, "content") and result.content:
                text_content: str = result.content[0].text
            elif hasattr(result, "__iter__") and len(result) > 0:  # type: ignore[arg-type]
                text_content = result[0].text  # type: ignore[index]
            else:
                text_content = str(result)

            data = json.loads(text_content)
            assert "projects" in data
            assert data["count"] == 2

    async def test_project_tools_registered(self, project_server: FastMCP) -> None:
        """Test that project tools are registered."""
        async with Client(project_server) as client:
            tools = await client.list_tools()
            tool_names: List[str] = [tool.name for tool in tools]
            assert "CYCLOID_PROJECT_LIST" in tool_names
            assert "CYCLOID_PROJECT_GET" in tool_names
            assert "CYCLOID_PROJECT_LIST_ENV" in tool_names

    async def test_project_resources_registered(self, project_server: FastMCP) -> None:
        """Test that project resources are registered."""
        async with Client(project_server) as client:
            resources = await client.list_resources()
            resource_uris: List[str] = [str(resource.uri) for resource in resources]
            assert "cycloid://projects" in resource_uris

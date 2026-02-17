"""Tests for Pipeline component functionality."""

import json
from typing import Any, Dict, List
from unittest.mock import MagicMock, patch

import pytest
from fastmcp import Client, FastMCP

from src.components.pipelines import get_pipelines_resource, list_pipelines


@pytest.fixture
def pipeline_server() -> FastMCP:
    """Create a test MCP server with pipeline components."""
    server: FastMCP = FastMCP("TestPipelineServer")
    server.add_tool(list_pipelines)
    server.add_resource(get_pipelines_resource)
    return server


@pytest.fixture
def sample_pipeline_data() -> List[Dict[str, Any]]:
    """Sample pipeline data for testing."""
    return [
        {
            "id": 226,
            "name": "semvertests-staging-be",
            "status": "paused",
            "jobs": [
                {
                    "id": 1290,
                    "name": "build",
                    "finished_build": {"status": "succeeded", "id": 1485},
                },
                {
                    "id": 1294,
                    "name": "deploy",
                    "finished_build": {"status": "errored", "id": 2762},
                },
            ],
            "component": {
                "project": {"name": "SemVerTests", "canonical": "semvertests"},
                "environment": {"name": "staging-be", "canonical": "staging-be"},
            },
        },
        {
            "id": 227,
            "name": "semvertests-staging-fe",
            "status": "paused",
            "jobs": [
                {
                    "id": 1299,
                    "name": "build",
                    "finished_build": {"status": "succeeded", "id": 1488},
                }
            ],
            "component": {
                "project": {"name": "SemVerTests", "canonical": "semvertests"},
                "environment": {"name": "staging-fe", "canonical": "staging-fe"},
            },
        },
    ]


class TestPipelineComponent:
    """Test pipeline component functionality via FastMCP Client."""

    @patch("src.cli.CLIMixin.execute_cli")
    @patch("src.cli.CLIMixin.process_cli_response")
    async def test_list_pipelines_json(
        self,
        mock_process: MagicMock,
        mock_execute_cli: MagicMock,
        pipeline_server: FastMCP,
        sample_pipeline_data: List[Dict[str, Any]],
    ) -> None:
        """Test pipeline listing returns JSON dict."""
        mock_execute_cli.return_value = sample_pipeline_data
        mock_process.return_value = sample_pipeline_data

        async with Client(pipeline_server) as client:
            result = await client.call_tool("CYCLOID_PIPELINE_LIST", {})

            result_text: str = (
                result.content[0].text if hasattr(result, "content") else str(result)
            )
            data = json.loads(result_text)

            assert "pipelines" in data
            assert "count" in data
            assert data["count"] == 2
            assert data["pipelines"][0]["name"] == "semvertests-staging-be"
            assert "_display_hints" in data
            assert data["_display_hints"]["display_format"] == "table"
            assert "key_fields" in data["_display_hints"]

    @patch("src.cli.CLIMixin.execute_cli")
    @patch("src.cli.CLIMixin.process_cli_response")
    async def test_list_pipelines_empty(
        self,
        mock_process: MagicMock,
        mock_execute_cli: MagicMock,
        pipeline_server: FastMCP,
    ) -> None:
        """Test pipeline listing with empty result."""
        mock_execute_cli.return_value = []
        mock_process.return_value = []

        async with Client(pipeline_server) as client:
            result = await client.call_tool("CYCLOID_PIPELINE_LIST", {})

            result_text: str = (
                result.content[0].text if hasattr(result, "content") else str(result)
            )
            data = json.loads(result_text)

            assert data["count"] == 0
            assert data["pipelines"] == []

    async def test_pipeline_tools_registered(self, pipeline_server: FastMCP) -> None:
        """Test that pipeline tools are registered."""
        async with Client(pipeline_server) as client:
            tools = await client.list_tools()
            tool_names: List[str] = [tool.name for tool in tools]
            assert "CYCLOID_PIPELINE_LIST" in tool_names

    async def test_pipeline_resources_registered(self, pipeline_server: FastMCP) -> None:
        """Test that pipeline resources are registered."""
        async with Client(pipeline_server) as client:
            resources = await client.list_resources()
            resource_uris: List[str] = [str(resource.uri) for resource in resources]
            assert "cycloid://pipelines" in resource_uris

    @patch("src.cli.CLIMixin.execute_cli")
    @patch("src.cli.CLIMixin.process_cli_response")
    async def test_get_pipelines_resource(
        self,
        mock_process: MagicMock,
        mock_execute_cli: MagicMock,
        pipeline_server: FastMCP,
        sample_pipeline_data: List[Dict[str, Any]],
    ) -> None:
        """Test pipeline resource retrieval."""
        mock_execute_cli.return_value = sample_pipeline_data
        mock_process.return_value = sample_pipeline_data

        async with Client(pipeline_server) as client:
            result = await client.read_resource("cycloid://pipelines")

            if hasattr(result, "content") and result.content:
                text_content: str = result.content[0].text
            elif hasattr(result, "__iter__") and len(result) > 0:
                text_content = result[0].text  # type: ignore[index]
            else:
                text_content = str(result)

            data = json.loads(text_content)
            assert "pipelines" in data
            assert data["count"] == 2

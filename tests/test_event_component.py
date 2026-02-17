"""Tests for Event component using FastMCP Client pattern."""

import json
from typing import List
from unittest.mock import MagicMock, patch

import pytest
from fastmcp import Client, FastMCP

from src.components.events import get_events_resource, list_events


@pytest.fixture
def event_server() -> FastMCP:
    """Create a test MCP server with event components."""
    server: FastMCP = FastMCP("TestEventServer")
    server.add_tool(list_events)
    server.add_resource(get_events_resource)
    return server


class TestEventComponent:
    """Test event component functionality."""

    @patch("src.cli.CLIMixin.execute_cli")
    async def test_list_events_json(
        self, mock_execute_cli: MagicMock, event_server: FastMCP
    ) -> None:
        """Test event listing returns JSON dict."""
        mock_execute_cli.return_value = [
            {
                "id": 1,
                "timestamp": 1234567890,
                "severity": "info",
                "type": "Cycloid",
                "title": "Test event",
            }
        ]

        async with Client(event_server) as client:
            result = await client.call_tool(
                "CYCLOID_EVENT_LIST",
                {"severity": ["info"], "type": ["Cycloid"]},
            )

            result_text: str = (
                result.content[0].text if hasattr(result, "content") else str(result)
            )
            data = json.loads(result_text)
            assert data["count"] == 1
            assert data["events"][0]["severity"] == "info"
            assert "_display_hints" in data
            assert data["_display_hints"]["display_format"] == "table"
            assert "key_fields" in data["_display_hints"]

    @patch("src.cli.CLIMixin.execute_cli")
    async def test_get_events_resource(
        self, mock_execute_cli: MagicMock, event_server: FastMCP
    ) -> None:
        """Test events resource."""
        mock_execute_cli.return_value = [
            {
                "id": 2,
                "timestamp": 1234567891,
                "severity": "warn",
                "type": "AWS",
                "title": "Another event",
            }
        ]

        async with Client(event_server) as client:
            result = await client.read_resource("cycloid://events")

            if hasattr(result, "content") and result.content:
                text_content: str = result.content[0].text
            elif hasattr(result, "__iter__") and len(result) > 0:  # type: ignore[arg-type]
                text_content = result[0].text  # type: ignore[index]
            else:
                text_content = str(result)

            data = json.loads(text_content)
            assert data["count"] == 1
            assert data["events"][0]["type"] == "AWS"

    async def test_event_tools_registered(self, event_server: FastMCP) -> None:
        """Test that event tools are registered."""
        async with Client(event_server) as client:
            tools = await client.list_tools()
            tool_names: List[str] = [tool.name for tool in tools]
            assert "CYCLOID_EVENT_LIST" in tool_names

    async def test_event_resources_registered(self, event_server: FastMCP) -> None:
        """Test that event resources are registered."""
        async with Client(event_server) as client:
            resources = await client.list_resources()
            resource_uris: List[str] = [str(resource.uri) for resource in resources]
            assert "cycloid://events" in resource_uris

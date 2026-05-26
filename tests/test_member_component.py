"""Tests for Member component using FastMCP Client pattern."""

import json
from typing import List
from unittest.mock import MagicMock, patch

import pytest
from fastmcp import Client, FastMCP

from src.components.members import list_members

SAMPLE_MEMBER = {
    "id": 42,
    "username": "alice",
    "full_name": "Alice Smith",
    "email": "alice@example.com",
    "role": {"canonical": "organization-admin", "name": "Admin"},
    "created_at": 1700000000,
}

SAMPLE_MEMBER_2 = {
    "id": 7,
    "username": "bob",
    "full_name": "Bob Jones",
    "email": "bob@example.com",
    "role": {"canonical": "organization-member", "name": "Member"},
    "created_at": 1700000001,
}


@pytest.fixture
def member_server() -> FastMCP:
    """Create a test MCP server with member components."""
    server: FastMCP = FastMCP("TestMemberServer")
    server.add_tool(list_members)
    return server


class TestMemberComponent:
    """Test member component functionality."""

    @patch("src.cli.CLIMixin.execute_cli")
    async def test_list_members_happy_path(
        self, mock_execute_cli: MagicMock, member_server: FastMCP
    ) -> None:
        """Test member listing returns expected fields including numeric id."""
        mock_execute_cli.return_value = [SAMPLE_MEMBER, SAMPLE_MEMBER_2]

        async with Client(member_server) as client:
            result = await client.call_tool("CYCLOID_MEMBER_LIST", {})

            result_text: str = (
                result.content[0].text if hasattr(result, "content") else str(result)
            )
            data = json.loads(result_text)

            assert data["count"] == 2
            assert data["members"][0]["id"] == 42
            assert data["members"][0]["username"] == "alice"
            assert data["members"][1]["username"] == "bob"
            assert "_display_hints" in data
            assert data["_display_hints"]["display_format"] == "table"
            assert "username" in data["_display_hints"]["key_fields"]

    @patch("src.cli.CLIMixin.execute_cli")
    async def test_list_members_empty(
        self, mock_execute_cli: MagicMock, member_server: FastMCP
    ) -> None:
        """Test member listing returns count=0 for empty org."""
        mock_execute_cli.return_value = []

        async with Client(member_server) as client:
            result = await client.call_tool("CYCLOID_MEMBER_LIST", {})

            result_text: str = (
                result.content[0].text if hasattr(result, "content") else str(result)
            )
            data = json.loads(result_text)

            assert data["count"] == 0
            assert data["members"] == []

    async def test_member_tool_registered(self, member_server: FastMCP) -> None:
        """Test that CYCLOID_MEMBER_LIST tool is registered."""
        async with Client(member_server) as client:
            tools = await client.list_tools()
            tool_names: List[str] = [tool.name for tool in tools]
            assert "CYCLOID_MEMBER_LIST" in tool_names

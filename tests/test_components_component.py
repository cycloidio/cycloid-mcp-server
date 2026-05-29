"""Tests for Component (cy components) using FastMCP Client pattern."""

import json
from typing import Any, Dict, List
from unittest.mock import MagicMock, patch

import pytest
from fastmcp import Client, FastMCP

from src.components.components import get_components, list_components
from src.exceptions import CycloidCLIError


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
        """Test getting multiple components (one CLI call per canonical)."""
        mock_execute_cli.side_effect = [
            sample_components_data[0],
            sample_components_data[1],
        ]

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

    @patch("src.cli.CLIMixin.execute_cli")
    async def test_get_components_uses_component_flag_not_positional(
        self,
        mock_execute_cli: MagicMock,
        component_server: FastMCP,
        sample_components_data: List[Dict[str, Any]],
    ) -> None:
        """Regression: each canonical must reach `cy components get` via the
        `--component` flag (one call per canonical), never as a positional
        arg. The positional form is silently ignored by the real CLI
        (v6.10.x) and fails with "component is not set"."""
        mock_execute_cli.side_effect = [
            sample_components_data[0],
            sample_components_data[1],
        ]

        async with Client(component_server) as client:
            await client.call_tool(
                "CYCLOID_COMPONENT_GET",
                {
                    "project": "demo-project",
                    "env": "prod",
                    "canonicals": ["web-app", "database"],
                },
            )

        assert mock_execute_cli.call_count == 2
        for call_obj, expected_canonical in zip(
            mock_execute_cli.call_args_list, ["web-app", "database"]
        ):
            args, kwargs = call_obj
            assert args[0] == "components"
            # The only positional CLI arg is the subcommand — NEVER the canonical.
            assert args[1] == ["get"]
            flags: Dict[str, Any] = kwargs["flags"]
            assert flags["component"] == expected_canonical
            assert flags["project"] == "demo-project"
            assert flags["env"] == "prod"

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


class TestGetComponentsLogging:
    """Tests verifying CYCLOID_COMPONENT_GET emits a warning before ToolError (WS2.3)."""

    @patch("src.components.components.logger")
    @patch("src.cli.CLIMixin.execute_cli")
    async def test_get_components_cli_error_logs_warning(
        self,
        mock_execute_cli: MagicMock,
        mock_logger: MagicMock,
        component_server: FastMCP,
    ) -> None:
        """CycloidCLIError must emit logger.warning with project/env/detail before ToolError."""
        mock_execute_cli.side_effect = CycloidCLIError(
            "CLI command failed: permission denied",
            command="/usr/local/bin/cy components get web-app --output json",
            exit_code=1,
            stderr="permission denied",
        )

        async with Client(component_server) as client:
            with pytest.raises(Exception):
                await client.call_tool(
                    "CYCLOID_COMPONENT_GET",
                    {
                        "project": "demo-project",
                        "env": "prod",
                        "canonicals": ["web-app"],
                    },
                )

        mock_logger.warning.assert_called_once()
        log_msg: str = mock_logger.warning.call_args[0][0]
        assert "CYCLOID_COMPONENT_GET" in log_msg
        extra: Dict[str, Any] = mock_logger.warning.call_args[1].get("extra", {})
        assert extra.get("project") == "demo-project"
        assert extra.get("env") == "prod"
        assert "permission denied" in extra.get("detail", "")

    @patch("src.components.components.logger")
    @patch("src.cli.CLIMixin.execute_cli")
    async def test_get_components_generic_error_logs_warning(
        self,
        mock_execute_cli: MagicMock,
        mock_logger: MagicMock,
        component_server: FastMCP,
    ) -> None:
        """Generic Exception must also emit logger.warning with project/env/detail."""
        mock_execute_cli.side_effect = RuntimeError("unexpected internal error")

        async with Client(component_server) as client:
            with pytest.raises(Exception):
                await client.call_tool(
                    "CYCLOID_COMPONENT_GET",
                    {
                        "project": "my-proj",
                        "env": "staging",
                        "canonicals": ["db"],
                    },
                )

        mock_logger.warning.assert_called_once()
        extra: Dict[str, Any] = mock_logger.warning.call_args[1].get("extra", {})
        assert extra.get("project") == "my-proj"
        assert extra.get("env") == "staging"
        assert "unexpected internal error" in extra.get("detail", "")

    @patch("src.components.components.logger")
    @patch("src.cli.CLIMixin.execute_cli")
    async def test_get_components_warning_detail_clipped_at_300(
        self,
        mock_execute_cli: MagicMock,
        mock_logger: MagicMock,
        component_server: FastMCP,
    ) -> None:
        """detail in warning extra must be clipped to 300 chars."""
        long_msg = "E: " + "x" * 400
        mock_execute_cli.side_effect = CycloidCLIError(
            long_msg,
            command="cy components get",
            exit_code=1,
            stderr=long_msg,
        )

        async with Client(component_server) as client:
            with pytest.raises(Exception):
                await client.call_tool(
                    "CYCLOID_COMPONENT_GET",
                    {
                        "project": "p",
                        "env": "e",
                        "canonicals": ["c"],
                    },
                )

        extra: Dict[str, Any] = mock_logger.warning.call_args[1].get("extra", {})
        assert len(extra.get("detail", "")) <= 300

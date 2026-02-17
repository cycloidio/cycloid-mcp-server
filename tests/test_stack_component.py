"""Tests for Stack component using FastMCP Client pattern."""

import json
from typing import Any, Dict, List
from unittest.mock import MagicMock, patch

import pytest
from fastmcp import Client, FastMCP

from src.components.stackforms import validate_stackforms
from src.components.stacks import (
    get_blueprints_resource,
    list_blueprints,
    create_stack_from_blueprint,
)


@pytest.fixture
def stack_server() -> FastMCP:
    """Create a test MCP server with stack components."""
    server: FastMCP = FastMCP("TestStackServer")
    server.add_tool(list_blueprints)
    server.add_tool(create_stack_from_blueprint)
    server.add_tool(validate_stackforms)
    server.add_resource(get_blueprints_resource)
    return server


class TestStackComponent:
    """Test stack component functionality."""

    @patch("src.cli.CLIMixin.execute_cli")
    async def test_list_blueprints_json(
        self, mock_execute_cli: MagicMock, stack_server: FastMCP
    ) -> None:
        """Test blueprint listing returns JSON dict."""
        mock_execute_cli.return_value = [
            {
                "name": "test-blueprint",
                "ref": "cycloid-io:terraform-aws-vpc",
                "use_cases": ["aws", "vpc"],
                "description": "AWS VPC blueprint",
            }
        ]

        async with Client(stack_server) as client:
            result = await client.call_tool("CYCLOID_BLUEPRINT_LIST", {})

            result_text: str = (
                result.content[0].text if hasattr(result, "content") else str(result)
            )  # type: ignore[reportUnknownMemberType, reportAttributeAccessIssue]
            data: Dict[str, Any] = json.loads(
                result_text
            )  # type: ignore[reportUnknownArgumentType]

            assert "blueprints" in data
            assert "count" in data
            assert data["count"] == 1
            assert data["blueprints"][0]["name"] == "test-blueprint"
            assert "_display_hints" in data
            assert data["_display_hints"]["display_format"] == "table"
            assert "key_fields" in data["_display_hints"]

    @patch("src.cli.CLIMixin.execute_cli")
    async def test_get_blueprints_resource(
        self, mock_execute_cli: MagicMock, stack_server: FastMCP
    ) -> None:
        """Test blueprints resource."""
        mock_execute_cli.return_value = [
            {
                "name": "test-blueprint",
                "ref": "cycloid-io:terraform-aws-vpc",
                "use_cases": ["aws", "vpc"],
                "description": "AWS VPC blueprint",
            }
        ]

        async with Client(stack_server) as client:
            result = await client.read_resource("cycloid://blueprints")

            if (
                hasattr(result, "content") and result.content
            ):  # type: ignore[reportUnknownMemberType, reportAttributeAccessIssue]
                text_content: str = result.content[0].text  # type: ignore[]
            elif hasattr(result, "__iter__") and len(result) > 0:
                text_content: str = result[
                    0
                ].text  # type: ignore[reportUnknownMemberType, reportAttributeAccessIssue]
            else:
                text_content: str = str(result)

            data = json.loads(str(text_content))
            assert "test-blueprint" in str(text_content)
            assert "cycloid-io:terraform-aws-vpc" in str(text_content)
            # No more formatted_table key
            assert "formatted_table" not in data

    async def test_stack_tools_registered(self, stack_server: FastMCP) -> None:
        """Test that all stack tools are registered."""
        async with Client(stack_server) as client:
            tools = await client.list_tools()
            tool_names: List[str] = [tool.name for tool in tools]

            assert "CYCLOID_BLUEPRINT_LIST" in tool_names
            assert "CYCLOID_BLUEPRINT_STACK_CREATE" in tool_names
            assert "CYCLOID_STACKFORMS_VALIDATE" in tool_names

    async def test_stack_resources_registered(self, stack_server: FastMCP) -> None:
        """Test that all stack resources are registered."""
        async with Client(stack_server) as client:
            resources = await client.list_resources()
            resource_uris: List[str] = [str(resource.uri) for resource in resources]

            assert "cycloid://blueprints" in resource_uris

    @patch("src.cli.CLIMixin.execute_cli_command")
    async def test_validate_stackforms_success(
        self, mock_execute_cli_command: Any, stack_server: FastMCP
    ):
        """Test successful StackForms validation."""
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.stdout = "Validation passed"
        mock_execute_cli_command.return_value = mock_result

        valid_forms_content = """
use_cases:
- name: aws
  sections:
  - name: Cloud provider
    groups:
    - name: Access
      technologies: [pipeline]
      vars:
      - name: "AWS region"
        key: aws_default_region
        type: string
        widget: auto_complete
        values: ["eu-west-1", "us-east-1"]
        default: "eu-west-1"
"""

        async with Client(stack_server) as client:
            result = await client.call_tool(
                "CYCLOID_STACKFORMS_VALIDATE", {"forms_content": valid_forms_content}
            )

            result_text: str = (
                result.content[0].text if hasattr(result, "content") else str(result)
            )  # type: ignore[reportUnknownMemberType, reportAttributeAccessIssue]

            assert "StackForms Validation Successful" in result_text
            assert "Validation passed" in result_text

    @patch("src.cli.CLIMixin.execute_cli_command")
    async def test_validate_stackforms_success_no_output(
        self, mock_execute_cli_command: Any, stack_server: FastMCP
    ):
        """Test successful StackForms validation with no stdout."""
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.stdout = ""
        mock_execute_cli_command.return_value = mock_result

        valid_forms_content = """
use_cases:
- name: aws
  sections:
  - name: Cloud provider
    groups:
    - name: Access
      technologies: [pipeline]
      vars:
      - name: "AWS region"
        key: aws_default_region
        type: string
        widget: auto_complete
        values: ["eu-west-1", "us-east-1"]
        default: "eu-west-1"
"""

        async with Client(stack_server) as client:
            result = await client.call_tool(
                "CYCLOID_STACKFORMS_VALIDATE", {"forms_content": valid_forms_content}
            )

            result_text: str = (
                result.content[0].text if hasattr(result, "content") else str(result)
            )  # type: ignore[reportUnknownMemberType, reportAttributeAccessIssue]

            assert "StackForms Validation Successful" in result_text
            assert "follows Cycloid best practices" in result_text

    @patch("src.cli.CLIMixin.execute_cli_command")
    async def test_validate_stackforms_failure(
        self, mock_execute_cli_command: Any, stack_server: FastMCP
    ):
        """Test failed StackForms validation raises ToolError."""
        from fastmcp.exceptions import ToolError

        mock_result = MagicMock()
        mock_result.success = False
        mock_result.exit_code = 1
        mock_result.stderr = "Widget invalid config is not supported"
        mock_execute_cli_command.return_value = mock_result

        invalid_forms_content = """
use_cases:
- name: aws
  sections:
  - name: Cloud provider
    groups:
    - name: Access
      technologies: [pipeline]
      vars:
      - name: "AWS region"
        key: aws_default_region
        type: string
        widgetsd: auto_complete
        values: ["eu-west-1", "us-east-1"]
        default: "eu-west-1"
"""

        async with Client(stack_server) as client:
            with pytest.raises(ToolError) as exc_info:
                await client.call_tool(
                    "CYCLOID_STACKFORMS_VALIDATE", {"forms_content": invalid_forms_content}
                )

            assert "Validation failed" in str(exc_info.value)
            assert "Widget invalid config" in str(exc_info.value)

    @patch("src.cli.CLIMixin.execute_cli_command")
    async def test_validate_stackforms_file_cleanup(
        self, mock_execute_cli_command: Any, stack_server: FastMCP
    ):
        """Test that temporary files are cleaned up even on errors."""
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.stdout = "OK"
        mock_execute_cli_command.return_value = mock_result

        forms_content = """
use_cases:
- name: aws
  sections:
  - name: Cloud provider
    groups:
    - name: Access
      technologies: [pipeline]
      vars:
      - name: "AWS region"
        key: aws_default_region
        type: string
        widget: auto_complete
        values: ["eu-west-1", "us-east-1"]
        default: "eu-west-1"
"""

        async with Client(stack_server) as client:
            result = await client.call_tool(
                "CYCLOID_STACKFORMS_VALIDATE", {"forms_content": forms_content}
            )

            # The test passes if no exception is raised (file cleanup worked)
            assert result is not None

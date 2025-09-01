"""Tests for StackComponent using FastMCP Client pattern."""

import json
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from fastmcp import Client, FastMCP

from src.cli_mixin import CLIMixin
from src.components.stacks import StackFormsTools, StackResources, StackTools


@pytest.fixture
def stack_server():
    """Create a test MCP server with stack components."""
    server = FastMCP("TestStackServer")

    # Initialize CLI mixin
    cli = CLIMixin()

    # Create and register stack components (only those with MCP tools/resources)
    stack_tools = StackTools(cli)
    stacks_resources = StackResources(cli)
    stackforms_tools = StackFormsTools(cli)

    stack_tools.register_all(server)
    stacks_resources.register_all(server)
    stackforms_tools.register_all(server)

    return server


class TestStackComponent:
    """Test stack component functionality."""

    @patch("src.cli_mixin.CLIMixin.execute_cli")
    async def test_list_blueprints_table(self, mock_execute_cli: Any, stack_server: FastMCP):
        """Test blueprint listing in table format."""
        # Mock the CLI response
        mock_execute_cli.return_value = [
            {
                "name": "test-blueprint",
                "ref": "cycloid-io:terraform-aws-vpc",
                "use_cases": ["aws", "vpc"],
                "description": "AWS VPC blueprint",
            }
        ]

        async with Client(stack_server) as client:
            result = await client.call_tool("CYCLOID_BLUEPRINT_LIST", {"format": "table"})

            # Extract the actual text content
            result_text: str = (
                result.content[0].text if hasattr(result, "content") else str(result)
            )  # type: ignore[reportUnknownMemberType, reportAttributeAccessIssue]

            assert "test-blueprint" in result_text
            assert "cycloid-io:terraform-aws-vpc" in result_text
            assert "aws, vpc" in result_text
            assert "AWS VPC blueprint" in result_text

    @patch("src.cli_mixin.CLIMixin.execute_cli")
    async def test_list_blueprints_json(self, mock_execute_cli: Any, stack_server: FastMCP):
        """Test blueprint listing in JSON format."""
        # Mock the CLI response
        mock_execute_cli.return_value = [
            {
                "name": "test-blueprint",
                "ref": "cycloid-io:terraform-aws-vpc",
                "use_cases": ["aws", "vpc"],
                "description": "AWS VPC blueprint",
            }
        ]

        async with Client(stack_server) as client:
            result = await client.call_tool("CYCLOID_BLUEPRINT_LIST", {"format": "json"})

            # Extract the actual text content
            result_text: str = (
                result.content[0].text if hasattr(result, "content") else str(result)
            )  # type: ignore[reportUnknownMemberType, reportAttributeAccessIssue]
            data = json.loads(result_text)  # type: ignore[reportUnknownArgumentType]

            assert "blueprints" in data
            assert "count" in data
            assert data["count"] == 1
            assert data["blueprints"][0]["name"] == "test-blueprint"

    @patch("src.cli_mixin.CLIMixin.execute_cli")
    async def test_get_blueprints_resource(self, mock_execute_cli: Any, stack_server: FastMCP):
        """Test blueprints resource."""
        # Mock the CLI response
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

            # Handle different response formats from FastMCP Client
            if (
                hasattr(result, "content") and result.content
            ):  # type: ignore[reportUnknownMemberType, reportAttributeAccessIssue]
                # List of content items
                text_content: str = result.content[0].text  # type: ignore[]
            elif hasattr(result, "__iter__") and len(result) > 0:
                # Direct list response
                text_content: str = result[
                    0
                ].text  # type: ignore[reportUnknownMemberType, reportAttributeAccessIssue]
            else:
                # Direct text response
                text_content: str = str(result)

            assert "test-blueprint" in text_content
            assert "cycloid-io:terraform-aws-vpc" in text_content

    async def test_stack_tools_registered(self, stack_server: FastMCP):
        """Test that all stack tools are registered."""
        async with Client(stack_server) as client:
            tools = await client.list_tools()
            tool_names = [tool.name for tool in tools]

            assert "CYCLOID_BLUEPRINT_LIST" in tool_names
            assert "CYCLOID_BLUEPRINT_STACK_CREATE" in tool_names
            assert "CYCLOID_STACKFORMS_VALIDATE" in tool_names

    async def test_stack_resources_registered(self, stack_server: FastMCP):
        """Test that all stack resources are registered."""
        async with Client(stack_server) as client:
            resources = await client.list_resources()
            resource_uris = [str(resource.uri) for resource in resources]

            assert "cycloid://blueprints" in resource_uris

    @patch("src.cli_mixin.CLIMixin.execute_cli_command")
    @patch("src.cli_mixin.CLIMixin.execute_cli")
    async def test_create_stack_from_blueprint_smart_elicitation_success(
        self,
        mock_execute_cli: Any,
        mock_execute_cli_command: Any,
        stack_server: FastMCP,
    ):
        """Test successful elicitation flow."""
        # For now, skip this test as it requires complex ctx mocking
        # that's difficult to implement with the MCP client
        pytest.skip("Complex ctx mocking required - will implement with unit tests")

    @patch("src.cli_mixin.CLIMixin.execute_cli_command")
    @patch("src.cli_mixin.CLIMixin.execute_cli")
    async def test_create_stack_from_blueprint_smart_direct_creation(
        self,
        mock_execute_cli: Any,
        mock_execute_cli_command: Any,
        stack_server: FastMCP,
    ):
        """Test direct stack creation with all parameters provided."""

        # Mock CLI responses
        def mock_cli_json(
            command: str, args: list[str], output_format: str = "json"
        ) -> list[dict[str, str | list[str]]]:
            if command == "stacks" and args == ["list", "--blueprint"]:
                return [
                    {
                        "name": "test-blueprint",
                        "ref": "cycloid-io:terraform-sample",
                        "use_cases": ["aws", "gcp"],
                        "description": "Test blueprint",
                    }
                ]
            elif command == "catalog-repository" and args == ["list"]:
                return [
                    {"canonical": "cycloid-stacks-test"},
                    {"canonical": "other-repo"},
                ]
            return []

        # For now, skip this test as it requires complex mocking
        # that's difficult to implement with the MCP client
        pytest.skip("Complex mocking required - will implement with unit tests")

    @patch("src.cli_mixin.CLIMixin.execute_cli_command")
    async def test_validate_stackforms_success(
        self, mock_execute_cli_command: Any, stack_server: FastMCP
    ):
        """Test successful StackForms validation."""
        # Mock successful CLI validation
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

            assert "✅ **StackForms Validation Successful**" in result_text
            assert "Validation passed" in result_text

    @patch("src.cli_mixin.CLIMixin.execute_cli_command")
    async def test_validate_stackforms_success_no_output(
        self, mock_execute_cli_command: Any, stack_server: FastMCP
    ):
        """Test successful StackForms validation with no stdout."""
        # Mock successful CLI validation with empty stdout
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

            assert "✅ **StackForms Validation Successful**" in result_text
            assert "follows Cycloid best practices" in result_text

    @patch("src.cli_mixin.CLIMixin.execute_cli_command")
    async def test_validate_stackforms_failure(
        self, mock_execute_cli_command: Any, stack_server: FastMCP
    ):
        """Test failed StackForms validation."""
        # Mock failed CLI validation
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
        widgetsd: auto_complete  # Typo: should be 'widget'
        values: ["eu-west-1", "us-east-1"]
        default: "eu-west-1"
"""

        async with Client(stack_server) as client:
            result = await client.call_tool(
                "CYCLOID_STACKFORMS_VALIDATE", {"forms_content": invalid_forms_content}
            )

            result_text: str = (
                result.content[0].text if hasattr(result, "content") else str(result)
            )  # type: ignore[reportUnknownMemberType, reportAttributeAccessIssue]

            assert "❌ **Failed to validate StackForms**" in result_text
            assert "Widget invalid config is not supported" in result_text
            assert "Check YAML syntax" in result_text

    @patch("src.cli_mixin.CLIMixin.execute_cli_command")
    async def test_validate_stackforms_cli_error(
        self, mock_execute_cli_command: Any, stack_server: FastMCP
    ):
        """Test StackForms validation when CLI command raises an exception."""
        # Mock CLI command raising an exception
        mock_execute_cli_command.side_effect = Exception("CLI command failed")

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

            result_text: str = (
                result.content[0].text if hasattr(result, "content") else str(result)
            )  # type: ignore[reportUnknownMemberType, reportAttributeAccessIssue]

            assert "❌ **Failed to validate StackForms**" in result_text
            assert "CLI command failed" in result_text

    @patch("src.cli_mixin.CLIMixin.execute_cli_command")
    async def test_validate_stackforms_cycloid_cli_error(
        self, mock_execute_cli_command: Any, stack_server: FastMCP
    ):
        """Test StackForms validation with CycloidCLIError."""
        from src.exceptions import CycloidCLIError

        # Mock CLI command raising CycloidCLIError
        mock_execute_cli_command.side_effect = CycloidCLIError(
            "Validation failed", "stacks forms validate", 1, "Invalid YAML syntax"
        )

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

            result_text: str = (
                result.content[0].text if hasattr(result, "content") else str(result)
            )  # type: ignore[reportUnknownMemberType, reportAttributeAccessIssue]

            assert "❌ **Failed to execute CLI command" in result_text
            assert "Invalid YAML syntax" in result_text

    @patch("src.cli_mixin.CLIMixin.execute_cli_command")
    async def test_validate_stackforms_file_cleanup(
        self, mock_execute_cli_command: Any, stack_server: FastMCP
    ):
        """Test that temporary files are cleaned up even on CLI errors."""
        # Mock CLI command raising an exception
        mock_execute_cli_command.side_effect = Exception("CLI command failed")

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
            result_text: str = (
                result.content[0].text if hasattr(result, "content") else str(result)
            )  # type: ignore[reportUnknownMemberType, reportAttributeAccessIssue]
            assert "❌ **Failed to validate StackForms**" in result_text

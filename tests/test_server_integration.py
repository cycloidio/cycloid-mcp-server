"""Tests for overall server integration using FastMCP Client pattern."""

import pytest
from fastmcp import Client, FastMCP

from src.cli_mixin import CLIMixin
from src.components.catalogs import CatalogResources, CatalogTools
from src.components.stacks import StackFormsTools, StackResources, StackTools


@pytest.fixture
def full_server():
    """Create a test MCP server with all components."""
    server = FastMCP("TestFullServer")

    # Initialize CLI mixin
    cli = CLIMixin()

    # Create and register all components (only those with MCP tools/resources)
    catalog_tools = CatalogTools(cli)
    catalog_resources = CatalogResources(cli)
    stack_tools = StackTools(cli)
    stacks_resources = StackResources(cli)
    stackforms_tools = StackFormsTools(cli)

    catalog_tools.register_all(server)
    catalog_resources.register_all(server)
    stack_tools.register_all(server)
    stacks_resources.register_all(server)
    stackforms_tools.register_all(server)

    return server


class TestServerIntegration:
    """Test overall server integration."""

    async def test_server_has_expected_tools(self, full_server: FastMCP):
        """Test that server has the expected tools registered."""
        async with Client(full_server) as client:
            tools = await client.list_tools()
            tool_names = [tool.name for tool in tools]

            # Check that our tools are registered with CYCLOID prefixes
            assert "CYCLOID_CATALOG_REPO_LIST" in tool_names
            assert "CYCLOID_BLUEPRINT_LIST" in tool_names
            assert "CYCLOID_BLUEPRINT_STACK_CREATE" in tool_names

    async def test_server_has_expected_resources(self, full_server: FastMCP):
        """Test that server has the expected resources registered."""
        async with Client(full_server) as client:
            resources = await client.list_resources()
            resource_uris = [str(resource.uri) for resource in resources]

            # Check that our resources are registered
            assert "cycloid://service-catalogs-repositories" in resource_uris
            assert "cycloid://blueprints" in resource_uris

    async def test_server_components_loaded(self, full_server: FastMCP):
        """Test that server has components loaded."""
        async with Client(full_server) as client:
            tools = await client.list_tools()
            resources = await client.list_resources()

            # We should have at least some tools loaded
            assert len(tools) > 0

            # We should have at least some resources loaded
            assert len(resources) > 0

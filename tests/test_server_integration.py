"""Tests for overall server integration using FastMCP Client pattern."""

from typing import List

import pytest
from fastmcp import Client, FastMCP

from src.components.catalogs import (
    get_service_catalogs_resource,
    list_catalog_repositories,
)
from src.components.events import get_events_resource, list_events
from src.components.pipelines import get_pipelines_resource, list_pipelines
from src.components.stackforms import validate_stackforms
from src.components.stacks import (
    create_stack_from_blueprint,
    get_blueprints_resource,
    list_blueprints,
)


@pytest.fixture
def full_server() -> FastMCP:
    """Create a test MCP server with all components."""
    server: FastMCP = FastMCP("TestFullServer")

    # Register all tools
    server.add_tool(list_catalog_repositories)
    server.add_tool(list_events)
    server.add_tool(list_pipelines)
    server.add_tool(list_blueprints)
    server.add_tool(create_stack_from_blueprint)
    server.add_tool(validate_stackforms)

    # Register all resources
    server.add_resource(get_service_catalogs_resource)
    server.add_resource(get_events_resource)
    server.add_resource(get_pipelines_resource)
    server.add_resource(get_blueprints_resource)

    return server


class TestServerIntegration:
    """Test overall server integration."""

    async def test_server_has_expected_tools(self, full_server: FastMCP) -> None:
        """Test that server has the expected tools registered."""
        async with Client(full_server) as client:
            tools = await client.list_tools()
            tool_names: List[str] = [tool.name for tool in tools]

            assert "CYCLOID_CATALOG_REPO_LIST" in tool_names
            assert "CYCLOID_EVENT_LIST" in tool_names
            assert "CYCLOID_PIPELINE_LIST" in tool_names
            assert "CYCLOID_BLUEPRINT_LIST" in tool_names
            assert "CYCLOID_BLUEPRINT_STACK_CREATE" in tool_names
            assert "CYCLOID_STACKFORMS_VALIDATE" in tool_names

    async def test_server_has_expected_resources(self, full_server: FastMCP) -> None:
        """Test that server has the expected resources registered."""
        async with Client(full_server) as client:
            resources = await client.list_resources()
            resource_uris: List[str] = [str(resource.uri) for resource in resources]

            assert "cycloid://service-catalogs-repositories" in resource_uris
            assert "cycloid://events" in resource_uris
            assert "cycloid://pipelines" in resource_uris
            assert "cycloid://blueprints" in resource_uris

    async def test_server_components_loaded(self, full_server: FastMCP) -> None:
        """Test that server has components loaded."""
        async with Client(full_server) as client:
            tools = await client.list_tools()
            resources = await client.list_resources()

            assert len(tools) > 0
            assert len(resources) > 0

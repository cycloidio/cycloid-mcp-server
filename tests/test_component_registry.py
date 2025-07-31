"""Tests for component registry."""

from typing import Any
from unittest.mock import Mock

import pytest
from fastmcp import FastMCP

from src.cli_mixin import CLIMixin
from src.component_registry import ComponentRegistry


class TestComponentRegistry:
    """Test component registry functionality."""

    @pytest.fixture
    def cli_mixin(self) -> Any:
        """Create a mock CLI mixin."""
        return Mock(spec=CLIMixin)

    @pytest.fixture
    def registry(self, cli_mixin: Any) -> ComponentRegistry:
        """Create a component registry instance."""
        return ComponentRegistry(cli_mixin)

    @pytest.fixture
    def mcp_server(self) -> Any:
        """Create a mock MCP server."""
        return Mock(spec=FastMCP)

    def test_registry_initialization(self, registry: ComponentRegistry):
        """Test registry initialization."""
        assert registry.cli is not None
        assert registry.registered_components == []
        assert registry.components_path.exists()

    def test_discover_mcp_components(self, registry: ComponentRegistry):
        """Test MCP component discovery."""
        components = registry.discover_mcp_components()

        # Should discover our actual components
        component_names = [c.__name__ for c in components]

        # Check that we have the expected components
        expected_components = [
            "StackTools",
            "StackResources",
            "StackFormsTools",
            "CatalogTools",
            "CatalogResources",
        ]

        for expected in expected_components:
            assert expected in component_names, f"Expected {expected} to be discovered"

    def test_register_components(self, registry: ComponentRegistry, mcp_server: Any):
        """Test component registration."""
        # Register components
        registry.register_components(mcp_server)

        # Should have registered components
        assert len(registry.registered_components) > 0

        # Each registered component should have been instantiated with CLI
        for component in registry.registered_components:
            assert hasattr(component, "handler")
            # Type assertion to help Pyright understand the structure
            component_with_handler: Any = component
            assert component_with_handler.handler.cli == registry.cli

    def test_get_registered_components(
        self, registry: ComponentRegistry, mcp_server: Any
    ):
        """Test getting registered components."""
        # Initially empty
        assert registry.get_registered_components() == []

        # Register components
        registry.register_components(mcp_server)

        # Should return registered components
        registered = registry.get_registered_components()
        assert len(registered) > 0
        assert registered == registry.registered_components

    def test_registry_with_mock_components(self, cli_mixin: Any):
        """Test registry with mock components to ensure proper instantiation."""
        registry = ComponentRegistry(cli_mixin)
        mcp_server = Mock(spec=FastMCP)

        # Register components
        registry.register_components(mcp_server)

        # Verify that each component was instantiated with CLI
        for component in registry.registered_components:
            # Type assertion to help Pyright understand the structure
            component_with_handler: Any = component
            assert component_with_handler.handler.cli == cli_mixin

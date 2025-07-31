"""Automatic component registration for Cycloid MCP server."""

import importlib
import inspect
from pathlib import Path
from typing import Any, List, Type

from fastmcp import FastMCP
from fastmcp.contrib.mcp_mixin import MCPMixin
from fastmcp.utilities.logging import get_logger

from src.cli_mixin import CLIMixin

logger = get_logger(__name__)


class ComponentRegistry:
    """Automatic component discovery and registration."""

    def __init__(self, cli: CLIMixin):  # type: ignore[reportMissingSuperCall]
        """Initialize component registry with CLI mixin."""
        self.cli = cli
        self.components_path = Path(__file__).parent / "components"
        self.registered_components: List[MCPMixin] = []

    def _is_mcp_component_file(self, file_path: Path) -> bool:
        """Check if a file is an MCP component file."""
        if file_path.name.startswith("_") or file_path.name == "__init__.py":
            return False

        return (
            file_path.name.endswith("_tools.py")
            or file_path.name.endswith("_resources.py")
            or file_path.name.endswith("_handler.py")
            or file_path.name.endswith("_prompts.py")
        )

    def _is_valid_component_directory(self, component_dir: Path) -> bool:
        """Check if a directory is a valid component directory."""
        return component_dir.is_dir() and not component_dir.name.startswith("_")

    def _find_mcp_classes_in_module(self, module_name: str) -> List[Type[MCPMixin]]:
        """Find MCP-enabled classes in a module."""
        mcp_components: List[Type[MCPMixin]] = []

        try:
            module = importlib.import_module(module_name)

            # Find MCP-enabled classes in the module
            for _, obj in inspect.getmembers(module):
                if (
                    inspect.isclass(obj)
                    and issubclass(obj, MCPMixin)
                    and obj != MCPMixin
                ):
                    # Type cast since we've verified it's an MCPMixin subclass
                    mcp_component_class: Type[MCPMixin] = obj
                    mcp_components.append(mcp_component_class)
                    component_name = obj.__name__
                    message = (
                        f"Discovered MCP component: {component_name} "
                        f"from {module_name}"
                    )
                    logger.debug(message)

        except ImportError as e:
            logger.warning(f"Failed to import {module_name}: {e}")
        except Exception as e:
            logger.warning(f"Error processing {module_name}: {e}")

        return mcp_components

    def discover_mcp_components(self) -> List[Type[MCPMixin]]:
        """Discover all MCP-enabled component classes."""
        mcp_components: List[Type[MCPMixin]] = []

        # Iterate through all component directories
        for component_dir in self.components_path.iterdir():
            if not self._is_valid_component_directory(component_dir):
                continue

            # Look for MCP component files
            for file_path in component_dir.glob("*.py"):
                if not self._is_mcp_component_file(file_path):
                    continue

                # Import the module
                module_name = f"src.components.{component_dir.name}.{file_path.stem}"
                module_components = self._find_mcp_classes_in_module(module_name)
                mcp_components.extend(module_components)

        return mcp_components

    def register_components(self, mcp: FastMCP[Any]) -> None:
        """Register all discovered MCP components using MCPMixin's register_all."""
        mcp_components = self.discover_mcp_components()

        for component_class in mcp_components:
            try:
                # Instantiate component with CLI mixin
                component = component_class(self.cli)

                # Register with MCP server using MCPMixin's register_all method
                # This automatically registers all @mcp_tool, @mcp_resource,
                # and @mcp_prompt decorated methods
                mcp_component: MCPMixin = component
                mcp_component.register_all(mcp)  # type: ignore[reportCallIssue]

                # Store for reference
                self.registered_components.append(component)

                # Log registration
                component_name = component_class.__name__
                logger.info(f"✅ Registered {component_name}")

            except Exception as e:
                logger.error(f"Failed to register {component_class.__name__}: {e}")

    def get_registered_components(self) -> List[MCPMixin]:
        """Get list of registered components."""
        return self.registered_components

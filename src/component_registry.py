"""Auto-magic component registration for Cycloid MCP server."""

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
    """Auto-magic component discovery using __all__ exports from component packages."""

    def __init__(self, cli: CLIMixin):  # type: ignore[reportMissingSuperCall]
        """Initialize component registry with CLI mixin."""
        self.cli = cli
        self.components_path = Path(__file__).parent / "components"
        self.registered_components: List[MCPMixin] = []

    def _discover_component_packages(self) -> List[str]:
        """Discover component packages by looking for directories with __init__.py."""
        packages = []

        for item in self.components_path.iterdir():
            if item.is_dir() and not item.name.startswith("_") and (item / "__init__.py").exists():
                packages.append(  # type: ignore[reportUnknownMemberType]
                    f"src.components.{item.name}"
                )

        return packages  # type: ignore[reportUnknownVariableType]

    def _get_mcp_classes_from_package(self, package_name: str) -> List[Type[MCPMixin]]:
        """Get MCP classes from a package's __all__ exports."""
        mcp_classes = []

        try:
            # Import the package
            package = importlib.import_module(package_name)

            # Get all exported classes
            if hasattr(package, "__all__"):
                for class_name in package.__all__:
                    if hasattr(package, class_name):
                        cls = getattr(package, class_name)

                        # Check if it's an MCP component class
                        if inspect.isclass(cls) and issubclass(cls, MCPMixin) and cls != MCPMixin:
                            mcp_classes.append(cls)  # type: ignore[reportUnknownMemberType]
                            logger.debug(
                                f"Discovered MCP component: {class_name} from {package_name}"
                            )

        except ImportError as e:
            logger.warning(f"Failed to import package {package_name}: {e}")
        except Exception as e:
            logger.warning(f"Error processing package {package_name}: {e}")

        return mcp_classes  # type: ignore[reportUnknownVariableType]

    def discover_mcp_components(self) -> List[Type[MCPMixin]]:
        """Auto-discover MCP components from component packages."""
        all_components = []

        # Discover component packages
        packages = self._discover_component_packages()
        logger.debug(f"Found component packages: {packages}")

        # Get MCP classes from each package
        for package_name in packages:
            components = self._get_mcp_classes_from_package(package_name)
            all_components.extend(components)  # type: ignore[reportUnknownMemberType]

        component_count = len(all_components)  # type: ignore[reportUnknownArgumentType]
        logger.info(f"Auto-discovered {component_count} MCP components")
        return all_components  # type: ignore[reportUnknownVariableType]

    def register_components(self, mcp: FastMCP[Any]) -> None:
        """Register all auto-discovered MCP components."""
        mcp_components = self.discover_mcp_components()

        for component_class in mcp_components:
            try:
                # Instantiate component with CLI mixin
                component = component_class(self.cli)  # type: ignore[reportCallIssue]

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

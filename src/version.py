"""Version utilities for the Cycloid MCP Server."""

import tomllib
from pathlib import Path


def get_version() -> str:
    """Get the version from pyproject.toml."""
    try:
        # Get the project root directory (where pyproject.toml is located)
        project_root = Path(__file__).parent.parent
        pyproject_path = project_root / "pyproject.toml"

        if not pyproject_path.exists():
            return "unknown"

        with open(pyproject_path, "rb") as f:
            data = tomllib.load(f)

        return data.get("project", {}).get("version", "unknown")

    except Exception:
        return "unknown"


def get_project_info() -> dict[str, str]:
    """Get project information from pyproject.toml."""
    try:
        project_root = Path(__file__).parent.parent
        pyproject_path = project_root / "pyproject.toml"

        if not pyproject_path.exists():
            return {"name": "unknown", "version": "unknown", "description": "unknown"}

        with open(pyproject_path, "rb") as f:
            data = tomllib.load(f)

        project = data.get("project", {})
        return {
            "name": project.get("name", "unknown"),
            "version": project.get("version", "unknown"),
            "description": project.get("description", "unknown"),
        }

    except Exception:
        return {"name": "unknown", "version": "unknown", "description": "unknown"}


# Export version for backward compatibility
__version__ = get_version()

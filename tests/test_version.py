"""Tests for version utilities."""

from src.version import get_project_info, get_version


def test_get_version():
    """Test that get_version returns a valid version string."""
    version = get_version()
    assert isinstance(version, str)
    assert version != "unknown"
    assert len(version) > 0

    # Version should follow semantic versioning pattern (x.y.z)
    version_parts = version.split(".")
    assert len(version_parts) >= 2, "Version should have at least major.minor format"

    # All parts should be numeric
    for part in version_parts:
        assert part.isdigit(), f"Version part '{part}' should be numeric"


def test_get_project_info():
    """Test that get_project_info returns valid project information."""
    info = get_project_info()

    assert isinstance(info, dict)
    assert "name" in info
    assert "version" in info
    assert "description" in info

    # Validate name
    assert isinstance(info["name"], str)
    assert len(info["name"]) > 0
    assert info["name"] != "unknown"

    # Validate version (same as get_version test)
    version = info["version"]
    assert isinstance(version, str)
    assert version != "unknown"
    assert len(version) > 0

    version_parts = version.split(".")
    assert len(version_parts) >= 2, "Version should have at least major.minor format"
    for part in version_parts:
        assert part.isdigit(), f"Version part '{part}' should be numeric"

    # Validate description
    assert isinstance(info["description"], str)
    assert len(info["description"]) > 0
    assert info["description"] != "unknown"


def test_version_consistency():
    """Test that version is consistent across different methods."""
    version1 = get_version()
    version2 = get_project_info()["version"]

    assert version1 == version2, "Version should be consistent across all methods"


def test_import_version():
    """Test that version can be imported from src package."""
    from src import __version__

    assert isinstance(__version__, str)
    assert __version__ != "unknown"
    assert len(__version__) > 0


def test_version_from_pyproject():
    """Test that version matches what's in pyproject.toml."""
    import tomllib
    from pathlib import Path

    # Read version from pyproject.toml
    project_root = Path(__file__).parent.parent
    pyproject_path = project_root / "pyproject.toml"

    with open(pyproject_path, "rb") as f:
        data = tomllib.load(f)

    pyproject_version = data.get("project", {}).get("version", "unknown")

    # Version from our utility should match pyproject.toml
    utility_version = get_version()
    assert utility_version == pyproject_version, (
        f"Version mismatch: utility={utility_version}, " f"pyproject={pyproject_version}"
    )


def test_project_info_from_pyproject():
    """Test that project info matches what's in pyproject.toml."""
    import tomllib
    from pathlib import Path

    # Read project info from pyproject.toml
    project_root = Path(__file__).parent.parent
    pyproject_path = project_root / "pyproject.toml"

    with open(pyproject_path, "rb") as f:
        data = tomllib.load(f)

    project = data.get("project", {})
    pyproject_name = project.get("name", "unknown")
    pyproject_version = project.get("version", "unknown")
    pyproject_description = project.get("description", "unknown")

    # Project info from our utility should match pyproject.toml
    utility_info = get_project_info()
    assert utility_info["name"] == pyproject_name
    assert utility_info["version"] == pyproject_version
    assert utility_info["description"] == pyproject_description


def test_error_handling():
    """Test that version utilities handle errors gracefully."""
    # Test with a non-existent pyproject.toml (should return "unknown")
    import shutil
    import tempfile
    from pathlib import Path

    # Create a temporary directory and move pyproject.toml temporarily
    project_root = Path(__file__).parent.parent
    pyproject_path = project_root / "pyproject.toml"

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_pyproject = Path(temp_dir) / "pyproject.toml"
        shutil.move(str(pyproject_path), str(temp_pyproject))

        try:
            # Version should return "unknown" when pyproject.toml is missing
            version = get_version()
            assert version == "unknown"

            info = get_project_info()
            assert info["name"] == "unknown"
            assert info["version"] == "unknown"
            assert info["description"] == "unknown"

        finally:
            # Restore pyproject.toml
            shutil.move(str(temp_pyproject), str(pyproject_path))

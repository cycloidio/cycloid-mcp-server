"""Pytest configuration and fixtures."""

import os
from unittest.mock import patch

import pytest


@pytest.fixture(autouse=True)
def mock_environment_variables():
    """Mock environment variables for all tests."""
    with patch.dict(
        os.environ,
        {
            "CY_ORG": "test-org",
            "CY_API_KEY": "test-api-key",
            "CY_API_URL": "https://test-api.cycloid.io",
            "CY_CLI_PATH": "/usr/local/bin/cy",
        },
    ):
        yield


@pytest.fixture
def mock_cli_mixin():
    """Mock CLI mixin for testing."""
    from unittest.mock import AsyncMock, MagicMock

    mock_mixin = MagicMock()
    mock_mixin.execute_cli_json = AsyncMock()
    mock_mixin.execute_cli_command = AsyncMock()

    return mock_mixin

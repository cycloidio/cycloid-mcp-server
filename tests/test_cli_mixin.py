"""Tests for CLI mixin functionality."""

import asyncio
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest

from src.cli_mixin import CLIMixin


class TestCLIMixin:
    """Test CLI mixin functionality."""

    def test_cli_mixin_initialization(self):
        """Test that CLI mixin can be initialized."""
        mixin = CLIMixin()
        assert hasattr(mixin, "execute_cli_command")
        assert hasattr(mixin, "execute_cli_json")
        assert hasattr(mixin, "config")

    @patch("asyncio.create_subprocess_exec")
    async def test_cli_command_execution_success(self, mock_subprocess: Any):
        """Test successful CLI command execution."""
        # Mock successful subprocess execution
        mock_process = AsyncMock()
        mock_process.communicate.return_value = (b'{"result": "success"}', b"")
        mock_process.returncode = 0
        mock_subprocess.return_value = mock_process

        mixin = CLIMixin()
        with patch.object(mixin, "config") as mock_config:
            mock_config.organization = "test-org"
            mock_config.api_key = "test-key"
            mock_config.api_url = "https://test-api.cycloid.io"
            mock_config.cli_path = "/usr/local/bin/cy"

            result = await mixin.execute_cli_json("test", ["command"])
            assert result == {"result": "success"}

    @patch("asyncio.create_subprocess_exec")
    async def test_cli_command_execution_error(self, mock_subprocess: Any):
        """Test CLI command execution with error."""
        # Mock failed subprocess execution
        mock_process = AsyncMock()
        mock_process.communicate.return_value = (b"", b"Error: command not found")
        mock_process.returncode = 1
        mock_subprocess.return_value = mock_process

        mixin = CLIMixin()
        with patch.object(mixin, "config") as mock_config:
            mock_config.organization = "test-org"
            mock_config.api_key = "test-key"
            mock_config.api_url = "https://test-api.cycloid.io"
            mock_config.cli_path = "/usr/local/bin/cy"

            with pytest.raises(Exception):
                _ = await mixin.execute_cli_json("test", ["command"])

    @patch("asyncio.create_subprocess_exec")
    async def test_cli_command_execution_timeout(self, mock_subprocess: Any):
        """Test CLI command execution timeout."""
        # Mock subprocess that hangs
        mock_process = AsyncMock()
        mock_process.communicate.side_effect = asyncio.TimeoutError()
        mock_subprocess.return_value = mock_process

        mixin = CLIMixin()
        with patch.object(mixin, "config") as mock_config:
            mock_config.organization = "test-org"
            mock_config.api_key = "test-key"
            mock_config.api_url = "https://test-api.cycloid.io"
            mock_config.cli_path = "/usr/local/bin/cy"

            with pytest.raises(Exception):  # Should raise CycloidCLIError
                _ = await mixin.execute_cli_json("test", ["command"])

    @patch("asyncio.create_subprocess_exec")
    async def test_cli_command_with_flags(self, mock_subprocess: Any):
        """Test CLI command execution with various flags."""
        # Mock successful subprocess execution
        mock_process = AsyncMock()
        mock_process.communicate.return_value = (b'{"result": "success"}', b"")
        mock_process.returncode = 0
        mock_subprocess.return_value = mock_process

        mixin = CLIMixin()
        with patch.object(mixin, "config") as mock_config:
            mock_config.organization = "test-org"
            mock_config.api_key = "test-key"
            mock_config.api_url = "https://test-api.cycloid.io"
            mock_config.cli_path = "/usr/local/bin/cy"

            # Test with boolean flags
            _ = await mixin.execute_cli_json(
                "test", ["command"], flags={"verbose": True, "quiet": False}
            )

            # Test with value flags
            _ = await mixin.execute_cli_json(
                "test", ["command"], flags={"name": "test-name", "type": "test-type"}
            )

    @patch("asyncio.create_subprocess_exec")
    async def test_cli_command_environment_variables(self, mock_subprocess: Any):
        """Test that environment variables are properly set."""
        # Mock successful subprocess execution
        mock_process = AsyncMock()
        mock_process.communicate.return_value = (b'{"result": "success"}', b"")
        mock_process.returncode = 0
        mock_subprocess.return_value = mock_process

        mixin = CLIMixin()
        with patch.object(mixin, "config") as mock_config:
            mock_config.organization = "test-org"
            mock_config.api_key = "test-key"
            mock_config.api_url = "https://test-api.cycloid.io"
            mock_config.cli_path = "/usr/local/bin/cy"

            _ = await mixin.execute_cli_json("test", ["command"])

            # Verify that subprocess was called with correct environment
            mock_subprocess.assert_called_once()
            call_args = mock_subprocess.call_args
            env = call_args[1]["env"]

            assert env["CY_ORG"] == "test-org"
            assert env["CY_API_KEY"] == "test-key"
            assert env["CY_API_URL"] == "https://test-api.cycloid.io"

    @patch("asyncio.create_subprocess_exec")
    async def test_cli_command_output_formats(self, mock_subprocess: Any):
        """Test CLI command execution with different output formats."""
        # Mock successful subprocess execution
        mock_process = AsyncMock()
        mock_process.communicate.return_value = (b'{"result": "success"}', b"")
        mock_process.returncode = 0
        mock_subprocess.return_value = mock_process

        mixin = CLIMixin()
        with patch.object(mixin, "config") as mock_config:
            mock_config.organization = "test-org"
            mock_config.api_key = "test-key"
            mock_config.api_url = "https://test-api.cycloid.io"
            mock_config.cli_path = "/usr/local/bin/cy"

            # Test JSON output
            result = await mixin.execute_cli_json("test", ["command"])
            assert result == {"result": "success"}

            # Test raw output - this returns a CLIResult object, not a string
            result = await mixin.execute_cli_command("test", ["command"])
            assert hasattr(result, "stdout")
            assert result.stdout == '{"result": "success"}'

    def test_cli_mixin_config_integration(self):
        """Test that CLI mixin properly integrates with configuration."""
        mixin = CLIMixin()
        assert hasattr(mixin, "config")
        assert mixin.config is not None


if __name__ == "__main__":
    _ = pytest.main([__file__, "-v"])

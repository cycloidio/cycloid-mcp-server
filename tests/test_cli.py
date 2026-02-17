"""Tests for CLI mixin functionality."""

import asyncio
from typing import Dict
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.cli import CLIMixin


class TestCLIMixin:
    """Test CLI mixin functionality."""

    def test_cli_mixin_initialization(self) -> None:
        """Test that CLI mixin can be initialized."""
        mixin: CLIMixin = CLIMixin()
        assert hasattr(mixin, "execute_cli_command")
        assert hasattr(mixin, "execute_cli")
        assert hasattr(mixin, "config")

    @patch("asyncio.create_subprocess_exec")
    @patch.object(CLIMixin, '_extract_auth_headers')
    async def test_cli_command_execution_success(
        self, mock_extract_headers: MagicMock, mock_subprocess: MagicMock
    ) -> None:
        """Test successful CLI command execution."""
        mock_extract_headers.return_value = ("test-org", "test-api-key")

        mock_process: AsyncMock = AsyncMock()
        mock_process.communicate.return_value = (b'{"result": "success"}', b"")
        mock_process.returncode = 0
        mock_subprocess.return_value = mock_process

        mixin: CLIMixin = CLIMixin()
        with patch.object(mixin, "config") as mock_config:
            mock_config.api_url = "https://test-api.cycloid.io"
            mock_config.cli_path = "/usr/local/bin/cy"

            result: Dict[str, str] = await mixin.execute_cli("test", ["command"])
            assert result == {"result": "success"}

    @patch("asyncio.create_subprocess_exec")
    async def test_cli_command_execution_error(self, mock_subprocess: MagicMock) -> None:
        """Test CLI command execution with error."""
        mock_process: AsyncMock = AsyncMock()
        mock_process.communicate.return_value = (b"", b"Error: command not found")
        mock_process.returncode = 1
        mock_subprocess.return_value = mock_process

        mixin: CLIMixin = CLIMixin()
        with patch.object(mixin, "config") as mock_config:
            mock_config.api_url = "https://test-api.cycloid.io"
            mock_config.cli_path = "/usr/local/bin/cy"

            with pytest.raises(Exception):
                _ = await mixin.execute_cli("test", ["command"])

    @patch("asyncio.create_subprocess_exec")
    async def test_cli_command_execution_timeout(self, mock_subprocess: MagicMock) -> None:
        """Test CLI command execution timeout."""
        mock_process: AsyncMock = AsyncMock()
        mock_process.communicate.side_effect = asyncio.TimeoutError()
        mock_subprocess.return_value = mock_process

        mixin: CLIMixin = CLIMixin()
        with patch.object(mixin, "config") as mock_config:
            mock_config.api_url = "https://test-api.cycloid.io"
            mock_config.cli_path = "/usr/local/bin/cy"

            with pytest.raises(Exception):
                _ = await mixin.execute_cli("test", ["command"])

    @patch("asyncio.create_subprocess_exec")
    @patch.object(CLIMixin, '_extract_auth_headers')
    async def test_cli_command_with_flags(
        self, mock_extract_headers: MagicMock, mock_subprocess: MagicMock
    ) -> None:
        """Test CLI command execution with various flags."""
        mock_extract_headers.return_value = ("test-org", "test-api-key")

        mock_process: AsyncMock = AsyncMock()
        mock_process.communicate.return_value = (b'{"result": "success"}', b"")
        mock_process.returncode = 0
        mock_subprocess.return_value = mock_process

        mixin: CLIMixin = CLIMixin()
        with patch.object(mixin, "config") as mock_config:
            mock_config.api_url = "https://test-api.cycloid.io"
            mock_config.cli_path = "/usr/local/bin/cy"

            # Test with boolean flags
            _ = await mixin.execute_cli(
                "test", ["command"], flags={"verbose": True, "quiet": False}
            )

            # Test with value flags
            _ = await mixin.execute_cli(
                "test", ["command"], flags={"name": "test-name", "type": "test-type"}
            )

    @patch("asyncio.create_subprocess_exec")
    @patch.object(CLIMixin, '_extract_auth_headers')
    async def test_cli_command_environment_variables(
        self, mock_extract_headers: MagicMock, mock_subprocess: MagicMock
    ) -> None:
        """Test that environment variables are properly set."""
        mock_extract_headers.return_value = ("test-org", "test-api-key")

        mock_process: AsyncMock = AsyncMock()
        mock_process.communicate.return_value = (b'{"result": "success"}', b"")
        mock_process.returncode = 0
        mock_subprocess.return_value = mock_process

        mixin: CLIMixin = CLIMixin()
        with patch.object(mixin, "config") as mock_config:
            mock_config.api_url = "https://test-api.cycloid.io"
            mock_config.cli_path = "/usr/local/bin/cy"

            _ = await mixin.execute_cli("test", ["command"])

            mock_subprocess.assert_called_once()
            call_args = mock_subprocess.call_args
            env = call_args[1]["env"]

            assert env["CY_ORG"] == "test-org"
            assert env["CY_API_KEY"] == "test-api-key"
            assert env["CY_API_URL"] == "https://test-api.cycloid.io"

    @patch("asyncio.create_subprocess_exec")
    @patch.object(CLIMixin, '_extract_auth_headers')
    async def test_cli_command_always_json(
        self, mock_extract_headers: MagicMock, mock_subprocess: MagicMock
    ) -> None:
        """Test that CLI always uses JSON output format."""
        mock_extract_headers.return_value = ("test-org", "test-api-key")

        mock_process: AsyncMock = AsyncMock()
        mock_process.communicate.return_value = (b'{"result": "success"}', b"")
        mock_process.returncode = 0
        mock_subprocess.return_value = mock_process

        mixin: CLIMixin = CLIMixin()
        with patch.object(mixin, "config") as mock_config:
            mock_config.api_url = "https://test-api.cycloid.io"
            mock_config.cli_path = "/usr/local/bin/cy"

            _ = await mixin.execute_cli("test", ["command"])

            # Verify --output json was passed
            call_args = mock_subprocess.call_args
            cmd = call_args[0]
            assert "--output" in cmd
            output_idx = cmd.index("--output")
            assert cmd[output_idx + 1] == "json"

    def test_cli_mixin_config_integration(self) -> None:
        """Test that CLI mixin properly integrates with configuration."""
        mixin: CLIMixin = CLIMixin()
        assert hasattr(mixin, "config")
        assert mixin.config is not None

    def test_build_command_always_json(self) -> None:
        """Test that _build_command always appends --output json."""
        mixin: CLIMixin = CLIMixin()
        cmd = mixin._build_command("test", ["list"])
        assert "--output" in cmd
        assert cmd[cmd.index("--output") + 1] == "json"


if __name__ == "__main__":
    _ = pytest.main([__file__, "-v"])

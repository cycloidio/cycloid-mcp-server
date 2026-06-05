"""Tests for CLI mixin functionality."""

import asyncio
from typing import Dict
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.cli import CLIMixin
from src.exceptions import CycloidCLIError


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


class TestCLILoggingObservability:
    """Tests verifying that failure reasons surface in log messages (WS2.1)."""

    @patch("src.cli.logger")
    @patch("asyncio.create_subprocess_exec")
    @patch.object(CLIMixin, "_extract_auth_headers")
    async def test_failed_command_log_contains_stderr(
        self,
        mock_extract_headers: MagicMock,
        mock_subprocess: MagicMock,
        mock_logger: MagicMock,
    ) -> None:
        """Failed CLI command: log message must contain the stderr reason."""
        mock_extract_headers.return_value = ("test-org", "test-api-key")

        mock_process: AsyncMock = AsyncMock()
        mock_process.communicate.return_value = (
            b"",
            b"Error: API authentication failed: invalid token",
        )
        mock_process.returncode = 1
        mock_subprocess.return_value = mock_process

        mixin: CLIMixin = CLIMixin()
        with patch.object(mixin, "config") as mock_config:
            mock_config.api_url = "https://test-api.cycloid.io"
            mock_config.cli_path = "/usr/local/bin/cy"

            with pytest.raises(CycloidCLIError):
                await mixin.execute_cli_command("test", ["command"])

        # The visible log message must contain the stderr text, not just extra={}
        mock_logger.error.assert_called_once()
        logged_message: str = mock_logger.error.call_args[0][0]
        assert "API authentication failed: invalid token" in logged_message
        assert "exit 1" in logged_message

    @patch("src.cli.logger")
    @patch("asyncio.create_subprocess_exec")
    @patch.object(CLIMixin, "_extract_auth_headers")
    async def test_failed_command_log_extra_dict_preserved(
        self,
        mock_extract_headers: MagicMock,
        mock_subprocess: MagicMock,
        mock_logger: MagicMock,
    ) -> None:
        """Failed CLI command: extra dict must still carry command/exit_code/stderr."""
        mock_extract_headers.return_value = ("test-org", "test-api-key")

        mock_process: AsyncMock = AsyncMock()
        mock_process.communicate.return_value = (b"", b"some stderr reason")
        mock_process.returncode = 2
        mock_subprocess.return_value = mock_process

        mixin: CLIMixin = CLIMixin()
        with patch.object(mixin, "config") as mock_config:
            mock_config.api_url = "https://test-api.cycloid.io"
            mock_config.cli_path = "/usr/local/bin/cy"

            with pytest.raises(CycloidCLIError):
                await mixin.execute_cli_command("test", ["command"])

        mock_logger.error.assert_called_once()
        call_kwargs = mock_logger.error.call_args[1]
        extra = call_kwargs.get("extra", {})
        assert extra.get("exit_code") == 2
        assert "some stderr reason" in extra.get("stderr", "")
        assert "command" in extra

    @patch("src.cli.logger")
    @patch("asyncio.create_subprocess_exec")
    @patch.object(CLIMixin, "_extract_auth_headers")
    async def test_timeout_log_contains_command(
        self,
        mock_extract_headers: MagicMock,
        mock_subprocess: MagicMock,
        mock_logger: MagicMock,
    ) -> None:
        """Timeout: log message must name the timed-out command."""
        mock_extract_headers.return_value = ("test-org", "test-api-key")

        mock_process: AsyncMock = AsyncMock()
        mock_process.communicate.side_effect = asyncio.TimeoutError()
        mock_subprocess.return_value = mock_process

        mixin: CLIMixin = CLIMixin()
        with patch.object(mixin, "config") as mock_config:
            mock_config.api_url = "https://test-api.cycloid.io"
            mock_config.cli_path = "/usr/local/bin/cy"

            with pytest.raises(CycloidCLIError):
                await mixin.execute_cli_command("test", ["command"], timeout=5)

        mock_logger.error.assert_called_once()
        logged_message: str = mock_logger.error.call_args[0][0]
        assert "timed out" in logged_message
        assert "5s" in logged_message

    @patch("src.cli.logger")
    @patch("asyncio.create_subprocess_exec")
    @patch.object(CLIMixin, "_extract_auth_headers")
    async def test_general_exception_log_contains_error_type_and_message(
        self,
        mock_extract_headers: MagicMock,
        mock_subprocess: MagicMock,
        mock_logger: MagicMock,
    ) -> None:
        """General exception: log message must contain exception type and reason."""
        mock_extract_headers.return_value = ("test-org", "test-api-key")

        mock_process: AsyncMock = AsyncMock()
        mock_process.communicate.side_effect = OSError("broken pipe in subprocess")
        mock_subprocess.return_value = mock_process

        mixin: CLIMixin = CLIMixin()
        with patch.object(mixin, "config") as mock_config:
            mock_config.api_url = "https://test-api.cycloid.io"
            mock_config.cli_path = "/usr/local/bin/cy"

            with pytest.raises(CycloidCLIError):
                await mixin.execute_cli_command("test", ["command"])

        mock_logger.error.assert_called_once()
        logged_message: str = mock_logger.error.call_args[0][0]
        assert "OSError" in logged_message
        assert "broken pipe in subprocess" in logged_message

    @patch("src.cli.logger")
    @patch("asyncio.create_subprocess_exec")
    @patch.object(CLIMixin, "_extract_auth_headers")
    async def test_stderr_clipped_at_500_chars(
        self,
        mock_extract_headers: MagicMock,
        mock_subprocess: MagicMock,
        mock_logger: MagicMock,
    ) -> None:
        """Stderr must be clipped to 500 chars in the visible log message."""
        mock_extract_headers.return_value = ("test-org", "test-api-key")

        long_stderr = b"E: " + b"x" * 600
        mock_process: AsyncMock = AsyncMock()
        mock_process.communicate.return_value = (b"", long_stderr)
        mock_process.returncode = 1
        mock_subprocess.return_value = mock_process

        mixin: CLIMixin = CLIMixin()
        with patch.object(mixin, "config") as mock_config:
            mock_config.api_url = "https://test-api.cycloid.io"
            mock_config.cli_path = "/usr/local/bin/cy"

            with pytest.raises(CycloidCLIError):
                await mixin.execute_cli_command("test", ["command"])

        logged_message: str = mock_logger.error.call_args[0][0]
        # Message itself must not exceed 500 chars of stderr content
        # (prefix "CLI command failed (exit 1): " + up to 500 chars of stderr)
        assert len(logged_message) < 600


if __name__ == "__main__":
    _ = pytest.main([__file__, "-v"])

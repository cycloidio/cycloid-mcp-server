"""Tests for HTTP CLI mixin module."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from src.http_cli_mixin import HTTPCLIMixin, extract_headers


class TestExtractHeaders:
    """Test extract_headers function."""

    def test_extract_headers_success(self):
        """Test successful header extraction."""
        headers = {
            "X-CY-ORG": "test-org",
            "X-CY-API-KEY": "test-api-key",
            "other-header": "other-value"
        }

        org, api_key = extract_headers(headers)

        assert org == "test-org"
        assert api_key == "test-api-key"

    def test_extract_headers_case_sensitive(self):
        """Test header extraction is case sensitive."""
        headers = {
            "x-cy-org": "test-org",
            "x-cy-api-key": "test-api-key"
        }

        with pytest.raises(HTTPException) as exc_info:
            extract_headers(headers)

        assert exc_info.value.status_code == 400
        assert "X-CY-ORG" in str(exc_info.value.detail)

    def test_extract_headers_missing_org(self):
        """Test error when X-CY-ORG header is missing."""
        headers = {
            "X-CY-API-KEY": "test-api-key"
        }

        with pytest.raises(HTTPException) as exc_info:
            extract_headers(headers)

        assert exc_info.value.status_code == 400
        assert "X-CY-ORG" in str(exc_info.value.detail)

    def test_extract_headers_missing_api_key(self):
        """Test error when X-CY-API-KEY header is missing."""
        headers = {
            "X-CY-ORG": "test-org"
        }

        with pytest.raises(HTTPException) as exc_info:
            extract_headers(headers)

        assert exc_info.value.status_code == 400
        assert "X-CY-API-KEY" in str(exc_info.value.detail)

    def test_extract_headers_both_missing(self):
        """Test error when both headers are missing."""
        headers = {
            "other-header": "other-value"
        }

        with pytest.raises(HTTPException) as exc_info:
            extract_headers(headers)

        assert exc_info.value.status_code == 400
        assert "X-CY-ORG" in str(exc_info.value.detail)

    def test_extract_headers_empty_values(self):
        """Test error when headers have empty values."""
        headers = {
            "X-CY-ORG": "",
            "X-CY-API-KEY": ""
        }

        with pytest.raises(HTTPException) as exc_info:
            extract_headers(headers)

        assert exc_info.value.status_code == 400


class TestHTTPCLIMixin:
    """Test HTTPCLIMixin class."""

    @pytest.fixture
    def mock_http_config(self):
        """Mock HTTP configuration."""
        config = MagicMock()
        config.cli_path = "/usr/local/bin/cy"
        config.api_url = "https://http-api.cycloid.io"
        return config

    @pytest.fixture
    def http_cli_mixin(self, mock_http_config):
        """Create HTTPCLIMixin instance with mocked config."""
        with patch('src.http_cli_mixin.get_http_config', return_value=mock_http_config):
            return HTTPCLIMixin()

    def test_initialization(self, mock_http_config):
        """Test HTTPCLIMixin initialization."""
        with patch('src.http_cli_mixin.get_http_config', return_value=mock_http_config):
            mixin = HTTPCLIMixin()

            assert mixin.config == mock_http_config

    def test_build_command(self, http_cli_mixin):
        """Test command building."""
        cmd = http_cli_mixin._build_command(
            "test-command",
            args=["arg1", "arg2"],
            flags={"flag1": "value1", "flag2": True},
            output_format="json"
        )

        expected = [
            "/usr/local/bin/cy",
            "test-command",
            "arg1",
            "arg2",
            "--flag1", "value1",
            "--flag2",
            "--output", "json"
        ]

        assert cmd == expected

    def test_build_environment(self, http_cli_mixin):
        """Test environment building."""
        env = http_cli_mixin._build_environment("test-org", "test-key")

        expected = {
            "CY_ORG": "test-org",
            "CY_API_KEY": "test-key",
            "CY_API_URL": "https://http-api.cycloid.io"
        }

        assert env == expected

    @pytest.mark.asyncio
    async def test_execute_command_success(self, http_cli_mixin):
        """Test successful command execution."""
        with patch('asyncio.create_subprocess_exec') as mock_subprocess:
            # Mock successful subprocess
            mock_process = MagicMock()
            mock_process.returncode = 0
            mock_process.communicate = AsyncMock(return_value=(b"success", b""))
            mock_subprocess.return_value = mock_process

            stdout, stderr, return_code = await http_cli_mixin._execute_command(
                ["cy", "test"], "test-org", "test-key", 30
            )

            assert stdout == b"success"
            assert stderr == b""
            assert return_code == 0

            # Verify subprocess was created with correct environment
            mock_subprocess.assert_called_once()
            call_args = mock_subprocess.call_args
            assert call_args[1]["env"]["CY_ORG"] == "test-org"
            assert call_args[1]["env"]["CY_API_KEY"] == "test-key"

    @pytest.mark.asyncio
    async def test_execute_command_timeout(self, http_cli_mixin):
        """Test command execution timeout."""
        with patch('asyncio.create_subprocess_exec') as mock_subprocess:
            with patch('asyncio.wait_for', side_effect=asyncio.TimeoutError()):
                mock_process = MagicMock()
                mock_subprocess.return_value = mock_process

                with pytest.raises(asyncio.TimeoutError):
                    await http_cli_mixin._execute_command(
                        ["cy", "test"], "test-org", "test-key", 1
                    )

    @pytest.mark.asyncio
    async def test_execute_cli_command_success(self, http_cli_mixin):
        """Test successful CLI command execution."""
        with patch.object(http_cli_mixin, '_execute_command') as mock_execute:
            mock_execute.return_value = (b'{"result": "success"}', b'', 0)

            result = await http_cli_mixin.execute_cli_command(
                "test-command",
                "test-org",
                "test-key",
                args=["arg1"],
                flags={"flag1": "value1"},
                output_format="json",
                timeout=30,
                auto_parse=True
            )

            assert result == {"result": "success"}
            mock_execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_cli_command_failure(self, http_cli_mixin):
        """Test CLI command execution failure."""
        with patch.object(http_cli_mixin, '_execute_command') as mock_execute:
            mock_execute.return_value = (b'', b'Error occurred', 1)

            with pytest.raises(HTTPException) as exc_info:
                await http_cli_mixin.execute_cli_command(
                    "test-command", "test-org", "test-key"
                )

            # The HTTPException is caught and re-raised as a 500 error
            assert exc_info.value.status_code == 500
            assert "CLI command failed: Error occurred" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_execute_cli_command_timeout(self, http_cli_mixin):
        """Test CLI command execution timeout."""
        with patch.object(http_cli_mixin, '_execute_command') as mock_execute:
            mock_execute.side_effect = asyncio.TimeoutError()

            with pytest.raises(HTTPException) as exc_info:
                await http_cli_mixin.execute_cli_command(
                    "test-command", "test-org", "test-key", timeout=1
                )

            assert exc_info.value.status_code == 408
            assert "timed out" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_execute_cli_command_json_parse_error(self, http_cli_mixin):
        """Test CLI command with invalid JSON output."""
        with patch.object(http_cli_mixin, '_execute_command') as mock_execute:
            mock_execute.return_value = (b'invalid json', b'', 0)

            result = await http_cli_mixin.execute_cli_command(
                "test-command", "test-org", "test-key", auto_parse=True
            )

            # Should return CLIResult when JSON parsing fails
            assert hasattr(result, 'stdout')
            assert result.stdout == 'invalid json'

    @pytest.mark.asyncio
    async def test_execute_cli_command_general_exception(self, http_cli_mixin):
        """Test CLI command with general exception."""
        with patch.object(http_cli_mixin, '_execute_command') as mock_execute:
            mock_execute.side_effect = Exception("General error")

            with pytest.raises(HTTPException) as exc_info:
                await http_cli_mixin.execute_cli_command(
                    "test-command", "test-org", "test-key"
                )

            assert exc_info.value.status_code == 500
            assert "General error" in str(exc_info.value.detail)

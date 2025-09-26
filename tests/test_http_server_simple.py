"""Tests for HTTP server functionality in server.py."""

import os
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from server import extract_headers, create_mcp_server, main


class TestExtractHeaders:
    """Test extract_headers function from server.py."""

    def test_extract_headers_success(self):
        """Test successful header extraction."""
        headers = {
            "X-CY-ORG": "test-org",
            "X-CY-API-KEY": "test-api-key"
        }

        org, api_key = extract_headers(headers)

        assert org == "test-org"
        assert api_key == "test-api-key"

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

    def test_extract_headers_empty_values(self):
        """Test error when headers have empty values."""
        headers = {
            "X-CY-ORG": "",
            "X-CY-API-KEY": ""
        }

        with pytest.raises(HTTPException) as exc_info:
            extract_headers(headers)

        assert exc_info.value.status_code == 400


class TestCreateMCPServer:
    """Test create_mcp_server function."""

    def test_create_stdio_server(self):
        """Test creating STDIO MCP server."""
        mcp, cli_mixin = create_mcp_server("stdio")

        assert mcp is not None
        assert cli_mixin is not None
        # Check that it's not HTTPCLIMixin
        assert cli_mixin.__class__.__name__ != "HTTPCLIMixin"

    def test_create_http_server(self):
        """Test creating HTTP MCP server."""
        mcp, cli_mixin = create_mcp_server("http")

        assert mcp is not None
        assert cli_mixin is not None
        # Check that it's HTTPCLIMixin
        assert cli_mixin.__class__.__name__ == "HTTPCLIMixin"

    def test_create_invalid_transport(self):
        """Test creating server with invalid transport defaults to STDIO."""
        mcp, cli_mixin = create_mcp_server("invalid")

        assert mcp is not None
        assert cli_mixin is not None
        # Should default to CLIMixin for invalid transport
        assert cli_mixin.__class__.__name__ != "HTTPCLIMixin"


class TestMainFunction:
    """Test main function."""

    @patch('server.run_stdio_server')
    def test_main_stdio_transport(self, mock_run_stdio):
        """Test main function with STDIO transport."""
        with patch.dict(os.environ, {"TRANSPORT": "stdio"}):
            main()

            mock_run_stdio.assert_called_once()

    @patch('server.run_http_server')
    def test_main_http_transport(self, mock_run_http):
        """Test main function with HTTP transport."""
        with patch.dict(os.environ, {"TRANSPORT": "http"}):
            main()

            mock_run_http.assert_called_once()

    @patch('server.run_stdio_server')
    def test_main_default_transport(self, mock_run_stdio):
        """Test main function with default transport."""
        with patch.dict(os.environ, {}, clear=True):
            main()

            mock_run_stdio.assert_called_once()

    def test_main_invalid_transport(self):
        """Test main function with invalid transport exits with error."""
        with patch.dict(os.environ, {"TRANSPORT": "invalid"}):
            with pytest.raises(SystemExit) as exc_info:
                main()

            # Should exit with code 1 for invalid transport
            assert exc_info.value.code == 1

    @patch('server.logger')
    def test_main_logging(self, mock_logger):
        """Test main function logging."""
        with patch.dict(os.environ, {"TRANSPORT": "http"}):
            with patch('server.run_http_server'):
                main()

                # Verify transport was logged
                log_calls = [call[0][0] for call in mock_logger.info.call_args_list]
                assert any("http" in call for call in log_calls)


class TestHTTPCLIMixinFromServer:
    """Test HTTPCLIMixin class from server.py."""

    def test_http_cli_mixin_initialization(self):
        """Test HTTPCLIMixin initialization."""
        from server import HTTPCLIMixin

        # The HTTPCLIMixin loads its own config, so we need to mock the import
        with patch('src.http_config.get_http_config') as mock_get_config:
            mock_config = MagicMock()
            mock_config.cli_path = "/usr/local/bin/cy"
            mock_get_config.return_value = mock_config

            mixin = HTTPCLIMixin()

            assert mixin.config == mock_config
            assert mixin._current_org is None
            assert mixin._current_api_key is None

    def test_http_cli_mixin_set_request_context(self):
        """Test setting request context."""
        from server import HTTPCLIMixin

        with patch('server.get_http_config'):
            mixin = HTTPCLIMixin()
            mixin.set_request_context("test-org", "test-key")

            assert mixin._current_org == "test-org"
            assert mixin._current_api_key == "test-key"

    def test_http_cli_mixin_inheritance(self):
        """Test that HTTPCLIMixin inherits from CLIMixin."""
        from server import HTTPCLIMixin
        from src.cli_mixin import CLIMixin

        with patch('server.get_http_config'):
            mixin = HTTPCLIMixin()

            assert isinstance(mixin, CLIMixin)
            assert hasattr(mixin, 'execute_cli_command')
            assert hasattr(mixin, 'set_request_context')
            assert hasattr(mixin, 'execute_cli')

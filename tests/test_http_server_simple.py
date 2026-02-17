"""Tests for HTTP server functionality in server.py."""

from unittest.mock import MagicMock, patch

import pytest

from server import create_mcp_server, create_http_app


class TestCreateMCPServer:
    """Test create_mcp_server function."""

    def test_create_server(self):
        """Test creating MCP server."""
        mcp = create_mcp_server()
        assert mcp is not None


class TestCreateHTTPApp:
    """Test create_http_app function."""

    @patch('server.get_http_config')
    def test_create_http_app(self, mock_get_config):
        """Test creating HTTP application."""
        mock_config = MagicMock()
        mock_config.host = "0.0.0.0"
        mock_config.port = 8000
        mock_config.cli_path = "/usr/local/bin/cy"
        mock_config.api_url = "https://http-api.cycloid.io"
        mock_get_config.return_value = mock_config

        http_app, config = create_http_app()

        assert http_app is not None
        assert config == mock_config

    @patch('server.get_http_config')
    def test_http_app_has_routes(self, mock_get_config):
        """Test that HTTP app has routes."""
        mock_config = MagicMock()
        mock_config.host = "0.0.0.0"
        mock_config.port = 8000
        mock_config.cli_path = "/usr/local/bin/cy"
        mock_config.api_url = "https://http-api.cycloid.io"
        mock_get_config.return_value = mock_config

        http_app, config = create_http_app()

        assert hasattr(http_app, 'routes')


class TestMainFunction:
    """Test main function."""

    @patch('server.create_http_app')
    @patch('uvicorn.run')
    def test_main_function(self, mock_uvicorn_run, mock_create_http_app):
        """Test main function starts HTTP server."""
        mock_app = MagicMock()
        mock_config = MagicMock()
        mock_config.host = "0.0.0.0"
        mock_config.port = 8000
        mock_create_http_app.return_value = (mock_app, mock_config)

        from server import main
        main()

        mock_create_http_app.assert_called_once()

        mock_uvicorn_run.assert_called_once_with(
            mock_app,
            host="0.0.0.0",
            port=8000,
            log_level="info",
        )


class TestCLIMixinHeaderExtraction:
    """Test CLIMixin header extraction functionality."""

    def test_extract_headers_success(self):
        """Test successful header extraction."""
        from src.cli import CLIMixin

        with patch('src.cli.get_http_headers') as mock_get_headers:
            mock_get_headers.return_value = {
                "x-cy-org": "test-org",
                "x-cy-api-key": "test-api-key"
            }

            with patch('src.cli.get_http_config'):
                mixin = CLIMixin()
                org, api_key = mixin._extract_auth_headers()

                assert org == "test-org"
                assert api_key == "test-api-key"

    def test_extract_headers_missing_org(self):
        """Test error when X-CY-ORG header is missing."""
        from src.cli import CLIMixin

        with patch('src.cli.get_http_headers') as mock_get_headers:
            mock_get_headers.return_value = {
                "x-cy-api-key": "test-api-key"
            }

            with patch('src.cli.get_http_config'):
                mixin = CLIMixin()

                with pytest.raises(ValueError) as exc_info:
                    mixin._extract_auth_headers()

                assert "X-CY-ORG" in str(exc_info.value)

    def test_extract_headers_missing_api_key(self):
        """Test error when X-CY-API-KEY header is missing."""
        from src.cli import CLIMixin

        with patch('src.cli.get_http_headers') as mock_get_headers:
            mock_get_headers.return_value = {
                "x-cy-org": "test-org"
            }

            with patch('src.cli.get_http_config'):
                mixin = CLIMixin()

                with pytest.raises(ValueError) as exc_info:
                    mixin._extract_auth_headers()

                assert "X-CY-API-KEY" in str(exc_info.value)

    def test_build_environment_with_headers(self):
        """Test building environment with headers."""
        from src.cli import CLIMixin

        with patch('src.cli.get_http_config') as mock_get_config:
            mock_config = MagicMock()
            mock_config.api_url = "https://http-api.cycloid.io"
            mock_get_config.return_value = mock_config

            mixin = CLIMixin()
            env = mixin._build_environment("test-org", "test-api-key")

            assert env["CY_ORG"] == "test-org"
            assert env["CY_API_KEY"] == "test-api-key"
            assert env["CY_API_URL"] == "https://http-api.cycloid.io"

    def test_build_environment_with_provided_params(self):
        """Test building environment with provided parameters."""
        from src.cli import CLIMixin

        with patch('src.cli.get_http_config') as mock_get_config:
            mock_config = MagicMock()
            mock_config.api_url = "https://http-api.cycloid.io"
            mock_get_config.return_value = mock_config

            mixin = CLIMixin()
            env = mixin._build_environment("provided-org", "provided-key")

            assert env["CY_ORG"] == "provided-org"
            assert env["CY_API_KEY"] == "provided-key"
            assert env["CY_API_URL"] == "https://http-api.cycloid.io"

"""Tests for HTTP configuration module."""

import os
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from src.config import HTTPCycloidConfig, get_http_config


class TestHTTPCycloidConfig:
    """Test HTTPCycloidConfig model."""

    def test_default_values(self):
        """Test default configuration values."""
        config = HTTPCycloidConfig()

        assert config.cli_path == "/usr/local/bin/cy"
        assert config.api_url == "https://http-api.cycloid.io"
        assert config.host == "0.0.0.0"
        assert config.port == 8000

    def test_custom_values(self):
        """Test custom configuration values."""
        config = HTTPCycloidConfig(
            cli_path="/custom/path/cy",
            api_url="https://custom-api.cycloid.io",
            host="127.0.0.1",
            port=9000
        )

        assert config.cli_path == "/custom/path/cy"
        assert config.api_url == "https://custom-api.cycloid.io"
        assert config.host == "127.0.0.1"
        assert config.port == 9000

    def test_port_validation(self):
        """Test port validation."""
        config = HTTPCycloidConfig(port=8080)
        assert config.port == 8080

        with pytest.raises(ValidationError):
            HTTPCycloidConfig(port=0)

        with pytest.raises(ValidationError):
            HTTPCycloidConfig(port=65536)

    def test_cli_path_validation(self):
        """Test CLI path validation."""
        config = HTTPCycloidConfig(cli_path="/usr/bin/cy")
        assert config.cli_path == "/usr/bin/cy"

        with pytest.raises(ValidationError):
            HTTPCycloidConfig(cli_path="")

    def test_api_url_validation(self):
        """Test API URL validation."""
        config = HTTPCycloidConfig(api_url="https://api.example.com")
        assert config.api_url == "https://api.example.com"

        config = HTTPCycloidConfig(api_url="https://api.example.com/")
        assert config.api_url == "https://api.example.com"

        with pytest.raises(ValueError):
            HTTPCycloidConfig(api_url="")

        with pytest.raises(ValueError):
            HTTPCycloidConfig(api_url="   ")

    def test_env_prefix_loading(self):
        """Test that env_prefix is configured."""
        config = HTTPCycloidConfig()
        assert config.cli_path == "/usr/local/bin/cy"
        assert config.api_url == "https://http-api.cycloid.io"
        assert config.host == "0.0.0.0"
        assert config.port == 8000


class TestGetHTTPConfig:
    """Test get_http_config function."""

    def test_load_http_config_defaults(self):
        """Test loading HTTP config with default values."""
        with patch.dict(os.environ, {}, clear=True):
            with patch('src.config.load_dotenv_if_exists'):
                config = get_http_config()

                assert config.cli_path == "/usr/local/bin/cy"
                assert config.api_url == "https://http-api.cycloid.io"
                assert config.host == "0.0.0.0"
                assert config.port == 8000

    def test_load_http_config_with_http_prefix(self):
        """Test loading HTTP config with CY_HTTP_ prefix."""
        env_vars = {
            "CY_HTTP_CLI_PATH": "/http/path/cy",
            "CY_HTTP_API_URL": "https://http-api.cycloid.io",
            "CY_HTTP_HOST": "0.0.0.0",
            "CY_HTTP_PORT": "8000",
        }

        with patch.dict(os.environ, env_vars):
            with patch('src.config.load_dotenv_if_exists'):
                config = get_http_config()

                assert config.cli_path == "/http/path/cy"
                assert config.api_url == "https://http-api.cycloid.io"
                assert config.host == "0.0.0.0"
                assert config.port == 8000

    def test_load_http_config_fallback_to_cy_prefix(self):
        """Test loading HTTP config with fallback to CY_ prefix."""
        env_vars = {
            "CY_CLI_PATH": "/fallback/path/cy",
            "CY_API_URL": "https://fallback-api.cycloid.io",
        }

        with patch.dict(os.environ, env_vars):
            with patch('src.config.load_dotenv_if_exists'):
                config = get_http_config()

                assert config.cli_path == "/fallback/path/cy"
                assert config.api_url == "https://fallback-api.cycloid.io"
                assert config.host == "0.0.0.0"
                assert config.port == 8000

    def test_load_http_config_http_prefix_takes_precedence(self):
        """Test that CY_HTTP_ prefix takes precedence over CY_ prefix."""
        env_vars = {
            "CY_HTTP_CLI_PATH": "/http/path/cy",
            "CY_CLI_PATH": "/cy/path/cy",
            "CY_HTTP_API_URL": "https://http-api.cycloid.io",
            "CY_API_URL": "https://cy-api.cycloid.io",
        }

        with patch.dict(os.environ, env_vars):
            with patch('src.config.load_dotenv_if_exists'):
                config = get_http_config()

                assert config.cli_path == "/http/path/cy"
                assert config.api_url == "https://http-api.cycloid.io"

    def test_load_http_config_invalid_port(self):
        """Test loading HTTP config with invalid port."""
        env_vars = {
            "CY_HTTP_PORT": "invalid"
        }

        with patch.dict(os.environ, env_vars):
            with patch('src.config.load_dotenv_if_exists'):
                with pytest.raises(ValueError):
                    get_http_config()

    def test_load_http_config_with_dotenv(self):
        """Test that load_dotenv_if_exists is called."""
        with patch('src.config.load_dotenv_if_exists') as mock_load_dotenv:
            get_http_config()
            mock_load_dotenv.assert_called_once()

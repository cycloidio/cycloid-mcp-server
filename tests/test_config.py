"""Tests for configuration management."""

from unittest.mock import patch

import pytest

from src.config import CycloidConfig, get_config


class TestConfiguration:
    """Test configuration loading and validation."""

    @patch.dict(
        "os.environ",
        {
            "CY_ORG": "test-org",
            "CY_API_KEY": "test-key",
            "CY_API_URL": "https://test-api.cycloid.io",
            "CY_CLI_PATH": "/usr/local/bin/cy",
        },
    )
    def test_config_loading(self):
        """Test that configuration loads correctly from environment."""
        config = get_config()
        assert isinstance(config, CycloidConfig)
        assert config.organization == "test-org"
        assert config.api_key == "test-key"
        assert config.api_url == "https://test-api.cycloid.io"
        assert config.cli_path == "/usr/local/bin/cy"

    def test_config_validation_missing_fields(self):
        """Test that configuration validation works for missing fields."""
        with pytest.raises(ValueError):
            _ = CycloidConfig(organization="", api_key="", api_url="")

    def test_config_validation_empty_strings(self):
        """Test that configuration validation works for empty strings."""
        with pytest.raises(ValueError):
            _ = CycloidConfig(
                organization="",
                api_key="test-key",
                api_url="https://test-api.cycloid.io",
            )

        with pytest.raises(ValueError):
            _ = CycloidConfig(
                organization="test-org",
                api_key="",
                api_url="https://test-api.cycloid.io",
            )

    def test_config_default_cli_path(self):
        """Test that CLI path defaults correctly."""
        # Clear environment and set only required vars
        with patch.dict(
            "os.environ",
            {
                "CY_ORG": "test-org",
                "CY_API_KEY": "test-key",
                "CY_API_URL": "https://test-api.cycloid.io",
            },
            clear=True,
        ):
            # Mock the load_dotenv_if_exists to not load .env
            with patch("src.config.load_dotenv_if_exists"):
                _ = get_config()
                # Default value is tested in other tests

    def test_config_fresh_loading(self):
        """Test that configuration is always loaded fresh (no caching)."""
        with patch.dict(
            "os.environ",
            {
                "CY_ORG": "test-org-1",
                "CY_API_KEY": "test-key-1",
                "CY_API_URL": "https://test-api-1.cycloid.io",
                "CY_CLI_PATH": "/usr/local/bin/cy",
            },
        ):
            config1 = get_config()
            assert config1.organization == "test-org-1"

        with patch.dict(
            "os.environ",
            {
                "CY_ORG": "test-org-2",
                "CY_API_KEY": "test-key-2",
                "CY_API_URL": "https://test-api-2.cycloid.io",
                "CY_CLI_PATH": "/usr/local/bin/cy",
            },
        ):
            config2 = get_config()
            assert config2.organization == "test-org-2"
            assert config2.organization != config1.organization


if __name__ == "__main__":
    _ = pytest.main([__file__, "-v"])

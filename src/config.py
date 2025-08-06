"""Configuration management for Cycloid MCP Server."""

import os
from functools import lru_cache
from pathlib import Path

from fastmcp.utilities.logging import get_logger
from pydantic import BaseModel, ConfigDict, Field, field_validator

logger = get_logger(__name__)


class CycloidConfig(BaseModel):
    """Configuration for Cycloid CLI integration."""

    model_config = ConfigDict(
        env_prefix="CY_", case_sensitive=False
    )  # type: ignore[reportCallIssue]

    organization: str = Field(..., description="Cycloid organization name")
    api_url: str = Field(
        default="https://http-api.cycloid.io",
        description="Cycloid API URL",
    )
    api_key: str = Field(..., description="Cycloid API key")
    cli_path: str = Field(
        default="cy",
        description="Path to Cycloid CLI binary",
    )

    @field_validator("organization")
    @classmethod
    def validate_organization(cls, v: str) -> str:
        """Validate organization name."""
        if not v or not v.strip():
            raise ValueError("Organization name cannot be empty")
        return v.strip()

    @field_validator("api_key")
    @classmethod
    def validate_api_key(cls, v: str) -> str:
        """Validate API key."""
        if not v or not v.strip():
            raise ValueError("API key cannot be empty")
        return v.strip()

    @field_validator("api_url")
    @classmethod
    def validate_api_url(cls, v: str) -> str:
        """Validate API URL."""
        if not v or not v.strip():
            raise ValueError("API URL cannot be empty")
        return v.strip().rstrip("/")


@lru_cache(maxsize=1)
def _find_env_file() -> Path | None:
    """
    Find .env file in current directory or parent directories.

    NOTE: This cache is safe because file system structure rarely changes
    during runtime. This is NOT suitable for dynamic API data.
    """
    current_dir = Path.cwd()

    # Check current directory first
    env_file = current_dir / ".env"
    if env_file.exists():
        return env_file

    # Check parent directories
    for parent in current_dir.parents:
        env_file = parent / ".env"
        if env_file.exists():
            return env_file

    return None


def load_dotenv_if_exists():
    """Load .env file if it exists."""
    try:
        from dotenv import load_dotenv

        env_file = _find_env_file()
        if env_file:
            _ = load_dotenv(env_file)
            logger.info(
                "Loaded environment variables from .env file",
                extra={"path": str(env_file)},
            )
    except ImportError:
        logger.warning("python-dotenv not installed, skipping .env file loading")
    except Exception as e:
        logger.warning("Failed to load .env file", extra={"error": str(e)})


def load_config() -> CycloidConfig:
    """Load configuration from environment variables."""
    # Try to load .env file first
    load_dotenv_if_exists()

    try:
        return CycloidConfig(
            organization=os.environ["CY_ORG"],
            api_key=os.environ["CY_API_KEY"],
            api_url=os.environ.get("CY_API_URL", "https://api.cycloid.io"),
            cli_path=os.environ.get("CY_CLI_PATH", "cy"),
        )
    except KeyError as e:
        missing_var = str(e).strip("'")
        logger.error(
            "Missing required environment variable",
            extra={
                "variable": missing_var,
                "available_vars": [k for k in os.environ.keys() if k.startswith("CY_")],
            },
        )
        raise ValueError(
            f"Missing required environment variable: {missing_var}. Please set CY_ORG, CY_API_KEY, and optionally CY_API_URL. You can create a .env file with these variables."  # noqa: E501
        ) from e


def get_config() -> CycloidConfig:
    """Get the current configuration instance."""
    # Always load fresh config - no caching during development
    return load_config()

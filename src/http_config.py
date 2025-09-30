"""HTTP-specific configuration management for Cycloid MCP Server."""

import os
from functools import lru_cache
from pathlib import Path

from fastmcp.utilities.logging import get_logger
from pydantic import BaseModel, ConfigDict, Field, field_validator

logger = get_logger(__name__)


class HTTPCycloidConfig(BaseModel):
    """HTTP-specific configuration for Cycloid CLI integration."""

    model_config = ConfigDict(
        env_prefix="CY_HTTP_", case_sensitive=False
    )  # type: ignore[reportCallIssue]

    cli_path: str = Field(
        default="/usr/local/bin/cy",
        description="Path to Cycloid CLI binary",
    )
    api_url: str = Field(
        default="https://http-api.cycloid.io",
        description="Cycloid API URL",
    )
    host: str = Field(
        default="0.0.0.0",
        description="Host to bind the HTTP server",
    )
    port: int = Field(
        default=8000,
        description="Port to bind the HTTP server",
    )

    @field_validator("cli_path")
    @classmethod
    def validate_cli_path(cls, v: str) -> str:
        """Validate CLI path."""
        if not v or not v.strip():
            raise ValueError("CLI path cannot be empty")
        return v.strip()

    @field_validator("api_url")
    @classmethod
    def validate_api_url(cls, v: str) -> str:
        """Validate API URL."""
        if not v or not v.strip():
            raise ValueError("API URL cannot be empty")
        return v.strip().rstrip("/")

    @field_validator("port")
    @classmethod
    def validate_port(cls, v: int) -> int:
        """Validate port number."""
        if not (1 <= v <= 65535):
            raise ValueError("Port must be between 1 and 65535")
        return v


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


def load_http_config() -> HTTPCycloidConfig:
    """Load HTTP configuration from environment variables."""
    # Try to load .env file first
    load_dotenv_if_exists()

    try:
        return HTTPCycloidConfig(
            cli_path=os.environ.get(
                "CY_HTTP_CLI_PATH", os.environ.get("CY_CLI_PATH", "/usr/local/bin/cy")
            ),
            api_url=os.environ.get(
                "CY_HTTP_API_URL", os.environ.get("CY_API_URL", "https://http-api.cycloid.io")
            ),
            host=os.environ.get("CY_HTTP_HOST", "0.0.0.0"),
            port=int(os.environ.get("CY_HTTP_PORT", "8000")),
        )
    except ValueError as e:
        logger.error(
            "Invalid HTTP configuration",
            extra={"error": str(e)},
        )
        raise


def get_http_config() -> HTTPCycloidConfig:
    """Get the current HTTP configuration instance."""
    # Always load fresh config - no caching during development
    return load_http_config()

"""HTTP-aware CLI mixin for Cycloid MCP Server."""

import asyncio
import json
from typing import Any, Dict, List, Optional, Union

from fastapi import HTTPException
from fastmcp.utilities.logging import get_logger
from pydantic import BaseModel

from src.http_config import get_http_config

logger = get_logger(__name__)


class CLIResult(BaseModel):
    """Result from CLI command execution."""

    stdout: str
    stderr: str
    return_code: int
    command: str


class HTTPCLIMixin:
    """HTTP-aware mixin providing Cycloid CLI execution functionality."""

    def __init__(self):  # type: ignore[reportMissingSuperCall]
        """Initialize the HTTP CLI mixin."""
        self.config = get_http_config()

    def _build_command(
        self,
        subcommand: str,
        args: Optional[List[str]] = None,
        flags: Optional[Dict[str, Union[str, bool]]] = None,
        output_format: str = "json",
    ) -> List[str]:
        """Build command for CLI execution."""
        args = args or []
        flags = flags or {}

        cmd_parts = [self.config.cli_path, subcommand] + args

        # Add flags
        for flag_name, flag_value in flags.items():
            if isinstance(flag_value, bool) and flag_value:
                cmd_parts.append(f"--{flag_name}")
            elif not isinstance(flag_value, bool):
                cmd_parts.extend([f"--{flag_name}", str(flag_value)])

        # Add output format
        cmd_parts.extend(["--output", output_format])
        return cmd_parts

    def _build_environment(self, organization: str, api_key: str) -> Dict[str, str]:
        """Build environment variables for CLI execution."""
        return {
            "CY_ORG": organization,
            "CY_API_KEY": api_key,
            "CY_API_URL": self.config.api_url,
        }

    async def _execute_command(
        self, cmd_parts: List[str], organization: str, api_key: str, timeout: int
    ) -> tuple[bytes, bytes, int]:
        """Execute the CLI process and return results."""
        env = self._build_environment(organization, api_key)

        process = await asyncio.create_subprocess_exec(
            *cmd_parts,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )

        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)

        return (
            stdout,
            stderr,
            process.returncode if process.returncode is not None else -1,
        )

    async def execute_cli_command(
        self,
        subcommand: str,
        organization: str,
        api_key: str,
        args: Optional[List[str]] = None,
        flags: Optional[Dict[str, Union[str, bool]]] = None,
        output_format: str = "json",
        timeout: int = 30,
        auto_parse: bool = False,
    ) -> Union[CLIResult, Dict[str, Any], str]:
        """
        Execute a CLI command with organization and API key from headers.

        Args:
            subcommand: The CLI subcommand to execute
            organization: Organization name from X-CY-ORG header
            api_key: API key from X-CY-API-KEY header
            args: Command arguments
            flags: Command flags
            output_format: Output format (default: json)
            timeout: Command timeout in seconds
            auto_parse: Whether to automatically parse JSON output

        Returns:
            CLIResult, parsed JSON, or raw string output
        """
        cmd_parts = self._build_command(subcommand, args, flags, output_format)

        logger.info(
            "Executing CLI command",
            extra={
                "command": " ".join(cmd_parts),
                "organization": organization,
                "subcommand": subcommand,
            },
        )

        try:
            stdout, stderr, return_code = await self._execute_command(
                cmd_parts, organization, api_key, timeout
            )

            stdout_str = stdout.decode("utf-8")
            stderr_str = stderr.decode("utf-8")

            result = CLIResult(
                stdout=stdout_str,
                stderr=stderr_str,
                return_code=return_code,
                command=" ".join(cmd_parts),
            )

            if return_code != 0:
                logger.error(
                    "CLI command failed",
                    extra={
                        "command": result.command,
                        "return_code": return_code,
                        "stderr": stderr_str,
                    },
                )
                raise HTTPException(
                    status_code=400,
                    detail=f"CLI command failed: {stderr_str or 'Unknown error'}",
                )

            if auto_parse and output_format == "json":
                try:
                    return json.loads(stdout_str)
                except json.JSONDecodeError as e:
                    logger.warning(
                        "Failed to parse JSON output",
                        extra={"error": str(e), "output": stdout_str},
                    )
                    return result

            return result

        except asyncio.TimeoutError:
            logger.error(
                "CLI command timed out",
                extra={"command": " ".join(cmd_parts), "timeout": timeout},
            )
            raise HTTPException(
                status_code=408,
                detail=f"CLI command timed out after {timeout} seconds",
            )
        except Exception as e:
            logger.error(
                "Unexpected error executing CLI command",
                extra={"command": " ".join(cmd_parts), "error": str(e)},
            )
            raise HTTPException(
                status_code=500,
                detail=f"Internal server error: {str(e)}",
            )


def extract_headers(request_headers: Dict[str, str]) -> tuple[str, str]:
    """
    Extract organization and API key from request headers.

    Args:
        request_headers: Dictionary of request headers

    Returns:
        Tuple of (organization, api_key)

    Raises:
        HTTPException: If required headers are missing
    """
    organization = request_headers.get("X-CY-ORG")
    api_key = request_headers.get("X-CY-API-KEY")

    if not organization:
        raise HTTPException(
            status_code=400,
            detail="Missing required header: X-CY-ORG",
        )

    if not api_key:
        raise HTTPException(
            status_code=400,
            detail="Missing required header: X-CY-API-KEY",
        )

    return organization, api_key

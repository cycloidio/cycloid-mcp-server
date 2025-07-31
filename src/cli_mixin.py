"""CLI mixin for Cycloid CLI execution."""

import asyncio
import json
import shlex
from typing import Any, Dict, List, Optional, Union

import structlog
from pydantic import BaseModel

from .config import get_config
from .exceptions import CycloidCLIError

logger = structlog.get_logger(__name__)


class CLIResult(BaseModel):
    """Result of CLI command execution."""

    success: bool
    stdout: str
    stderr: str
    exit_code: int
    command: str


class CLIMixin:
    """Mixin providing Cycloid CLI execution functionality."""

    def __init__(self):
        """Initialize the CLI mixin."""
        self.config = get_config()

    async def execute_cli_command(
        self,
        subcommand: str,
        args: Optional[List[str]] = None,
        flags: Optional[Dict[str, Union[str, bool]]] = None,
        output_format: str = "json",
        timeout: int = 30,
    ) -> CLIResult:
        """
        Execute a Cycloid CLI command asynchronously.

        Args:
            subcommand: The CLI subcommand (e.g., 'stack', 'catalog')
            args: List of positional arguments
            flags: Dictionary of flag names and values
            output_format: Output format ('json', 'table', 'yaml')
            timeout: Command timeout in seconds

        Returns:
            CLIResult with execution details

        Raises:
            CycloidCLIError: If command execution fails
        """
        if args is None:
            args = []
        if flags is None:
            flags = {}

        # Build command
        cmd_parts = [self.config.cli_path, subcommand] + args

        # Add flags
        for flag_name, flag_value in flags.items():
            if isinstance(flag_value, bool):
                if flag_value:
                    cmd_parts.append(f"--{flag_name}")
            else:
                cmd_parts.extend([f"--{flag_name}", str(flag_value)])

        # Add output format
        cmd_parts.extend(["--output", output_format])

        command = " ".join(shlex.quote(part) for part in cmd_parts)

        logger.debug(
            "Executing Cycloid CLI command",
            command=command,
            subcommand=subcommand,
            args=args,
            flags=flags,
        )

        # Set environment variables
        env = {
            "CY_ORG": self.config.organization,
            "CY_API_KEY": self.config.api_key,
            "CY_API_URL": self.config.api_url,
        }

        try:
            # Build command arguments
            cmd_args = [self.config.cli_path, subcommand] + args
            
            # Add boolean flags
            for k, v in flags.items():
                if isinstance(v, bool) and v:
                    cmd_args.append(f"--{k}")
            
            # Add value flags
            for k, v in flags.items():
                if not isinstance(v, bool):
                    cmd_args.extend([f"--{k}", str(v)])
            
            # Add output format
            cmd_args.extend(["--output", output_format])
            
            # Execute command
            process = await asyncio.create_subprocess_exec(
                *cmd_args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
            )

            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=timeout
            )

            result = CLIResult(
                success=process.returncode == 0,
                stdout=stdout.decode("utf-8").strip(),
                stderr=stderr.decode("utf-8").strip(),
                exit_code=process.returncode,
                command=command,
            )

            if not result.success:
                logger.error(
                    "CLI command failed",
                    command=command,
                    exit_code=result.exit_code,
                    stderr=result.stderr,
                )
                raise CycloidCLIError(
                    f"CLI command failed: {result.stderr}",
                    command=command,
                    exit_code=result.exit_code,
                    stderr=result.stderr,
                )

            logger.debug(
                "CLI command executed successfully",
                command=command,
                stdout_length=len(result.stdout),
            )

            return result

        except asyncio.TimeoutError:
            logger.error("CLI command timed out", command=command, timeout=timeout)
            raise CycloidCLIError(
                f"CLI command timed out after {timeout} seconds",
                command=command,
                exit_code=-1,
                stderr="Command timed out",
            )
        except Exception as e:
            logger.error("CLI command execution error", command=command, error=str(e))
            raise CycloidCLIError(
                f"CLI command execution error: {str(e)}",
                command=command,
                exit_code=-1,
                stderr=str(e),
            )

    async def execute_cli_json(
        self,
        subcommand: str,
        args: Optional[List[str]] = None,
        flags: Optional[Dict[str, Union[str, bool]]] = None,
        timeout: int = 30,
    ) -> Dict[str, Any]:
        """
        Execute a Cycloid CLI command and return parsed JSON output.

        Args:
            subcommand: The CLI subcommand
            args: List of positional arguments
            flags: Dictionary of flag names and values
            timeout: Command timeout in seconds

        Returns:
            Parsed JSON response as dictionary

        Raises:
            CycloidCLIError: If command execution fails or JSON parsing fails
        """
        result = await self.execute_cli_command(
            subcommand, args, flags, "json", timeout
        )

        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError as e:
            logger.error(
                "Failed to parse CLI JSON output",
                stdout=result.stdout,
                error=str(e),
            )
            raise CycloidCLIError(
                f"Failed to parse CLI JSON output: {str(e)}",
                command=result.command,
                exit_code=result.exit_code,
                stderr=result.stderr,
            )

    async def execute_cli_table(
        self,
        subcommand: str,
        args: Optional[List[str]] = None,
        flags: Optional[Dict[str, Union[str, bool]]] = None,
        timeout: int = 30,
    ) -> str:
        """
        Execute a Cycloid CLI command and return table output.

        Args:
            subcommand: The CLI subcommand
            args: List of positional arguments
            flags: Dictionary of flag names and values
            timeout: Command timeout in seconds

        Returns:
            Table formatted output as string

        Raises:
            CycloidCLIError: If command execution fails
        """
        result = await self.execute_cli_command(
            subcommand, args, flags, "table", timeout
        )
        return result.stdout 
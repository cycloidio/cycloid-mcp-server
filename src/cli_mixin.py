"""CLI mixin for Cycloid CLI execution."""

import asyncio
import json
import shlex
from typing import Any, Dict, List, Optional, Union

from fastmcp.utilities.logging import get_logger
from pydantic import BaseModel

from .config import get_config
from .exceptions import CycloidCLIError

logger = get_logger(__name__)


class CLIResult(BaseModel):
    """Result of CLI command execution."""

    success: bool
    stdout: str
    stderr: str
    exit_code: int
    command: str


class CLIMixin:
    """Mixin providing Cycloid CLI execution functionality."""

    def __init__(self):  # type: ignore[reportMissingSuperCall]
        """Initialize the CLI mixin."""
        self.config = get_config()

    def _build_command_parts(
        self,
        subcommand: str,
        args: List[str],
        flags: Dict[str, Union[str, bool]],
        output_format: str,
    ) -> List[str]:
        """Build command parts for CLI execution."""
        cmd_parts = [self.config.cli_path, subcommand] + args

        # Add boolean flags
        for flag_name, flag_value in flags.items():
            if isinstance(flag_value, bool) and flag_value:
                cmd_parts.append(f"--{flag_name}")

        # Add value flags
        for flag_name, flag_value in flags.items():
            if not isinstance(flag_value, bool):
                cmd_parts.extend([f"--{flag_name}", str(flag_value)])

        # Add output format
        cmd_parts.extend(["--output", output_format])

        return cmd_parts

    def _build_environment(self) -> Dict[str, str]:
        """Build environment variables for CLI execution."""
        return {
            "CY_ORG": self.config.organization,
            "CY_API_KEY": self.config.api_key,
            "CY_API_URL": self.config.api_url,
        }

    def _log_debug_info(self, command: str, env: Dict[str, str]) -> None:
        """Log debug information for CLI execution."""
        # DEBUG: Print all CY_ env variables
        debug_env = {k: v for k, v in env.items() if k.startswith("CY_")}
        logger.info(
            "[DEBUG] CLI execution environment",
            extra={
                "cy_env": debug_env,
                "timestamp": asyncio.get_event_loop().time(),
            },
        )

        # DEBUG: Print system info
        import os
        logger.info(
            "[DEBUG] System context",
            extra={
                "cwd": os.getcwd(),
                "user": os.environ.get("USER", "unknown"),
                "hostname": os.environ.get("HOSTNAME", "unknown"),
                "path": (
                    os.environ.get("PATH", "unknown")[:200] + "..."
                    if len(os.environ.get("PATH", "")) > 200
                    else os.environ.get("PATH", "unknown")
                ),
            },
        )

    async def _execute_process(
        self, cmd_args: List[str], env: Dict[str, str], timeout: int
    ) -> tuple[bytes, bytes, int]:
        """Execute the CLI process and return results."""
        process = await asyncio.create_subprocess_exec(
            *cmd_args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )

        logger.info(
            "[DEBUG] CLI command execution",
            extra={
                "cmd_args": cmd_args,
                "process_pid": process.pid,
                "env_keys": list(env.keys()),
            },
        )

        stdout, stderr = await asyncio.wait_for(
            process.communicate(), timeout=timeout
        )

        return stdout, stderr, process.returncode if process.returncode is not None else -1

    def _log_command_output(self, stdout: bytes, stderr: bytes) -> None:
        """Log command output for debugging."""
        logger.info(
            "[DEBUG] CLI command raw output",
            extra={
                "stdout_length": len(stdout),
                "stderr_length": len(stderr),
                "stdout_preview": (
                    stdout.decode("utf-8")[:500] + "..."
                    if len(stdout) > 500
                    else stdout.decode("utf-8")
                ),
                "stderr_preview": (
                    stderr.decode("utf-8")[:500] + "..."
                    if len(stderr) > 500
                    else stderr.decode("utf-8")
                ),
            },
        )

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
        cmd_parts = self._build_command_parts(subcommand, args, flags, output_format)
        command = " ".join(shlex.quote(part) for part in cmd_parts)

        logger.debug(
            "Executing Cycloid CLI command",
            command=command,
            subcommand=subcommand,
            args=args,
            flags=flags,
        )

        # Set environment variables
        env = self._build_environment()
        self._log_debug_info(command, env)

        try:
            # Execute command
            stdout, stderr, exit_code = await self._execute_process(
                cmd_parts, env, timeout
            )
            self._log_command_output(stdout, stderr)

            result = CLIResult(
                success=exit_code == 0,
                stdout=stdout.decode("utf-8").strip(),
                stderr=stderr.decode("utf-8").strip(),
                exit_code=exit_code,
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
            logger.error("CLI command timed out", extra={"command": command, "timeout": timeout})
            raise CycloidCLIError(
                f"CLI command timed out after {timeout} seconds",
                command=command,
                exit_code=-1,
                stderr="Command timed out",
            )
        except Exception as e:
            logger.error("CLI command execution error", extra={"command": command, "error": str(e)})
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

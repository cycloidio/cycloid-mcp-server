"""CLI mixin for Cycloid CLI execution."""

import asyncio
import json

from fastmcp.utilities.logging import get_logger
from pydantic import BaseModel

from .config import get_config
from .exceptions import CycloidCLIError
from .types import Any, Dict, List, Optional, Union

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

    def _build_environment(self) -> Dict[str, str]:
        """Build environment variables for CLI execution."""
        return {
            "CY_ORG": self.config.organization,
            "CY_API_KEY": self.config.api_key,
            "CY_API_URL": self.config.api_url,
        }

    async def _execute_command(
        self, cmd_parts: List[str], timeout: int
    ) -> tuple[bytes, bytes, int]:
        """Execute the CLI process and return results."""
        env = self._build_environment()

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
        args: Optional[List[str]] = None,
        flags: Optional[Dict[str, Union[str, bool]]] = None,
        output_format: str = "json",
        timeout: int = 30,
        auto_parse: bool = False,
    ) -> Union[CLIResult, Dict[str, Any], str]:
        """
        Execute a Cycloid CLI command asynchronously.

        Args:
            subcommand: The CLI subcommand (e.g., 'stack', 'catalog')
            args: List of positional arguments
            flags: Dictionary of flag names and values
            output_format: Output format ('json', 'table', 'yaml')
            timeout: Command timeout in seconds
            auto_parse: Whether to automatically parse JSON output

        Returns:
            CLIResult if auto_parse=False, parsed dict/str if auto_parse=True

        Raises:
            CycloidCLIError: If command execution fails
        """
        cmd_parts = self._build_command(subcommand, args, flags, output_format)
        command = " ".join(cmd_parts)

        try:
            stdout, stderr, exit_code = await self._execute_command(cmd_parts, timeout)

            result = CLIResult(
                success=exit_code == 0,
                stdout=stdout.decode() if stdout else "",
                stderr=stderr.decode() if stderr else "",
                exit_code=exit_code,
                command=command,
            )

            if not result.success:
                logger.error(
                    f"CLI command failed with exit code {exit_code}",
                    extra={
                        "command": command,
                        "exit_code": exit_code,
                        "stderr": result.stderr,
                    },
                )
                raise CycloidCLIError(
                    f"CLI command failed: {result.stderr}",
                    command=command,
                    exit_code=exit_code,
                    stderr=result.stderr,
                )

            if auto_parse:
                if output_format == "json":
                    try:
                        return json.loads(result.stdout)
                    except json.JSONDecodeError as e:
                        logger.error(
                            f"Failed to parse JSON output: {str(e)}",
                            extra={
                                "command": command,
                                "stdout": result.stdout,
                                "error": str(e),
                            },
                        )
                        raise CycloidCLIError(
                            f"Failed to parse JSON output: {str(e)}",
                            command=command,
                            exit_code=exit_code,
                            stderr=f"JSON parse error: {str(e)}",
                        )
                else:
                    return result.stdout

            return result

        except asyncio.TimeoutError:
            logger.error(
                f"CLI command timed out after {timeout} seconds",
                extra={"command": command, "timeout": timeout},
            )
            raise CycloidCLIError(
                f"CLI command timed out after {timeout} seconds",
                command=command,
                exit_code=-1,
                stderr="Command timed out",
            )
        except Exception as e:
            logger.error(
                f"CLI command execution error: {str(e)}",
                extra={"command": command, "error": str(e)},
            )
            raise CycloidCLIError(
                f"CLI command execution error: {str(e)}",
                command=command,
                exit_code=-1,
                stderr=str(e),
            )

    async def execute_cli(
        self,
        subcommand: str,
        args: Optional[List[str]] = None,
        flags: Optional[Dict[str, Union[str, bool]]] = None,
        output_format: str = "json",
        timeout: int = 30,
    ) -> Union[Dict[str, Any], List[Dict[str, Any]], str]:
        """
        Execute a Cycloid CLI command with automatic output parsing.

        Args:
            subcommand: The CLI subcommand
            args: List of positional arguments
            flags: Dictionary of flag names and values
            output_format: Output format ('json', 'table', 'yaml')
            timeout: Command timeout in seconds

        Returns:
            Parsed output - JSON dict/list for 'json' format, string for others

        Raises:
            CycloidCLIError: If command execution fails or parsing fails
        """
        result = await self.execute_cli_command(
            subcommand, args, flags, output_format, timeout, auto_parse=False
        )

        # Parse the result if it's a CLIResult
        if isinstance(result, CLIResult):
            if output_format == "json":
                try:
                    return self.parse_cli_output(result.stdout)
                except ValueError as e:
                    logger.error(
                        f"Failed to parse CLI JSON output: {str(e)}",
                        extra={
                            "command": result.command,
                            "stdout": result.stdout,
                            "error": str(e),
                        },
                    )
                    raise CycloidCLIError(
                        f"Failed to parse CLI JSON output: {str(e)}",
                        command=result.command,
                        exit_code=result.exit_code,
                        stderr=result.stderr,
                    )
            else:
                return result.stdout

        # If auto_parse was already done, return as-is
        return result

    @staticmethod
    def process_cli_response(
        data: Any,
        list_key: Optional[str] = None,
        default: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Process CLI response data with common patterns.

        Args:
            data: Raw CLI response data
            list_key: Key to extract from dict response (e.g., "service_catalogs")
            default: Default value if processing fails

        Returns:
            Processed list of dictionaries
        """
        if default is None:
            default = []

        if isinstance(data, list):
            # Type guard: ensure it's a list of dictionaries
            filtered_items = []
            for item in data:  # type: ignore[reportUnknownVariableType]
                if isinstance(item, dict):
                    filtered_items.append(item)  # type: ignore[reportUnknownArgumentType]
            return filtered_items  # type: ignore[reportUnknownVariableType]
        elif isinstance(data, dict) and list_key:
            result = data.get(list_key, default)  # type: ignore[reportUnknownMemberType]
            if isinstance(result, list):  # type: ignore[reportUnknownVariableType]
                filtered_items = []
                for item in result:  # type: ignore[reportUnknownVariableType]
                    if isinstance(item, dict):
                        filtered_items.append(item)  # type: ignore[reportUnknownArgumentType]
                return filtered_items  # type: ignore[reportUnknownVariableType]
            return default
        else:
            return default

    @staticmethod
    def parse_cli_output(
        output: Union[str, Dict[str, Any], List[Dict[str, Any]]]
    ) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Parse CLI output that may be in JSON or Python literal format.

        Args:
            output: Raw CLI output (string, dict, or list)

        Returns:
            Parsed output as dict or list

        Raises:
            ValueError: If parsing fails completely
        """
        # If already parsed, return as-is
        if isinstance(output, (dict, list)):
            return output

        # Try to parse as JSON first
        try:
            return json.loads(output)
        except json.JSONDecodeError:
            # If JSON parsing fails, try to evaluate as Python literal
            try:
                import ast
                return ast.literal_eval(output)
            except (ValueError, SyntaxError):
                # If both fail, raise an error
                raise ValueError(
                    f"Failed to parse CLI output as JSON or Python literal: {output[:100]}..."
                )

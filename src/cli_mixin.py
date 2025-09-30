"""CLI mixin for Cycloid CLI execution."""

import asyncio
import json

from fastmcp.utilities.logging import get_logger
from fastmcp.server.dependencies import get_http_headers, get_http_request
from pydantic import BaseModel

from .http_config import get_http_config
from .error_handling import error_context, get_correlation_id
from .error_monitoring import record_error
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

    def _extract_headers_from_context(self) -> tuple[str, str]:
        """Extract organization and API key from HTTP headers using FastMCP context."""
        try:
            # Use get_http_request() as the primary method (more reliable)
            request = get_http_request()
            headers = dict(request.headers)
        except Exception:
            try:
                # Fallback to get_http_headers()
                headers = get_http_headers()
            except Exception as e2:
                raise ValueError(f"Failed to extract headers: {e2}")

        organization = headers.get("X-CY-ORG")
        api_key = headers.get("X-CY-API-KEY")

        if not organization:
            raise ValueError("Missing required header: X-CY-ORG")

        if not api_key:
            raise ValueError("Missing required header: X-CY-API-KEY")

        return organization, api_key

    def _extract_auth_headers(self) -> tuple[str, str]:
        """Extract organization and API key from HTTP headers."""
        try:
            # Use get_http_request() as the primary method (more reliable)
            request = get_http_request()
            headers = dict(request.headers)
        except Exception:
            try:
                # Fallback to get_http_headers()
                headers = get_http_headers()
            except Exception as e2:
                raise ValueError(f"Failed to extract headers: {e2}")

        # Make header lookup case-insensitive
        headers_lower = {k.lower(): v for k, v in headers.items()}
        organization = headers_lower.get("x-cy-org")
        api_key = headers_lower.get("x-cy-api-key")

        if not organization:
            raise ValueError("Missing required header: X-CY-ORG")

        if not api_key:
            raise ValueError("Missing required header: X-CY-API-KEY")

        return organization, api_key

    def _build_environment(self, organization: str, api_key: str) -> Dict[str, str]:
        """Build environment variables for CLI execution."""
        # Start with the current environment and add our custom variables
        import os
        env = os.environ.copy()
        env.update({
            "CY_ORG": organization,
            "CY_API_KEY": api_key,
            "CY_API_URL": self.config.api_url,
        })

        return env

    async def _execute_command(
        self,
        cmd_parts: List[str],
        timeout: int,
        organization: Optional[str] = None,
        api_key: Optional[str] = None,
    ) -> tuple[bytes, bytes, int]:
        """Execute the CLI process and return results."""
        # Extract headers if not provided
        if not organization or not api_key:
            organization, api_key = self._extract_auth_headers()

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
        args: Optional[List[str]] = None,
        flags: Optional[Dict[str, Union[str, bool]]] = None,
        output_format: str = "json",
        timeout: int = 30,
        auto_parse: bool = False,
        organization: Optional[str] = None,
        api_key: Optional[str] = None,
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
        correlation_id = get_correlation_id()

        with error_context(f"CLI command execution: {command}", correlation_id):
            try:
                stdout, stderr, exit_code = await self._execute_command(
                    cmd_parts, timeout, organization, api_key
                )

                result = CLIResult(
                    success=exit_code == 0,
                    stdout=stdout.decode() if stdout else "",
                    stderr=stderr.decode() if stderr else "",
                    exit_code=exit_code,
                    command=command,
                )

                if not result.success:
                    cli_error = CycloidCLIError(
                        f"CLI command failed: {result.stderr}",
                        command=command,
                        exit_code=exit_code,
                        stderr=result.stderr,
                    )

                    # Record error for monitoring
                    record_error(
                        cli_error,
                        f"CLI command execution: {command}",
                        severity="error",
                        metadata={
                            "command": command,
                            "exit_code": exit_code,
                            "stderr": result.stderr,
                            "correlation_id": correlation_id,
                        },
                    )

                    logger.error(
                        f"CLI command failed with exit code {exit_code}",
                        extra={
                            "correlation_id": correlation_id,
                            "command": command,
                            "exit_code": exit_code,
                            "stderr": result.stderr,
                        },
                    )
                    raise cli_error

                if auto_parse:
                    if output_format == "json":
                        try:
                            return json.loads(result.stdout)
                        except json.JSONDecodeError as e:
                            parse_error = CycloidCLIError(
                                f"Failed to parse JSON output: {str(e)}",
                                command=command,
                                exit_code=exit_code,
                                stderr=f"JSON parse error: {str(e)}",
                            )

                            # Record error for monitoring
                            record_error(
                                parse_error,
                                f"JSON parsing for command: {command}",
                                severity="error",
                                metadata={
                                    "command": command,
                                    "stdout": result.stdout,
                                    "error": str(e),
                                    "correlation_id": correlation_id,
                                },
                            )

                            logger.error(
                                f"Failed to parse JSON output: {str(e)}",
                                extra={
                                    "correlation_id": correlation_id,
                                    "command": command,
                                    "stdout": result.stdout,
                                    "error": str(e),
                                },
                            )
                            raise parse_error
                    else:
                        return result.stdout

                return result

            except asyncio.TimeoutError:
                timeout_error = CycloidCLIError(
                    f"CLI command timed out after {timeout} seconds",
                    command=command,
                    exit_code=-1,
                    stderr="Command timed out",
                )

                # Record error for monitoring
                record_error(
                    timeout_error,
                    f"CLI command timeout: {command}",
                    severity="warning",
                    metadata={
                        "command": command,
                        "timeout": timeout,
                        "correlation_id": correlation_id,
                    },
                )

                logger.error(
                    f"CLI command timed out after {timeout} seconds",
                    extra={
                        "correlation_id": correlation_id,
                        "command": command,
                        "timeout": timeout,
                    },
                )
                raise timeout_error
            except Exception as e:
                execution_error = CycloidCLIError(
                    f"CLI command execution error: {str(e)}",
                    command=command,
                    exit_code=-1,
                    stderr=str(e),
                )

                # Record error for monitoring
                record_error(
                    execution_error,
                    f"CLI command execution: {command}",
                    severity="error",
                    metadata={
                        "command": command,
                        "error": str(e),
                        "correlation_id": correlation_id,
                    },
                )

                logger.error(
                    f"CLI command execution error: {str(e)}",
                    extra={
                        "correlation_id": correlation_id,
                        "command": command,
                        "error": str(e),
                    },
                )
                raise execution_error

    async def execute_cli(
        self,
        subcommand: str,
        args: Optional[List[str]] = None,
        flags: Optional[Dict[str, Union[str, bool]]] = None,
        output_format: str = "json",
        timeout: int = 30,
    ) -> Union[Dict[str, Any], List[Dict[str, Any]], str]:
        """
        Execute a Cycloid CLI command with automatic output parsing and header extraction.

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
        # Extract authentication headers automatically
        organization, api_key = self._extract_auth_headers()

        result = await self.execute_cli_command(
            subcommand, args, flags, output_format, timeout, auto_parse=False,
            organization=organization, api_key=api_key
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
        elif isinstance(data, str):
            # Handle string responses (usually error messages)
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

"""CLI mixin for Cycloid CLI execution."""

import asyncio
import json
import os

from fastmcp.server.dependencies import get_http_headers, get_http_request
from fastmcp.utilities.logging import get_logger
from pydantic import BaseModel

from .config import get_http_config
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

        # Always use JSON output
        cmd_parts.extend(["--output", "json"])
        return cmd_parts

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
        timeout: int = 30,
        auto_parse: bool = False,
        organization: Optional[str] = None,
        api_key: Optional[str] = None,
    ) -> Union[CLIResult, Dict[str, Any], str]:
        """Execute a Cycloid CLI command asynchronously.

        Args:
            subcommand: The CLI subcommand (e.g., 'stack', 'catalog')
            args: List of positional arguments
            flags: Dictionary of flag names and values
            timeout: Command timeout in seconds
            auto_parse: Whether to automatically parse JSON output
            organization: Optional org override
            api_key: Optional API key override

        Returns:
            CLIResult if auto_parse=False, parsed dict/str if auto_parse=True

        Raises:
            CycloidCLIError: If command execution fails
        """
        cmd_parts = self._build_command(subcommand, args, flags)
        command = " ".join(cmd_parts)

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
        except CycloidCLIError:
            raise
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
        timeout: int = 30,
    ) -> Union[Dict[str, Any], List[Dict[str, Any]], str]:
        """Execute a Cycloid CLI command with automatic output parsing.

        Args:
            subcommand: The CLI subcommand
            args: List of positional arguments
            flags: Dictionary of flag names and values
            timeout: Command timeout in seconds

        Returns:
            Parsed JSON dict/list

        Raises:
            CycloidCLIError: If command execution fails or parsing fails
        """
        organization, api_key = self._extract_auth_headers()

        result = await self.execute_cli_command(
            subcommand, args, flags, timeout, auto_parse=False,
            organization=organization, api_key=api_key
        )

        if isinstance(result, CLIResult):
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

        return result

    @staticmethod
    def process_cli_response(
        data: Any,
        list_key: Optional[str] = None,
        default: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        """Process CLI response data with common patterns.

        Args:
            data: Raw CLI response data
            list_key: Key to extract from dict response
            default: Default value if processing fails

        Returns:
            Processed list of dictionaries
        """
        if default is None:
            default = []

        if isinstance(data, list):
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
            return default
        else:
            return default

    @staticmethod
    def parse_cli_output(
        output: Union[str, Dict[str, Any], List[Dict[str, Any]]]
    ) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """Parse CLI output that may be in JSON or Python literal format.

        Args:
            output: Raw CLI output (string, dict, or list)

        Returns:
            Parsed output as dict or list

        Raises:
            ValueError: If parsing fails completely
        """
        if isinstance(output, (dict, list)):
            return output

        try:
            return json.loads(output)
        except json.JSONDecodeError:
            try:
                import ast
                return ast.literal_eval(output)
            except (ValueError, SyntaxError):
                raise ValueError(
                    f"Failed to parse CLI output as JSON or Python literal: {output[:100]}..."
                )

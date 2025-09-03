"""Event handler utilities and core logic."""

# Standard library imports
from typing import List

# Local imports
from src.base_handler import BaseHandler
from src.cli_mixin import CLIMixin
from src.error_handling import handle_errors
from src.types import JSONList, JSONDict, OptionalString, OptionalStringList


class EventHandler(BaseHandler):
    """Core event operations and utilities."""

    def __init__(self, cli: CLIMixin):
        """Initialize event handler with CLI mixin."""
        super().__init__(cli)

    @handle_errors(
        action="fetch organization events",
        suggestions=[
            "Check your Cycloid CLI configuration",
            "Verify API credentials and organization settings",
            "Adjust filters like severity or type if too restrictive",
        ],
    )
    async def list_events(
        self,
        begin: OptionalString = None,
        end: OptionalString = None,
        severity: OptionalStringList = None,
        type: OptionalStringList = None,
    ) -> JSONList:
        """List events using `cy event list` with optional filters.

        Args:
            begin: Unix timestamp (string) for the start date.
            end: Unix timestamp (string) for the end date.
            severity: List of severities (e.g., ["info","warn","err","crit"]).
            type: List of event types (e.g., ["Cycloid","AWS","Monitoring","Custom"]).

        Returns:
            List of event objects as dictionaries.
        """
        args: List[str] = ["list"]

        flags: JSONDict = {}
        if begin:
            flags["begin"] = begin
        if end:
            flags["end"] = end
        if severity:
            # CLI expects comma-separated list
            flags["severity"] = ",".join(severity)
        if type:
            flags["type"] = ",".join(type)

        events_data = await self.cli.execute_cli(
            "event", args, flags=flags, output_format="json"
        )

        return self.cli.process_cli_response(events_data, list_key=None)

"""Base handler class for common functionality across all handlers."""

from fastmcp.utilities.logging import get_logger

from .cli_mixin import CLIMixin


class BaseHandler:
    """Base handler providing common CLI functionality and logging."""

    def __init__(self, cli: CLIMixin):
        """Initialize base handler with CLI mixin."""
        super().__init__()  # Call parent class constructor
        self.cli = cli
        self.logger = get_logger(self.__class__.__module__)

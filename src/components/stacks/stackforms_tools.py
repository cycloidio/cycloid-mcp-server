"""StackForms MCP tools."""

from fastmcp.contrib.mcp_mixin import MCPMixin, mcp_tool
from fastmcp.utilities.logging import get_logger

from src.cli_mixin import CLIMixin

from .stackforms_handler import StackFormsHandler

logger = get_logger(__name__)


class StackFormsTools(MCPMixin):
    """StackForms MCP tools."""

    def __init__(self, cli: CLIMixin):
        """Initialize StackForms tools with CLI mixin."""
        super().__init__()
        self.handler = StackFormsHandler(cli)

    @mcp_tool(
        name="CYCLOID_STACKFORMS_VALIDATE",
        description=(
            "Validate a StackForms (.forms.yml) file using the Cycloid CLI. "
            "This tool can validate StackForms configuration and provide detailed "
            "feedback for fixing issues."
        ),
        enabled=True,
    )
    async def validate_stackforms(self, forms_content: str) -> str:
        """Validate a StackForms (.forms.yml) file.

        This tool validates StackForms configuration and provides detailed feedback
        for fixing any issues found. It's useful for ensuring StackForms files are
        correctly formatted and follow Cycloid best practices.

        Args:
            forms_content: The content of the .forms.yml file to validate
        """
        try:
            result = await self.handler.validate_stackforms(forms_content)
            return result

        except Exception as e:
            error_msg = f"❌ StackForms validation failed: {str(e)}"
            logger.error("StackForms validation failed", extra={"error": str(e)})
            return error_msg

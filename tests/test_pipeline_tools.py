"""Tests for PipelineTools MCP tool."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.components.pipelines.pipelines_tools import PipelineTools
from src.components.pipelines.pipelines_handler import PipelineHandler
from src.cli_mixin import CLIMixin


class TestPipelineTools:
    """Test cases for PipelineTools MCP tool."""

    @pytest.fixture
    def mock_cli(self):
        """Create a mock CLI mixin."""
        cli = MagicMock(spec=CLIMixin)
        return cli

    @pytest.fixture
    def mock_handler(self):
        """Create a mock PipelineHandler."""
        handler = MagicMock(spec=PipelineHandler)
        handler.get_pipelines = AsyncMock()
        return handler

    @pytest.fixture
    def pipeline_tools(self, mock_cli):
        """Create a PipelineTools instance with mocked CLI."""
        with patch('src.components.pipelines.pipelines_tools.PipelineHandler') as mock_class:
            mock_handler_instance = MagicMock()
            mock_handler_instance.get_pipelines = AsyncMock()
            mock_class.return_value = mock_handler_instance
            tools = PipelineTools(mock_cli)
            tools.handler = mock_handler_instance
            return tools

    @pytest.mark.asyncio
    async def test_list_pipelines_summary_format_success(self, pipeline_tools):
        """Test successful pipeline listing in summary format."""
        # Arrange
        mock_pipelines = [
            {"id": 1, "name": "test-pipeline-1"},
            {"id": 2, "name": "test-pipeline-2"}
        ]
        pipeline_tools.handler.get_pipelines.return_value = mock_pipelines

        # Act
        result = await pipeline_tools.list_pipelines(format="summary")

        # Assert
        assert "🚀 Pipelines" in result
        assert "Found 2 pipelines" in result
        pipeline_tools.handler.get_pipelines.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_pipelines_json_format_success(self, pipeline_tools):
        """Test successful pipeline listing in JSON format."""
        # Arrange
        mock_pipelines = [
            {"id": 1, "name": "test-pipeline-1"},
            {"id": 2, "name": "test-pipeline-2"}
        ]
        pipeline_tools.handler.get_pipelines.return_value = mock_pipelines

        # Act
        result = await pipeline_tools.list_pipelines(format="json")

        # Assert
        assert isinstance(result, dict)
        assert "pipelines" in result
        assert "count" in result
        assert result["pipelines"] == mock_pipelines
        assert result["count"] == 2
        pipeline_tools.handler.get_pipelines.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_pipelines_hierarchy_format_success(self, pipeline_tools):
        """Test successful pipeline listing in hierarchy format (treated as summary)."""
        # Arrange
        mock_pipelines = [
            {"id": 1, "name": "test-pipeline-1"},
            {"id": 2, "name": "test-pipeline-2"}
        ]
        pipeline_tools.handler.get_pipelines.return_value = mock_pipelines

        # Act
        result = await pipeline_tools.list_pipelines(format="hierarchy")

        # Assert
        assert "🚀 Pipelines" in result
        assert "Found 2 pipelines" in result
        pipeline_tools.handler.get_pipelines.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_pipelines_default_format(self, pipeline_tools):
        """Test pipeline listing with default format (summary)."""
        # Arrange
        mock_pipelines = [{"id": 1, "name": "test-pipeline-1"}]
        pipeline_tools.handler.get_pipelines.return_value = mock_pipelines

        # Act
        result = await pipeline_tools.list_pipelines()

        # Assert
        assert "🚀 Pipelines" in result
        assert "Found 1 pipelines" in result

    @pytest.mark.asyncio
    async def test_list_pipelines_empty_result(self, pipeline_tools):
        """Test pipeline listing with empty result."""
        # Arrange
        pipeline_tools.handler.get_pipelines.return_value = []

        # Act
        result = await pipeline_tools.list_pipelines(format="summary")

        # Assert
        assert "🚀 Pipelines" in result
        assert "Found 0 pipelines" in result

    @pytest.mark.asyncio
    async def test_list_pipelines_exception_handling(self, pipeline_tools):
        """Test exception handling in pipeline listing."""
        # Arrange
        pipeline_tools.handler.get_pipelines.side_effect = Exception("Test error")

        # Act
        result = await pipeline_tools.list_pipelines(format="summary")

        # Assert
        assert "❌ Error listing pipelines" in result
        assert "Test error" in result

    def test_tools_initialization(self, mock_cli):
        """Test PipelineTools initialization."""
        # Act
        with patch('src.components.pipelines.pipelines_tools.PipelineHandler'):
            tools = PipelineTools(mock_cli)

        # Assert
        assert hasattr(tools, 'handler')

    def test_tools_inherits_from_mcp_mixin(self, mock_cli):
        """Test that PipelineTools inherits from MCPMixin."""
        # Act
        with patch('src.components.pipelines.pipelines_tools.PipelineHandler'):
            tools = PipelineTools(mock_cli)

        # Assert
        # MCPMixin should provide the mcp_tool decorator functionality
        assert hasattr(tools, 'list_pipelines')

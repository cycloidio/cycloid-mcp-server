"""Tests for PipelineResources MCP resource."""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.components.pipelines.pipelines_resources import PipelineResources
from src.components.pipelines.pipelines_handler import PipelineHandler
from src.cli_mixin import CLIMixin


class TestPipelineResources:
    """Test cases for PipelineResources MCP resource."""

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
    def pipeline_resources(self, mock_cli):
        """Create a PipelineResources instance with mocked CLI."""
        with patch('src.components.pipelines.pipelines_resources.PipelineHandler') as mock_class:
            mock_class.return_value = MagicMock()
            resources = PipelineResources(mock_cli)
            resources.handler = MagicMock()
            return resources

    @pytest.mark.asyncio
    async def test_get_pipelines_resource_success(self, pipeline_resources):
        """Test successful pipeline resource retrieval."""
        # Act
        result = await pipeline_resources.get_pipelines_resource()

        # Assert
        assert isinstance(result, str)

        # Parse the JSON result
        parsed_result = json.loads(result)
        assert "message" in parsed_result
        assert parsed_result["message"] == "Pipeline resources are working!"

    @pytest.mark.asyncio
    async def test_get_pipelines_resource_empty_pipelines(self, pipeline_resources):
        """Test pipeline resource retrieval with empty pipelines."""
        # Act
        result = await pipeline_resources.get_pipelines_resource()

        # Assert
        assert isinstance(result, str)

        # Parse the JSON result
        parsed_result = json.loads(result)
        assert "message" in parsed_result
        assert parsed_result["message"] == "Pipeline resources are working!"

    @pytest.mark.asyncio
    async def test_get_pipelines_resource_cli_error(self, pipeline_resources):
        """Test pipeline resource retrieval with CLI error."""
        # Act
        result = await pipeline_resources.get_pipelines_resource()

        # Assert
        assert isinstance(result, str)

        # Parse the JSON result
        parsed_result = json.loads(result)
        assert "message" in parsed_result
        assert parsed_result["message"] == "Pipeline resources are working!"

    @pytest.mark.asyncio
    async def test_get_pipelines_resource_general_exception(self, pipeline_resources):
        """Test pipeline resource retrieval with general exception."""
        # Act
        result = await pipeline_resources.get_pipelines_resource()

        # Assert
        assert isinstance(result, str)

        # Parse the JSON result
        parsed_result = json.loads(result)
        assert "message" in parsed_result
        assert parsed_result["message"] == "Pipeline resources are working!"

    @pytest.mark.asyncio
    async def test_get_pipelines_resource_json_formatting(self, pipeline_resources):
        """Test that the resource returns properly formatted JSON."""
        # Act
        result = await pipeline_resources.get_pipelines_resource()

        # Assert
        assert isinstance(result, str)

        # Should be valid JSON
        parsed_result = json.loads(result)
        assert isinstance(parsed_result, dict)

        # Should have proper structure
        assert "message" in parsed_result
        assert parsed_result["message"] == "Pipeline resources are working!"

    def test_resources_initialization(self, mock_cli):
        """Test PipelineResources initialization."""
        # Act
        with patch('src.components.pipelines.pipelines_resources.PipelineHandler'):
            resources = PipelineResources(mock_cli)

        # Assert
        assert hasattr(resources, 'handler')

    def test_resources_inherits_from_mcp_mixin(self, mock_cli):
        """Test that PipelineResources inherits from MCPMixin."""
        # Act
        with patch('src.components.pipelines.pipelines_resources.PipelineHandler'):
            resources = PipelineResources(mock_cli)

        # Assert
        # MCPMixin should provide the mcp_resource decorator functionality
        assert hasattr(resources, 'get_pipelines_resource')

    @pytest.mark.asyncio
    async def test_resource_returns_string(self, pipeline_resources):
        """Test that the resource method returns a string (JSON)."""
        # Act
        result = await pipeline_resources.get_pipelines_resource()

        # Assert
        assert isinstance(result, str)
        # Should be valid JSON
        json.loads(result)  # This will raise an exception if not valid JSON

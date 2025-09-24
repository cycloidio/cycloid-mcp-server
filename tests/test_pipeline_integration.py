"""Integration tests for pipeline functionality."""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock

from src.components.pipelines.pipelines_handler import PipelineHandler
from src.components.pipelines.pipelines_tools import PipelineTools
from src.components.pipelines.pipelines_resources import PipelineResources
from src.cli_mixin import CLIMixin
from src.exceptions import CycloidCLIError


class TestPipelineIntegration:
    """Integration tests for pipeline functionality."""

    @pytest.fixture
    def mock_cli(self):
        """Create a mock CLI mixin."""
        cli = MagicMock(spec=CLIMixin)
        cli.execute_cli = AsyncMock()
        cli.process_cli_response = MagicMock()
        return cli

    @pytest.fixture
    def sample_pipeline_data(self):
        """Sample pipeline data for testing."""
        return [
            {
                "id": 226,
                "name": "semvertests-staging-be",
                "status": "paused",
                "jobs": [
                    {
                        "id": 1290,
                        "name": "build",
                        "finished_build": {
                            "status": "succeeded",
                            "id": 1485
                        }
                    },
                    {
                        "id": 1294,
                        "name": "deploy",
                        "finished_build": {
                            "status": "errored",
                            "id": 2762
                        }
                    }
                ],
                "component": {
                    "project": {"name": "SemVerTests", "canonical": "semvertests"},
                    "environment": {"name": "staging-be", "canonical": "staging-be"}
                }
            },
            {
                "id": 227,
                "name": "semvertests-staging-fe",
                "status": "paused",
                "jobs": [
                    {
                        "id": 1299,
                        "name": "build",
                        "finished_build": {
                            "status": "succeeded",
                            "id": 1488
                        }
                    }
                ],
                "component": {
                    "project": {"name": "SemVerTests", "canonical": "semvertests"},
                    "environment": {"name": "staging-fe", "canonical": "staging-fe"}
                }
            }
        ]

    @pytest.mark.asyncio
    async def test_end_to_end_pipeline_listing(self, mock_cli, sample_pipeline_data):
        """Test end-to-end pipeline listing functionality."""
        # Arrange
        mock_cli.execute_cli.return_value = sample_pipeline_data
        mock_cli.process_cli_response.return_value = sample_pipeline_data

        # Create handler
        handler = PipelineHandler(mock_cli)

        # Create tools
        tools = PipelineTools(mock_cli)
        tools.handler = handler

        # Act - Test summary format
        summary_result = await tools.list_pipelines(format="summary")

        # Act - Test JSON format
        json_result = await tools.list_pipelines(format="json")

        # Assert
        assert "🚀 Pipelines" in summary_result
        assert "Found 2 pipelines" in summary_result

        assert isinstance(json_result, dict)
        assert json_result["count"] == 2
        assert len(json_result["pipelines"]) == 2
        assert json_result["pipelines"][0]["name"] == "semvertests-staging-be"

    @pytest.mark.asyncio
    async def test_end_to_end_pipeline_listing_json(self, mock_cli, sample_pipeline_data):
        """Test end-to-end pipeline listing functionality in JSON format."""
        # Arrange
        mock_cli.execute_cli.return_value = sample_pipeline_data
        mock_cli.process_cli_response.return_value = sample_pipeline_data

        # Create handler
        handler = PipelineHandler(mock_cli)

        # Create tools
        tools = PipelineTools(mock_cli)
        tools.handler = handler

        # Act
        result = await tools.list_pipelines(format="json")

        # Assert
        assert isinstance(result, dict)
        assert result["count"] == 2
        assert len(result["pipelines"]) == 2
        assert result["pipelines"][0]["name"] == "semvertests-staging-be"

    @pytest.mark.asyncio
    async def test_end_to_end_pipeline_resource(self, mock_cli, sample_pipeline_data):
        """Test end-to-end pipeline resource functionality."""
        # Create resources
        resources = PipelineResources(mock_cli)

        # Act
        result = await resources.get_pipelines_resource()

        # Assert
        assert isinstance(result, str)
        parsed_result = json.loads(result)
        assert "message" in parsed_result
        assert parsed_result["message"] == "Pipeline resources are working!"

    @pytest.mark.asyncio
    async def test_error_propagation_through_layers(self, mock_cli):
        """Test that errors propagate correctly through all layers."""
        # Arrange
        mock_cli.execute_cli.side_effect = CycloidCLIError(
            "CLI authentication failed", "pipeline list", 1
        )

        # Create handler
        handler = PipelineHandler(mock_cli)

        # Create tools
        tools = PipelineTools(mock_cli)
        tools.handler = handler

        # Create resources
        resources = PipelineResources(mock_cli)

        # Act & Assert - Handler level
        handler_result = await handler.get_pipelines()
        assert handler_result == []

        # Act & Assert - Tools level
        tools_result = await tools.list_pipelines(format="summary")
        assert "🚀 Pipelines" in tools_result
        assert "Found 0 pipelines" in tools_result

        # Act & Assert - Resources level
        resources_result = await resources.get_pipelines_resource()
        parsed_result = json.loads(resources_result)
        assert "message" in parsed_result
        assert parsed_result["message"] == "Pipeline resources are working!"

    @pytest.mark.asyncio
    async def test_empty_pipeline_data_handling(self, mock_cli):
        """Test handling of empty pipeline data across all components."""
        # Arrange
        mock_cli.execute_cli.return_value = []
        mock_cli.process_cli_response.return_value = []

        # Create handler
        handler = PipelineHandler(mock_cli)

        # Create tools
        tools = PipelineTools(mock_cli)
        tools.handler = handler

        # Create resources
        resources = PipelineResources(mock_cli)

        # Act & Assert - Handler level
        handler_result = await handler.get_pipelines()
        assert handler_result == []

        # Act & Assert - Tools level
        tools_result = await tools.list_pipelines(format="summary")
        assert "Found 0 pipelines" in tools_result

        json_result = await tools.list_pipelines(format="json")
        assert json_result["count"] == 0
        assert json_result["pipelines"] == []

        # Act & Assert - Resources level
        resources_result = await resources.get_pipelines_resource()
        parsed_result = json.loads(resources_result)
        assert "message" in parsed_result

    @pytest.mark.asyncio
    async def test_pipeline_listing_different_formats(self, mock_cli, sample_pipeline_data):
        """Test pipeline listing in different formats."""
        # Arrange
        mock_cli.execute_cli.return_value = sample_pipeline_data
        mock_cli.process_cli_response.return_value = sample_pipeline_data

        # Create handler
        handler = PipelineHandler(mock_cli)

        # Create tools
        tools = PipelineTools(mock_cli)
        tools.handler = handler

        # Act & Assert - Summary format
        summary_result = await tools.list_pipelines(format="summary")
        assert "🚀 Pipelines" in summary_result
        assert "Found 2 pipelines" in summary_result

        # Act & Assert - JSON format
        json_result = await tools.list_pipelines(format="json")
        assert isinstance(json_result, dict)
        assert "pipelines" in json_result
        assert json_result["count"] == 2

    @pytest.mark.asyncio
    async def test_different_format_types(self, mock_cli, sample_pipeline_data):
        """Test different format types in tools."""
        # Arrange
        mock_cli.execute_cli.return_value = sample_pipeline_data
        mock_cli.process_cli_response.return_value = sample_pipeline_data

        # Create handler
        handler = PipelineHandler(mock_cli)

        # Create tools
        tools = PipelineTools(mock_cli)
        tools.handler = handler

        # Act & Assert - Summary format
        summary_result = await tools.list_pipelines(format="summary")
        assert "🚀 Pipelines" in summary_result

        # Act & Assert - JSON format
        json_result = await tools.list_pipelines(format="json")
        assert isinstance(json_result, dict)
        assert "pipelines" in json_result

        # Act & Assert - Hierarchy format (treated as summary)
        hierarchy_result = await tools.list_pipelines(format="hierarchy")
        assert "🚀 Pipelines" in hierarchy_result

    @pytest.mark.asyncio
    async def test_component_initialization_and_dependencies(self, mock_cli):
        """Test that all components initialize correctly with dependencies."""
        # Act
        handler = PipelineHandler(mock_cli)
        tools = PipelineTools(mock_cli)
        resources = PipelineResources(mock_cli)

        # Assert
        assert handler.cli == mock_cli
        assert hasattr(handler, 'logger')

        assert hasattr(tools, 'handler')
        assert hasattr(tools, 'list_pipelines')

        assert hasattr(resources, 'handler')
        assert hasattr(resources, 'get_pipelines_resource')

"""Tests for PipelineHandler."""

from typing import Any, Dict, List
import pytest
from unittest.mock import AsyncMock, MagicMock

from src.components.pipelines.pipelines_handler import PipelineHandler
from src.cli_mixin import CLIMixin
from src.exceptions import CycloidCLIError


class TestPipelineHandler:
    """Test cases for PipelineHandler."""

    @pytest.fixture
    def mock_cli(self) -> MagicMock:
        """Create a mock CLI mixin."""
        cli = MagicMock(spec=CLIMixin)
        cli.execute_cli = AsyncMock()
        cli.process_cli_response = MagicMock()
        return cli

    @pytest.fixture
    def pipeline_handler(self, mock_cli: MagicMock) -> PipelineHandler:
        """Create a PipelineHandler instance with mocked CLI."""
        return PipelineHandler(mock_cli)

    @pytest.mark.asyncio
    async def test_get_pipelines_success(
        self, pipeline_handler: PipelineHandler, mock_cli: MagicMock
    ) -> None:
        """Test successful pipeline retrieval."""
        # Arrange
        mock_pipeline_data: List[Dict[str, Any]] = [
            {"id": 1, "name": "test-pipeline-1", "status": "succeeded"},
            {"id": 2, "name": "test-pipeline-2", "status": "errored"}
        ]
        mock_cli.execute_cli.return_value = mock_pipeline_data
        mock_cli.process_cli_response.return_value = mock_pipeline_data

        # Act
        result: Any = await pipeline_handler.get_pipelines()

        # Assert
        assert result == mock_pipeline_data
        mock_cli.execute_cli.assert_called_once_with(
            "pipeline", ["list"], output_format="json"
        )
        mock_cli.process_cli_response.assert_called_once_with(mock_pipeline_data)

    @pytest.mark.asyncio
    async def test_get_pipelines_cli_returns_none(
        self, pipeline_handler: PipelineHandler, mock_cli: MagicMock
    ) -> None:
        """Test handling when CLI returns None."""
        # Arrange
        mock_cli.execute_cli.return_value = None
        mock_cli.process_cli_response.return_value = None

        # Act
        result: Any = await pipeline_handler.get_pipelines()

        # Assert
        assert result is None
        mock_cli.execute_cli.assert_called_once_with(
            "pipeline", ["list"], output_format="json"
        )
        mock_cli.process_cli_response.assert_called_once_with(None)

    @pytest.mark.asyncio
    async def test_get_pipelines_processed_data_none(
        self, pipeline_handler: PipelineHandler, mock_cli: MagicMock
    ) -> None:
        """Test handling when processed data is None."""
        # Arrange
        mock_cli.execute_cli.return_value = [{"id": 1}]
        mock_cli.process_cli_response.return_value = None

        # Act
        result: Any = await pipeline_handler.get_pipelines()

        # Assert
        assert result is None

    @pytest.mark.asyncio
    async def test_get_pipelines_processed_data_not_list(
        self, pipeline_handler: PipelineHandler, mock_cli: MagicMock
    ) -> None:
        """Test handling when processed data is not a list."""
        # Arrange
        mock_cli.execute_cli.return_value = [{"id": 1}]
        mock_cli.process_cli_response.return_value = {"error": "not a list"}

        # Act
        result: Any = await pipeline_handler.get_pipelines()

        # Assert
        assert result == {"error": "not a list"}

    @pytest.mark.asyncio
    async def test_get_pipelines_cli_exception(
        self, pipeline_handler: PipelineHandler, mock_cli: MagicMock
    ) -> None:
        """Test handling CLI exceptions."""
        # Arrange
        mock_cli.execute_cli.side_effect = CycloidCLIError("CLI failed", "pipeline list", 1)

        # Act
        result: Any = await pipeline_handler.get_pipelines()

        # Assert
        assert result == []
        mock_cli.execute_cli.assert_called_once_with(
            "pipeline", ["list"], output_format="json"
        )

    @pytest.mark.asyncio
    async def test_get_pipelines_general_exception(
        self, pipeline_handler: PipelineHandler, mock_cli: MagicMock
    ) -> None:
        """Test handling general exceptions."""
        # Arrange
        mock_cli.execute_cli.side_effect = Exception("Unexpected error")

        # Act
        result: Any = await pipeline_handler.get_pipelines()

        # Assert
        assert result == []
        mock_cli.execute_cli.assert_called_once_with(
            "pipeline", ["list"], output_format="json"
        )

    def test_handler_initialization(self, mock_cli: MagicMock) -> None:
        """Test PipelineHandler initialization."""
        # Act
        handler: PipelineHandler = PipelineHandler(mock_cli)

        # Assert
        assert handler.cli == mock_cli
        assert hasattr(handler, 'logger')

    def test_handler_inherits_from_base_handler(self, mock_cli: MagicMock) -> None:
        """Test that PipelineHandler inherits from BaseHandler."""
        # Act
        handler: PipelineHandler = PipelineHandler(mock_cli)

        # Assert
        assert hasattr(handler, 'cli')
        assert hasattr(handler, 'logger')

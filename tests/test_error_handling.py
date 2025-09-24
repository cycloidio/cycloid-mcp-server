"""Tests for enhanced error handling functionality."""

import asyncio
import time
from typing import Any, Dict

import pytest

from src.error_handling import (
    CorrelationContext,
    ErrorFormatter,
    GracefulDegradation,
    RetryMechanism,
    error_context,
    get_correlation_id,
    handle_errors,
    set_correlation_id,
)
from src.error_monitoring import (
    ErrorEvent,
    ErrorMonitor,
    HealthChecker,
    check_system_health,
    get_error_monitor,
    get_health_checker,
    record_error,
)
from src.exceptions import CycloidCLIError, CycloidAPIError


class TestCorrelationContext:
    """Test correlation ID context management."""

    def test_correlation_context_creation(self) -> None:
        """Test correlation context creation."""
        with CorrelationContext() as correlation_id:
            assert correlation_id is not None
            assert len(correlation_id) == 36  # UUID length
            assert get_correlation_id() == correlation_id

    def test_correlation_context_nested(self) -> None:
        """Test nested correlation contexts."""
        with CorrelationContext("outer-id"):
            assert get_correlation_id() == "outer-id"

            with CorrelationContext("inner-id"):
                assert get_correlation_id() == "inner-id"

            assert get_correlation_id() == "outer-id"

    def test_correlation_context_manual_set(self) -> None:
        """Test manual correlation ID setting."""
        set_correlation_id("test-id")
        assert get_correlation_id() == "test-id"

    def test_error_context_manager(self) -> None:
        """Test error context manager."""
        with error_context("test action") as correlation_id:
            assert correlation_id is not None
            assert get_correlation_id() == correlation_id


class TestErrorFormatter:
    """Test error formatting functionality."""

    def test_format_error_basic(self) -> None:
        """Test basic error formatting."""
        result = ErrorFormatter.format_error("test action", "test error")
        assert "❌" in result
        assert "test action" in result
        assert "test error" in result

    def test_format_error_with_suggestions(self) -> None:
        """Test error formatting with suggestions."""
        suggestions = ["suggestion 1", "suggestion 2"]
        result = ErrorFormatter.format_error("test action", "test error", suggestions)
        assert "suggestion 1" in result
        assert "suggestion 2" in result

    def test_format_error_with_correlation_id(self) -> None:
        """Test error formatting with correlation ID."""
        with CorrelationContext("test-id"):
            result = ErrorFormatter.format_error(
                "test action", "test error", correlation_id="test-id"
            )
            assert "test-id" in result

    def test_categorize_error_cli(self) -> None:
        """Test error categorization for CLI errors."""
        cli_error = CycloidCLIError("test", "command", 1)
        category = ErrorFormatter.categorize_error(cli_error)
        assert category == "authentication"

    def test_categorize_error_api(self) -> None:
        """Test error categorization for API errors."""
        api_error = CycloidAPIError("test", 401)
        category = ErrorFormatter.categorize_error(api_error)
        assert category == "authentication"

    def test_format_cli_error(self) -> None:
        """Test CLI error formatting."""
        cli_error = CycloidCLIError("test error", "test command", 1, "stderr")
        result = ErrorFormatter.format_cli_error(cli_error)
        assert "test command" in result
        assert "Exit code 1" in result


class TestGracefulDegradation:
    """Test graceful degradation functionality."""

    def test_handle_api_failure_with_fallback(self) -> None:
        """Test API failure handling with fallback data."""
        error = CycloidAPIError("API failed", 500)
        fallback_data = {"cached": "data"}

        result = GracefulDegradation.handle_api_failure(
            error, fallback_data, "Using cached data"
        )
        assert result == fallback_data

    def test_handle_api_failure_no_fallback(self) -> None:
        """Test API failure handling without fallback."""
        error = CycloidAPIError("API failed", 500)

        with pytest.raises(CycloidAPIError):
            GracefulDegradation.handle_api_failure(error)


class TestRetryMechanism:
    """Test retry mechanism functionality."""

    def test_should_retry_api_error(self) -> None:
        """Test retry decision for API errors."""
        api_error = CycloidAPIError("test", 500)
        assert RetryMechanism.should_retry(api_error, 1, 3) is True

    def test_should_retry_rate_limit(self) -> None:
        """Test retry decision for rate limit errors."""
        api_error = CycloidAPIError("test", 429)
        assert RetryMechanism.should_retry(api_error, 1, 3) is True

    def test_should_not_retry_auth_error(self) -> None:
        """Test retry decision for auth errors."""
        api_error = CycloidAPIError("test", 401)
        assert RetryMechanism.should_retry(api_error, 1, 3) is False

    def test_should_not_retry_max_attempts(self) -> None:
        """Test retry decision when max attempts reached."""
        api_error = CycloidAPIError("test", 500)
        assert RetryMechanism.should_retry(api_error, 3, 3) is False

    def test_get_retry_delay(self) -> None:
        """Test retry delay calculation."""
        assert RetryMechanism.get_retry_delay(1) == 1.0
        assert RetryMechanism.get_retry_delay(2) == 2.0
        assert RetryMechanism.get_retry_delay(3) == 4.0


class TestHandleErrorsDecorator:
    """Test the handle_errors decorator."""

    def test_handle_errors_success(self) -> None:
        """Test successful function execution."""
        @handle_errors("test action")
        def test_func() -> str:
            return "success"

        result = test_func()
        assert result == "success"

    def test_handle_errors_exception(self) -> None:
        """Test error handling with exception."""
        @handle_errors("test action", return_on_error="error occurred")
        def test_func() -> str:
            raise ValueError("test error")

        result = test_func()
        assert "error occurred" in result

    def test_handle_errors_async(self) -> None:
        """Test async error handling."""
        @handle_errors("test action", return_on_error="async error")
        async def test_func() -> str:
            raise ValueError("async error")

        result = asyncio.run(test_func())
        assert "async error" in result

    def test_handle_errors_with_retry(self) -> None:
        """Test error handling with retry enabled."""
        call_count = 0

        @handle_errors("test action", enable_retry=True, max_retries=2)
        def test_func() -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise CycloidAPIError("retry error", 500)
            return "success after retry"

        result = test_func()
        assert result == "success after retry"
        assert call_count == 2


class TestErrorMonitor:
    """Test error monitoring functionality."""

    def test_error_monitor_initialization(self) -> None:
        """Test error monitor initialization."""
        monitor = ErrorMonitor()
        assert monitor.window_size == 100
        assert monitor.time_window == 300.0

    def test_record_error(self) -> None:
        """Test error recording."""
        monitor = ErrorMonitor()
        error = CycloidCLIError("test", "command", 1)

        monitor.record_error(error, "test action")

        assert len(monitor.error_events) == 1
        assert monitor.error_counts["CycloidCLIError"] == 1

    def test_get_error_stats(self) -> None:
        """Test error statistics retrieval."""
        monitor = ErrorMonitor()
        error = CycloidCLIError("test", "command", 1)

        monitor.record_error(error, "test action")
        stats = monitor.get_error_stats()

        assert stats["total_errors"] == 1
        assert stats["recent_errors"] == 1
        assert "CycloidCLIError" in stats["error_types"]

    def test_alert_callback(self) -> None:
        """Test alert callback functionality."""
        monitor = ErrorMonitor()
        alert_data = None

        def alert_callback(data: Dict[str, Any]) -> None:
            nonlocal alert_data
            alert_data = data

        monitor.add_alert_callback(alert_callback)

        # Trigger an alert by recording many errors
        for _ in range(15):
            error = CycloidCLIError("test", "command", 1)
            monitor.record_error(error, "test action")

        assert alert_data is not None
        assert alert_data["alert_type"] in ["high_error_rate", "consecutive_errors"]


class TestHealthChecker:
    """Test health checking functionality."""

    def test_health_check_healthy(self) -> None:
        """Test health check when system is healthy."""
        monitor = ErrorMonitor()
        checker = HealthChecker(monitor)

        health = checker.check_health()
        assert health["status"] == "healthy"

    def test_health_check_warning(self) -> None:
        """Test health check when system has warnings."""
        monitor = ErrorMonitor()
        checker = HealthChecker(monitor)

        # Record some errors
        for _ in range(3):
            error = CycloidCLIError("test", "command", 1)
            monitor.record_error(error, "test action")

        health = checker.check_health()
        assert health["status"] == "warning"

    def test_health_check_critical(self) -> None:
        """Test health check when system is critical."""
        monitor = ErrorMonitor()
        checker = HealthChecker(monitor)

        # Record many errors
        for _ in range(10):
            error = CycloidCLIError("test", "command", 1)
            monitor.record_error(error, "test action")

        health = checker.check_health()
        assert health["status"] == "critical"

    def test_get_recommendations(self) -> None:
        """Test recommendation generation."""
        monitor = ErrorMonitor()
        checker = HealthChecker(monitor)

        # Record CLI errors
        error = CycloidCLIError("test", "command", 1)
        monitor.record_error(error, "test action")

        health = checker.check_health()
        recommendations = health["recommendations"]

        assert "Check CLI configuration and connectivity" in recommendations


class TestGlobalFunctions:
    """Test global error monitoring functions."""

    def test_record_error_global(self) -> None:
        """Test global error recording."""
        error = CycloidCLIError("test", "command", 1)

        # Get initial count
        monitor = get_error_monitor()
        initial_count = len(monitor.error_events)

        record_error(error, "test action")

        # Check that an error was added
        assert len(monitor.error_events) == initial_count + 1

    def test_check_system_health_global(self) -> None:
        """Test global health check."""
        health = check_system_health()
        assert "status" in health
        assert "timestamp" in health
        assert "error_stats" in health

    def test_get_monitor_and_checker(self) -> None:
        """Test getting monitor and checker instances."""
        monitor = get_error_monitor()
        checker = get_health_checker()

        assert isinstance(monitor, ErrorMonitor)
        assert isinstance(checker, HealthChecker)


class TestErrorEvent:
    """Test error event data structure."""

    def test_error_event_creation(self) -> None:
        """Test error event creation."""
        event = ErrorEvent(
            timestamp=time.time(),
            correlation_id="test-id",
            error_type="TestError",
            error_message="test message",
            action="test action",
            severity="error",
            metadata={"key": "value"},
        )

        assert event.correlation_id == "test-id"
        assert event.error_type == "TestError"
        assert event.error_message == "test message"
        assert event.action == "test action"
        assert event.severity == "error"
        assert event.metadata["key"] == "value"

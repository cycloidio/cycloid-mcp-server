"""Error monitoring and alerting system for Cycloid MCP Server."""

import time
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

from fastmcp.utilities.logging import get_logger

from .error_handling import get_correlation_id
from .exceptions import CycloidAPIError

logger = get_logger(__name__)


@dataclass
class ErrorEvent:
    """Represents an error event for monitoring."""

    timestamp: float
    correlation_id: Optional[str]
    error_type: str
    error_message: str
    action: str
    severity: str
    metadata: Dict[str, Any]


class ErrorMonitor:
    """Monitors error patterns and triggers alerts."""

    def __init__(self, window_size: int = 100, time_window: float = 300.0) -> None:  # type: ignore[reportMissingSuperCall]  # noqa: E501
        """Initialize error monitor.

        Args:
            window_size: Maximum number of errors to track
            time_window: Time window in seconds for error rate calculation
        """
        self.window_size = window_size
        self.time_window = time_window
        self.error_events: deque[ErrorEvent] = deque(maxlen=window_size)
        self.error_counts: Dict[str, int] = defaultdict(int)
        self.alert_thresholds = {
            "error_rate": 10,  # errors per time window
            "consecutive_errors": 5,  # consecutive errors of same type
            "critical_errors": 3,  # critical errors per time window
        }
        self.alert_callbacks: List[Callable[[Dict[str, Any]], None]] = []

    def record_error(
        self,
        error: Exception,
        action: str,
        severity: str = "error",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Record an error event.

        Args:
            error: The exception that occurred
            action: The action that failed
            severity: Error severity level
            metadata: Additional metadata about the error
        """
        event = ErrorEvent(
            timestamp=time.time(),
            correlation_id=get_correlation_id(),
            error_type=type(error).__name__,
            error_message=str(error),
            action=action,
            severity=severity,
            metadata=metadata or {},
        )

        self.error_events.append(event)
        self.error_counts[event.error_type] += 1

        # Check for alerts
        self._check_alerts(event)

    def _check_alerts(self, event: ErrorEvent) -> None:
        """Check if any alert conditions are met."""
        current_time = time.time()

        # Calculate error rate in time window
        recent_errors = [
            e for e in self.error_events
            if current_time - e.timestamp <= self.time_window
        ]

        error_rate = len(recent_errors)
        if error_rate >= self.alert_thresholds["error_rate"]:
            self._trigger_alert(
                "high_error_rate",
                f"High error rate detected: {error_rate} errors in {self.time_window}s",
                {"error_rate": error_rate, "time_window": self.time_window},
            )

        # Check for consecutive errors of same type
        consecutive_count = 0
        for e in reversed(self.error_events):
            if e.error_type == event.error_type:
                consecutive_count += 1
            else:
                break

        if consecutive_count >= self.alert_thresholds["consecutive_errors"]:
            self._trigger_alert(
                "consecutive_errors",
                f"Consecutive {event.error_type} errors: {consecutive_count}",
                {"error_type": event.error_type, "count": consecutive_count},
            )

        # Check for critical errors
        critical_errors = [
            e for e in recent_errors
            if e.severity == "critical" or isinstance(e, CycloidAPIError)
        ]

        if len(critical_errors) >= self.alert_thresholds["critical_errors"]:
            self._trigger_alert(
                "critical_errors",
                f"Multiple critical errors detected: {len(critical_errors)}",
                {"critical_count": len(critical_errors)},
            )

    def _trigger_alert(
        self,
        alert_type: str,
        message: str,
        metadata: Dict[str, Any],
    ) -> None:
        """Trigger an alert."""
        alert_data = {
            "alert_type": alert_type,
            "message": message,
            "timestamp": time.time(),
            "metadata": metadata,
        }

        logger.critical(
            f"ALERT: {message}",
            extra={
                "alert_type": alert_type,
                "alert_data": alert_data,
            },
        )

        # Call registered alert callbacks
        for callback in self.alert_callbacks:
            try:
                callback(alert_data)
            except Exception as e:
                logger.error(f"Alert callback failed: {e}")

    def add_alert_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """Add an alert callback function.

        Args:
            callback: Function to call when alerts are triggered
        """
        self.alert_callbacks.append(callback)

    def get_error_stats(self) -> Dict[str, Any]:
        """Get error statistics."""
        current_time = time.time()
        recent_errors = [
            e for e in self.error_events
            if current_time - e.timestamp <= self.time_window
        ]

        return {
            "total_errors": len(self.error_events),
            "recent_errors": len(recent_errors),
            "error_types": dict(self.error_counts),
            "time_window": self.time_window,
            "window_size": self.window_size,
        }


class HealthChecker:
    """Checks system health and reports issues."""

    def __init__(self, error_monitor: ErrorMonitor) -> None:  # type: ignore[reportMissingSuperCall]
        """Initialize health checker.

        Args:
            error_monitor: Error monitor instance to check
        """
        self.error_monitor = error_monitor

    def check_health(self) -> Dict[str, Any]:
        """Perform health check and return status.

        Returns:
            Health status dictionary
        """
        stats = self.error_monitor.get_error_stats()

        # Determine health status
        if stats["recent_errors"] == 0:
            status = "healthy"
        elif stats["recent_errors"] < 5:
            status = "warning"
        else:
            status = "critical"

        return {
            "status": status,
            "timestamp": time.time(),
            "error_stats": stats,
            "recommendations": self._get_recommendations(stats),
        }

    def _get_recommendations(self, stats: Dict[str, Any]) -> List[str]:
        """Get recommendations based on error stats."""
        recommendations: List[str] = []

        if stats["recent_errors"] > 0:
            recommendations.append("Monitor error logs for patterns")

        if stats["recent_errors"] > 10:
            recommendations.append("Consider implementing circuit breaker pattern")

        if "CycloidCLIError" in stats["error_types"]:
            recommendations.append("Check CLI configuration and connectivity")

        if "CycloidAPIError" in stats["error_types"]:
            recommendations.append("Verify API credentials and rate limits")

        return recommendations


# Global error monitor instance
_error_monitor = ErrorMonitor()
_health_checker = HealthChecker(_error_monitor)


def get_error_monitor() -> ErrorMonitor:
    """Get the global error monitor instance."""
    return _error_monitor


def get_health_checker() -> HealthChecker:
    """Get the global health checker instance."""
    return _health_checker


def record_error(
    error: Exception,
    action: str,
    severity: str = "error",
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    """Record an error with the global error monitor."""
    _error_monitor.record_error(error, action, severity, metadata)


def check_system_health() -> Dict[str, Any]:
    """Check system health and return status."""
    return _health_checker.check_health()

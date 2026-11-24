"""ORBIT Observability and Metrics.

Provides system observability, metrics collection, health checks,
and structured logging for the ORBIT discovery network.
"""

import logging
import time
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from dataclasses import dataclass, field
from collections import defaultdict

logger = logging.getLogger("orbit.core.monitoring")


@dataclass
class Metric:
    """A single metric observation."""
    name: str
    value: float
    unit: str
    tags: Dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class MetricsCollector:
    """Collects and aggregates system metrics."""

    def __init__(self):
        self._metrics: List[Metric] = []
        self._counters: Dict[str, float] = defaultdict(float)
        self._gauges: Dict[str, float] = {}
        self._histograms: Dict[str, List[float]] = defaultdict(list)

    def increment(self, name: str, value: float = 1.0, tags: Optional[Dict[str, str]] = None):
        """Increment a counter metric."""
        self._counters[name] += value
        self._metrics.append(Metric(name=name, value=value, unit="count", tags=tags or {}))

    def gauge(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """Set a gauge metric."""
        self._gauges[name] = value
        self._metrics.append(Metric(name=name, value=value, unit="gauge", tags=tags or {}))

    def histogram(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """Add a value to a histogram."""
        self._histograms[name].append(value)
        self._metrics.append(Metric(name=name, value=value, unit="histogram", tags=tags or {}))

    def get_counter(self, name: str) -> float:
        return self._counters.get(name, 0.0)

    def get_gauge(self, name: str) -> Optional[float]:
        return self._gauges.get(name)

    def get_histogram_stats(self, name: str) -> Optional[Dict[str, float]]:
        values = self._histograms.get(name, [])
        if not values:
            return None
        return {
            "count": len(values),
            "sum": sum(values),
            "min": min(values),
            "max": max(values),
            "avg": sum(values) / len(values),
        }

    def get_all_metrics(self) -> Dict[str, Any]:
        return {
            "counters": dict(self._counters),
            "gauges": dict(self._gauges),
            "histograms": {
                name: self.get_histogram_stats(name)
                for name in self._histograms
            },
        }


class HealthChecker:
    """System health checker for ORBIT components."""

    def __init__(self):
        self._checks: Dict[str, callable] = {}
        self._results: Dict[str, Dict[str, Any]] = {}

    def register_check(self, name: str, check_func: callable):
        """Register a health check function."""
        self._checks[name] = check_func

    async def run_check(self, name: str) -> Dict[str, Any]:
        """Run a single health check."""
        if name not in self._checks:
            return {"status": "unknown", "error": f"Check {name} not registered"}

        start = time.time()
        try:
            result = await self._checks[name]()
            elapsed = time.time() - start
            if isinstance(result, dict):
                result["response_time_seconds"] = elapsed
                result["timestamp"] = datetime.now(timezone.utc).isoformat()
            else:
                result = {
                    "status": "healthy" if result else "unhealthy",
                    "response_time_seconds": elapsed,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            self._results[name] = result
            return result
        except Exception as e:
            elapsed = time.time() - start
            result = {
                "status": "unhealthy",
                "error": str(e),
                "response_time_seconds": elapsed,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            self._results[name] = result
            return result

    async def run_all_checks(self) -> Dict[str, Any]:
        """Run all registered health checks."""
        results = {}
        overall_healthy = True

        for name in self._checks:
            result = await self.run_check(name)
            results[name] = result
            if result.get("status") != "healthy":
                overall_healthy = False

        return {
            "status": "healthy" if overall_healthy else "unhealthy",
            "checks": results,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def get_last_results(self) -> Dict[str, Any]:
        return dict(self._results)


class StructuredLogger:
    """Structured logging for ORBIT components."""

    def __init__(self, name: str):
        self.logger = logging.getLogger(name)

    def info(self, message: str, **kwargs):
        self.logger.info(message, extra=kwargs)

    def warn(self, message: str, **kwargs):
        self.logger.warning(message, extra=kwargs)

    def error(self, message: str, **kwargs):
        self.logger.error(message, extra=kwargs)

    def debug(self, message: str, **kwargs):
        self.logger.debug(message, extra=kwargs)


# Global instances
metrics = MetricsCollector()
health = HealthChecker()

__all__ = ["metrics", "health", "MetricsCollector", "HealthChecker", "StructuredLogger", "Metric"]

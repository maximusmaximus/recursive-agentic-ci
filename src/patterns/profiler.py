"""Performance & Traffic Profiler Ingestion Pattern.

Collects API latency metrics, slow query traces, and throughput logs,
identifying systemic bottlenecks to inform targeted caching and indexing proposals.
"""
from typing import Dict, List, Any

class PerformanceProfiler:
    """Ingests API and database performance metrics to detect optimization targets."""

    def __init__(self, slow_query_ms: float = 200.0, latency_p95_ms: float = 300.0):
        self.slow_query_ms = slow_query_ms
        self.latency_p95_ms = latency_p95_ms
        self._metrics: List[Dict[str, Any]] = []

    def ingest_metric(self, metric: Dict[str, Any]):
        self._metrics.append(metric)

    def get_bottlenecks(self) -> List[Dict[str, Any]]:
        bottlenecks = []
        for m in self._metrics:
            p95 = m.get("p95_latency_ms", 0.0)
            if p95 >= self.latency_p95_ms:
                bottlenecks.append({
                    "endpoint": m.get("endpoint"),
                    "p95_latency_ms": p95,
                    "p99_latency_ms": m.get("p99_latency_ms"),
                    "severity": "high" if p95 > 500 else "medium",
                    "reason": m.get("bottleneck_reason", "High latency threshold exceeded"),
                    "recommended_action": "Introduce cache layer or database index"
                })
        return bottlenecks

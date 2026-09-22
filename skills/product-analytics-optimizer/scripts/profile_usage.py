"""Helper script for ingesting usage metrics and identifying bottlenecks."""
import argparse
import json
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))
from src.patterns.profiler import PerformanceProfiler

def main():
    parser = argparse.ArgumentParser(description="Profile usage metrics for Hermes optimization dashes")
    parser.add_argument("--metric", help="JSON string representing endpoint latency metric")
    parser.add_argument("--list", action="store_true", help="List current identified bottlenecks")
    args = parser.parse_args()

    profiler = PerformanceProfiler(latency_p95_ms=250.0)

    if args.metric:
        data = json.loads(args.metric)
        profiler.ingest_metric(data)
        print(f"[*] Ingested metric for {data.get('endpoint')}")

    if args.list or not args.metric:
        bottlenecks = profiler.get_bottlenecks()
        print("\n[*] Detected Performance Bottlenecks:")
        if not bottlenecks:
            print("  No bottlenecks currently exceeding 250ms threshold.")
        for b in bottlenecks:
            print(f"  • {b['endpoint']} (p95: {b['p95_latency_ms']}ms) — Action: {b['recommended_action']}")

if __name__ == "__main__":
    main()

---
name: product-analytics-optimizer
description: "Translates product usage telemetry (API query waterfalls, funnel drop-offs, slow database traces, and access skews) into high-impact code optimizations and feature enhancements."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [analytics, performance, profiling, product-usage, latency, optimization]
---

# Product Analytics Optimizer Skill

Drives autonomous repository feature evolution based on real-world user behavior and system usage patterns.

## When to Use

Activate this skill when:
- Endpoint latency percentiles (p95/p99) exceed performance thresholds (>250ms).
- Client applications exhibit sequential N+1 network request waterfalls that need resource expansion APIs.
- User signup/checkout funnels drop off due to overly rigid input validation.
- Database access patterns demonstrate heavy read skews requiring multi-tiered caching.

## Quick Dispatch

| Task | Command | Description |
|---|---|---|
| **Ingest Performance Metric** | `python skills/product-analytics-optimizer/scripts/profile_usage.py --metric <json>` | Logs route latency and identifies bottlenecks |
| **Inspect Bottlenecks** | `python skills/product-analytics-optimizer/scripts/profile_usage.py --list` | Lists endpoints exceeding latency thresholds |
| **Trigger Optimization Dash** | `python skills/recursive-ci/scripts/run_dash.py --repo <id>` | Generates caching or indexing proposals |

## Pattern Recognition Archetypes

1. **Sequential N+1 API Waterfall**:
   - Signal: Multiple related endpoints called in rapid succession by the same client.
   - Evolution: Generates unified `?include=` query expansion parameter.
2. **Form Validation Drop-off**:
   - Signal: High 422 error rates on phone/postal/coupon fields in analytics webhooks.
   - Evolution: Builds permissive pre-sanitizers (stripping whitespace, normalizing formats).
3. **Pareto 80/20 Read Skew**:
   - Signal: 90%+ of queries target data created within the last 48 hours.
   - Evolution: Designs adaptive multi-tier TTL cache preventing cache thrashing.

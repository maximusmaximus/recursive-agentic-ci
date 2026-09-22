---
name: sandbox-benchmark-runner
description: "Executes candidate code patches inside isolated scratch worktrees, runs full test suites (pytest/unittest), and benchmarks RAM footprint and latency before/after modifications."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [sandbox, benchmarking, worktrees, performance, testing, isolation]
---

# Sandbox Benchmark Runner Skill

Guarantees hermetic isolation and empirical performance proof before any code is approved for mainline integration.

## When to Use

Activate this skill when:
- Testing candidate patches without risking developer or production branch integrity.
- Proving empirical performance claims (e.g. proving a streaming exporter drops RAM consumption from 1.8 GB to 50 MB).
- Validating zero regressions across test runners (`pytest`, `unittest`, `npm test`, `cargo test`).

## Quick Dispatch

| Task | Command | Description |
|---|---|---|
| **Run Sandbox Test** | `python skills/sandbox-benchmark-runner/scripts/run_benchmark.py --path <repo>` | Clones to temp worktree and runs tests |
| **Inspect Concurrency** | `python -m src.cli status` | Checks active sandbox slots and system limits |

## Isolation Guarantees

1. **Scratch Space Isolation**:
   The sandbox creates a randomized temporary directory (`tempfile.mkdtemp(prefix="rec_ci_sandbox_")`) completely outside the target repository.
2. **Environment Encapsulation**:
   Sets clean `PYTHONPATH` pointing strictly to the sandbox copy, ensuring modified files do not leak into other processes.
3. **Execution Guardrails**:
   - Hard execution timeout (default: 120 seconds) kills runaway or deadlocked processes.
   - Guaranteed cleanup in `finally` blocks prevents disk bloat.

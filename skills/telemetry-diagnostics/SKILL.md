---
name: telemetry-diagnostics
description: "Ingests real-world crash logs, Sentry error events, and OpenTelemetry stack traces, mapping them to codebase AST nodes to formulate bug-fixing sprint dashes."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [telemetry, sentry, crashes, stack-traces, bug-fixing, diagnostics]
---

# Telemetry Diagnostics Skill

Bridges production and staging exception telemetry directly into the Hermes recursive bug-fixing loop.

## When to Use

Activate this skill when:
- Sentry, OpenTelemetry, or a log collector alerts on unhandled production crashes.
- The user provides a raw stack trace or log file to analyze and fix.
- Generating a "Bug Fix Sprint Dash" prioritized by real-world user pain rather than theoretical issues.

## Quick Dispatch

| Task | Command | Description |
|---|---|---|
| **Ingest Raw Stack Trace** | `python skills/telemetry-diagnostics/scripts/ingest_trace.py --file <trace.txt>` | Maps trace to failing file, function, and line |
| **Ingest Sentry Webhook JSON** | `curl -X POST http://localhost:18880/api/v1/telemetry -d @sentry.json` | Ingests crash dump via REST API |
| **Generate Crash Fix Dash** | `python skills/recursive-ci/scripts/run_dash.py --repo <id> --batch 2` | Prioritizes ingested crashes at top of sprint |

## How Hermes Executes the Diagnostic Loop

```
1. Raw Trace Ingest ──> 2. Frame Locator ──> 3. Privacy Scrubber
                                                       │
                                                       ▼
6. Telegram Alert <── 5. Isolated Sandbox Test <── 4. Regression Test Proof
```

1. **Stack Trace Extraction**:
   Extracts innermost failing frame: `File "path.py", line 42, in func_name` along with the exception type (`AttributeError`, `ZeroDivisionError`, `KeyError`).
2. **AST Mapping**:
   Correlates the failing frame with the target repository's local AST to inspect the surrounding scope.
3. **Venice Privacy Redaction**:
   Removes database passwords, session IDs, and user PII before sending the context to Venice AI.
4. **Reproduction Unit Test Generation**:
   Before proposing the code fix, Hermes automatically drafts a unit test asserting that the crash condition triggers. Once the fix is applied, the test suite must pass 100%.

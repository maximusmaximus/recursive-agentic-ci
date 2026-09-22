---
name: recursive-ci
description: "Master autonomous continuous integration skill: repository auditing, AST vector discovery, feature sprint dashes, Venice AI zero-retention planning, and Telegram HITL gatekeeping."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [ci, recursive-development, git, hitl, telegram, venice-ai, mcp]
---

# Recursive CI Master Skill

Autonomous continuous integration and recursive repository evolution with a human in the middle of the loop.

## When to Use

Activate this skill when:
- The user asks to audit a target codebase for technical debt, missing capabilities, or test gaps.
- A scheduled cron triggers a periodic repository development sprint ("Feature Dash").
- A human maintainer interacts via Telegram to approve, reject (with rationale), or snooze proposals.
- Connecting external agents or IDEs via the Model Context Protocol (MCP).

## Quick Dispatch

| Task | Command | Description |
|---|---|---|
| **Audit Repository** | `python -m src.cli audit --path <path>` | Scans AST, discovers test frameworks & vectors |
| **Trigger Sprint Dash** | `python -m src.cli dash --repo <id> --batch 3` | Generates candidate feature proposals via Venice AI |
| **Launch Management Server** | `python -m src.cli server --port 18880` | Starts Web UI Dashboard & MCP JSON-RPC server |
| **Run Telegram HITL Bot** | `python -m src.cli bot` | Long-polling daemon for mobile maintainer gate |
| **System Status** | `python -m src.cli status` | Checks active repos, token burn & health scores |

## Core Workflow

```
1. Target Repo Audit ──> 2. Venice AI Privacy Plan ──> 3. Semantic Delta Scoring
                                                                    │
                                                                    ▼
6. Mainline Merge <── 5. Isolated Sandbox CI <── 4. Telegram Maintainer Gate
```

### 1. Venice AI Privacy Guarantee
All code inspected by this skill must pass through local AST redaction before dispatch:
- Secrets, tokens (`sk-...`, `ghp_...`, `AIza...`), and passwords are automatically scrubbed.
- PII (emails, internal IPs) is redacted.
- Requests to Venice AI endpoints enforce `X-Venice-Zero-Retention: true` and `include_venice_system_prompt: false`.

### 2. Anti-Gamification Safeguards
- Daily hard-caps enforce maximum token burn (250k tokens/day) and proposal limits (5/day).
- Semantic delta scorer blocks trivial formatting churn and cosmetic commit farming.
- 3 consecutive maintainer rejections trip a 7-day circuit breaker.

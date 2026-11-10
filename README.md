# Hermes Recursive Agentic Continuous Integration (HITL) 🚀

[![CI Suite](https://github.com/maximusmaximus/recursive-agentic-ci/actions/workflows/ci.yml/badge.svg)](https://github.com/maximusmaximus/recursive-agentic-ci/actions/workflows/ci.yml)
[![Venice AI Privacy](https://img.shields.io/badge/Venice%20AI-ZDR%20%2B%20E2EE%20Enclave-10b981?style=flat-square)](https://venice.ai)
[![Telegram HITL](https://img.shields.io/badge/Telegram-HITL%20Inline%20Controls-0284c7?style=flat-square)](https://telegram.org)
[![Model Context Protocol](https://img.shields.io/badge/Protocol-MCP%20JSON--RPC%202.0-6366f1?style=flat-square)](https://modelcontextprotocol.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-71717a?style=flat-square)](LICENSE)

A generalized, production-ready framework for **Recursive Continuous Integration with Human-and-Agent-in-the-Loop (HITL)**.

Hermes continuously audits your target codebases, formulates high-impact feature enhancements and mutation resilience tests, guarantees enterprise privacy via **Venice AI**, blocks gamification abuse via **Semantic Delta Scoring**, and orchestrates approvals interactively via **Telegram** and a real-time **Web Management Dashboard**.

---

## Key Highlights

- 🔒 **Venice AI ZDR & E2EE Enclave Privacy Boundary**: Local AST redaction, PoA/Venice/PEM/Bearer secret scrubbers, zero-data retention headers, and optional hardware-enclave `e2ee-*` model routing (`VENICE_E2EE=true`).
- 🧬 **Polyglot AST Audit & `RepoGenome` JIT Skill Dispatch**: Static analysis across Python, TypeScript/JavaScript, Go, and Rust with event-driven Just-In-Time skill mounting & eviction to save context window tokens.
- ⚡ **Cadence Sprint Dashes**: Scheduled batch proposals ("Feature Dashes") combining capability upgrades, coverage gap stubs, telemetry crash fixes, and mutation resilience probes.
- 💬 **Interactive Telegram & Clarification Q&A Gate**: One-tap inline buttons (`[✅ Approve]`, `[❌ Reject + Rationale]`, `[⏳ Snooze +24h]`, `[🔍 Diff]`, `[🚀 Merge]`) plus automatic `AWAITING_ANSWERS` clarification gates before sandbox execution.
- 🛑 **Anti-Gamification & Abuse Governance**: Cross-process SQLite WAL persistence for daily token caps, circuit breakers, and semantic delta value scoring to prevent vanity commit farming.
- 🧪 **Hermetic Sandbox & Git Worktree Branches**: Candidate patches are verified in isolated scratch environments and materialized onto clean `rec-ci/<proposal_id>` git branches via `git worktree` only after 100% test suite pass.
- 🔌 **Model Context Protocol (MCP) Server**: Full JSON-RPC 2.0 tool suite (`audit_repository`, `create_feature_dash`, `approve_proposal`, `answer_proposal_questions`, `merge_proposal`, `reject_proposal`, `snooze_proposal`, `ingest_telemetry`, `get_repo_health`).
- 📊 **Threaded Real-time Web Dashboard**: Responsive dark-mode management UI backed by `ThreadedHTTPServer` for non-blocking repository, Q&A, diff, and quota control.
- 📥 **Patterned Data Ingestion**: Built-in modules for Sentry/OTel crash traces, API latency profiling, GitHub issue sync, webhook HMAC verification, RBAC, and persistent maintainer preference learning.

---

## Quick Start

### 1. Installation

```bash
git clone https://github.com/maximusmaximus/recursive-agentic-ci.git
cd recursive-agentic-ci
pip install -e .[full]
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env and configure VENICE_API_KEY and TELEGRAM_BOT_TOKEN
```

### 3. Audit a Target Repository

```bash
python -m src.cli audit --path ./examples/sample_forked_repo
```

### 4. Launch the Management Server & Web UI

```bash
python -m src.cli server --port 18880
# Open http://localhost:18880 in your browser!
```

### 5. Launch the Telegram HITL Bot

```bash
python -m src.cli bot
```

---

## Documentation

- 📘 [Architecture Blueprint](docs/ARCHITECTURE.md)
- 🛠 [Operator Deployment Guide](docs/OPERATOR_GUIDE.md)
- 📱 [User & Maintainer Telegram Guide](docs/USER_GUIDE.md)
- 🛡 [Anti-Abuse & Threat Model Whitepaper](docs/ANTI_ABUSE.md)
- 🔌 [Model Context Protocol (MCP) Guide](docs/MCP_GUIDE.md)
- 🧩 [Patterned Ingestion Modules](docs/PATTERNED_MODULES.md)

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

- 🔒 **Venice AI Privacy Boundary**: Complete local AST redaction, secret/PII scrubbers, and zero-data retention model routing.
- ⚡ **Cadence Sprint Dashes**: Scheduled batch proposals ("Feature Dashes") containing both new capabilities and mutation resilience tests.
- 📱 **Interactive Telegram Gatekeeper**: One-tap inline buttons (`[✅ Approve]`, `[❌ Reject + Rationale]`, `[⏳ Snooze +24h]`, `[🔍 Diff]`, `[📊 Status]`).
- 🛑 **Anti-Gamification & Abuse Governance**: Strict token hard-caps, circuit breakers, and semantic delta value scoring to prevent vanity commit farming.
- 🧪 **Hermetic Sandbox Worktrees**: All candidate patches are validated in isolated temporary environments; zero code enters mainline without a 100% test suite pass.
- 🔌 **Model Context Protocol (MCP) Server**: Full JSON-RPC 2.0 tool suite ready for Hermes, Claude, and external AI agents.
- 📊 **Real-time Web Management Dashboard**: Responsive dark-mode dashboard for monitoring repositories, diffs, and resource quotas.
- 📥 **Patterned Data Ingestion**: Built-in modules for Sentry/OTel crash traces, API latency profiling, GitHub issue sync, and maintainer preference learning.

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

# Model Context Protocol (MCP) Guide

Hermes Recursive CI implements the standard **Model Context Protocol (MCP)** specification (JSON-RPC 2.0). Any MCP-compliant client (including Hermes Agent, Claude Desktop, Cursor, and custom agent daemons) can discover and execute CI tools seamlessly.

---

## 1. Supported Transports

- **HTTP / SSE Transport**: Accessible at `http://<host>:<port>/mcp`
- **Stdio Transport**: Executable directly via standard input/output for local process isolation.

---

## 2. Tool Catalog

### `audit_repository`
- **Purpose**: Performs AST structural analysis, discovers test suites, and calculates a baseline repository health score.
- **Arguments**:
  - `repo_id` (string, required): Registered repository ID.

### `create_feature_dash`
- **Purpose**: Generates an autonomous batch of proposed improvements and mutation resilience tests.
- **Arguments**:
  - `repo_id` (string, required): Repository ID.
  - `batch_size` (integer, optional): Number of proposals (default: 3).

### `approve_proposal`
- **Purpose**: Approves a proposal, acquires sandbox resources, and runs the test suite in an isolated worktree.
- **Arguments**:
  - `proposal_id` (string, required): Proposal identifier.
  - `notes` (string, optional): Implementation guidance.

### `reject_proposal`
- **Purpose**: Rejects proposal and records negative constraint feedback.
- **Arguments**:
  - `proposal_id` (string, required)
  - `rationale` (string, required)

### `snooze_proposal`
- **Purpose**: Delays proposal review by a specified duration.
- **Arguments**:
  - `proposal_id` (string, required)
  - `duration_hours` (number, required)

### `ingest_telemetry`
- **Purpose**: Ingests production crash stack traces or latency bottlenecks.
- **Arguments**:
  - `stack_trace` (string, required)
  - `exception_type` (string, optional)

---

## 3. Pairing with Telegram

Maintainers can pair any external or local MCP server to their Telegram bot session:

```
/pair_mcp http://localhost:18880
```

Once paired, typing `/mcp_tools` renders interactive inline buttons for all discovered tools.

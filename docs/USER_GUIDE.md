# User & Maintainer Guide: Interacting with Hermes over Telegram & Web UI

This guide outlines how developers and repository maintainers interact with Hermes to review, approve, snooze, and reject recursive code proposals.

---

## 1. Telegram Interface

The Telegram bot acts as an interactive gatekeeper directly on your mobile device or desktop.

### Slash Commands

| Command | Action |
|---|---|
| `/start` | Displays welcome overview and registered shortcuts |
| `/dash [repo_id]` | Triggers a fresh sprint dash of candidate improvements |
| `/status` | Displays repository health scores, token burn, and pending counts |
| `/snooze_list` | Displays all proposals currently delayed with wake times |
| `/pair_mcp <url>` | Pairs an external Model Context Protocol server |
| `/mcp_tools` | Explores and triggers registered MCP tools |

---

## 2. Interactive Review Workflow

When Hermes runs a scheduled cadence sprint (e.g. daily at 09:00 AM) or when you type `/dash`, you receive a proposal card with inline buttons:

```
⚡ [Hermes Recursive CI] FEATURE PROPOSED

Title: Add prime factorization & batch math to Calculator
Repository: sample-forked-repo
Proposal ID: prop_e82f1b4a

Why this was proposed:
Extends Calculator with robust factorization and boundary error guards.

🔒 Privacy Guarantee: Venice AI (Zero-Data Retention)
🛡 Safety Score: 96% | Delta Score: 0.75

[✅ Approve & Run CI]
[❌ Reject (Give Reason)]  [⏳ Snooze / Delay]
[🔍 View Diff Summary]    [📊 Repo Status]
```

### Action 1: `✅ Approve & Run CI`
- Tapping **Approve** moves the proposal to `IN_SANDBOX`.
- Hermes creates an isolated worktree clone, applies the candidate patch, and runs the entire test suite (`unittest`, `pytest`).
- You receive an instant follow-up alert:
  - If tests pass: `✅ SANDBOX VERIFICATION PASSED! Ready for final merge.`
  - If tests fail: `❌ SANDBOX VERIFICATION FAILED. Patch discarded to protect codebase.`

### Action 2: `❌ Reject (Give Reason)`
- Tapping **Reject** prompts you for feedback: *"Please reply with your rationale for rejecting..."*
- Send a message explaining why (e.g. *"We avoid external math libraries, keep it vanilla"*).
- Hermes ingests this rationale into its **Maintainer Preferences** vector. It will **never** propose that pattern again!

### Action 3: `⏳ Snooze / Delay`
- Tapping **Snooze** opens the duration menu:
  - `[+24 Hours (1 Day)]`
  - `[+72 Hours (3 Days)]`
  - `[+1 Week (7 Days)]`
- The proposal is moved to `SNOOZED` and will not clutter your sprints until the timer elapses.

---

## 3. Web Management Dashboard

Maintainers can also access the rich dark-mode dashboard at `http://localhost:18880`:
- View active repository health metrics.
- Track real-time token quotas and concurrency limits.
- Filter proposals by status (`PROPOSED`, `SNOOZED`, `TESTS_PASSED`, `REJECTED`).
- One-click trigger for on-demand Feature Dashes.

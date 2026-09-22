"""Telegram Rich Notification Formatter.

Formats proposals, sandbox CI outcomes, and health status reports into
clean, high-visibility Telegram messages with action buttons.
"""
from typing import Dict, Any, List

def format_proposal_message(proposal: Dict[str, Any]) -> str:
    """Format single proposal alert with Venice privacy indicator."""
    ptype = proposal.get("type", "feature").upper()
    title = proposal.get("title", "Untitled")
    rationale = proposal.get("rationale", "No rationale provided.")
    safety = int(proposal.get("safety_score", 0.9) * 100)
    delta = proposal.get("semantic_delta_score", 0.5)
    repo = proposal.get("repo_id", "unknown")
    prop_id = proposal.get("id")

    icon = "⚡" if ptype == "FEATURE" else "🧪"
    if ptype == "BUG_FIX":
        icon = "🚑"

    return (
        f"{icon} *[Hermes Recursive CI] {ptype} PROPOSED*\n\n"
        f"*Title:* {title}\n"
        f"*Repository:* `{repo}`\n"
        f"*Proposal ID:* `{prop_id}`\n\n"
        f"*Why this was proposed:*\n{rationale}\n\n"
        f"🔒 *Privacy Guarantee:* Venice AI (Zero-Data Retention)\n"
        f"🛡 *Safety Score:* `{safety}%` | *Delta Score:* `{delta}`\n\n"
        f"_Tap a button below to approve for isolated CI testing, reject with feedback, or snooze._"
    )

def format_sandbox_result_message(proposal: Dict[str, Any], ci_result: Dict[str, Any]) -> str:
    """Format isolated sandbox test results."""
    title = proposal.get("title")
    prop_id = proposal.get("id")
    success = ci_result.get("success", False)
    elapsed = ci_result.get("elapsed_seconds", 0.0)

    if success:
        return (
            f"✅ *SANDBOX VERIFICATION PASSED*\n\n"
            f"*Proposal:* {title}\n"
            f"*ID:* `{prop_id}`\n"
            f"*Execution Time:* `{elapsed}s`\n\n"
            f"All unit tests and lint checks passed with zero regressions in the isolated worktree.\n"
            f"🚀 *Ready for final main branch merge gate.*"
        )
    else:
        err = ci_result.get("stderr", "Unknown failure")
        return (
            f"❌ *SANDBOX VERIFICATION FAILED*\n\n"
            f"*Proposal:* {title}\n"
            f"*ID:* `{prop_id}`\n"
            f"*Execution Time:* `{elapsed}s`\n\n"
            f"*Error Output:*\n```\n{err[:500]}\n```\n"
            f"⚠️ Candidate modification was automatically rejected to protect the target codebase."
        )

def format_status_report_message(repos: List[Dict[str, Any]], resources: Dict[str, Any], pending_count: int) -> str:
    """Format global system status report."""
    consumed = resources.get("tokens_consumed_today", 0)
    quota = resources.get("daily_token_quota", 250000)
    pct = resources.get("quota_utilization_pct", 0)
    free_gb = resources.get("disk_free_gb", 0.0)

    repo_lines = []
    for r in repos:
        repo_lines.append(f"• `{r.get('id')}` — Health: *{r.get('health_score', 80)}%* ({r.get('default_branch')})")
    repos_text = "\n".join(repo_lines) if repo_lines else "_No repositories registered_"

    return (
        f"📊 *Hermes Recursive CI — Status Report*\n\n"
        f"*Monitored Repositories ({len(repos)}):*\n{repos_text}\n\n"
        f"*Pending Review Gates:* `{pending_count}`\n"
        f"*Daily Token Consumption:* `{consumed:,} / {quota:,}` (*{pct}%*)\n"
        f"*Active Sandboxes:* `{resources.get('active_sandboxes', 0)} / {resources.get('max_concurrent_sandboxes', 2)}`\n"
        f"*Host Disk Free:* `{free_gb} GB`\n\n"
        f"Type `/dash <repo_id>` to generate a new feature batch."
    )

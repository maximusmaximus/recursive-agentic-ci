"""Telegram Inline Keyboards.

Provides interactive buttons for approving, rejecting with rationale,
snoozing, viewing diffs, and invoking paired MCP tools.
"""
from typing import Dict, Any, List

def build_proposal_keyboard(proposal_id: str, repo_id: str) -> Dict[str, Any]:
    """Assemble interactive inline keyboard for proposal review."""
    return {
        "inline_keyboard": [
            [
                {"text": "✅ Approve & Run CI", "callback_data": f"approve:{proposal_id}"}
            ],
            [
                {"text": "❌ Reject (Give Reason)", "callback_data": f"reject:{proposal_id}"},
                {"text": "⏳ Snooze / Delay", "callback_data": f"snooze_menu:{proposal_id}"}
            ],
            [
                {"text": "🔍 View Diff Summary", "callback_data": f"diff:{proposal_id}"},
                {"text": "📊 Repo Status", "callback_data": f"status:{repo_id}"}
            ]
        ]
    }

def build_snooze_menu_keyboard(proposal_id: str) -> Dict[str, Any]:
    """Snooze duration selection menu."""
    return {
        "inline_keyboard": [
            [
                {"text": "⏳ +24 Hours (1 Day)", "callback_data": f"snooze:{proposal_id}:24"},
                {"text": "⏳ +72 Hours (3 Days)", "callback_data": f"snooze:{proposal_id}:72"}
            ],
            [
                {"text": "⏳ +1 Week (7 Days)", "callback_data": f"snooze:{proposal_id}:168"}
            ],
            [
                {"text": "« Back to Proposal", "callback_data": f"view:{proposal_id}"}
            ]
        ]
    }

def build_mcp_tools_keyboard(tools: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Assemble keyboard of available MCP tools."""
    keyboard_rows = []
    for tool in tools[:6]:
        name = tool.get("name", "tool")
        keyboard_rows.append([
            {"text": f"🛠 {name}", "callback_data": f"mcp_call:{name}"}
        ])
    return {"inline_keyboard": keyboard_rows}

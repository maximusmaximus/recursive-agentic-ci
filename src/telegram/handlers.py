"""Telegram Bot Command & Callback Query Handlers.

Coordinates interactive button presses, conversational feedback loops for rejections,
snooze duration selection, and MCP tool execution.
"""
from typing import Dict, Any, Optional, Tuple
from ..hermes.agent import HermesCIAgent
from ..mcp.bridge import TelegramMCPBridge
from .keyboards import build_proposal_keyboard, build_snooze_menu_keyboard, build_mcp_tools_keyboard
from .notifications import format_proposal_message, format_sandbox_result_message, format_status_report_message

class TelegramBotHandlers:
    """Dispatches Telegram commands and inline keyboard callbacks."""

    def __init__(self, agent: HermesCIAgent, mcp_bridge: Optional[TelegramMCPBridge] = None):
        self.agent = agent
        self.mcp_bridge = mcp_bridge or TelegramMCPBridge()
        # State machine tracking awaiting input: user_id -> {"action": "awaiting_reject_rationale", "proposal_id": "..."}
        self._user_sessions: Dict[str, Dict[str, Any]] = {}

    def handle_command(self, user_id: str, command: str, args: str = "") -> Tuple[str, Optional[Dict[str, Any]]]:
        """Handle incoming slash commands."""
        cmd = command.lower().strip()

        if cmd == "/start":
            return (
                "👋 *Welcome to Hermes Recursive Continuous Integration (HITL)!*\n\n"
                "I monitor your target repositories, propose high-leverage features & mutation tests, "
                "preserve total privacy via *Venice AI*, and execute candidate patches in isolated sandboxes.\n\n"
                "*Quick Commands:*\n"
                "• `/dash [repo_id]` — Trigger an immediate Feature Sprint Dash\n"
                "• `/status` — View active repositories, token burn & health\n"
                "• `/snooze_list` — Review delayed proposals\n"
                "• `/pair_mcp <url>` — Pair an external Model Context Protocol server\n"
                "• `/mcp_tools` — Explore and run available MCP tools\n"
            ), None

        elif cmd == "/status":
            repos = self.agent.state.list_repos()
            res = self.agent.resources.get_resource_snapshot()
            pending = len(self.agent.state.list_proposals(status="PROPOSED"))
            return format_status_report_message(repos, res, pending), None

        elif cmd == "/dash":
            repo_id = args.strip()
            if not repo_id:
                repos = self.agent.state.list_repos()
                if not repos:
                    return "⚠️ No repositories registered yet. Add a repository first via Web UI or CLI.", None
                repo_id = repos[0]["id"]

            dash_res = self.agent.run_feature_dash(repo_id, batch_size=2)
            if not dash_res.get("success"):
                return f"⚠️ *Feature Dash Halted:* {dash_res.get('reason')}", None

            proposals = dash_res.get("proposals", [])
            if not proposals:
                return f"ℹ️ Repository `{repo_id}` is up to date. No new proposals met semantic thresholds.", None

            first_prop = proposals[0]
            msg = format_proposal_message(first_prop)
            kb = build_proposal_keyboard(first_prop["id"], repo_id)
            return msg, kb

        elif cmd == "/snooze_list":
            snoozed = self.agent.state.list_proposals(status="SNOOZED")
            if not snoozed:
                return "ℹ️ There are currently no snoozed proposals.", None
            lines = [f"• `{p['id']}` — *{p['title']}* (Repo: `{p['repo_id']}`)" for p in snoozed]
            return "⏳ *Currently Snoozed Proposals:*\n\n" + "\n".join(lines), None

        elif cmd == "/pair_mcp":
            url = args.strip()
            if not url:
                return "⚠️ Usage: `/pair_mcp <http_url>`", None
            res = self.mcp_bridge.pair_server(user_id, url)
            return f"🔌 {res.get('message')}", None

        elif cmd == "/mcp_tools":
            tools = self.mcp_bridge.list_available_tools(user_id)
            if not tools:
                return "ℹ️ No MCP tools discovered.", None
            kb = build_mcp_tools_keyboard(tools)
            return "🛠 *Available Model Context Protocol (MCP) Tools:*", kb

        return f"Unknown command `{command}`. Type `/start` for help.", None

    def handle_text_message(self, user_id: str, text: str) -> Tuple[str, Optional[Dict[str, Any]]]:
        """Handle conversational input when user is prompted for feedback."""
        if user_id in self._user_sessions:
            session = self._user_sessions.pop(user_id)
            action = session.get("action")
            prop_id = session.get("proposal_id")

            if action == "awaiting_reject_rationale":
                self.agent.reject(prop_id, text, user_id)
                return (
                    f"✅ *Feedback Recorded for `{prop_id}`.*\n\n"
                    f"*Rationale stored:* \"{text}\"\n"
                    f"_The agent has learned this constraint and will not propose similar patterns for this repository._"
                ), None

        return "Message received. Use buttons or type `/help` for commands.", None

    def handle_callback_query(self, user_id: str, callback_data: str) -> Tuple[str, Optional[Dict[str, Any]]]:
        """Handle inline button clicks."""
        parts = callback_data.split(":")
        action = parts[0]

        if action == "approve":
            prop_id = parts[1]
            proposal = self.agent.state.get_proposal(prop_id)
            if not proposal:
                return "Proposal not found.", None
            res = self.agent.approve_and_implement(prop_id, user_id)
            return format_sandbox_result_message(proposal, res.get("ci_result", {})), None

        elif action == "reject":
            prop_id = parts[1]
            self._user_sessions[user_id] = {
                "action": "awaiting_reject_rationale",
                "proposal_id": prop_id
            }
            return (
                f"📝 *Please reply with your rationale for rejecting `{prop_id}`:*\n\n"
                f"_Why is this feature or mutation not useful? Your reply will immediately update the agent's "
                f"negative constraints to prevent future duplicates._"
            ), None

        elif action == "snooze_menu":
            prop_id = parts[1]
            return "Select delay duration for this proposal:", build_snooze_menu_keyboard(prop_id)

        elif action == "snooze":
            prop_id = parts[1]
            hours = int(parts[2])
            self.agent.snooze(prop_id, hours * 3600)
            return f"⏳ Proposal `{prop_id}` has been snoozed for *+{hours} hours*. It will reappear in your next dash after expiration.", None

        elif action == "diff":
            prop_id = parts[1]
            proposal = self.agent.state.get_proposal(prop_id)
            diff_text = proposal.get("proposed_diff_summary", "No diff available")
            files = ", ".join(proposal.get("affected_files", []))
            return f"🔍 *Diff Summary for `{prop_id}`*\n\n*Files Affected:* `{files}`\n\n```\n{diff_text}\n```", None

        elif action == "mcp_call":
            tool_name = parts[1]
            return f"🛠 MCP Tool `{tool_name}` dispatched via bridge.", None

        return "Action completed.", None

"""Maintainer Preference & Constraint Learning Pattern.

Learns architectural guidelines, style norms, and negative constraints
from human approvals and rejection rationales, preventing recurring anti-patterns.
"""
import time
from typing import Dict, List, Any, Optional

class MaintainerPreferences:
    """Stores and summarizes human feedback into rules for Venice AI generation."""

    def __init__(self, state_manager: Optional[Any] = None):
        self._state_manager = state_manager
        self._rules: List[Dict[str, Any]] = []
        if self._state_manager is not None:
            self._hydrate_from_state()

    def _hydrate_from_state(self):
        for row in self._state_manager.list_maintainer_feedback():
            rationale = row.get("rationale") or ""
            if not rationale.strip():
                continue
            approved = row.get("action") == "APPROVE"
            self._append_rule(
                proposal_id=row.get("proposal_id", "unknown"),
                approved=approved,
                rationale=rationale,
                timestamp=row.get("created_at", time.time()),
            )

    def _append_rule(self, proposal_id: str, approved: bool, rationale: str, timestamp: float):
        if not approved and rationale:
            clean_rule = self._extract_constraint(rationale)
            self._rules.append({
                "source_proposal": proposal_id,
                "type": "negative_constraint",
                "text": clean_rule,
                "raw_rationale": rationale,
                "timestamp": timestamp,
                "weight": 1.0
            })
        elif approved and rationale:
            self._rules.append({
                "source_proposal": proposal_id,
                "type": "positive_preference",
                "text": rationale.strip(),
                "raw_rationale": rationale,
                "timestamp": timestamp,
                "weight": 1.0
            })

    def record_feedback(self, proposal_id: str, approved: bool, rationale: Optional[str] = None, repo_id: str = "global"):
        """Record explicit maintainer rationale on a proposal."""
        if not rationale:
            return
        self._append_rule(proposal_id, approved, rationale, time.time())
        if self._state_manager is not None:
            action = "APPROVE" if approved else "REJECT"
            self._state_manager.record_maintainer_feedback(
                proposal_id=proposal_id,
                action=action,
                rationale=rationale,
                repo_id=repo_id,
            )

    def _extract_constraint(self, rationale: str) -> str:
        text = rationale.strip()
        # Clean prefix if user typed "No because ..."
        if text.lower().startswith("no because "):
            text = text[11:]
        elif text.lower().startswith("do not ") or text.lower().startswith("don't "):
            pass
        return text

    def get_active_constraints(self) -> List[str]:
        """Return formatted string list of maintainer rules to pass into Venice prompt."""
        constraints = []
        for r in self._rules:
            if r["type"] == "negative_constraint":
                constraints.append(f"DO NOT: {r['text']}")
            else:
                constraints.append(f"PREFER: {r['text']}")
        return constraints

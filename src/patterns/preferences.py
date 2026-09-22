"""Maintainer Preference & Constraint Learning Pattern.

Learns architectural guidelines, style norms, and negative constraints
from human approvals and rejection rationales, preventing recurring anti-patterns.
"""
import time
from typing import Dict, List, Any, Optional

class MaintainerPreferences:
    """Stores and summarizes human feedback into rules for Venice AI generation."""

    def __init__(self):
        self._rules: List[Dict[str, Any]] = []

    def record_feedback(self, proposal_id: str, approved: bool, rationale: Optional[str] = None):
        """Record explicit maintainer rationale on a proposal."""
        if not approved and rationale:
            clean_rule = self._extract_constraint(rationale)
            self._rules.append({
                "source_proposal": proposal_id,
                "type": "negative_constraint",
                "text": clean_rule,
                "raw_rationale": rationale,
                "timestamp": time.time(),
                "weight": 1.0
            })
        elif approved and rationale:
            self._rules.append({
                "source_proposal": proposal_id,
                "type": "positive_preference",
                "text": rationale.strip(),
                "raw_rationale": rationale,
                "timestamp": time.time(),
                "weight": 1.0
            })

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

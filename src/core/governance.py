"""Anti-Abuse, Anti-Gamification & Governance Engine.

Protects repositories from runaway recursive loops, cosmetic commit farming,
token bleed, and vanity PR gaming. Enforces strict quality and semantic delta thresholds.
"""
import time
from typing import Dict, Any, List, Optional, Tuple

class GovernanceEngine:
    """Enforces resource limits, quality gates, and anti-gamification rules."""

    def __init__(
        self,
        daily_token_budget: int = 250000,
        daily_proposals_max: int = 5,
        min_cooldown_seconds: int = 3600,
        min_semantic_delta_score: float = 0.45,
        state_manager: Optional[Any] = None,
    ):
        self.daily_token_budget = daily_token_budget
        self.daily_proposals_max = daily_proposals_max
        self.min_cooldown_seconds = min_cooldown_seconds
        self.min_semantic_delta_score = min_semantic_delta_score
        self._state_manager = state_manager

        # In-memory cache per repo (backed by SQLite when state_manager is provided)
        self._usage: Dict[str, Dict[str, Any]] = {}

    def _persist(self, repo_id: str):
        if self._state_manager is not None and repo_id in self._usage:
            self._state_manager.save_governance_usage(repo_id, self._usage[repo_id])

    def get_repo_state(self, repo_id: str) -> Dict[str, Any]:
        now = time.time()
        if repo_id not in self._usage and self._state_manager is not None:
            persisted = self._state_manager.get_governance_usage(repo_id)
            if persisted:
                self._usage[repo_id] = persisted

        if repo_id not in self._usage:
            self._usage[repo_id] = {
                "tokens_used_today": 0,
                "proposals_today": 0,
                "consecutive_rejections": 0,
                "last_run_timestamp": 0,
                "circuit_breaker_active": False,
                "reset_timestamp": now + 86400
            }
            self._persist(repo_id)

        state = self._usage[repo_id]
        if now > state["reset_timestamp"]:
            state["tokens_used_today"] = 0
            state["proposals_today"] = 0
            state["reset_timestamp"] = now + 86400
            state["circuit_breaker_active"] = False
            self._persist(repo_id)
        return state

    def check_preflight(self, repo_id: str, estimated_tokens: int = 2000) -> Tuple[bool, str]:
        """Verify if a new recursive CI cycle is authorized to run."""
        state = self.get_repo_state(repo_id)

        if state["circuit_breaker_active"]:
            return False, "Circuit breaker tripped: Too many consecutive maintainer rejections. Cooling down."

        if state["proposals_today"] >= self.daily_proposals_max:
            return False, f"Daily proposal limit reached ({self.daily_proposals_max}/day). Gamification guard active."

        if (state["tokens_used_today"] + estimated_tokens) > self.daily_token_budget:
            return False, f"Daily token budget exceeded ({state['tokens_used_today']}/{self.daily_token_budget})."

        time_since_last = time.time() - state["last_run_timestamp"]
        if state["last_run_timestamp"] > 0 and time_since_last < self.min_cooldown_seconds:
            remaining = int(self.min_cooldown_seconds - time_since_last)
            return False, f"Cooldown in effect. Please wait {remaining} seconds before next automated run."

        return True, "Preflight authorized."

    def evaluate_semantic_delta(self, proposal: Dict[str, Any]) -> Tuple[float, bool, str]:
        """Score proposal to detect trivial vanity commits or cosmetic fluff.
        
        Returns: (score, is_acceptable, explanation)
        """
        title = proposal.get("title", "").lower()
        summary = proposal.get("proposed_diff_summary", "").lower()
        rationale = proposal.get("rationale", "").lower()
        affected = proposal.get("affected_files", [])

        score = 0.5 # Baseline

        # Penalize cosmetic / vanity indicators
        cosmetic_phrases = ["formatting", "whitespace", "reorder imports", "typo in comment", "cleanup unused var"]
        for phrase in cosmetic_phrases:
            if phrase in title or phrase in summary:
                score -= 0.25

        # Reward high-value engineering patterns
        high_value_phrases = [
            "zero-division", "boundary", "validation", "prime", "index", "cache",
            "resilience", "concurrency", "test coverage", "unit test", "stack trace",
            "crash", "complexity", "exception", "telemetry", "factorization"
        ]
        for phrase in high_value_phrases:
            if phrase in title or phrase in summary or phrase in rationale:
                score += 0.15

        # Factor file breadth
        if len(affected) >= 2:
            score += 0.1 # Requires test + implementation symmetry
        elif len(affected) == 0:
            score -= 0.3

        score = max(0.0, min(1.0, round(score, 2)))
        is_acceptable = score >= self.min_semantic_delta_score
        status_msg = "Passed quality gate" if is_acceptable else "Rejected: Low semantic value / cosmetic churn"

        return score, is_acceptable, status_msg

    def record_run(self, repo_id: str, tokens_burned: int, proposals_created: int = 1):
        state = self.get_repo_state(repo_id)
        state["tokens_used_today"] += tokens_burned
        state["proposals_today"] += proposals_created
        state["last_run_timestamp"] = time.time()
        self._persist(repo_id)

    def record_feedback(self, repo_id: str, approved: bool):
        state = self.get_repo_state(repo_id)
        if approved:
            state["consecutive_rejections"] = 0
        else:
            state["consecutive_rejections"] += 1
            if state["consecutive_rejections"] >= 3:
                state["circuit_breaker_active"] = True
        self._persist(repo_id)

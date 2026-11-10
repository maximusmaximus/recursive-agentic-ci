"""Recursive Improvement & Feature Dash Planner.

Combines AST analysis, Venice privacy boundaries, and governance scoring
to assemble validated batches of candidate proposals ("Feature Dashes").
"""
import uuid
import time
from typing import Dict, Any, List, Optional
from .analyzer import RepoAnalyzer
from .privacy import VenicePrivacyProxy
from .governance import GovernanceEngine

class RecursivePlanner:
    """Orchestrates candidate generation for continuous repository evolution."""

    def __init__(
        self,
        privacy_proxy: Optional[VenicePrivacyProxy] = None,
        governance: Optional[GovernanceEngine] = None
    ):
        self.privacy = privacy_proxy or VenicePrivacyProxy()
        self.governance = governance or GovernanceEngine()

    def generate_feature_dash(
        self,
        repo_path: str,
        repo_id: str,
        batch_size: int = 3,
        include_mutations: bool = True,
        maintainer_rules: Optional[List[str]] = None,
        runtime_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate a structured batch ('Dash') of proposed features and mutation tests."""
        # 1. Preflight governance check
        authorized, reason = self.governance.check_preflight(repo_id)
        if not authorized:
            return {
                "success": False,
                "reason": reason,
                "proposals": []
            }

        # 2. Analyze repository structure
        analyzer = RepoAnalyzer(repo_path)
        audit_report = analyzer.audit()

        candidate_vectors = list(audit_report.get("feature_vectors", []))
        if include_mutations:
            candidate_vectors.extend(audit_report.get("mutation_bug_vectors", []))

        # Augment with runtime context (telemetry/profiler) if provided
        if runtime_context and "crashes" in runtime_context:
            for crash in runtime_context["crashes"]:
                candidate_vectors.insert(0, {
                    "type": "bug_fix",
                    "module": crash.get("module"),
                    "target": crash.get("function"),
                    "title": f"Fix production exception: `{crash.get('exception_type')}` in `{crash.get('function')}`",
                    "impact": "critical",
                    "category": "runtime_telemetry",
                    "stack_trace": crash.get("stack_trace")
                })

        # 3. Plan through Venice Privacy Layer & Score via Governance
        proposals = []
        tokens_burned = 0

        for vec in candidate_vectors[:batch_size]:
            plan = self.privacy.plan_improvement(audit_report, vec, maintainer_rules)
            tokens_burned += 1500

            # Governance semantic delta check
            score, is_acceptable, msg = self.governance.evaluate_semantic_delta(plan)
            if not is_acceptable:
                continue

            proposal_id = f"prop_{uuid.uuid4().hex[:8]}"
            proposal = {
                "id": proposal_id,
                "repo_id": repo_id,
                "type": vec.get("type", "feature"),
                "title": plan.get("title"),
                "rationale": plan.get("rationale"),
                "proposed_diff_summary": plan.get("proposed_diff_summary"),
                "affected_files": plan.get("affected_files", []),
                "clarifying_questions": plan.get("clarifying_questions", []),
                "test_plan": plan.get("test_plan"),
                "safety_score": plan.get("safety_score", 0.9),
                "semantic_delta_score": score,
                "created_at": time.time(),
                "status": "PROPOSED"
            }
            proposals.append(proposal)

        # Record governance token burn
        self.governance.record_run(repo_id, tokens_burned, len(proposals))

        return {
            "success": True,
            "repo_id": repo_id,
            "proposals_count": len(proposals),
            "proposals": proposals,
            "health_score": audit_report.get("health_score", 85.0),
            "total_lines": audit_report.get("total_lines", 0)
        }

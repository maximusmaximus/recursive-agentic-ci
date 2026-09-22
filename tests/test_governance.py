import unittest
from src.core.governance import GovernanceEngine

class TestGovernanceEngine(unittest.TestCase):
    def setUp(self):
        self.gov = GovernanceEngine(
            daily_token_budget=10000,
            daily_proposals_max=2,
            min_cooldown_seconds=10,
            min_semantic_delta_score=0.45
        )

    def test_preflight_budget_and_cooldown(self):
        # 1. First run allowed
        ok, msg = self.gov.check_preflight("repo-1")
        self.assertTrue(ok)

        # Record run
        self.gov.record_run("repo-1", tokens_burned=2000, proposals_created=1)

        # 2. Cooldown active
        ok, msg = self.gov.check_preflight("repo-1")
        self.assertFalse(ok)
        self.assertIn("Cooldown in effect", msg)

    def test_semantic_delta_cosmetic_penalty(self):
        cosmetic_prop = {
            "title": "Minor formatting and whitespace cleanup",
            "proposed_diff_summary": "Reorder imports and fix typo in comment",
            "rationale": "Clean styling",
            "affected_files": ["app.py"]
        }
        score, ok, msg = self.gov.evaluate_semantic_delta(cosmetic_prop)
        self.assertFalse(ok)
        self.assertLess(score, 0.45)
        self.assertIn("Low semantic value", msg)

    def test_semantic_delta_high_value(self):
        valuable_prop = {
            "title": "Add zero-division guard and prime factorization",
            "proposed_diff_summary": "Boundary check in compute and add factorize method",
            "rationale": "Prevents crash from stack trace and expands test coverage",
            "affected_files": ["calculator.py", "tests/test_calculator.py"]
        }
        score, ok, msg = self.gov.evaluate_semantic_delta(valuable_prop)
        self.assertTrue(ok)
        self.assertGreaterEqual(score, 0.6)

    def test_circuit_breaker(self):
        repo_id = "failing-repo"
        self.gov.record_feedback(repo_id, approved=False)
        self.gov.record_feedback(repo_id, approved=False)
        self.gov.record_feedback(repo_id, approved=False)

        ok, msg = self.gov.check_preflight(repo_id)
        self.assertFalse(ok)
        self.assertIn("Circuit breaker tripped", msg)

if __name__ == "__main__":
    unittest.main()

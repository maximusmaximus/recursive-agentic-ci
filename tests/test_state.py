import os
import tempfile
import unittest
from src.hermes.state import HermesStateManager

class TestStateManager(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.tmp_dir, "test_state.db")
        self.state = HermesStateManager(self.db_path)

    def test_repo_lifecycle(self):
        repo = self.state.register_repo("test-repo", "Test Repo", "/tmp/test", "main")
        self.assertEqual(repo["id"], "test-repo")
        self.assertEqual(repo["name"], "Test Repo")

        fetched = self.state.get_repo("test-repo")
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched["default_branch"], "main")

    def test_proposal_lifecycle_and_snooze(self):
        self.state.register_repo("test-repo", "Test Repo", "/tmp/test")
        prop = {
            "id": "prop-123",
            "repo_id": "test-repo",
            "type": "feature",
            "title": "Add prime caching",
            "rationale": "Boost speed",
            "proposed_diff_summary": "Add dict cache",
            "affected_files": ["calc.py"],
            "safety_score": 0.95,
            "semantic_delta_score": 0.8
        }
        saved = self.state.save_proposal(prop)
        self.assertEqual(saved["status"], "PROPOSED")

        # Snooze proposal for 1 second
        ok = self.state.snooze_proposal("prop-123", 1)
        self.assertTrue(ok)
        snoozed = self.state.get_proposal("prop-123")
        self.assertEqual(snoozed["status"], "SNOOZED")

        # Approve proposal
        ok = self.state.approve_proposal("prop-123", user_id="user_admin", notes="Looks solid")
        self.assertTrue(ok)
        approved = self.state.get_proposal("prop-123")
        self.assertEqual(approved["status"], "APPROVED")

    def test_reject_with_feedback(self):
        self.state.register_repo("test-repo", "Test Repo", "/tmp/test")
        prop = {
            "id": "prop-456",
            "repo_id": "test-repo",
            "type": "feature",
            "title": "Add unwanted framework",
            "affected_files": []
        }
        self.state.save_proposal(prop)
        ok = self.state.reject_proposal("prop-456", rationale="We only use stdlib", user_id="lead_dev")
        self.assertTrue(ok)
        rejected = self.state.get_proposal("prop-456")
        self.assertEqual(rejected["status"], "REJECTED")
        self.assertEqual(rejected["rejection_reason"], "We only use stdlib")

if __name__ == "__main__":
    unittest.main()

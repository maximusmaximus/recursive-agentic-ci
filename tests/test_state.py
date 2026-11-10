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

    def test_cross_instance_governance_preferences_and_telemetry_persistence(self):
        from src.core.governance import GovernanceEngine
        from src.hermes.resources import ResourceGovernor
        from src.patterns.preferences import MaintainerPreferences
        from src.patterns.telemetry import TelemetryIngestor

        # Process 1 records governance burn, feedback constraints, and runtime crash
        gov1 = GovernanceEngine(min_cooldown_seconds=120, state_manager=self.state)
        gov1.record_run("repo-alpha", tokens_burned=4500, proposals_created=2)
        gov1.record_feedback("repo-alpha", approved=False)

        prefs1 = MaintainerPreferences(state_manager=self.state)
        prefs1.record_feedback("prop-900", approved=False, rationale="No third-party ORM dependencies", repo_id="repo-alpha")

        telem1 = TelemetryIngestor(state_manager=self.state)
        telem1.ingest_raw_stacktrace(
            'Traceback:\n  File "worker.py", line 42, in dispatch\nRuntimeError: boom',
            "RuntimeError",
        )
        telem1.ingest_raw_stacktrace(
            'Traceback:\n  File "worker.py", line 42, in dispatch\nRuntimeError: boom',
            "RuntimeError",
        )

        # Process 2 reconnects to the same SQLite DB in a fresh object graph
        state2 = HermesStateManager(self.db_path)
        gov2 = GovernanceEngine(min_cooldown_seconds=120, state_manager=state2)
        res2 = ResourceGovernor(state_manager=state2)
        prefs2 = MaintainerPreferences(state_manager=state2)
        telem2 = TelemetryIngestor(state_manager=state2)

        ok, msg = gov2.check_preflight("repo-alpha")
        self.assertFalse(ok)
        self.assertIn("Cooldown in effect", msg)
        self.assertEqual(res2.get_resource_snapshot()["tokens_consumed_today"], 4500)

        constraints = prefs2.get_active_constraints()
        self.assertTrue(any("DO NOT: No third-party ORM dependencies" in c for c in constraints))

        crashes = telem2.get_priority_crashes(limit=5)
        self.assertEqual(len(crashes), 1)
        self.assertEqual(crashes[0]["module"], "worker.py")
        self.assertEqual(crashes[0]["frequency"], 2)

if __name__ == "__main__":
    unittest.main()

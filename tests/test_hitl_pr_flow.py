import json
import os
import shutil
import socket
import subprocess
import tempfile
import threading
import time
import unittest
import urllib.request

from src.hermes.agent import HermesCIAgent
from src.hermes.state import HermesStateManager
from src.server.app import run_server
from src.telegram.handlers import TelegramBotHandlers


class TestHITLClarificationAndGitMergeFlow(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp(prefix="rec_ci_hitl_test_")
        self.db_path = os.path.join(self.tmp_dir, "hitl.db")
        self.repo_dir = os.path.join(self.tmp_dir, "git_target_repo")
        shutil.copytree(
            os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "examples", "sample_forked_repo")),
            self.repo_dir,
        )

        # Initialize a real git repository on branch 'main'
        subprocess.run(["git", "init"], cwd=self.repo_dir, check=True, capture_output=True)
        subprocess.run(["git", "checkout", "-B", "main"], cwd=self.repo_dir, check=True, capture_output=True)
        subprocess.run(["git", "add", "."], cwd=self.repo_dir, check=True, capture_output=True)
        subprocess.run(
            [
                "git",
                "-c", "user.name=Test User",
                "-c", "user.email=test@example.com",
                "commit", "-m", "Initial commit",
            ],
            cwd=self.repo_dir,
            check=True,
            capture_output=True,
        )

        self.state = HermesStateManager(self.db_path)
        self.agent = HermesCIAgent(state_manager=self.state)
        self.agent.register_repo("git-calc", "Git Calculator Service", self.repo_dir, default_branch="main")

    def tearDown(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_jit_skill_affinities_and_eviction_accounting(self):
        repo = self.state.get_repo("git-calc")
        self.assertIn("recursive-ci", repo["skill_affinities"])
        self.assertIn("sandbox-benchmark-runner", repo["skill_affinities"])
        self.assertEqual(self.agent.dispatcher.mounted_skills, [])

        snap = self.agent.resources.get_resource_snapshot()
        self.assertGreater(snap["context_tokens_saved"], 0)

    def test_clarifying_qa_gate_telegram_and_git_worktree_branch_merge(self):
        prop = {
            "id": "prop_qa_01",
            "repo_id": "git-calc",
            "type": "feature",
            "title": "Add prime factorization & zero-division guard",
            "rationale": "Improve math safety and algorithmic coverage",
            "proposed_diff_summary": "Add factorize(n) and ValueError zero guard",
            "affected_files": ["calculator.py", "tests/test_calculator.py"],
            "clarifying_questions": [
                "Should division by zero raise ValueError or return None?",
                "Should factorize(1) return an empty list?",
            ],
            "safety_score": 0.96,
            "semantic_delta_score": 0.85,
        }
        self.state.save_proposal(prop)

        tg = TelegramBotHandlers(self.agent)

        # 1. Approving while questions are unanswered pauses at AWAITING_ANSWERS
        msg1, kb1 = tg.handle_callback_query("maint_1", "approve:prop_qa_01")
        self.assertIn("Clarification Needed", msg1)
        self.assertIsNone(kb1)
        self.assertEqual(self.state.get_proposal("prop_qa_01")["status"], "AWAITING_ANSWERS")

        # 2. Replying with answers unlocks sandbox verification -> TESTS_PASSED
        msg2, kb2 = tg.handle_text_message(
            "maint_1",
            "Raise ValueError on zero divisor\nReturn empty list for n <= 1",
        )
        self.assertIn("SANDBOX VERIFICATION PASSED", msg2)
        self.assertIsNotNone(kb2)
        self.assertEqual(self.state.get_proposal("prop_qa_01")["status"], "TESTS_PASSED")

        # Verify main branch working tree is STILL untouched prior to merge gate
        with open(os.path.join(self.repo_dir, "calculator.py"), "r", encoding="utf-8") as f:
            self.assertNotIn("def factorize", f.read())

        # 3. Triggering merge creates branch rec-ci/prop_qa_01 with real git commit
        msg3, _ = tg.handle_callback_query("maint_1", "merge:prop_qa_01")
        self.assertIn("rec-ci/prop_qa_01", msg3)

        merged_prop = self.state.get_proposal("prop_qa_01")
        self.assertEqual(merged_prop["status"], "MERGED")
        self.assertEqual(merged_prop["branch_name"], "rec-ci/prop_qa_01")
        self.assertTrue(bool(merged_prop["commit_sha"]))

        branches = subprocess.run(
            ["git", "branch", "--list", "rec-ci/prop_qa_01"],
            cwd=self.repo_dir,
            capture_output=True,
            text=True,
        ).stdout
        self.assertIn("rec-ci/prop_qa_01", branches)

    def test_untested_module_test_stub_synthesis_and_http_endpoints(self):
        prop = {
            "id": "prop_cov_02",
            "repo_id": "git-calc",
            "type": "feature",
            "title": "Add dedicated unit test coverage suite for `data_store.py`",
            "rationale": "Close test coverage gap on MemoryDataStore",
            "proposed_diff_summary": "Create unit test contract suite for data_store",
            "affected_files": ["data_store.py", "tests/test_data_store.py"],
            "clarifying_questions": ["Confirm unittest framework?"],
            "safety_score": 0.95,
            "semantic_delta_score": 0.8,
        }
        self.state.save_proposal(prop)

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("127.0.0.1", 0))
            port = s.getsockname()[1]

        t = threading.Thread(
            target=run_server,
            kwargs={"host": "127.0.0.1", "port": port, "agent": self.agent},
            daemon=True,
        )
        t.start()
        time.sleep(0.5)

        def _post(path: str, payload: dict) -> dict:
            req = urllib.request.Request(
                f"http://127.0.0.1:{port}{path}",
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read().decode("utf-8"))

        # Approve pauses for question
        r1 = _post("/api/v1/proposals/prop_cov_02/approve", {})
        self.assertEqual(r1["status"], "AWAITING_ANSWERS")

        # Answer runs sandbox with synthesized tests/test_data_store.py
        r2 = _post("/api/v1/proposals/prop_cov_02/answer", {"answers": ["Yes, use stdlib unittest"]})
        self.assertTrue(r2["success"])
        self.assertEqual(r2["status"], "TESTS_PASSED")

        # Merge with fast-forward into main
        r3 = _post("/api/v1/proposals/prop_cov_02/merge", {"merge_to_base": True})
        self.assertTrue(r3["success"])
        self.assertEqual(r3["status"], "MERGED")
        self.assertTrue(r3["merged_to_base"])
        self.assertTrue(os.path.exists(os.path.join(self.repo_dir, "tests", "test_data_store.py")))


if __name__ == "__main__":
    unittest.main()

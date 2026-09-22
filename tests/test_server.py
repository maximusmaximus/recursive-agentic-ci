import json
import os
import tempfile
import threading
import time
import unittest
import urllib.request
from src.server.app import run_server, RecursiveCIHandler
from src.hermes.agent import HermesCIAgent
from src.hermes.state import HermesStateManager
from http.server import HTTPServer

class TestServerAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp_dir = tempfile.mkdtemp()
        cls.db_path = os.path.join(cls.tmp_dir, "test_server.db")
        state = HermesStateManager(cls.db_path)
        cls.agent = HermesCIAgent(state_manager=state)

        # Register sample repo
        sample_repo = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "examples", "sample_forked_repo"))
        cls.agent.register_repo("sample-forked-repo", "Sample Forked Service", sample_repo)

        # Start test HTTP server on random high port
        cls.port = 18895
        cls.server_thread = threading.Thread(
            target=run_server,
            kwargs={"host": "127.0.0.1", "port": cls.port, "agent": cls.agent},
            daemon=True
        )
        cls.server_thread.start()
        time.sleep(1.0) # Wait for server socket bind

    def _url(self, path: str) -> str:
        return f"http://127.0.0.1:{self.port}{path}"

    def test_get_static_index(self):
        req = urllib.request.Request(self._url("/"))
        with urllib.request.urlopen(req, timeout=5) as resp:
            self.assertEqual(resp.status, 200)
            body = resp.read().decode("utf-8")
            self.assertIn("Hermes Recursive Agentic CI", body)

    def test_get_repos(self):
        req = urllib.request.Request(self._url("/api/v1/repos"))
        with urllib.request.urlopen(req, timeout=5) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertTrue(data["success"])
            self.assertGreaterEqual(len(data["repos"]), 1)

    def test_get_resources(self):
        req = urllib.request.Request(self._url("/api/v1/resources"))
        with urllib.request.urlopen(req, timeout=5) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertTrue(data["success"])
            self.assertIn("daily_token_quota", data["resources"])

    def test_post_dash(self):
        payload = json.dumps({"repo_id": "sample-forked-repo", "batch_size": 2}).encode("utf-8")
        req = urllib.request.Request(
            self._url("/api/v1/dash"),
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertTrue(data["success"])
            self.assertGreater(len(data["proposals"]), 0)

    def test_mcp_rpc_endpoint(self):
        payload = json.dumps({
            "jsonrpc": "2.0",
            "id": 42,
            "method": "tools/list",
            "params": {}
        }).encode("utf-8")
        req = urllib.request.Request(
            self._url("/mcp"),
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertEqual(data["id"], 42)
            self.assertIn("tools", data["result"])

if __name__ == "__main__":
    unittest.main()

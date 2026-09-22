import json
import os
import tempfile
import unittest
from src.mcp.server import MCPServer
from src.hermes.agent import HermesCIAgent
from src.hermes.state import HermesStateManager

class TestMCPServer(unittest.TestCase):
    def setUp(self):
        tmp_dir = tempfile.mkdtemp()
        db_path = os.path.join(tmp_dir, "test_mcp.db")
        state = HermesStateManager(db_path)
        self.agent = HermesCIAgent(state_manager=state)
        self.mcp = MCPServer(self.agent)

        sample_repo = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "examples", "sample_forked_repo"))
        self.agent.register_repo("sample-forked-repo", "Sample Forked", sample_repo)

    def test_initialize(self):
        req = json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {}
        })
        resp = json.loads(self.mcp.handle_request(req))
        self.assertEqual(resp["id"], 1)
        self.assertEqual(resp["result"]["serverInfo"]["name"], "recursive-agentic-ci-mcp")

    def test_tools_list(self):
        req = json.dumps({
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        })
        resp = json.loads(self.mcp.handle_request(req))
        tools = resp["result"]["tools"]
        tool_names = [t["name"] for t in tools]
        self.assertIn("audit_repository", tool_names)
        self.assertIn("create_feature_dash", tool_names)
        self.assertIn("approve_proposal", tool_names)

    def test_tool_call_audit(self):
        req = json.dumps({
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "audit_repository",
                "arguments": {"repo_id": "sample-forked-repo"}
            }
        })
        resp = json.loads(self.mcp.handle_request(req))
        self.assertFalse(resp["result"].get("isError", False))
        content = json.loads(resp["result"]["content"][0]["text"])
        self.assertGreater(content["health_score"], 50)

if __name__ == "__main__":
    unittest.main()

"""Web UI & Management REST API Server.

Serves the developer management dashboard and provides REST & MCP endpoints
for controlling repositories, reviewing proposals, and monitoring resources.
"""
import json
import os
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
from typing import Dict, Any, Optional

from ..hermes.agent import HermesCIAgent
from ..mcp.server import MCPServer


class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """Multi-threaded HTTP server preventing sandbox runs from blocking dashboard/MCP polling."""
    daemon_threads = True
    allow_reuse_address = True

class RecursiveCIHandler(BaseHTTPRequestHandler):
    agent: Optional[HermesCIAgent] = None
    mcp_server: Optional[MCPServer] = None
    static_dir: str = os.path.join(os.path.dirname(__file__), "static")

    def _send_json(self, status: int, data: Any):
        payload = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()
        self.wfile.write(payload)

    def _send_file(self, file_path: str, content_type: str):
        if not os.path.exists(file_path):
            self.send_error(404, "File not found")
            return
        with open(file_path, "rb") as f:
            content = f.read()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        # Static file routing
        if path == "/" or path == "/index.html":
            self._send_file(os.path.join(self.static_dir, "index.html"), "text/html")
            return
        elif path == "/style.css":
            self._send_file(os.path.join(self.static_dir, "style.css"), "text/css")
            return
        elif path == "/app.js":
            self._send_file(os.path.join(self.static_dir, "app.js"), "application/javascript")
            return

        # REST API routing
        if path == "/api/v1/repos":
            repos = self.agent.state.list_repos()
            self._send_json(200, {"success": True, "repos": repos})

        elif path == "/api/v1/proposals":
            repo_id = query.get("repo_id", [None])[0]
            status = query.get("status", [None])[0]
            proposals = self.agent.state.list_proposals(repo_id, status)
            self._send_json(200, {"success": True, "proposals": proposals})

        elif path == "/api/v1/resources":
            res = self.agent.resources.get_resource_snapshot()
            self._send_json(200, {"success": True, "resources": res})

        elif path == "/api/v1/mcp/tools":
            tools = self.mcp_server.registry.get_tool_definitions()
            self._send_json(200, {"success": True, "tools": tools})

        elif path == "/api/v1/skills":
            snap = self.agent.resources.get_resource_snapshot()
            self._send_json(200, {
                "success": True,
                "micro_catalog": self.agent.dispatcher.get_micro_catalog(),
                "mounted_skills": self.agent.dispatcher.mounted_skills,
                "context_tokens_saved": snap.get("context_tokens_saved", 0),
            })

        else:
            self._send_json(404, {"error": f"Endpoint not found: {path}"})

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        content_len = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_len).decode("utf-8") if content_len > 0 else "{}"
        try:
            body = json.loads(post_data) if post_data else {}
        except json.JSONDecodeError:
            self._send_json(400, {"error": "Invalid JSON payload"})
            return

        # MCP Endpoint
        if path == "/mcp":
            resp_str = self.mcp_server.handle_request(post_data)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(resp_str.encode("utf-8"))
            return

        # REST API endpoints
        if path == "/api/v1/repos":
            repo_id = body.get("id")
            name = body.get("name", repo_id)
            repo_path = body.get("path")
            default_branch = body.get("default_branch", "main")
            test_command = body.get("test_command", "python -m unittest discover tests")

            if not repo_id or not repo_path:
                self._send_json(400, {"error": "Missing 'id' or 'path'"})
                return

            try:
                repo = self.agent.register_repo(repo_id, name, repo_path, default_branch, test_command)
                self._send_json(201, {"success": True, "repo": repo})
            except Exception as e:
                self._send_json(500, {"error": str(e)})

        elif path == "/api/v1/dash":
            repo_id = body.get("repo_id")
            batch_size = int(body.get("batch_size", 3))
            if not repo_id:
                self._send_json(400, {"error": "Missing 'repo_id'"})
                return
            try:
                result = self.agent.run_feature_dash(repo_id, batch_size)
                self._send_json(200, result)
            except Exception as e:
                self._send_json(500, {"error": str(e)})

        elif path.startswith("/api/v1/proposals/") and path.endswith("/approve"):
            prop_id = path.split("/")[4]
            notes = body.get("notes")
            answers = body.get("answers")
            res = self.agent.approve_and_implement(prop_id, maintainer_notes=notes, answers=answers)
            self._send_json(200, res)

        elif path.startswith("/api/v1/proposals/") and path.endswith("/answer"):
            prop_id = path.split("/")[4]
            answers = body.get("answers", {})
            res = self.agent.answer_questions(prop_id, answers=answers)
            self._send_json(200, res)

        elif path.startswith("/api/v1/proposals/") and path.endswith("/merge"):
            prop_id = path.split("/")[4]
            merge_to_base = bool(body.get("merge_to_base", False))
            res = self.agent.merge_proposal(prop_id, merge_to_base=merge_to_base)
            self._send_json(200, res)

        elif path.startswith("/api/v1/proposals/") and path.endswith("/reject"):
            prop_id = path.split("/")[4]
            rationale = body.get("rationale", "No specific reason provided")
            res = self.agent.reject(prop_id, rationale)
            self._send_json(200, res)

        elif path.startswith("/api/v1/proposals/") and path.endswith("/snooze"):
            prop_id = path.split("/")[4]
            hours = float(body.get("duration_hours", 24))
            res = self.agent.snooze(prop_id, int(hours * 3600))
            self._send_json(200, res)

        elif path == "/api/v1/telemetry":
            added = self.agent.telemetry.ingest_payload(body)
            self._send_json(200, {"success": True, "crashes_ingested": added})

        else:
            self._send_json(404, {"error": f"Endpoint not found: {path}"})

def run_server(host: str = "0.0.0.0", port: int = 18880, agent: Optional[HermesCIAgent] = None):
    """Start the HTTP server."""
    agent_instance = agent or HermesCIAgent()
    mcp_instance = MCPServer(agent_instance)

    RecursiveCIHandler.agent = agent_instance
    RecursiveCIHandler.mcp_server = mcp_instance

    server_address = (host, port)
    httpd = ThreadedHTTPServer(server_address, RecursiveCIHandler)
    print(f"[*] Hermes Recursive CI Management Server running at http://{host}:{port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[*] Shutting down server.")
        httpd.server_close()

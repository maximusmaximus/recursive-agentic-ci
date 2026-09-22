"""Model Context Protocol (MCP) JSON-RPC 2.0 Server.

Supports stdio transport (stdin/stdout) and HTTP/SSE transports
for interfacing with Hermes, Claude, and external AI agents.
"""
import json
import sys
from typing import Dict, Any, Optional
from .tools import MCPToolRegistry
from ..hermes.agent import HermesCIAgent

class MCPServer:
    """JSON-RPC 2.0 Server handling Model Context Protocol requests."""

    PROTOCOL_VERSION = "2024-11-05"

    def __init__(self, agent: Optional[HermesCIAgent] = None):
        self.agent = agent or HermesCIAgent()
        self.registry = MCPToolRegistry(self.agent)

    def handle_request(self, request_json: str) -> str:
        """Process a raw JSON-RPC string and return JSON response."""
        try:
            req = json.loads(request_json)
        except json.JSONDecodeError:
            return json.dumps({
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": "Parse error"}
            })

        msg_id = req.get("id")
        method = req.get("method")
        params = req.get("params", {})

        try:
            if method == "initialize":
                result = {
                    "protocolVersion": self.PROTOCOL_VERSION,
                    "serverInfo": {
                        "name": "recursive-agentic-ci-mcp",
                        "version": "1.0.0"
                    },
                    "capabilities": {
                        "tools": {}
                    }
                }
            elif method == "tools/list":
                result = {
                    "tools": self.registry.get_tool_definitions()
                }
            elif method == "tools/call":
                tool_name = params.get("name")
                tool_args = params.get("arguments", {})
                res = self.registry.execute_tool(tool_name, tool_args)
                result = {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(res, indent=2)
                        }
                    ],
                    "isError": False
                }
            elif method == "ping":
                result = {}
            else:
                return json.dumps({
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "error": {"code": -32601, "message": f"Method not found: {method}"}
                })

            return json.dumps({
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": result
            })

        except Exception as e:
            return json.dumps({
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {"code": -32000, "message": str(e)}
            })

    def run_stdio(self):
        """Run stdio loop reading JSON-RPC requests line-by-line."""
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            resp = self.handle_request(line)
            sys.stdout.write(resp + "\n")
            sys.stdout.flush()

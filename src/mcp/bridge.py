"""Telegram to MCP Bridge.

Allows users to pair remote or local MCP servers directly from Telegram
and invoke tools via interactive inline buttons.
"""
import json
import urllib.request
from typing import Dict, Any, List, Optional
from .server import MCPServer

class TelegramMCPBridge:
    """Bridges Telegram user commands with an active or remote MCP Server."""

    def __init__(self, local_server: Optional[MCPServer] = None):
        self.local_server = local_server or MCPServer()
        self._paired_servers: Dict[str, Dict[str, str]] = {}

    def pair_server(self, user_id: str, endpoint_url: str, auth_token: Optional[str] = None) -> Dict[str, Any]:
        """Pair an external MCP endpoint to a Telegram user session."""
        self._paired_servers[user_id] = {
            "url": endpoint_url.rstrip("/"),
            "token": auth_token or ""
        }
        return {
            "success": True,
            "user_id": user_id,
            "endpoint": endpoint_url,
            "message": f"Successfully paired MCP server at `{endpoint_url}` to Telegram session."
        }

    def list_available_tools(self, user_id: str) -> List[Dict[str, Any]]:
        """List tools available for the user (paired remote or local fallback)."""
        if user_id in self._paired_servers:
            # Remote query
            endpoint = self._paired_servers[user_id]["url"]
            token = self._paired_servers[user_id]["token"]
            req_body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}).encode("utf-8")
            headers = {"Content-Type": "application/json"}
            if token:
                headers["Authorization"] = f"Bearer {token}"
            req = urllib.request.Request(f"{endpoint}/mcp", data=req_body, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data.get("result", {}).get("tools", [])

        # Local fallback
        resp = json.loads(self.local_server.handle_request(json.dumps({
            "jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}
        })))
        return resp.get("result", {}).get("tools", [])

    def execute_user_tool(self, user_id: str, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute tool on behalf of Telegram user."""
        if user_id in self._paired_servers:
            endpoint = self._paired_servers[user_id]["url"]
            token = self._paired_servers[user_id]["token"]
            req_body = json.dumps({
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {"name": tool_name, "arguments": arguments}
            }).encode("utf-8")
            headers = {"Content-Type": "application/json"}
            if token:
                headers["Authorization"] = f"Bearer {token}"
            req = urllib.request.Request(f"{endpoint}/mcp", data=req_body, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data.get("result", {})

        # Local execution
        req_str = json.dumps({
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": arguments}
        })
        resp = json.loads(self.local_server.handle_request(req_str))
        return resp.get("result", {})

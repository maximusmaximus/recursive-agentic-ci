"""Example Python MCP Client.

Demonstrates pairing and invoking tools on the Recursive CI MCP server.
"""
import json
import urllib.request

def test_mcp_connection(server_url: str = "http://localhost:18880/mcp"):
    print(f"[*] Testing MCP Connection to {server_url}...")

    # 1. Initialize
    init_payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {}
    }
    resp = _call_rpc(server_url, init_payload)
    print("\n[1] MCP Initialize Response:")
    print(json.dumps(resp, indent=2))

    # 2. List tools
    list_payload = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list",
        "params": {}
    }
    resp = _call_rpc(server_url, list_payload)
    print("\n[2] Available MCP Tools:")
    for tool in resp.get("result", {}).get("tools", []):
        print(f"  - {tool['name']}: {tool['description']}")

    # 3. Call get_repo_health
    health_payload = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "get_repo_health",
            "arguments": {}
        }
    }
    resp = _call_rpc(server_url, health_payload)
    print("\n[3] get_repo_health Tool Result:")
    print(json.dumps(resp, indent=2))

def _call_rpc(url: str, payload: dict) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))

if __name__ == "__main__":
    test_mcp_connection()

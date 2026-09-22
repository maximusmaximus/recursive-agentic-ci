"""MCP Tool Specifications and Dispatchers.

Defines JSON-RPC 2.0 tool definitions and schemas for the Model Context Protocol.
"""
from typing import Dict, Any, List, Optional
from ..hermes.agent import HermesCIAgent

class MCPToolRegistry:
    """Manages MCP tool definitions and dispatches requests to HermesCIAgent."""

    def __init__(self, agent: HermesCIAgent):
        self.agent = agent

    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Return list of standard MCP tool definitions."""
        return [
            {
                "name": "audit_repository",
                "description": "Scans a repository AST, uncovers enhancement and mutation testing vectors, and returns a health score.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "repo_id": {"type": "string", "description": "Identifier of the target repository."}
                    },
                    "required": ["repo_id"]
                }
            },
            {
                "name": "create_feature_dash",
                "description": "Triggers a recursive sprint batch ('Dash') of proposed features and mutation bug resilience tests.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "repo_id": {"type": "string", "description": "Target repository identifier."},
                        "batch_size": {"type": "integer", "description": "Number of proposals to generate (default: 3)."}
                    },
                    "required": ["repo_id"]
                }
            },
            {
                "name": "approve_proposal",
                "description": "Approves a proposal and triggers isolated sandboxed test execution.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "proposal_id": {"type": "string", "description": "Identifier of the proposal to approve."},
                        "notes": {"type": "string", "description": "Optional maintainer implementation guidance."}
                    },
                    "required": ["proposal_id"]
                }
            },
            {
                "name": "reject_proposal",
                "description": "Rejects a proposal and records negative constraint rationale to train future proposals.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "proposal_id": {"type": "string", "description": "Proposal ID."},
                        "rationale": {"type": "string", "description": "Why this proposal is not useful or accepted."}
                    },
                    "required": ["proposal_id", "rationale"]
                }
            },
            {
                "name": "snooze_proposal",
                "description": "Delays proposal consideration by a specific number of seconds or hours.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "proposal_id": {"type": "string", "description": "Proposal ID."},
                        "duration_hours": {"type": "number", "description": "Hours to delay (e.g. 24, 72)."}
                    },
                    "required": ["proposal_id", "duration_hours"]
                }
            },
            {
                "name": "ingest_telemetry",
                "description": "Ingests production crash stack traces or latency metrics to prioritize real bug fixes.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "exception_type": {"type": "string", "description": "Type of exception (e.g. ZeroDivisionError)."},
                        "stack_trace": {"type": "string", "description": "Raw stack trace dump."}
                    },
                    "required": ["stack_trace"]
                }
            },
            {
                "name": "get_repo_health",
                "description": "Returns current health score, proposal counts, and active status of all repositories.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "repo_id": {"type": "string", "description": "Optional specific repository ID."}
                    }
                }
            }
        ]

    def execute_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Dispatch tool call to agent."""
        if name == "audit_repository":
            return self.agent.audit_repository(arguments["repo_id"])

        elif name == "create_feature_dash":
            repo_id = arguments["repo_id"]
            batch_size = arguments.get("batch_size", 3)
            return self.agent.run_feature_dash(repo_id, batch_size)

        elif name == "approve_proposal":
            proposal_id = arguments["proposal_id"]
            notes = arguments.get("notes")
            return self.agent.approve_and_implement(proposal_id, maintainer_notes=notes)

        elif name == "reject_proposal":
            proposal_id = arguments["proposal_id"]
            rationale = arguments["rationale"]
            return self.agent.reject(proposal_id, rationale)

        elif name == "snooze_proposal":
            proposal_id = arguments["proposal_id"]
            hours = float(arguments.get("duration_hours", 24))
            seconds = int(hours * 3600)
            return self.agent.snooze(proposal_id, seconds)

        elif name == "ingest_telemetry":
            trace = arguments["stack_trace"]
            exc = arguments.get("exception_type", "UnhandledException")
            entry = self.agent.telemetry.ingest_raw_stacktrace(trace, exc)
            return {"status": "ingested", "entry": entry}

        elif name == "get_repo_health":
            repo_id = arguments.get("repo_id")
            if repo_id:
                return {
                    "repo": self.agent.state.get_repo(repo_id),
                    "proposals": self.agent.state.list_proposals(repo_id)
                }
            return {
                "repos": self.agent.state.list_repos(),
                "proposals": self.agent.state.list_proposals()
            }

        raise ValueError(f"Unknown MCP tool: {name}")

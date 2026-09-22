"""User Feedback & Issue Tracker Synchronization Pattern.

Bridges GitHub Issues, Jira tickets, and user feedback into structured
feature proposals for recursive sprint dashes.
"""
from typing import Dict, List, Any, Optional

class FeedbackSyncManager:
    """Synchronizes external feedback and tickets into enhancement proposals."""

    def __init__(self):
        self._items: List[Dict[str, Any]] = []

    def ingest_ticket(self, ticket_id: str, title: str, description: str, tags: Optional[List[str]] = None):
        self._items.append({
            "id": ticket_id,
            "title": title,
            "description": description,
            "tags": tags or [],
            "status": "pending_analysis"
        })

    def get_pending_tasks(self) -> List[Dict[str, Any]]:
        return [item for item in self._items if item.get("status") == "pending_analysis"]

    def mark_processed(self, ticket_id: str):
        for item in self._items:
            if item.get("id") == ticket_id:
                item["status"] = "converted_to_proposal"

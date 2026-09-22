"""SQLite State Persistence Layer for Proposals, Snooze Timers, and Repositories.

Provides atomic transitions across the proposal lifecycle:
PROPOSED -> SNOOZED / REJECTED / APPROVED -> IN_SANDBOX -> VERIFIED / FAILED -> MERGED
"""
import json
import os
import sqlite3
import time
from typing import Dict, List, Any, Optional

class HermesStateManager:
    """Manages persistent SQLite state for repositories, proposals, and feedback."""

    def __init__(self, db_path: str = "data/recursive_ci.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS repositories (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    path TEXT NOT NULL,
                    default_branch TEXT DEFAULT 'main',
                    test_command TEXT DEFAULT 'python -m unittest discover tests',
                    health_score REAL DEFAULT 80.0,
                    status TEXT DEFAULT 'ACTIVE',
                    registered_at REAL NOT NULL
                );

                CREATE TABLE IF NOT EXISTS proposals (
                    id TEXT PRIMARY KEY,
                    repo_id TEXT NOT NULL,
                    type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    rationale TEXT,
                    proposed_diff_summary TEXT,
                    affected_files TEXT,
                    test_plan TEXT,
                    safety_score REAL DEFAULT 0.9,
                    semantic_delta_score REAL DEFAULT 0.5,
                    status TEXT DEFAULT 'PROPOSED',
                    snooze_until REAL DEFAULT 0,
                    rejection_reason TEXT,
                    maintainer_notes TEXT,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL,
                    FOREIGN KEY(repo_id) REFERENCES repositories(id)
                );

                CREATE TABLE IF NOT EXISTS maintainer_feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    proposal_id TEXT NOT NULL,
                    repo_id TEXT NOT NULL,
                    user_id TEXT,
                    action TEXT NOT NULL,
                    rationale TEXT,
                    created_at REAL NOT NULL
                );
            """)

    def register_repo(self, repo_id: str, name: str, path: str, default_branch: str = "main", test_command: str = "python -m unittest discover tests") -> Dict[str, Any]:
        with self._get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO repositories (id, name, path, default_branch, test_command, registered_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (repo_id, name, path, default_branch, test_command, time.time()))
        return self.get_repo(repo_id)

    def get_repo(self, repo_id: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            row = conn.execute("SELECT * FROM repositories WHERE id = ?", (repo_id,)).fetchone()
            return dict(row) if row else None

    def list_repos(self) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM repositories ORDER BY registered_at DESC").fetchall()
            return [dict(r) for r in rows]

    def update_repo_health(self, repo_id: str, health_score: float):
        with self._get_connection() as conn:
            conn.execute("UPDATE repositories SET health_score = ? WHERE id = ?", (health_score, repo_id))

    def save_proposal(self, proposal: Dict[str, Any]) -> Dict[str, Any]:
        now = time.time()
        with self._get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO proposals (
                    id, repo_id, type, title, rationale, proposed_diff_summary,
                    affected_files, test_plan, safety_score, semantic_delta_score,
                    status, snooze_until, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                proposal["id"],
                proposal["repo_id"],
                proposal.get("type", "feature"),
                proposal["title"],
                proposal.get("rationale", ""),
                proposal.get("proposed_diff_summary", ""),
                json.dumps(proposal.get("affected_files", [])),
                proposal.get("test_plan", ""),
                proposal.get("safety_score", 0.9),
                proposal.get("semantic_delta_score", 0.5),
                proposal.get("status", "PROPOSED"),
                proposal.get("snooze_until", 0),
                proposal.get("created_at", now),
                now
            ))
        return self.get_proposal(proposal["id"])

    def get_proposal(self, proposal_id: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            row = conn.execute("SELECT * FROM proposals WHERE id = ?", (proposal_id,)).fetchone()
            if not row:
                return None
            res = dict(row)
            try:
                res["affected_files"] = json.loads(res["affected_files"])
            except Exception:
                res["affected_files"] = []
            return res

    def list_proposals(self, repo_id: Optional[str] = None, status: Optional[str] = None) -> List[Dict[str, Any]]:
        query = "SELECT * FROM proposals WHERE 1=1"
        params = []
        if repo_id:
            query += " AND repo_id = ?"
            params.append(repo_id)
        if status:
            query += " AND status = ?"
            params.append(status)
        query += " ORDER BY created_at DESC"

        with self._get_connection() as conn:
            rows = conn.execute(query, params).fetchall()
            results = []
            for r in rows:
                item = dict(r)
                try:
                    item["affected_files"] = json.loads(item["affected_files"])
                except Exception:
                    item["affected_files"] = []
                results.append(item)
            return results

    def approve_proposal(self, proposal_id: str, user_id: str = "telegram_user", notes: Optional[str] = None) -> bool:
        now = time.time()
        with self._get_connection() as conn:
            cur = conn.execute("""
                UPDATE proposals 
                SET status = 'APPROVED', maintainer_notes = ?, updated_at = ?
                WHERE id = ? AND status IN ('PROPOSED', 'SNOOZED')
            """, (notes or "", now, proposal_id))
            if cur.rowcount > 0:
                p = self.get_proposal(proposal_id)
                conn.execute("""
                    INSERT INTO maintainer_feedback (proposal_id, repo_id, user_id, action, rationale, created_at)
                    VALUES (?, ?, ?, 'APPROVE', ?, ?)
                """, (proposal_id, p["repo_id"], user_id, notes or "", now))
                return True
        return False

    def reject_proposal(self, proposal_id: str, rationale: str, user_id: str = "telegram_user") -> bool:
        now = time.time()
        with self._get_connection() as conn:
            cur = conn.execute("""
                UPDATE proposals 
                SET status = 'REJECTED', rejection_reason = ?, updated_at = ?
                WHERE id = ? AND status IN ('PROPOSED', 'SNOOZED')
            """, (rationale, now, proposal_id))
            if cur.rowcount > 0:
                p = self.get_proposal(proposal_id)
                conn.execute("""
                    INSERT INTO maintainer_feedback (proposal_id, repo_id, user_id, action, rationale, created_at)
                    VALUES (?, ?, ?, 'REJECT', ?, ?)
                """, (proposal_id, p["repo_id"], user_id, rationale, now))
                return True
        return False

    def snooze_proposal(self, proposal_id: str, duration_seconds: int) -> bool:
        now = time.time()
        snooze_until = now + duration_seconds
        with self._get_connection() as conn:
            cur = conn.execute("""
                UPDATE proposals 
                SET status = 'SNOOZED', snooze_until = ?, updated_at = ?
                WHERE id = ?
            """, (snooze_until, now, proposal_id))
            return cur.rowcount > 0

    def wake_snoozed_proposals(self) -> List[Dict[str, Any]]:
        """Find snoozed proposals whose timer has expired and reset to PROPOSED."""
        now = time.time()
        with self._get_connection() as conn:
            rows = conn.execute("""
                SELECT * FROM proposals 
                WHERE status = 'SNOOZED' AND snooze_until <= ? AND snooze_until > 0
            """, (now,)).fetchall()
            woken = []
            for r in rows:
                item = dict(r)
                conn.execute("""
                    UPDATE proposals SET status = 'PROPOSED', snooze_until = 0, updated_at = ?
                    WHERE id = ?
                """, (now, item["id"]))
                woken.append(item)
            return woken

    def update_proposal_status(self, proposal_id: str, status: str, notes: Optional[str] = None):
        now = time.time()
        with self._get_connection() as conn:
            conn.execute("""
                UPDATE proposals SET status = ?, maintainer_notes = COALESCE(?, maintainer_notes), updated_at = ?
                WHERE id = ?
            """, (status, notes, now, proposal_id))

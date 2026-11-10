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
        conn = sqlite3.connect(self.db_path, timeout=5.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA busy_timeout=5000;")
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
                    skill_affinities TEXT DEFAULT '["recursive-ci"]',
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
                    clarifying_questions TEXT DEFAULT '[]',
                    question_answers TEXT DEFAULT '{}',
                    candidate_patches TEXT DEFAULT '{}',
                    branch_name TEXT,
                    commit_sha TEXT,
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

                CREATE TABLE IF NOT EXISTS governance_usage (
                    repo_id TEXT PRIMARY KEY,
                    tokens_used_today INTEGER DEFAULT 0,
                    proposals_today INTEGER DEFAULT 0,
                    consecutive_rejections INTEGER DEFAULT 0,
                    last_run_timestamp REAL DEFAULT 0,
                    circuit_breaker_active INTEGER DEFAULT 0,
                    reset_timestamp REAL NOT NULL
                );

                CREATE TABLE IF NOT EXISTS telemetry_crashes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    exception_type TEXT NOT NULL,
                    module TEXT NOT NULL,
                    line_number INTEGER DEFAULT 0,
                    function TEXT NOT NULL,
                    stack_trace TEXT,
                    frequency INTEGER DEFAULT 1,
                    updated_at REAL NOT NULL,
                    UNIQUE(module, function)
                );
            """)
            self._ensure_column(conn, "repositories", "skill_affinities", "TEXT DEFAULT '[\"recursive-ci\"]'")
            self._ensure_column(conn, "proposals", "clarifying_questions", "TEXT DEFAULT '[]'")
            self._ensure_column(conn, "proposals", "question_answers", "TEXT DEFAULT '{}'")
            self._ensure_column(conn, "proposals", "candidate_patches", "TEXT DEFAULT '{}'")
            self._ensure_column(conn, "proposals", "branch_name", "TEXT")
            self._ensure_column(conn, "proposals", "commit_sha", "TEXT")

    def _ensure_column(self, conn: sqlite3.Connection, table: str, column: str, col_def: str):
        cols = {row["name"] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}
        if column not in cols:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_def}")

    def _deserialize_repo(self, row: sqlite3.Row) -> Dict[str, Any]:
        item = dict(row)
        try:
            item["skill_affinities"] = json.loads(item.get("skill_affinities") or '["recursive-ci"]')
        except Exception:
            item["skill_affinities"] = ["recursive-ci"]
        return item

    def _deserialize_proposal(self, row: sqlite3.Row) -> Dict[str, Any]:
        res = dict(row)
        for field, fallback in (
            ("affected_files", []),
            ("clarifying_questions", []),
            ("question_answers", {}),
            ("candidate_patches", {}),
        ):
            try:
                res[field] = json.loads(res.get(field) or json.dumps(fallback))
            except Exception:
                res[field] = fallback
        return res

    def register_repo(
        self,
        repo_id: str,
        name: str,
        path: str,
        default_branch: str = "main",
        test_command: str = "python -m unittest discover tests",
        skill_affinities: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        affinities_json = json.dumps(skill_affinities or ["recursive-ci"])
        with self._get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO repositories (id, name, path, default_branch, test_command, skill_affinities, registered_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (repo_id, name, path, default_branch, test_command, affinities_json, time.time()))
        return self.get_repo(repo_id)

    def get_repo(self, repo_id: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            row = conn.execute("SELECT * FROM repositories WHERE id = ?", (repo_id,)).fetchone()
            return self._deserialize_repo(row) if row else None

    def list_repos(self) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM repositories ORDER BY registered_at DESC").fetchall()
            return [self._deserialize_repo(r) for r in rows]

    def update_repo_health(self, repo_id: str, health_score: float, skill_affinities: Optional[List[str]] = None):
        with self._get_connection() as conn:
            if skill_affinities is not None:
                conn.execute(
                    "UPDATE repositories SET health_score = ?, skill_affinities = ? WHERE id = ?",
                    (health_score, json.dumps(skill_affinities), repo_id),
                )
            else:
                conn.execute("UPDATE repositories SET health_score = ? WHERE id = ?", (health_score, repo_id))

    def save_proposal(self, proposal: Dict[str, Any]) -> Dict[str, Any]:
        now = time.time()
        with self._get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO proposals (
                    id, repo_id, type, title, rationale, proposed_diff_summary,
                    affected_files, clarifying_questions, question_answers, candidate_patches,
                    branch_name, commit_sha, test_plan, safety_score, semantic_delta_score,
                    status, snooze_until, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                proposal["id"],
                proposal["repo_id"],
                proposal.get("type", "feature"),
                proposal["title"],
                proposal.get("rationale", ""),
                proposal.get("proposed_diff_summary", ""),
                json.dumps(proposal.get("affected_files", [])),
                json.dumps(proposal.get("clarifying_questions", [])),
                json.dumps(proposal.get("question_answers", {})),
                json.dumps(proposal.get("candidate_patches", {})),
                proposal.get("branch_name"),
                proposal.get("commit_sha"),
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
            return self._deserialize_proposal(row)

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
            return [self._deserialize_proposal(r) for r in rows]

    def save_proposal_answers(self, proposal_id: str, answers: Dict[str, str]):
        now = time.time()
        with self._get_connection() as conn:
            conn.execute(
                "UPDATE proposals SET question_answers = ?, updated_at = ? WHERE id = ?",
                (json.dumps(answers), now, proposal_id),
            )

    def save_candidate_patches(self, proposal_id: str, patch_files: Dict[str, str]):
        now = time.time()
        with self._get_connection() as conn:
            conn.execute(
                "UPDATE proposals SET candidate_patches = ?, updated_at = ? WHERE id = ?",
                (json.dumps(patch_files), now, proposal_id),
            )

    def mark_proposal_merged(self, proposal_id: str, branch_name: str, commit_sha: Optional[str] = None, notes: Optional[str] = None):
        now = time.time()
        with self._get_connection() as conn:
            conn.execute(
                """
                UPDATE proposals
                SET status = 'MERGED', branch_name = ?, commit_sha = ?, maintainer_notes = COALESCE(?, maintainer_notes), updated_at = ?
                WHERE id = ?
                """,
                (branch_name, commit_sha, notes, now, proposal_id),
            )

    def approve_proposal(self, proposal_id: str, user_id: str = "telegram_user", notes: Optional[str] = None) -> bool:
        now = time.time()
        with self._get_connection() as conn:
            cur = conn.execute("""
                UPDATE proposals 
                SET status = 'APPROVED', maintainer_notes = ?, updated_at = ?
                WHERE id = ? AND status IN ('PROPOSED', 'SNOOZED', 'AWAITING_ANSWERS')
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
                WHERE id = ? AND status IN ('PROPOSED', 'SNOOZED', 'AWAITING_ANSWERS')
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

    def get_governance_usage(self, repo_id: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            row = conn.execute("SELECT * FROM governance_usage WHERE repo_id = ?", (repo_id,)).fetchone()
            if not row:
                return None
            data = dict(row)
            data["circuit_breaker_active"] = bool(data.get("circuit_breaker_active", 0))
            return data

    def save_governance_usage(self, repo_id: str, state: Dict[str, Any]):
        with self._get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO governance_usage (
                    repo_id, tokens_used_today, proposals_today, consecutive_rejections,
                    last_run_timestamp, circuit_breaker_active, reset_timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                repo_id,
                int(state.get("tokens_used_today", 0)),
                int(state.get("proposals_today", 0)),
                int(state.get("consecutive_rejections", 0)),
                float(state.get("last_run_timestamp", 0.0)),
                1 if state.get("circuit_breaker_active") else 0,
                float(state.get("reset_timestamp", time.time() + 86400)),
            ))

    def get_total_tokens_today(self) -> int:
        now = time.time()
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT COALESCE(SUM(tokens_used_today), 0) AS total FROM governance_usage WHERE reset_timestamp > ?",
                (now,),
            ).fetchone()
            return int(row["total"]) if row else 0

    def record_maintainer_feedback(
        self,
        proposal_id: str,
        action: str,
        rationale: str,
        repo_id: str = "global",
        user_id: str = "maintainer",
    ):
        if not rationale:
            return
        now = time.time()
        with self._get_connection() as conn:
            existing = conn.execute(
                "SELECT id FROM maintainer_feedback WHERE proposal_id = ? AND action = ? AND rationale = ?",
                (proposal_id, action, rationale),
            ).fetchone()
            if not existing:
                conn.execute("""
                    INSERT INTO maintainer_feedback (proposal_id, repo_id, user_id, action, rationale, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (proposal_id, repo_id, user_id, action, rationale, now))

    def list_maintainer_feedback(self, repo_id: Optional[str] = None) -> List[Dict[str, Any]]:
        query = "SELECT * FROM maintainer_feedback WHERE rationale IS NOT NULL AND rationale != ''"
        params: List[Any] = []
        if repo_id:
            query += " AND repo_id = ?"
            params.append(repo_id)
        query += " ORDER BY id ASC"
        with self._get_connection() as conn:
            rows = conn.execute(query, params).fetchall()
            return [dict(r) for r in rows]

    def upsert_telemetry_crash(self, crash: Dict[str, Any], max_history: int = 200):
        now = time.time()
        mod = crash.get("module", "unknown")
        fn = crash.get("function", "unknown")
        freq = int(crash.get("frequency", 1))
        with self._get_connection() as conn:
            existing = conn.execute(
                "SELECT id, frequency FROM telemetry_crashes WHERE module = ? AND function = ?",
                (mod, fn),
            ).fetchone()
            if existing:
                conn.execute(
                    "UPDATE telemetry_crashes SET frequency = ?, stack_trace = COALESCE(?, stack_trace), updated_at = ? WHERE id = ?",
                    (int(existing["frequency"]) + freq, crash.get("stack_trace"), now, existing["id"]),
                )
            else:
                conn.execute("""
                    INSERT INTO telemetry_crashes (exception_type, module, line_number, function, stack_trace, frequency, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    crash.get("exception_type", "UnhandledException"),
                    mod,
                    int(crash.get("line_number", 0)),
                    fn,
                    crash.get("stack_trace", ""),
                    freq,
                    now,
                ))
                conn.execute("""
                    DELETE FROM telemetry_crashes WHERE id NOT IN (
                        SELECT id FROM telemetry_crashes ORDER BY updated_at DESC LIMIT ?
                    )
                """, (max_history,))

    def list_telemetry_crashes(self, limit: int = 200) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT exception_type, module, line_number, function, stack_trace, frequency FROM telemetry_crashes ORDER BY frequency DESC, updated_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return [dict(r) for r in rows]

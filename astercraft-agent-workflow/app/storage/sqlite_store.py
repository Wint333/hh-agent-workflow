import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from app.core.config import get_settings


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class SQLiteStore:
    def __init__(self, db_path: Optional[Path] = None):
        self.settings = get_settings()
        self.db_path = db_path or self.settings.db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_db()

    @contextmanager
    def connect(self):
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def init_db(self) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    user_id TEXT PRIMARY KEY,
                    state_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    session_epoch INTEGER NOT NULL DEFAULT 0
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS outbox (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    status TEXT NOT NULL,
                    meta_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS analytics_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    event_type TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )

    def get_session_state(self, user_id: str) -> Optional[Dict[str, Any]]:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT state_json FROM sessions WHERE user_id = ?",
                (user_id,),
            ).fetchone()
        if not row:
            return None
        return json.loads(row["state_json"])

    def upsert_session_state(self, user_id: str, state: Dict[str, Any]) -> None:
        now = utc_now()
        state_json = json.dumps(state, ensure_ascii=False)
        with self.connect() as conn:
            exists = conn.execute(
                "SELECT user_id FROM sessions WHERE user_id = ?",
                (user_id,),
            ).fetchone()
            if exists:
                conn.execute(
                    "UPDATE sessions SET state_json = ?, updated_at = ? WHERE user_id = ?",
                    (state_json, now, user_id),
                )
            else:
                conn.execute(
                    """
                    INSERT INTO sessions(user_id, state_json, created_at, updated_at, session_epoch)
                    VALUES (?, ?, ?, ?, 0)
                    """,
                    (user_id, state_json, now, now),
                )

    def reset_session(self, user_id: str, state: Dict[str, Any]) -> None:
        now = utc_now()
        state_json = json.dumps(state, ensure_ascii=False)
        with self.connect() as conn:
            row = conn.execute(
                "SELECT session_epoch FROM sessions WHERE user_id = ?",
                (user_id,),
            ).fetchone()
            epoch = int(row["session_epoch"]) + 1 if row else 1
            conn.execute(
                """
                INSERT INTO sessions(user_id, state_json, created_at, updated_at, session_epoch)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    state_json=excluded.state_json,
                    updated_at=excluded.updated_at,
                    session_epoch=excluded.session_epoch
                """,
                (user_id, state_json, now, now, epoch),
            )
            conn.execute(
                "UPDATE outbox SET status = 'cancelled', updated_at = ? WHERE user_id = ? AND status = 'pending'",
                (now, user_id),
            )

    def add_message(self, user_id: str, role: str, content: str) -> None:
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO messages(user_id, role, content, created_at) VALUES (?, ?, ?, ?)",
                (user_id, role, content, utc_now()),
            )

    def create_outbox_task(self, task_id: str, user_id: str, task_type: str, content: str, meta: Dict[str, Any]) -> None:
        now = utc_now()
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO outbox(id, user_id, type, content, status, meta_json, created_at, updated_at)
                VALUES (?, ?, ?, ?, 'pending', ?, ?, ?)
                """,
                (task_id, user_id, task_type, content, json.dumps(meta, ensure_ascii=False), now, now),
            )

    def list_pending_outbox(self, limit: int = 20) -> List[Dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM outbox
                WHERE status = 'pending'
                ORDER BY created_at ASC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [self._outbox_row(row) for row in rows]

    def ack_outbox(self, task_id: str) -> bool:
        with self.connect() as conn:
            cursor = conn.execute(
                "UPDATE outbox SET status = 'sent', updated_at = ? WHERE id = ? AND status = 'pending'",
                (utc_now(), task_id),
            )
            return cursor.rowcount > 0

    def record_event(self, event_type: str, payload: Dict[str, Any], user_id: Optional[str] = None) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO analytics_events(user_id, event_type, payload_json, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (user_id, event_type, json.dumps(payload, ensure_ascii=False), utc_now()),
            )

    def fetch_events(self, event_types: Optional[Iterable[str]] = None) -> List[Dict[str, Any]]:
        sql = "SELECT * FROM analytics_events"
        params: tuple[Any, ...] = ()
        if event_types:
            event_types = list(event_types)
            placeholders = ",".join("?" for _ in event_types)
            sql += f" WHERE event_type IN ({placeholders})"
            params = tuple(event_types)
        with self.connect() as conn:
            rows = conn.execute(sql, params).fetchall()
        return [
            {
                "id": row["id"],
                "user_id": row["user_id"],
                "event_type": row["event_type"],
                "payload": json.loads(row["payload_json"]),
                "created_at": row["created_at"],
            }
            for row in rows
        ]

    def count_rows(self, table: str) -> int:
        if table not in {"sessions", "messages", "outbox", "analytics_events"}:
            raise ValueError("invalid table")
        with self.connect() as conn:
            row = conn.execute(f"SELECT COUNT(*) AS c FROM {table}").fetchone()
        return int(row["c"])

    @staticmethod
    def _outbox_row(row: sqlite3.Row) -> Dict[str, Any]:
        return {
            "id": row["id"],
            "user_id": row["user_id"],
            "type": row["type"],
            "content": row["content"],
            "status": row["status"],
            "created_at": row["created_at"],
            "meta": json.loads(row["meta_json"]),
        }

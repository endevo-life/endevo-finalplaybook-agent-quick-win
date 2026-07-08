"""File-backed SQLite store: persists across restarts, no server, no AWS."""
from typing import Optional

from app.data.store.base import now, month_key

class SqliteStore:
    """File-backed store using SQLite. Persists across restarts with ZERO extra
    setup (no server, no AWS) -- the right choice for local dev and early launch.
    DB path from SQLITE_PATH (default ./final_playbook.db). Same interface as the
    other stores, so route code never changes."""

    def __init__(self, path: str):
        import sqlite3
        # check_same_thread=False: FastAPI may serve requests on worker threads.
        self._conn = sqlite3.connect(path, check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL")  # better concurrent reads
        self._init_schema()

    def _init_schema(self):
        c = self._conn
        c.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                email TEXT PRIMARY KEY,
                tier TEXT NOT NULL DEFAULT 'free',
                created_at INTEGER NOT NULL,
                stripe_customer_id TEXT
            );
            CREATE TABLE IF NOT EXISTS sessions (
                token TEXT PRIMARY KEY,
                email TEXT NOT NULL,
                expires_at INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS usage (
                email TEXT NOT NULL,
                month TEXT NOT NULL,
                personalize_count INTEGER NOT NULL DEFAULT 0,
                chat_count INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (email, month)
            );
            CREATE TABLE IF NOT EXISTS plans (
                email TEXT PRIMARY KEY,
                answers TEXT, plan TEXT, tracked TEXT, narrative TEXT,
                updated_at INTEGER
            );
            CREATE TABLE IF NOT EXISTS chat (
                email TEXT NOT NULL,
                seq INTEGER NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                PRIMARY KEY (email, seq)
            );
            """
        )
        c.commit()

    # --- users / entitlements ---
    def get_user(self, email: str) -> Optional[dict]:
        row = self._conn.execute(
            "SELECT email, tier, created_at, stripe_customer_id FROM users WHERE email=?",
            (email,),
        ).fetchone()
        if not row:
            return None
        return {"email": row[0], "tier": row[1], "created_at": row[2], "stripe_customer_id": row[3]}

    def upsert_user(self, email: str, tier: str = "free", stripe_customer_id: str = None) -> dict:
        existing = self.get_user(email)
        if existing:
            self._conn.execute(
                "UPDATE users SET tier=?, stripe_customer_id=COALESCE(?, stripe_customer_id) WHERE email=?",
                (tier, stripe_customer_id, email),
            )
        else:
            self._conn.execute(
                "INSERT INTO users (email, tier, created_at, stripe_customer_id) VALUES (?,?,?,?)",
                (email, tier, now(), stripe_customer_id),
            )
        self._conn.commit()
        return self.get_user(email)

    def set_tier(self, email: str, tier: str) -> None:
        if self.get_user(email):
            self._conn.execute("UPDATE users SET tier=? WHERE email=?", (tier, email))
        else:
            self._conn.execute(
                "INSERT INTO users (email, tier, created_at) VALUES (?,?,?)",
                (email, tier, now()),
            )
        self._conn.commit()

    def email_for_stripe_customer(self, stripe_customer_id: str) -> Optional[str]:
        row = self._conn.execute(
            "SELECT email FROM users WHERE stripe_customer_id=?", (stripe_customer_id,)
        ).fetchone()
        return row[0] if row else None

    # --- sessions ---
    def create_session(self, token: str, email: str, ttl_seconds: int) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO sessions (token, email, expires_at) VALUES (?,?,?)",
            (token, email, now() + ttl_seconds),
        )
        self._conn.commit()

    def get_session_email(self, token: str) -> Optional[str]:
        row = self._conn.execute(
            "SELECT email, expires_at FROM sessions WHERE token=?", (token,)
        ).fetchone()
        if not row or row[1] < now():
            if row:
                self.delete_session(token)
            return None
        return row[0]

    def delete_session(self, token: str) -> None:
        self._conn.execute("DELETE FROM sessions WHERE token=?", (token,))
        self._conn.commit()

    # --- usage metering ---
    def get_usage(self, email: str) -> dict:
        row = self._conn.execute(
            "SELECT personalize_count, chat_count FROM usage WHERE email=? AND month=?",
            (email, month_key()),
        ).fetchone()
        if not row:
            return {"personalize_count": 0, "chat_count": 0}
        return {"personalize_count": row[0], "chat_count": row[1]}

    def increment_usage(self, email: str, field: str) -> int:
        if field not in ("personalize_count", "chat_count"):
            raise ValueError(f"bad usage field: {field!r}")
        month = month_key()
        self._conn.execute(
            "INSERT OR IGNORE INTO usage (email, month) VALUES (?,?)", (email, month)
        )
        self._conn.execute(
            f"UPDATE usage SET {field} = {field} + 1 WHERE email=? AND month=?",
            (email, month),
        )
        self._conn.commit()
        return self.get_usage(email)[field]

    def reset_usage(self, email: str) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO usage (email, month, personalize_count, chat_count) "
            "VALUES (?,?,0,0)", (email, month_key()),
        )
        self._conn.commit()

    # --- saved plan + progress ---
    def get_plan(self, email: str) -> Optional[dict]:
        import json as _json
        row = self._conn.execute(
            "SELECT answers, plan, tracked, narrative, updated_at FROM plans WHERE email=?",
            (email,),
        ).fetchone()
        if not row:
            return None
        return {
            "answers": _json.loads(row[0]) if row[0] else {},
            "plan": _json.loads(row[1]) if row[1] else None,
            "tracked": _json.loads(row[2]) if row[2] else {},
            "narrative": _json.loads(row[3]) if row[3] else None,
            "updated_at": row[4] or 0,
        }

    def save_plan(self, email: str, answers=None, plan=None, tracked=None, narrative=None) -> None:
        import json as _json
        cur = self.get_plan(email) or {}
        merged = {
            "answers": answers if answers is not None else cur.get("answers", {}),
            "plan": plan if plan is not None else cur.get("plan"),
            "tracked": tracked if tracked is not None else cur.get("tracked", {}),
            "narrative": narrative if narrative is not None else cur.get("narrative"),
        }
        self._conn.execute(
            "INSERT OR REPLACE INTO plans (email, answers, plan, tracked, narrative, updated_at) "
            "VALUES (?,?,?,?,?,?)",
            (email, _json.dumps(merged["answers"]), _json.dumps(merged["plan"]),
             _json.dumps(merged["tracked"]), _json.dumps(merged["narrative"]), now()),
        )
        self._conn.commit()

    # --- chat history ---
    def get_chat_history(self, email: str, limit: int = 100) -> list:
        rows = self._conn.execute(
            "SELECT role, content FROM chat WHERE email=? ORDER BY seq ASC LIMIT ?",
            (email, limit),
        ).fetchall()
        return [{"role": r[0], "content": r[1]} for r in rows]

    def append_chat(self, email: str, role: str, content: str) -> None:
        row = self._conn.execute("SELECT COALESCE(MAX(seq),0)+1 FROM chat WHERE email=?", (email,)).fetchone()
        self._conn.execute(
            "INSERT INTO chat (email, seq, role, content) VALUES (?,?,?,?)",
            (email, row[0], role, content),
        )
        self._conn.commit()

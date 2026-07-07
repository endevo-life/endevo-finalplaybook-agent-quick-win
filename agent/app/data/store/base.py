"""Persistence abstraction: users, entitlements, sessions, usage, saved plans,
and chat history.

One interface, three backends selected by the STORE_BACKEND env var:
- "memory"   -- in-process dict. Zero setup, LOST ON RESTART. Test suite only.
- "sqlite"   -- local SQLite file (SQLITE_PATH). Persists, offline local dev.
- "dynamodb" -- AWS, five tables under DDB_TABLE_PREFIX (default "mfp-dev-"):
                {prefix}users, sessions, usage, plans, chat.

Every store implements the same method set (see MemoryStore for the canonical
reference), so swapping backends never touches service or route code.

Store contract
--------------
Users/entitlements: get_user, upsert_user, set_tier, email_for_stripe_customer
Sessions:           create_session, get_session_email, delete_session
Usage metering:     get_usage, increment_usage
Saved plan:         get_plan, save_plan
Chat history:       get_chat_history, append_chat
"""
import os
import time
from typing import Optional


def now() -> int:
    return int(time.time())


def month_key(ts: Optional[int] = None) -> str:
    t = time.gmtime(ts if ts is not None else now())
    return f"{t.tm_year:04d}-{t.tm_mon:02d}"


_store = None


def get_store():
    """Singleton store selected by STORE_BACKEND ("memory" | "sqlite" | "dynamodb")."""
    global _store
    if _store is not None:
        return _store
    backend = os.environ.get("STORE_BACKEND", "memory")
    if backend == "dynamodb":
        from app.data.store.dynamodb import DynamoStore
        _store = DynamoStore(os.environ.get("DDB_TABLE_PREFIX", "mfp-dev-"))
    elif backend == "sqlite":
        from app.data.store.sqlite import SqliteStore
        _store = SqliteStore(os.environ.get("SQLITE_PATH", "final_playbook.db"))
    elif backend == "memory":
        from app.data.store.memory import MemoryStore
        _store = MemoryStore()
    else:
        raise ValueError(
            f"Unknown STORE_BACKEND: {backend!r} (expected 'memory', 'sqlite', or 'dynamodb')"
        )
    return _store


def reset_store():
    """Drop the singleton so the next get_store() reconnects. Used by tests and
    after a config change."""
    global _store
    _store = None

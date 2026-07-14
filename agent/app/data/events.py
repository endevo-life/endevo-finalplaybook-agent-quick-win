"""Analytics events + admin config store.

Standalone, share-ready: every event carries a `plane` tag ("b2c") and a stable
shape, so this B2C stream can later be merged into the shared B2B operator
dashboard without reshaping data. This does NOT write to the live B2B audit
stream -- it owns its own tables (mfp-dev-events, mfp-dev-config).

Two tiny stores, backend-selected the same way as the main store:
- memory  : in-process (tests)
- sqlite  : local file (dev)
- dynamodb: mfp-dev-events (PK plane, SK ts#id), mfp-dev-config (PK key)
"""
import json
import os
import time
from typing import Optional

PLANE = "b2c"


def _now_ms() -> int:
    return int(time.time() * 1000)


# ── Memory backend ───────────────────────────────────────────────────────────
class _MemoryEvents:
    def __init__(self):
        self.events = []          # [{ts, plane, type, email, props}]
        self.config = {}          # key -> value

    def emit(self, event_type, email=None, props=None):
        self.events.append({
            "ts": _now_ms(), "plane": PLANE, "type": event_type,
            "email": email, "props": props or {},
        })

    def list_events(self, limit=1000):
        return list(self.events[-limit:])

    def get_config(self, key, default=None):
        return self.config.get(key, default)

    def set_config(self, key, value):
        self.config[key] = value

    def all_config(self):
        return dict(self.config)


# ── SQLite backend ───────────────────────────────────────────────────────────
class _SqliteEvents:
    def __init__(self, path):
        import sqlite3
        self._c = sqlite3.connect(path, check_same_thread=False)
        self._c.executescript(
            """
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts INTEGER, plane TEXT, type TEXT, email TEXT, props TEXT
            );
            CREATE TABLE IF NOT EXISTS config (key TEXT PRIMARY KEY, value TEXT);
            """
        )
        self._c.commit()

    def emit(self, event_type, email=None, props=None):
        self._c.execute(
            "INSERT INTO events (ts, plane, type, email, props) VALUES (?,?,?,?,?)",
            (_now_ms(), PLANE, event_type, email, json.dumps(props or {})),
        )
        self._c.commit()

    def list_events(self, limit=1000):
        rows = self._c.execute(
            "SELECT ts, plane, type, email, props FROM events ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [{"ts": r[0], "plane": r[1], "type": r[2], "email": r[3],
                 "props": json.loads(r[4] or "{}")} for r in rows]

    def get_config(self, key, default=None):
        row = self._c.execute("SELECT value FROM config WHERE key=?", (key,)).fetchone()
        return json.loads(row[0]) if row else default

    def set_config(self, key, value):
        self._c.execute("INSERT OR REPLACE INTO config (key, value) VALUES (?,?)",
                        (key, json.dumps(value)))
        self._c.commit()

    def all_config(self):
        rows = self._c.execute("SELECT key, value FROM config").fetchall()
        return {k: json.loads(v) for k, v in rows}


# ── DynamoDB backend ─────────────────────────────────────────────────────────
class _DynamoEvents:
    def __init__(self, prefix):
        import boto3
        ddb = boto3.resource("dynamodb")
        self.t_events = ddb.Table(f"{prefix}events")
        self.t_config = ddb.Table(f"{prefix}config")

    def emit(self, event_type, email=None, props=None):
        ts = _now_ms()
        self.t_events.put_item(Item={
            "plane": PLANE, "ts_id": f"{ts}#{event_type}",
            "ts": ts, "type": event_type, "email": email or "-",
            "props": props or {},
        })

    def list_events(self, limit=1000):
        resp = self.t_events.query(
            KeyConditionExpression="plane = :p",
            ExpressionAttributeValues={":p": PLANE},
            ScanIndexForward=False, Limit=limit,
        )
        out = []
        for i in resp.get("Items", []):
            out.append({"ts": int(i.get("ts", 0)), "plane": i["plane"],
                        "type": i.get("type"), "email": i.get("email"),
                        "props": _dec(i.get("props", {}))})
        return out

    def get_config(self, key, default=None):
        item = self.t_config.get_item(Key={"key": key}).get("Item")
        return _dec(item.get("value")) if item else default

    def set_config(self, key, value):
        self.t_config.put_item(Item={"key": key, "value": value})

    def all_config(self):
        items = self.t_config.scan().get("Items", [])
        return {i["key"]: _dec(i.get("value")) for i in items}


def _dec(obj):
    """DynamoDB Decimal -> int/float for clean JSON."""
    from decimal import Decimal
    if isinstance(obj, Decimal):
        return int(obj) if obj % 1 == 0 else float(obj)
    if isinstance(obj, dict):
        return {k: _dec(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_dec(v) for v in obj]
    return obj


_events = None


def get_events():
    """Singleton events/config store, backend from STORE_BACKEND."""
    global _events
    if _events is not None:
        return _events
    backend = os.environ.get("STORE_BACKEND", "memory")
    if backend == "dynamodb":
        _events = _DynamoEvents(os.environ.get("DDB_TABLE_PREFIX", "mfp-dev-"))
    elif backend == "sqlite":
        _events = _SqliteEvents(os.environ.get("SQLITE_PATH", "final_playbook.db"))
    else:
        _events = _MemoryEvents()
    return _events


def reset_events():
    global _events
    _events = None

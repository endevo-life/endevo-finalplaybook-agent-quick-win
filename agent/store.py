"""Persistence abstraction: users, entitlements, sessions, and usage counters.

One interface, two backends selected by the STORE_BACKEND env var:
- "memory" (default) -- an in-process dict. Zero setup; perfect for local dev
  and tests. Data is lost on restart.
- "dynamodb" -- a single DynamoDB table (single-table design). This is the
  production backend on AWS. Table name from DDB_TABLE (default "final-playbook").

Single-table layout (DynamoDB):
    PK              SK              attributes
    USER#<email>    PROFILE         email, tier, created_at, stripe_customer_id
    USER#<email>    USAGE#<yyyy-mm> personalize_count, chat_count
    SESSION#<token> META            email, expires_at   (TTL on expires_at)
    STRIPE#<cust>   USER            email               (webhook -> user lookup)

Everything the API needs goes through the Store methods below, so swapping
backends never touches route code.
"""
import os
import time
from typing import Optional


def _now() -> int:
    return int(time.time())


def _month_key(ts: Optional[int] = None) -> str:
    t = time.gmtime(ts if ts is not None else _now())
    return f"{t.tm_year:04d}-{t.tm_mon:02d}"


class MemoryStore:
    """In-process store for local dev and tests."""

    def __init__(self):
        self.users = {}      # email -> {email, tier, created_at, stripe_customer_id}
        self.usage = {}      # (email, month) -> {personalize_count, chat_count}
        self.sessions = {}   # token -> {email, expires_at}
        self.stripe_map = {} # stripe_customer_id -> email

    # --- users / entitlements ---
    def get_user(self, email: str) -> Optional[dict]:
        return self.users.get(email)

    def upsert_user(self, email: str, tier: str = "free", stripe_customer_id: str = None) -> dict:
        user = self.users.get(email) or {"email": email, "created_at": _now()}
        user["tier"] = tier
        if stripe_customer_id:
            user["stripe_customer_id"] = stripe_customer_id
            self.stripe_map[stripe_customer_id] = email
        self.users[email] = user
        return user

    def set_tier(self, email: str, tier: str) -> None:
        user = self.users.get(email) or {"email": email, "created_at": _now()}
        user["tier"] = tier
        self.users[email] = user

    def email_for_stripe_customer(self, stripe_customer_id: str) -> Optional[str]:
        return self.stripe_map.get(stripe_customer_id)

    # --- sessions ---
    def create_session(self, token: str, email: str, ttl_seconds: int) -> None:
        self.sessions[token] = {"email": email, "expires_at": _now() + ttl_seconds}

    def get_session_email(self, token: str) -> Optional[str]:
        s = self.sessions.get(token)
        if not s or s["expires_at"] < _now():
            self.sessions.pop(token, None)
            return None
        return s["email"]

    def delete_session(self, token: str) -> None:
        self.sessions.pop(token, None)

    # --- usage metering ---
    def get_usage(self, email: str) -> dict:
        return self.usage.get((email, _month_key()), {"personalize_count": 0, "chat_count": 0})

    def increment_usage(self, email: str, field: str) -> int:
        key = (email, _month_key())
        rec = self.usage.setdefault(key, {"personalize_count": 0, "chat_count": 0})
        rec[field] = rec.get(field, 0) + 1
        return rec[field]


class DynamoStore:
    """Production store backed by one DynamoDB table (single-table design)."""

    def __init__(self, table_name: str):
        import boto3  # lazy import: only needed when STORE_BACKEND=dynamodb
        self.table = boto3.resource("dynamodb").Table(table_name)

    # --- users / entitlements ---
    def get_user(self, email: str) -> Optional[dict]:
        resp = self.table.get_item(Key={"PK": f"USER#{email}", "SK": "PROFILE"})
        item = resp.get("Item")
        if not item:
            return None
        return {
            "email": item["email"],
            "tier": item.get("tier", "free"),
            "created_at": int(item.get("created_at", 0)),
            "stripe_customer_id": item.get("stripe_customer_id"),
        }

    def upsert_user(self, email: str, tier: str = "free", stripe_customer_id: str = None) -> dict:
        expr = "SET tier = :t, created_at = if_not_exists(created_at, :c), email = :e"
        vals = {":t": tier, ":c": _now(), ":e": email}
        if stripe_customer_id:
            expr += ", stripe_customer_id = :s"
            vals[":s"] = stripe_customer_id
            self.table.put_item(Item={"PK": f"STRIPE#{stripe_customer_id}", "SK": "USER", "email": email})
        self.table.update_item(
            Key={"PK": f"USER#{email}", "SK": "PROFILE"},
            UpdateExpression=expr,
            ExpressionAttributeValues=vals,
        )
        return self.get_user(email)

    def set_tier(self, email: str, tier: str) -> None:
        self.table.update_item(
            Key={"PK": f"USER#{email}", "SK": "PROFILE"},
            UpdateExpression="SET tier = :t, email = if_not_exists(email, :e), created_at = if_not_exists(created_at, :c)",
            ExpressionAttributeValues={":t": tier, ":e": email, ":c": _now()},
        )

    def email_for_stripe_customer(self, stripe_customer_id: str) -> Optional[str]:
        resp = self.table.get_item(Key={"PK": f"STRIPE#{stripe_customer_id}", "SK": "USER"})
        item = resp.get("Item")
        return item.get("email") if item else None

    # --- sessions ---
    def create_session(self, token: str, email: str, ttl_seconds: int) -> None:
        self.table.put_item(Item={
            "PK": f"SESSION#{token}", "SK": "META",
            "email": email, "expires_at": _now() + ttl_seconds,  # DDB TTL attribute
        })

    def get_session_email(self, token: str) -> Optional[str]:
        resp = self.table.get_item(Key={"PK": f"SESSION#{token}", "SK": "META"})
        item = resp.get("Item")
        if not item or int(item.get("expires_at", 0)) < _now():
            return None
        return item["email"]

    def delete_session(self, token: str) -> None:
        self.table.delete_item(Key={"PK": f"SESSION#{token}", "SK": "META"})

    # --- usage metering ---
    def get_usage(self, email: str) -> dict:
        resp = self.table.get_item(Key={"PK": f"USER#{email}", "SK": f"USAGE#{_month_key()}"})
        item = resp.get("Item") or {}
        return {
            "personalize_count": int(item.get("personalize_count", 0)),
            "chat_count": int(item.get("chat_count", 0)),
        }

    def increment_usage(self, email: str, field: str) -> int:
        resp = self.table.update_item(
            Key={"PK": f"USER#{email}", "SK": f"USAGE#{_month_key()}"},
            UpdateExpression=f"ADD {field} :one",
            ExpressionAttributeValues={":one": 1},
            ReturnValues="UPDATED_NEW",
        )
        return int(resp["Attributes"][field])


_store = None


def get_store():
    """Singleton store selected by STORE_BACKEND ("memory" default, "dynamodb")."""
    global _store
    if _store is not None:
        return _store
    backend = os.environ.get("STORE_BACKEND", "memory")
    if backend == "dynamodb":
        _store = DynamoStore(os.environ.get("DDB_TABLE", "final-playbook"))
    elif backend == "memory":
        _store = MemoryStore()
    else:
        raise ValueError(f"Unknown STORE_BACKEND: {backend!r} (expected 'memory' or 'dynamodb')")
    return _store

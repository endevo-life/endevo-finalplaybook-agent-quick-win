"""In-process store for local dev and tests (lost on restart)."""
from typing import Optional

from app.data.store.base import now, month_key

class MemoryStore:
    """In-process store for local dev and tests."""

    def __init__(self):
        self.users = {}      # email -> {email, tier, created_at, stripe_customer_id}
        self.usage = {}      # (email, month) -> {personalize_count, chat_count}
        self.sessions = {}   # token -> {email, expires_at}
        self.stripe_map = {} # stripe_customer_id -> email
        self.plans = {}      # email -> {answers, plan, tracked, narrative, updated_at}
        self.chat = {}       # email -> [{role, content}, ...]

    # --- users / entitlements ---
    def get_user(self, email: str) -> Optional[dict]:
        return self.users.get(email)

    def upsert_user(self, email: str, tier: str = "free", stripe_customer_id: str = None) -> dict:
        user = self.users.get(email) or {"email": email, "created_at": now()}
        user["tier"] = tier
        if stripe_customer_id:
            user["stripe_customer_id"] = stripe_customer_id
            self.stripe_map[stripe_customer_id] = email
        self.users[email] = user
        return user

    def set_tier(self, email: str, tier: str) -> None:
        user = self.users.get(email) or {"email": email, "created_at": now()}
        user["tier"] = tier
        self.users[email] = user

    def email_for_stripe_customer(self, stripe_customer_id: str) -> Optional[str]:
        return self.stripe_map.get(stripe_customer_id)

    # --- sessions ---
    def create_session(self, token: str, email: str, ttl_seconds: int) -> None:
        self.sessions[token] = {"email": email, "expires_at": now() + ttl_seconds}

    def get_session_email(self, token: str) -> Optional[str]:
        s = self.sessions.get(token)
        if not s or s["expires_at"] < now():
            self.sessions.pop(token, None)
            return None
        return s["email"]

    def delete_session(self, token: str) -> None:
        self.sessions.pop(token, None)

    # --- usage metering ---
    def get_usage(self, email: str) -> dict:
        return self.usage.get((email, month_key()), {"personalize_count": 0, "chat_count": 0})

    def increment_usage(self, email: str, field: str) -> int:
        key = (email, month_key())
        rec = self.usage.setdefault(key, {"personalize_count": 0, "chat_count": 0})
        rec[field] = rec.get(field, 0) + 1
        return rec[field]

    # --- saved plan + progress ---
    def get_plan(self, email: str) -> Optional[dict]:
        return self.plans.get(email)

    def save_plan(self, email: str, answers=None, plan=None, tracked=None, narrative=None) -> None:
        rec = self.plans.setdefault(email, {})
        if answers is not None:
            rec["answers"] = answers
        if plan is not None:
            rec["plan"] = plan
        if tracked is not None:
            rec["tracked"] = tracked
        if narrative is not None:
            rec["narrative"] = narrative
        rec["updated_at"] = now()

    # --- chat history ---
    def get_chat_history(self, email: str, limit: int = 100) -> list:
        return self.chat.get(email, [])[-limit:]

    def append_chat(self, email: str, role: str, content: str) -> None:
        self.chat.setdefault(email, []).append({"role": role, "content": content})

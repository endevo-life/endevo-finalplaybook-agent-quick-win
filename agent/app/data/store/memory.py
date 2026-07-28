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
        self.feedback = []   # [{id, email, kind, message, rating, page, created_at}]

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

    def set_tier(self, email: str, tier: str, paid_until: int = None, canceled: bool = None) -> None:
        user = self.users.get(email) or {"email": email, "created_at": now()}
        user["tier"] = tier
        if paid_until is not None:
            user["paid_until"] = paid_until
        if canceled is not None:
            user["canceled"] = canceled
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

    def reset_usage(self, email: str) -> None:
        self.usage[(email, month_key())] = {"personalize_count": 0, "chat_count": 0}

    # --- saved plan + progress ---
    def get_plan(self, email: str) -> Optional[dict]:
        return self.plans.get(email)

    def save_plan(self, email: str, answers=None, plan=None, tracked=None, narrative=None, fields=None) -> None:
        rec = self.plans.setdefault(email, {})
        if answers is not None:
            rec["answers"] = answers
        if plan is not None:
            rec["plan"] = plan
        if tracked is not None:
            rec["tracked"] = tracked
        if narrative is not None:
            rec["narrative"] = narrative
        if fields is not None:
            rec["fields"] = fields
        rec["updated_at"] = now()

    # --- chat history ---
    def get_chat_history(self, email: str, limit: int = 100) -> list:
        return self.chat.get(email, [])[-limit:]

    def append_chat(self, email: str, role: str, content: str) -> None:
        self.chat.setdefault(email, []).append({"role": role, "content": content})

    # --- member feedback (help / complaint / survey) ---
    def save_feedback(self, email, kind, message, rating=None, page=None,
                      signed_in=False) -> dict:
        entry = {
            "id": f"fb_{len(self.feedback) + 1}_{now()}",
            "email": email, "kind": kind, "message": message,
            "rating": rating, "page": page, "signed_in": signed_in,
            "created_at": now(),
        }
        self.feedback.append(entry)
        return entry

    def list_feedback(self, limit: int = 100, since: int = None) -> list:
        rows = self.feedback
        if since is not None:
            rows = [f for f in rows if f["created_at"] >= since]
        return list(reversed(rows[-limit:]))

    def count_feedback_since(self, email: str, since: int) -> int:
        """Submissions from one email since a timestamp -- powers rate limiting."""
        return sum(1 for f in self.feedback
                   if f.get("email") == email and f["created_at"] >= since)

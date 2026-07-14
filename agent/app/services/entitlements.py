"""Server-side entitlement + quota enforcement -- the security boundary the
original "trust the client's tier string" design was missing.

A user's effective tier comes from the store (set by billing.py on a successful
Stripe payment), never from the request body. Before any metered LLM call, the
route asks can_personalize()/can_chat(); after a successful call it records
usage. When a quota is exhausted, the caller gets a 402/429-style error, not a
silent overspend.
"""
from dataclasses import dataclass

from app.services.plans import get_plan
from app.data.store import get_store


class EntitlementError(Exception):
    """Raised when a user isn't allowed to perform a metered action.
    `code` maps to an HTTP status the API layer surfaces (402 = upgrade needed,
    429 = quota exhausted)."""
    def __init__(self, message: str, code: int):
        super().__init__(message)
        self.code = code


@dataclass
class Entitlement:
    email: str
    tier: str
    plan_name: str
    canceled: bool = False       # subscription canceled but still within paid period
    paid_until: int = None       # epoch seconds paid access ends (if canceled)

    def _plan(self):
        return get_plan(self.tier)

    def require_personalize(self) -> None:
        plan = self._plan()
        if not plan.can_personalize:
            raise EntitlementError(
                "Personalized plans are a paid feature. Upgrade to unlock.", 402
            )
        used = get_store().get_usage(self.email)["personalize_count"]
        if used >= plan.monthly_personalize_quota:
            raise EntitlementError(
                "You've reached your monthly personalized-plan limit. "
                "It resets at the start of next month.", 429
            )

    def require_chat(self) -> None:
        plan = self._plan()
        if not plan.can_chat:
            raise EntitlementError(
                "Follow-up chat is a paid feature. Upgrade to unlock.", 402
            )
        used = get_store().get_usage(self.email)["chat_count"]
        if used >= plan.monthly_chat_quota:
            raise EntitlementError(
                "You've reached your monthly chat limit. "
                "It resets at the start of next month.", 429
            )

    def record_personalize(self) -> None:
        get_store().increment_usage(self.email, "personalize_count")

    def record_chat(self) -> None:
        get_store().increment_usage(self.email, "chat_count")

    def snapshot(self) -> dict:
        """What the frontend needs to render tier + remaining quota."""
        plan = self._plan()
        usage = get_store().get_usage(self.email)
        return {
            "email": self.email,
            "tier": self.tier,
            "planName": plan.name,
            "canPersonalize": plan.can_personalize,
            "canChat": plan.can_chat,
            "usage": {
                "personalizeUsed": usage["personalize_count"],
                "personalizeQuota": plan.monthly_personalize_quota,
                "chatUsed": usage["chat_count"],
                "chatQuota": plan.monthly_chat_quota,
            },
            "canceled": self.canceled,
            "paidUntil": self.paid_until,
        }


def entitlement_for(email: str) -> Entitlement:
    """Load a user's live entitlement from the store. Auto-provisions a free
    user if they somehow have a valid session but no profile row.

    A canceled paid user KEEPS paid access until `paid_until` passes (they paid
    for the period). Once that timestamp is in the past, they resolve to free."""
    from app.data.store.base import now
    store = get_store()
    user = store.get_user(email) or store.upsert_user(email, tier="free")
    tier = get_plan(user["tier"]).tier
    # Downgrade an expired cancellation to free at read time (self-healing;
    # no cron needed). Only when they actually canceled AND the paid period ended.
    paid_until = user.get("paid_until")
    canceled = bool(user.get("canceled"))
    if tier == "paid" and canceled and paid_until and int(paid_until) < now():
        tier = "free"
        canceled = False
        paid_until = None
        store.set_tier(email, "free", canceled=False)  # settle it
    return Entitlement(
        email=email, tier=tier, plan_name=get_plan(tier).name,
        canceled=(canceled and tier == "paid"),
        paid_until=int(paid_until) if (paid_until and tier == "paid") else None,
    )

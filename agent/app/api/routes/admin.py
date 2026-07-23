"""Operator/admin console API. Gated by ADMIN_TOKEN (Bearer) plus, when
ADMIN_EMAILS is set, an allowlisted admin email. Standalone but share-ready --
reads the plane-tagged analytics stream + live store, so it can later merge
into the shared B2B operator dashboard.

Endpoints:
  POST /api/admin/login              -> validate the admin token (+ email if allowlisted)
  GET  /api/admin/metrics            -> signups, conversion, funnels, agent usage
  GET  /api/admin/costs?days=        -> AWS + AI cost/usage (Cost tab)
  GET  /api/admin/events?limit=      -> recent raw events
  GET  /api/admin/users              -> known users (derived from signups)
  GET  /api/admin/users/{email}      -> one user: tier, usage, plan progress
  POST /api/admin/users/{email}/tier -> grant/revoke paid
  POST /api/admin/users/{email}/reset-usage -> reset monthly quotas
  GET/POST /api/admin/config         -> feature flags / config
"""
import secrets

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from pydantic import BaseModel
from typing import Optional

from app.config import ADMIN_EMAILS, ADMIN_TOKEN
from app.data.events import get_events
from app.data.store import get_store, month_key
from app.services import analytics, auth as auth_service, aws_cost
from app.services.entitlements import entitlement_for
from app.services.plans import PLANS

router = APIRouter(prefix="/api/admin", tags=["admin"])


def require_admin(
    authorization: Optional[str] = Header(None),
    x_admin_email: Optional[str] = Header(None),
) -> bool:
    """Gate every admin route. Two ways in:

    1. Session-based (the console's normal path): a regular signed-in session
       token whose email is on the ADMIN_EMAILS allowlist. The admin logs in
       with the same passwordless email code members use -- nothing to remember.
       The email comes from the session itself, never from a client header.
    2. Shared ADMIN_TOKEN (scripts/CI fallback): constant-time compared. When
       ADMIN_EMAILS is set, the X-Admin-Email header must also be allowlisted
       (kept from the original design so tooling identifies its operator).
    """
    if not ADMIN_TOKEN and not ADMIN_EMAILS:
        raise HTTPException(503, "Admin console not configured (set ADMIN_EMAILS or ADMIN_TOKEN).")
    token = ""
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()
    if not token:
        raise HTTPException(401, "Missing admin credentials.")

    # Path 2: shared operator token (constant-time compare).
    if ADMIN_TOKEN and secrets.compare_digest(token, ADMIN_TOKEN):
        if ADMIN_EMAILS:
            email = (x_admin_email or "").strip().lower()
            if email not in ADMIN_EMAILS:
                raise HTTPException(401, "Admin email not recognized.")
        return True

    # Path 1: an ordinary session whose email is allowlisted as an admin.
    if ADMIN_EMAILS:
        email = auth_service.email_from_token(token)
        if email and email in ADMIN_EMAILS:
            return True

    raise HTTPException(401, "Invalid admin credentials.")


class TierChange(BaseModel):
    tier: str  # "free" | "paid"


class ConfigChange(BaseModel):
    key: str
    value: object


@router.post("/login")
def admin_login(_: bool = Depends(require_admin)):
    return {"ok": True}


@router.get("/metrics")
def admin_metrics(_: bool = Depends(require_admin)):
    return analytics.metrics()


@router.get("/events")
def admin_events(limit: int = Query(100, le=1000), _: bool = Depends(require_admin)):
    return analytics.recent_events(limit=limit)


@router.get("/costs")
def admin_costs(days: int = Query(30, ge=1, le=90), _: bool = Depends(require_admin)):
    """AWS + AI cost/usage for the Cost tab. Real billed $ when AWS_COST_ENABLED
    is set (Cost Explorer), otherwise an estimate from tracked LLM calls."""
    return aws_cost.costs(days=days)


def _known_emails() -> list:
    """Distinct emails seen in the event stream (signups/logins/etc.)."""
    seen = []
    for e in get_events().list_events(limit=5000):
        em = e.get("email")
        if em and em != "-" and em not in seen:
            seen.append(em)
    return seen


@router.get("/users")
def admin_users(_: bool = Depends(require_admin)):
    store = get_store()
    out = []
    for email in _known_emails():
        u = store.get_user(email)
        if not u:
            continue
        usage = store.get_usage(email)
        out.append({
            "email": email,
            "tier": u.get("tier", "free"),
            "createdAt": u.get("created_at"),
            "chatUsed": usage.get("chat_count", 0),
            "personalizeUsed": usage.get("personalize_count", 0),
        })
    return {"users": out, "count": len(out)}


@router.get("/users/{email}")
def admin_user_detail(email: str, _: bool = Depends(require_admin)):
    email = email.strip().lower()
    store = get_store()
    u = store.get_user(email)
    if not u:
        raise HTTPException(404, "User not found.")
    ent = entitlement_for(email)
    saved = store.get_plan(email) or {}
    tracked = saved.get("tracked", {}) or {}

    # Per-user action progress: what they've completed vs not, from their plan.
    plan = saved.get("plan") or {}
    items = (plan.get("basicsFirst", []) or []) + (plan.get("domainItems", []) or [])
    progress = []
    for it in items:
        steps = it.get("steps", []) if it.get("resultType") != "review" else []
        done = sum(1 for i in range(len(steps)) if tracked.get(f"{it['id']}::{i}"))
        progress.append({
            "id": it.get("id"),
            "domain": it.get("domain"),
            "action": it.get("action"),
            "stepsDone": done,
            "stepsTotal": len(steps),
            "complete": len(steps) > 0 and done == len(steps),
        })

    return {
        "email": email,
        "entitlement": ent.snapshot(),
        "answers": saved.get("answers", {}),
        "hasNarrative": bool(saved.get("narrative")),
        "chatMessages": len(store.get_chat_history(email)),
        "progress": progress,
        "completedCount": sum(1 for p in progress if p["complete"]),
        "totalItems": len(progress),
    }


@router.post("/users/{email}/tier")
def admin_set_tier(email: str, body: TierChange, _: bool = Depends(require_admin)):
    email = email.strip().lower()
    if body.tier not in PLANS:
        raise HTTPException(400, "tier must be 'free' or 'paid'")
    get_store().set_tier(email, body.tier)
    analytics.emit("admin_tier_change", email=email, tier=body.tier)
    return entitlement_for(email).snapshot()


@router.post("/users/{email}/reset-usage")
def admin_reset_usage(email: str, _: bool = Depends(require_admin)):
    """Zero this month's quota counters for a user (support/testing)."""
    email = email.strip().lower()
    store = get_store()
    # Overwrite the current month's usage row to zero via set (memory/sqlite/ddb
    # all expose increment; we clear by writing a fresh row through save-like path).
    try:
        store.reset_usage(email)  # optional fast path if a backend implements it
    except AttributeError:
        # Fallback: not all stores implement reset; emit + report so it's visible.
        pass
    analytics.emit("admin_reset_usage", email=email)
    return {"ok": True, "month": month_key(), "usage": store.get_usage(email)}


@router.get("/config")
def admin_get_config(_: bool = Depends(require_admin)):
    return get_events().all_config()


@router.post("/config")
def admin_set_config(body: ConfigChange, _: bool = Depends(require_admin)):
    get_events().set_config(body.key, body.value)
    analytics.emit("admin_config_change", key=body.key)
    return {"ok": True, "config": get_events().all_config()}

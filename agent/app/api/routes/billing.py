"""Billing routes: Stripe Checkout, the webhook (source of truth for tier), and a
guarded dev-upgrade for demoing paid before Stripe is live."""
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request

from app.api.deps import require_email
from app.config import ALLOW_DEV_UPGRADE
from app.data.store import get_store
from app.services import analytics, billing as billing_service
from app.services.entitlements import entitlement_for

router = APIRouter(prefix="/api/billing", tags=["billing"])


@router.post("/checkout")
def billing_checkout(email: str = Depends(require_email)):
    if not billing_service.is_configured():
        raise HTTPException(503, "Billing is not configured on this server yet.")
    try:
        url = billing_service.create_checkout_session(email)
    except Exception as e:
        raise HTTPException(502, f"Checkout error: {e}")
    return {"url": url}


@router.post("/dev-upgrade")
def billing_dev_upgrade(email: str = Depends(require_email)):
    """Unlock the paid tier WITHOUT Stripe -- for demos/early testing. Guarded by
    ALLOW_DEV_UPGRADE so it can never be hit in production (Stripe's webhook is the
    only way to grant paid there)."""
    if not ALLOW_DEV_UPGRADE:
        raise HTTPException(403, "Dev upgrade is disabled. Use Stripe checkout.")
    get_store().set_tier(email, "paid")
    analytics.emit(analytics.UPGRADE, email=email, via="dev")
    return entitlement_for(email).snapshot()


@router.post("/downgrade")
def billing_downgrade(email: str = Depends(require_email)):
    """Cancel the subscription. The member KEEPS paid access until the end of the
    period they've paid for (paid_until), then auto-resolves to free -- the same
    'cancel now, access until renewal' behavior real subscriptions have. Guarded
    by ALLOW_DEV_UPGRADE (prod cancellation flows through the Stripe portal +
    webhook). Idempotent for an already-free user."""
    from app.data.store.base import now
    if not ALLOW_DEV_UPGRADE:
        raise HTTPException(403, "Manage your subscription through the billing portal.")
    store = get_store()
    user = store.get_user(email)
    if not user or user.get("tier") != "paid":
        return entitlement_for(email).snapshot()  # nothing to cancel
    # Access continues to the end of the current 30-day period. If a real
    # subscription set paid_until, keep it; otherwise grant 30 days from now.
    paid_until = user.get("paid_until") or (now() + 30 * 24 * 3600)
    store.set_tier(email, "paid", paid_until=paid_until, canceled=True)
    analytics.emit(analytics.UPGRADE_BLOCKED, email=email, feature="downgrade", code=0)
    return entitlement_for(email).snapshot()


@router.post("/webhook")
async def billing_webhook(request: Request, stripe_signature: Optional[str] = Header(None)):
    payload = await request.body()
    try:
        result = billing_service.handle_webhook(payload, stripe_signature)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(502, f"Webhook error: {e}")
    # A real Stripe upgrade -> record it for conversion analytics.
    if isinstance(result, dict) and result.get("tier") == "paid" and result.get("email"):
        analytics.emit(analytics.UPGRADE, email=result["email"], via="stripe")
    return result

"""Stripe Checkout integration -- the payment gate that actually unlocks the
paid tier.

Flow:
1. A logged-in user hits POST /api/billing/checkout. We create a Stripe Checkout
   Session for the configured recurring Price and return its URL; the frontend
   redirects there. PCI is entirely Stripe's problem -- no card data touches us.
2. Stripe redirects the user back to success_url / cancel_url.
3. Stripe calls our webhook (POST /api/billing/webhook) asynchronously. On
   `checkout.session.completed` we flip the user's tier to "paid"; on
   `customer.subscription.deleted` we flip them back to "free". The webhook --
   not the redirect -- is the source of truth, because the redirect can be
   skipped or forged.

All of this no-ops cleanly if STRIPE_SECRET_KEY isn't set, so the app still runs
end-to-end in dev without a Stripe account (you can grant paid tier manually via
the store for testing).

The paid tier is sold monthly or annually. Each interval maps to its own Stripe
Price via the env var named in `plans.BILLING_INTERVALS` -- annual is optional, so
a deploy that only sets STRIPE_PRICE_ID still works and simply offers monthly.

Env:
    STRIPE_SECRET_KEY        sk_live_... / sk_test_...
    STRIPE_PRICE_ID          price_...  (monthly paid-tier price)
    STRIPE_PRICE_ID_ANNUAL   price_...  (annual paid-tier price; optional)
    STRIPE_WEBHOOK_SECRET    whsec_...  (verifies webhook authenticity)
    APP_BASE_URL             where to send users back after checkout
"""
import os

from app.data.store import get_store
from app.services.plans import BILLING_INTERVALS, get_interval


def is_configured() -> bool:
    return bool(os.environ.get("STRIPE_SECRET_KEY") and os.environ.get("STRIPE_PRICE_ID"))


def price_id_for(interval: str) -> str:
    """Resolve a billing interval to its configured Stripe Price ID. Raises if
    that interval has no price set -- better a clear 502 than silently charging
    someone the monthly rate when they clicked annual."""
    spec = get_interval(interval)
    price_id = os.environ.get(spec.stripe_price_env)
    if not price_id:
        raise RuntimeError(
            f"No Stripe price configured for {spec.key} billing "
            f"(set {spec.stripe_price_env})."
        )
    return price_id


def available_intervals() -> list:
    """Interval keys that actually have a Stripe Price configured. The pricing
    UI uses this so we never show an annual toggle that would 502 on click."""
    if not is_configured():
        return []
    return [k for k, spec in BILLING_INTERVALS.items()
            if os.environ.get(spec.stripe_price_env)]


def _client():
    import stripe  # lazy import: only needed when billing is configured
    stripe.api_key = os.environ["STRIPE_SECRET_KEY"]
    return stripe


def create_checkout_session(email: str, interval: str = "monthly") -> str:
    """Create a Stripe Checkout Session for `email` on the given billing
    interval ("monthly" | "annual") and return its URL. Reuses/creates a Stripe
    customer keyed to the email so the webhook can map the payment back to our
    user."""
    if not is_configured():
        raise RuntimeError("Billing is not configured (set STRIPE_SECRET_KEY and STRIPE_PRICE_ID).")
    price_id = price_id_for(interval)  # validates the interval before any API call
    stripe = _client()
    base = os.environ.get("APP_BASE_URL", "http://localhost:3200")

    store = get_store()
    user = store.get_user(email) or store.upsert_user(email, tier="free")
    customer_id = user.get("stripe_customer_id")
    if not customer_id:
        customer = stripe.Customer.create(email=email)
        customer_id = customer["id"]
        store.upsert_user(email, tier=user["tier"], stripe_customer_id=customer_id)

    session = stripe.checkout.Session.create(
        mode="subscription",
        customer=customer_id,
        line_items=[{"price": price_id, "quantity": 1}],
        success_url=f"{base}/?checkout=success",
        cancel_url=f"{base}/?checkout=cancel",
        client_reference_id=email,
    )
    return session["url"]


def handle_webhook(payload: bytes, sig_header: str) -> dict:
    """Verify and process a Stripe webhook. Returns a small status dict. Raises
    ValueError on signature failure (the API layer turns that into a 400)."""
    stripe = _client()
    webhook_secret = os.environ.get("STRIPE_WEBHOOK_SECRET")
    if webhook_secret:
        try:
            event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
        except Exception as e:
            raise ValueError(f"webhook signature verification failed: {e}")
    else:
        # Dev fallback: no secret configured -> parse without verification.
        import json
        event = json.loads(payload)

    etype = event["type"]
    obj = event["data"]["object"]
    store = get_store()

    if etype == "checkout.session.completed":
        email = obj.get("client_reference_id") or _email_from_customer(store, obj.get("customer"))
        if email:
            store.set_tier(email, "paid")
            return {"handled": etype, "email": email, "tier": "paid"}

    elif etype in ("customer.subscription.deleted", "customer.subscription.paused"):
        email = _email_from_customer(store, obj.get("customer"))
        if email:
            store.set_tier(email, "free")
            return {"handled": etype, "email": email, "tier": "free"}

    return {"handled": etype, "noop": True}


def _email_from_customer(store, customer_id):
    if not customer_id:
        return None
    return store.email_for_stripe_customer(customer_id)

"""Cancel keeps paid access until the period ends, then auto-resolves to free.

Bug being locked in: cancelling used to drop the member to free immediately.
A real subscription keeps access until the renewal date. These tests prove the
entitlement resolver honors paid_until and self-heals once it passes.
"""
from app.data.store import get_store
from app.data.store.base import now
from app.services.entitlements import entitlement_for


def test_canceled_user_keeps_paid_until_period_ends():
    store = get_store()
    email = "cancel-active@example.com"
    # Paid, canceled, but paid_until is in the FUTURE -> still paid.
    store.set_tier(email, "paid", paid_until=now() + 3600, canceled=True)

    ent = entitlement_for(email)
    assert ent.tier == "paid", "canceled but within period should stay paid"
    snap = ent.snapshot()
    assert snap["canceled"] is True
    assert snap["paidUntil"] is not None


def test_canceled_user_drops_to_free_after_period():
    store = get_store()
    email = "cancel-expired@example.com"
    # Paid, canceled, paid_until in the PAST -> resolves to free.
    store.set_tier(email, "paid", paid_until=now() - 10, canceled=True)

    ent = entitlement_for(email)
    assert ent.tier == "free", "canceled and past the period should be free"
    # and it should have settled the record (self-healing, no cron needed)
    assert store.get_user(email)["tier"] == "free"


def test_active_paid_user_not_affected():
    store = get_store()
    email = "active-paid@example.com"
    # Paid, NOT canceled -> stays paid regardless of paid_until.
    store.set_tier(email, "paid")

    ent = entitlement_for(email)
    assert ent.tier == "paid"
    assert ent.snapshot()["canceled"] is False


def test_snapshot_shape_for_canceled_user():
    """The snapshot exposes canceled + paidUntil so the UI can show
    'paid until <date>'."""
    store = get_store()
    email = "cancel-snap@example.com"
    future = now() + 5 * 24 * 3600
    store.set_tier(email, "paid", paid_until=future, canceled=True)

    snap = entitlement_for(email).snapshot()
    assert snap["tier"] == "paid"
    assert snap["canceled"] is True
    assert snap["paidUntil"] == future

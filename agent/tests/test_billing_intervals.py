"""Billing-interval selection: the paid tier is sold monthly ($25) and annually
($199), and picking one must charge that one.

The risk being covered here is a mispriced charge -- a bad or missing interval
silently falling back to the wrong Stripe Price -- so these tests assert that a
wrong interval FAILS rather than defaulting to something purchasable.
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services import billing
from app.services.plans import BILLING_INTERVALS, normalize_interval

client = TestClient(app)


# --- the plan table ----------------------------------------------------------
def test_both_intervals_defined_with_expected_prices():
    assert BILLING_INTERVALS["monthly"].price_usd == 25.0
    assert BILLING_INTERVALS["annual"].price_usd == 199.0


def test_annual_is_cheaper_per_month_than_monthly():
    """The whole reason annual exists. If someone edits the prices so annual
    costs more per month, that's a pricing bug, not a valid config."""
    monthly = BILLING_INTERVALS["monthly"]
    annual = BILLING_INTERVALS["annual"]
    assert annual.price_usd / 12 < monthly.price_usd


def test_normalize_interval_defaults_to_monthly_when_empty():
    assert normalize_interval("") == "monthly"
    assert normalize_interval(None) == "monthly"


def test_normalize_interval_is_case_and_space_insensitive():
    assert normalize_interval("  Annual ") == "annual"


def test_unknown_interval_raises_rather_than_defaulting():
    # Silently falling back to monthly would charge $25 to someone who asked
    # for something else -- fail loudly instead.
    with pytest.raises(ValueError):
        normalize_interval("weekly")


# --- resolving an interval to a Stripe price ---------------------------------
def test_price_id_for_reads_the_env_var_named_by_the_interval(monkeypatch):
    monkeypatch.setenv("STRIPE_PRICE_ID", "price_monthly_123")
    monkeypatch.setenv("STRIPE_PRICE_ID_ANNUAL", "price_annual_456")
    assert billing.price_id_for("monthly") == "price_monthly_123"
    assert billing.price_id_for("annual") == "price_annual_456"


def test_price_id_for_raises_when_that_interval_has_no_price(monkeypatch):
    """Annual is optional. If it isn't configured, asking for it must error --
    not quietly bill the monthly price."""
    monkeypatch.setenv("STRIPE_PRICE_ID", "price_monthly_123")
    monkeypatch.delenv("STRIPE_PRICE_ID_ANNUAL", raising=False)
    with pytest.raises(RuntimeError, match="STRIPE_PRICE_ID_ANNUAL"):
        billing.price_id_for("annual")


def test_available_intervals_reports_only_configured_ones(monkeypatch):
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_x")
    monkeypatch.setenv("STRIPE_PRICE_ID", "price_monthly_123")
    monkeypatch.delenv("STRIPE_PRICE_ID_ANNUAL", raising=False)
    assert billing.available_intervals() == ["monthly"]

    monkeypatch.setenv("STRIPE_PRICE_ID_ANNUAL", "price_annual_456")
    assert set(billing.available_intervals()) == {"monthly", "annual"}


def test_available_intervals_empty_when_billing_not_configured(monkeypatch):
    monkeypatch.delenv("STRIPE_SECRET_KEY", raising=False)
    monkeypatch.delenv("STRIPE_PRICE_ID", raising=False)
    assert billing.available_intervals() == []


# --- the checkout route ------------------------------------------------------
def _login(email="interval@example.com"):
    """Run the dev login flow and return a bearer token. conftest forces
    AUTH_RETURN_CODE=true, so the code comes back in the response."""
    start = client.post("/api/auth/start", json={"email": email})
    assert start.status_code == 200
    code = start.json()["devLoginCode"]
    verify = client.post("/api/auth/verify", json={"email": email, "code": code})
    assert verify.status_code == 200
    return verify.json()["token"]


def test_checkout_rejects_an_unknown_interval(monkeypatch):
    """A bad interval is the caller's error (400), not a Stripe failure (502),
    and must never reach Stripe at all."""
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_x")
    monkeypatch.setenv("STRIPE_PRICE_ID", "price_monthly_123")
    token = _login()
    resp = client.post(
        "/api/billing/checkout",
        json={"interval": "weekly"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 400


def test_checkout_requires_login_regardless_of_interval():
    resp = client.post("/api/billing/checkout", json={"interval": "annual"})
    assert resp.status_code in (401, 403)

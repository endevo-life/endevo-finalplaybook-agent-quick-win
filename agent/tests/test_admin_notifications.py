"""Admin console: the digest trigger, the feedback inbox, and delivery status.

Also covers the Lambda dispatch, since the weekly schedule reaches the digest
through lambda_handler rather than through HTTP -- that branch is production-only
code and would otherwise never be exercised by a test.
"""
import pytest
from fastapi.testclient import TestClient

from app.api.routes import admin as admin_routes
from app.data import email as email_mod
from app.data.events import reset_events
from app.data.store import reset_store
from app.main import create_app

ADMIN_EMAIL = "admin@example.com"
OPERATOR_TOKEN = "test-operator-token"
OPERATORS = "niki@finalplaybook.com,hello@endevo.life,bluesproutagency@gmail.com"


@pytest.fixture(autouse=True)
def _setup(monkeypatch):
    reset_store()
    reset_events()
    email_mod.reset_email()
    monkeypatch.setattr(admin_routes, "ADMIN_EMAILS", [ADMIN_EMAIL])
    monkeypatch.setattr(admin_routes, "ADMIN_TOKEN", OPERATOR_TOKEN)
    monkeypatch.setenv("EMAIL_BACKEND", "console")
    monkeypatch.setenv("OPERATOR_EMAILS", OPERATORS)
    yield
    reset_store()
    reset_events()
    email_mod.reset_email()


@pytest.fixture
def client():
    return TestClient(create_app())


@pytest.fixture
def admin(client):
    """Headers for an authenticated admin (the shared-token path)."""
    return {"Authorization": f"Bearer {OPERATOR_TOKEN}", "X-Admin-Email": ADMIN_EMAIL}


# ── Feedback inbox ───────────────────────────────────────────────────────────
def test_admin_sees_feedback(client, admin):
    client.post("/api/feedback", json={
        "kind": "complaint", "message": "The tone felt cold.", "email": "m@example.com"})
    client.post("/api/feedback", json={
        "kind": "survey", "message": "Really helpful.", "rating": 5})

    r = client.get("/api/admin/feedback", headers=admin)
    assert r.status_code == 200
    body = r.json()
    assert body["count"] == 2
    assert body["byKind"]["complaint"] == 1
    assert body["byKind"]["survey"] == 1


def test_feedback_inbox_requires_admin(client):
    assert client.get("/api/admin/feedback").status_code == 401


# ── Digest trigger ───────────────────────────────────────────────────────────
def test_admin_can_send_digest_now(client, admin):
    r = client.post("/api/admin/digest/send", headers=admin)
    assert r.status_code == 200
    assert r.json()["sent"] is True
    assert len(email_mod.last_sends()) == 1


def test_double_click_does_not_double_send(client, admin):
    client.post("/api/admin/digest/send", headers=admin)
    second = client.post("/api/admin/digest/send", headers=admin)
    assert second.json()["sent"] is False
    assert second.json()["reason"] == "already_sent"
    assert len(email_mod.last_sends()) == 1


def test_force_resends(client, admin):
    client.post("/api/admin/digest/send", headers=admin)
    r = client.post("/api/admin/digest/send?force=true", headers=admin)
    assert r.json()["sent"] is True
    assert len(email_mod.last_sends()) == 2


def test_digest_send_requires_admin(client):
    assert client.post("/api/admin/digest/send").status_code == 401


def test_preview_does_not_send(client, admin):
    r = client.get("/api/admin/digest/preview", headers=admin)
    assert r.status_code == 200
    body = r.json()
    assert "subject" in body and "body" in body
    assert body["summary"]["signupCount"] == 0
    assert email_mod.last_sends() == [], "preview must never send"


# ── Delivery status ──────────────────────────────────────────────────────────
def test_notifications_status_reports_config(client, admin):
    r = client.get("/api/admin/notifications", headers=admin)
    assert r.status_code == 200
    body = r.json()
    assert body["backend"] == "console"
    assert body["configured"] is True
    assert body["recipients"] == OPERATORS.split(",")


def test_status_shows_unconfigured_when_no_recipients(client, admin, monkeypatch):
    monkeypatch.setenv("OPERATOR_EMAILS", "")
    body = client.get("/api/admin/notifications", headers=admin).json()
    assert body["configured"] is False


# ── Lambda dispatch (production-only path) ───────────────────────────────────
def test_lambda_routes_scheduled_job_to_the_digest():
    import lambda_handler
    result = lambda_handler.handler({"job": "weekly_digest"}, None)
    assert result["sent"] is True
    assert len(email_mod.last_sends()) == 1


def test_lambda_rejects_an_unknown_job():
    import lambda_handler
    result = lambda_handler.handler({"job": "not_a_real_job"}, None)
    assert result["ok"] is False


def test_lambda_still_serves_http_events():
    """The scheduled branch must not swallow ordinary API Gateway traffic."""
    import lambda_handler
    event = {
        "version": "2.0",
        "routeKey": "GET /api/pricing",
        "rawPath": "/api/pricing",
        "rawQueryString": "",
        "headers": {"host": "test"},
        "requestContext": {
            "http": {"method": "GET", "path": "/api/pricing", "protocol": "HTTP/1.1",
                     "sourceIp": "1.2.3.4"},
            "stage": "$default", "requestId": "1", "apiId": "x",
            "domainName": "test", "domainPrefix": "test", "time": "x", "timeEpoch": 0,
            "accountId": "1",
        },
        "isBase64Encoded": False,
    }
    result = lambda_handler.handler(event, None)
    assert result["statusCode"] == 200

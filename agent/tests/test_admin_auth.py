"""Admin auth: passwordless session-based access (email on ADMIN_EMAILS) plus
the shared ADMIN_TOKEN fallback for scripts. The console's normal path is now
"log in like a member, be on the allowlist" -- no token to remember."""
import pytest
from fastapi.testclient import TestClient

from app.api.routes import admin as admin_routes
from app.data.store import reset_store
from app.main import app

client = TestClient(app)

ADMIN_EMAIL = "admin@example.com"
OPERATOR_TOKEN = "test-operator-token"


@pytest.fixture(autouse=True)
def _admin_config(monkeypatch):
    reset_store()
    monkeypatch.setattr(admin_routes, "ADMIN_EMAILS", [ADMIN_EMAIL])
    monkeypatch.setattr(admin_routes, "ADMIN_TOKEN", OPERATOR_TOKEN)


def _session_token_for(email):
    """Run the normal member login flow and return the session token."""
    r = client.post("/api/auth/start", json={"email": email})
    assert r.status_code == 200
    code = r.json()["devLoginCode"]  # conftest forces AUTH_RETURN_CODE=true
    r = client.post("/api/auth/verify", json={"email": email, "code": code})
    assert r.status_code == 200
    return r.json()["token"]


def test_allowlisted_email_session_gets_admin_access():
    tok = _session_token_for(ADMIN_EMAIL)
    r = client.post("/api/admin/login", headers={"Authorization": f"Bearer {tok}"})
    assert r.status_code == 200
    # and a real admin endpoint works with the same session
    r = client.get("/api/admin/metrics", headers={"Authorization": f"Bearer {tok}"})
    assert r.status_code == 200


def test_non_admin_session_is_rejected():
    tok = _session_token_for("member@example.com")
    r = client.post("/api/admin/login", headers={"Authorization": f"Bearer {tok}"})
    assert r.status_code == 401


def test_shared_token_fallback_still_works():
    r = client.post(
        "/api/admin/login",
        headers={"Authorization": f"Bearer {OPERATOR_TOKEN}", "X-Admin-Email": ADMIN_EMAIL},
    )
    assert r.status_code == 200


def test_shared_token_requires_allowlisted_header_email():
    r = client.post(
        "/api/admin/login",
        headers={"Authorization": f"Bearer {OPERATOR_TOKEN}", "X-Admin-Email": "intruder@example.com"},
    )
    assert r.status_code == 401


def test_garbage_token_is_rejected():
    r = client.post("/api/admin/login", headers={"Authorization": "Bearer not-a-real-token"})
    assert r.status_code == 401


def test_missing_credentials_rejected():
    r = client.post("/api/admin/login")
    assert r.status_code == 401


def test_unconfigured_console_is_503(monkeypatch):
    monkeypatch.setattr(admin_routes, "ADMIN_EMAILS", [])
    monkeypatch.setattr(admin_routes, "ADMIN_TOKEN", "")
    r = client.post("/api/admin/login", headers={"Authorization": "Bearer anything"})
    assert r.status_code == 503

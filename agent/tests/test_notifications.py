"""Operator notifications: signup alerts and the weekly digest.

Runs entirely offline. EMAIL_BACKEND=console (forced in conftest) records each
send in-process, so these assert on real payloads with no mocks and no AWS.

The load-bearing property: a mail failure must NEVER cost us a signup.
"""
import pytest
from fastapi.testclient import TestClient

from app.data import email as email_mod
from app.data.events import reset_events
from app.data.store import reset_store
from app.main import create_app
from app.services import notifications

OPERATORS = "niki@finalplaybook.com,hello@endevo.life,bluesproutagency@gmail.com"


@pytest.fixture(autouse=True)
def clean(monkeypatch):
    """Fresh store, events, and email transport per test."""
    reset_store()
    reset_events()
    email_mod.reset_email()
    monkeypatch.setenv("EMAIL_BACKEND", "console")
    monkeypatch.setenv("OPERATOR_EMAILS", OPERATORS)
    yield
    reset_store()
    reset_events()
    email_mod.reset_email()


@pytest.fixture
def client():
    return TestClient(create_app())


def sent():
    return email_mod.last_sends(limit=50)


# ── Signup alerts ────────────────────────────────────────────────────────────
def test_signup_sends_one_email_to_all_operators(client):
    r = client.post("/api/auth/start", json={"email": "new@example.com"})
    assert r.status_code == 200

    msgs = sent()
    assert len(msgs) == 1, f"expected exactly one alert, got {len(msgs)}"
    assert msgs[0]["to"] == [
        "niki@finalplaybook.com", "hello@endevo.life", "bluesproutagency@gmail.com",
    ]
    assert "new@example.com" in msgs[0]["subject"]


def test_returning_login_sends_nothing(client):
    client.post("/api/auth/start", json={"email": "repeat@example.com"})
    assert len(sent()) == 1

    # Same address again -- a login, not a signup.
    client.post("/api/auth/start", json={"email": "repeat@example.com"})
    client.post("/api/auth/start", json={"email": "repeat@example.com"})
    assert len(sent()) == 1, "returning logins must not re-alert"


def test_signup_email_contains_tier_and_timestamp(client):
    client.post("/api/auth/start", json={"email": "tiers@example.com"})
    body = sent()[0]["body"]
    assert "tiers@example.com" in body
    assert "free" in body
    assert "Total signups to date: 1" in body


def test_signup_email_carries_no_plan_content(client):
    """PRIVACY: operator mail carries identity only -- never assessment content."""
    client.post("/api/auth/start", json={"email": "private@example.com"})
    body = sent()[0]["body"].lower()
    for leak in ("answers", "narrative", "diagnosis", "will", "funeral"):
        assert leak not in body


def test_email_failure_does_not_break_signup(client, monkeypatch):
    """The whole point of best-effort: SES dying must not cost us the signup.

    Patch the name `notifications` resolves (it does `from ... import send`, so
    patching app.data.email.send would miss the already-bound reference).
    """
    def boom(*a, **k):
        raise RuntimeError("SES is down")
    monkeypatch.setattr(notifications, "send", boom)

    r = client.post("/api/auth/start", json={"email": "resilient@example.com"})
    assert r.status_code == 200
    assert r.json()["sent"] is True

    from app.data.store import get_store
    assert get_store().get_user("resilient@example.com") is not None


def test_unconfigured_recipients_is_a_noop(client, monkeypatch):
    monkeypatch.setenv("OPERATOR_EMAILS", "")
    r = client.post("/api/auth/start", json={"email": "quiet@example.com"})
    assert r.status_code == 200
    assert sent() == [], "no recipients configured -> no sends"


def test_notify_signup_never_raises(monkeypatch):
    monkeypatch.setattr(notifications, "send",
                        lambda *a, **k: (_ for _ in ()).throw(Exception("x")))
    assert notifications.notify_signup("x@example.com") is False


def test_transport_send_swallows_backend_failure(monkeypatch):
    """The transport layer's own contract: send() returns False, never raises."""
    class Broken:
        backend = "broken"
        sent = []
        def send(self, *a, **k):
            raise RuntimeError("SES rejected the message")
    monkeypatch.setattr(email_mod, "get_email", lambda: Broken())
    assert email_mod.send(["a@example.com"], "s", "b") is False


def test_transport_empty_recipients_is_false():
    assert email_mod.send([], "s", "b") is False
    assert email_mod.send(None, "s", "b") is False


# ── Weekly digest ────────────────────────────────────────────────────────────
def _seed_week(emails=(), assessments=0, chats=0, upgrades=()):
    """Emit events timestamped inside last week's digest window."""
    from app.data.events import get_events
    from app.services import analytics

    window = notifications._last_week_window()
    mid = (window["start_ms"] + window["end_ms"]) // 2
    store = get_events()

    def stamp(evt_type, email=None):
        store.emit(evt_type, email=email)
        store.events[-1]["ts"] = mid  # memory backend: retime into the window

    for em in emails:
        stamp(analytics.SIGNUP, em)
        from app.data.store import get_store
        get_store().upsert_user(em, tier="free")
    for em in upgrades:
        stamp(analytics.UPGRADE, em)
    for _ in range(assessments):
        stamp(analytics.ASSESSMENT_COMPLETED, "a@example.com")
    for _ in range(chats):
        stamp(analytics.CHAT, "c@example.com")
    return window


def test_digest_counts_the_right_week():
    _seed_week(emails=["a@example.com", "b@example.com"], assessments=3, chats=7,
               upgrades=["a@example.com"])

    result = notifications.send_weekly_digest()
    assert result["sent"] is True

    s = result["summary"]
    assert s["signupCount"] == 2
    assert s["assessmentsCompleted"] == 3
    assert s["chatMessages"] == 7
    assert s["upgradeCount"] == 1
    assert s["conversionPct"] == 50.0

    body = sent()[-1]["body"]
    assert "a@example.com" in body and "b@example.com" in body


def test_digest_excludes_events_outside_the_window():
    """Events from today (this week) must not land in last week's digest."""
    from app.services import analytics
    _seed_week(emails=["inwindow@example.com"])
    analytics.emit(analytics.SIGNUP, email="thisweek@example.com")  # now = out

    result = notifications.send_weekly_digest()
    emails = [m["email"] for m in result["summary"]["signups"]]
    assert "inwindow@example.com" in emails
    assert "thisweek@example.com" not in emails


def test_digest_zero_activity_still_sends():
    """Silence is ambiguous; '0 signups' is information."""
    result = notifications.send_weekly_digest()
    assert result["sent"] is True
    assert result["summary"]["signupCount"] == 0
    assert "No new signups" in sent()[-1]["subject"]


def test_digest_is_idempotent_per_week():
    _seed_week(emails=["once@example.com"])

    first = notifications.send_weekly_digest()
    assert first["sent"] is True
    assert len(sent()) == 1

    second = notifications.send_weekly_digest()
    assert second["sent"] is False
    assert second["reason"] == "already_sent"
    assert len(sent()) == 1, "must not double-send the same week"


def test_digest_force_overrides_the_watermark():
    notifications.send_weekly_digest()
    assert len(sent()) == 1
    forced = notifications.send_weekly_digest(force=True)
    assert forced["sent"] is True
    assert len(sent()) == 2


def test_digest_without_recipients_still_reports_summary(monkeypatch):
    monkeypatch.setenv("OPERATOR_EMAILS", "")
    _seed_week(emails=["x@example.com"])
    result = notifications.send_weekly_digest()
    assert result["sent"] is False
    assert result["reason"] == "no_recipients"
    assert result["summary"]["signupCount"] == 1  # still computed, just not sent


def test_digest_never_raises(monkeypatch):
    monkeypatch.setattr(notifications, "weekly_summary",
                        lambda *a, **k: (_ for _ in ()).throw(Exception("boom")))
    result = notifications.send_weekly_digest()
    assert result["sent"] is False
    assert "error" in result["reason"]

"""Member feedback: help requests, complaints, survey responses.

Covers both doors (anonymous + signed-in), validation, rate limiting, and the
load-bearing guarantee: a member's words are PERSISTED even when email fails.
Losing a complaint because SES was misconfigured is the worst failure mode here.
"""
import pytest
from fastapi.testclient import TestClient

from app.data import email as email_mod
from app.data.events import reset_events
from app.data.store import get_store, reset_store
from app.main import create_app
from app.services import feedback as feedback_service
from app.services import notifications

OPERATORS = "niki@finalplaybook.com,hello@endevo.life,bluesproutagency@gmail.com"


@pytest.fixture(autouse=True)
def clean(monkeypatch):
    reset_store()
    reset_events()
    email_mod.reset_email()
    monkeypatch.setenv("EMAIL_BACKEND", "console")
    monkeypatch.setenv("OPERATOR_EMAILS", OPERATORS)
    feedback_service._ip_hits.clear()  # in-process, so it leaks between tests
    yield
    reset_store()
    reset_events()
    email_mod.reset_email()


@pytest.fixture
def client():
    return TestClient(create_app())


def login(client, email):
    """Sign in and return an auth header (local auth returns the code in dev)."""
    start = client.post("/api/auth/start", json={"email": email}).json()
    verify = client.post(
        "/api/auth/verify", json={"email": email, "code": start["devLoginCode"]}
    ).json()
    return {"Authorization": f"Bearer {verify['token']}"}


def sent():
    return email_mod.last_sends(limit=50)


# ── Anonymous + signed-in submission ─────────────────────────────────────────
def test_anonymous_submission_works(client):
    r = client.post("/api/feedback", json={
        "kind": "help", "message": "I can't sign in with my email.",
        "email": "stuck@example.com",
    })
    assert r.status_code == 200
    assert r.json()["ok"] is True

    stored = get_store().list_feedback()
    assert len(stored) == 1
    assert stored[0]["email"] == "stuck@example.com"
    assert stored[0]["signed_in"] is False


def test_signed_in_submission_uses_session_email(client):
    headers = login(client, "member@example.com")
    email_mod.reset_email()  # drop the signup alert so we count only feedback

    r = client.post("/api/feedback", json={
        "kind": "survey", "message": "The walkthrough was calmer than I expected.",
        "rating": 5,
    }, headers=headers)
    assert r.status_code == 200

    stored = get_store().list_feedback()[0]
    assert stored["email"] == "member@example.com"
    assert stored["signed_in"] is True
    assert stored["rating"] == 5


def test_session_email_overrides_a_spoofed_body_email(client):
    """A signed-in submission can never be attributed to someone else."""
    headers = login(client, "real@example.com")
    client.post("/api/feedback", json={
        "kind": "complaint", "message": "Wrong tone on the funeral step.",
        "email": "someone-else@example.com",
    }, headers=headers)

    assert get_store().list_feedback()[0]["email"] == "real@example.com"


def test_all_three_kinds_accepted(client):
    for kind in ("help", "complaint", "survey"):
        r = client.post("/api/feedback", json={
            "kind": kind, "message": f"A {kind} message.", "email": "k@example.com",
        })
        assert r.status_code == 200, f"{kind} rejected"
    assert len(get_store().list_feedback()) == 3


# ── Notification ─────────────────────────────────────────────────────────────
def test_feedback_notifies_operators(client):
    client.post("/api/feedback", json={
        "kind": "help", "message": "How do I share this with my daughter?",
        "email": "asker@example.com",
    })
    msgs = sent()
    assert len(msgs) == 1
    assert msgs[0]["to"] == OPERATORS.split(",")
    assert "asker@example.com" in msgs[0]["body"]
    assert "How do I share this" in msgs[0]["body"]


def test_complaint_is_subject_tagged_for_triage(client):
    client.post("/api/feedback", json={
        "kind": "complaint", "message": "This felt cold when I just lost my father.",
        "email": "upset@example.com",
    })
    assert "COMPLAINT" in sent()[0]["subject"]


def test_feedback_persists_when_email_fails(client, monkeypatch):
    """The system of record is the store. Email is best-effort."""
    monkeypatch.setattr(notifications, "send",
                        lambda *a, **k: (_ for _ in ()).throw(RuntimeError("SES down")))

    r = client.post("/api/feedback", json={
        "kind": "complaint", "message": "Something important we must not lose.",
        "email": "critical@example.com",
    })
    assert r.status_code == 200

    stored = get_store().list_feedback()
    assert len(stored) == 1
    assert "must not lose" in stored[0]["message"]


# ── Validation ───────────────────────────────────────────────────────────────
def test_invalid_kind_is_422(client):
    r = client.post("/api/feedback", json={
        "kind": "spam", "message": "hello", "email": "a@example.com",
    })
    assert r.status_code == 422


def test_empty_message_is_422(client):
    r = client.post("/api/feedback", json={
        "kind": "help", "message": "   ", "email": "a@example.com",
    })
    assert r.status_code == 422


def test_overlong_message_is_422(client):
    r = client.post("/api/feedback", json={
        "kind": "survey", "message": "x" * (feedback_service.MAX_MESSAGE_CHARS + 1),
        "email": "a@example.com",
    })
    assert r.status_code == 422


def test_help_without_email_is_422(client):
    """We can't answer a help request with no return address."""
    r = client.post("/api/feedback", json={"kind": "help", "message": "Help me please."})
    assert r.status_code == 422


def test_anonymous_survey_needs_no_email(client):
    """A survey response needs no reply, so it may stay fully anonymous."""
    r = client.post("/api/feedback", json={
        "kind": "survey", "message": "Useful, thank you.", "rating": 4,
    })
    assert r.status_code == 200
    assert get_store().list_feedback()[0]["email"] is None


def test_bad_email_is_422(client):
    r = client.post("/api/feedback", json={
        "kind": "help", "message": "Hello there.", "email": "not-an-email",
    })
    assert r.status_code == 422


def test_out_of_range_rating_is_422(client):
    r = client.post("/api/feedback", json={
        "kind": "survey", "message": "Fine.", "rating": 9, "email": "a@example.com",
    })
    assert r.status_code == 422


# ── Rate limiting ────────────────────────────────────────────────────────────
def test_rate_limited_after_five_per_hour(client):
    payload = {"kind": "help", "message": "Repeated ask.", "email": "chatty@example.com"}
    for i in range(feedback_service.RATE_LIMIT_MAX):
        assert client.post("/api/feedback", json=payload).status_code == 200, f"#{i+1}"

    r = client.post("/api/feedback", json=payload)
    assert r.status_code == 429


def test_anonymous_submissions_are_rate_limited_by_ip(client):
    """An anonymous survey carries no email, so there'd be no key to limit on --
    without the IP fallback this public endpoint would write rows and send mail
    without bound. Regression test for that hole."""
    payload = {"kind": "survey", "message": "No email on this one.", "rating": 3}
    ok = 0
    for _ in range(feedback_service.IP_RATE_LIMIT_MAX + 5):
        if client.post("/api/feedback", json=payload).status_code == 200:
            ok += 1
    assert ok <= feedback_service.IP_RATE_LIMIT_MAX, (
        f"anonymous path accepted {ok} submissions with no ceiling")


def test_ip_limit_uses_the_first_forwarded_address(client, monkeypatch):
    """Behind API Gateway the real caller is the FIRST X-Forwarded-For entry;
    distinct clients must not share one bucket."""
    monkeypatch.setattr(feedback_service, "_ip_hits", {})
    payload = {"kind": "survey", "message": "Anonymous note."}
    for _ in range(feedback_service.IP_RATE_LIMIT_MAX):
        client.post("/api/feedback", json=payload,
                    headers={"X-Forwarded-For": "1.1.1.1, 10.0.0.1"})

    blocked = client.post("/api/feedback", json=payload,
                          headers={"X-Forwarded-For": "1.1.1.1, 10.0.0.1"})
    assert blocked.status_code == 429

    other = client.post("/api/feedback", json=payload,
                        headers={"X-Forwarded-For": "2.2.2.2, 10.0.0.1"})
    assert other.status_code == 200, "a different client must get its own budget"


def test_signed_in_members_are_not_limited_by_shared_ip(client, monkeypatch):
    """Identified users are limited by email, not IP -- a family behind one NAT
    must not lock each other out."""
    monkeypatch.setattr(feedback_service, "_ip_hits", {})
    headers = login(client, "known@example.com")
    r = client.post("/api/feedback", json={"kind": "survey", "message": "Signed in."},
                    headers={**headers, "X-Forwarded-For": "3.3.3.3"})
    assert r.status_code == 200
    assert feedback_service._ip_hits == {}, "identified submissions shouldn't touch the IP bucket"


def test_rate_limit_is_per_email(client):
    for _ in range(feedback_service.RATE_LIMIT_MAX):
        client.post("/api/feedback", json={
            "kind": "help", "message": "Mine.", "email": "first@example.com"})

    r = client.post("/api/feedback", json={
        "kind": "help", "message": "Mine too.", "email": "second@example.com"})
    assert r.status_code == 200, "one member's limit must not block another"


# ── Options endpoint ─────────────────────────────────────────────────────────
def test_options_endpoint_matches_server_rules(client):
    body = client.get("/api/feedback/options").json()
    assert [k["value"] for k in body["kinds"]] == list(feedback_service.KINDS)
    assert body["maxMessageChars"] == feedback_service.MAX_MESSAGE_CHARS


# ── Digest integration ───────────────────────────────────────────────────────
def test_feedback_appears_in_the_weekly_digest(client, monkeypatch):
    client.post("/api/feedback", json={
        "kind": "complaint", "message": "The wording on step 3 upset me.",
        "email": "voice@example.com",
    })
    # Retime into last week's window (memory store keeps entries mutable).
    window = notifications._last_week_window()
    mid_s = (window["start_ms"] + window["end_ms"]) // 2000
    get_store().feedback[0]["created_at"] = mid_s

    summary = notifications.weekly_summary()
    assert summary["feedback"]["total"] == 1
    assert summary["feedback"]["byKind"]["complaint"] == 1
    assert "step 3" in summary["feedback"]["complaints"][0]["message"]

    body = notifications._digest_body(summary, window)
    assert "MEMBER FEEDBACK" in body
    assert "voice@example.com" in body

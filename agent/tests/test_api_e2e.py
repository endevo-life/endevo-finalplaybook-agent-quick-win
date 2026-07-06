"""End-to-end tests against the FastAPI layer via TestClient (no dev server
needs to be running). Free-tier, auth, entitlement, and validation tests need
nothing beyond requirements.txt. The paid-tier LLM tests are gated on
ANTHROPIC_API_KEY so the suite is runnable with or without credentials.

The store defaults to the in-memory backend (STORE_BACKEND unset), so these
tests exercise real auth + entitlement logic without any AWS dependency.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from fastapi.testclient import TestClient

from api import app
from store import get_store

client = TestClient(app)


# --- helpers -----------------------------------------------------------------
def _login(email: str) -> str:
    """Run the dev login flow and return a bearer token."""
    start = client.post("/api/auth/start", json={"email": email})
    assert start.status_code == 200
    code = start.json()["devLoginCode"]
    verify = client.post("/api/auth/verify", json={"email": email, "code": code})
    assert verify.status_code == 200
    return verify.json()["token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _grant_paid(email: str):
    """Simulate a completed Stripe payment by flipping the tier in the store."""
    get_store().set_tier(email.lower(), "paid")


# --- public content ----------------------------------------------------------
def test_glossary_endpoint_returns_terms():
    resp = client.get("/api/glossary")
    assert resp.status_code == 200
    terms = resp.json()
    assert len(terms) > 0
    assert all("term" in t and "shortDefinition" in t for t in terms)


def test_pricing_endpoint_lists_both_plans():
    resp = client.get("/api/pricing")
    assert resp.status_code == 200
    tiers = {p["tier"] for p in resp.json()["plans"]}
    assert tiers == {"free", "paid"}


# --- domain assessment (condensed tiered model, free/anonymous) --------------
def test_assessment_questions_available():
    resp = client.get("/api/assessment")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["basicsFirst"]) >= 2   # docbox + phone legacy contact
    assert len(data["questions"]) >= 3      # financial, physical, digital
    # every question has tiered options with an action per answer
    for q in data["questions"]:
        assert len(q["options"]) >= 2
        assert all("action" in o and "value" in o for o in q["options"])


def test_assessment_plan_maps_answers_to_actions():
    resp = client.post("/api/assessment/plan", json={"answers": {
        "FIN_contacts": "no",
        "DIG_password_manager": "partial",
    }})
    assert resp.status_code == 200
    data = resp.json()
    # basics-first always prepended, in order
    assert [b["id"] for b in data["basicsFirst"]][:2] == ["basics_docbox", "basics_legacy_contact"]
    # answered questions resolved to their selected option
    by_id = {d["id"]: d for d in data["domainItems"]}
    assert by_id["FIN_contacts"]["resultType"] == "steps"
    assert len(by_id["FIN_contacts"]["steps"]) > 0
    assert by_id["DIG_password_manager"]["answer"].startswith("I use one")


def test_assessment_review_answer_returns_checklist_not_steps():
    resp = client.post("/api/assessment/plan", json={"answers": {"FIN_contacts": "yes"}})
    item = resp.json()["domainItems"][0]
    assert item["resultType"] == "review"
    assert len(item["checklist"]) > 0


def test_assessment_ignores_unknown_question_and_option():
    resp = client.post("/api/assessment/plan", json={"answers": {
        "NOT_A_QUESTION": "no",
        "FIN_contacts": "not_an_option",
    }})
    assert resp.status_code == 200
    assert resp.json()["domainItems"] == []  # nothing resolved, but no error


# --- free tier (anonymous) ---------------------------------------------------
def test_free_tier_e2e_no_account_needed():
    resp = client.post("/api/plan", json={
        "flags": {"hasAgingParent": True, "parentHasNoDocs": True},
        "memberFirstName": "Elisa",
        "tier": "free",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["tier"] == "free"
    assert data["plan"]["leadProfile"]["id"] == "profile_aging_parent"
    assert "personalized" not in data


def test_trial_alias_still_works():
    """Older clients send tier='trial'; it must still route to the free path."""
    resp = client.post("/api/plan", json={
        "flags": {"hasAgingParent": True, "parentHasNoDocs": True},
        "memberFirstName": "Elisa",
        "tier": "trial",
    })
    assert resp.status_code == 200
    assert resp.json()["tier"] == "free"


def test_unknown_flag_rejected():
    resp = client.post("/api/plan", json={
        "flags": {"notARealFlag": True}, "memberFirstName": "Test", "tier": "free",
    })
    assert resp.status_code == 400


def test_invalid_tier_rejected():
    resp = client.post("/api/plan", json={
        "flags": {}, "memberFirstName": "Test", "tier": "enterprise",
    })
    assert resp.status_code == 400


# --- auth --------------------------------------------------------------------
def test_login_flow_returns_token_and_free_user():
    token = _login("newuser@example.com")
    me = client.get("/api/me", headers=_auth(token))
    assert me.status_code == 200
    assert me.json()["tier"] == "free"


def test_bad_login_code_rejected():
    client.post("/api/auth/start", json={"email": "someone@example.com"})
    resp = client.post("/api/auth/verify", json={"email": "someone@example.com", "code": "000000"})
    assert resp.status_code == 401


def test_me_requires_auth():
    assert client.get("/api/me").status_code == 401


# --- entitlement enforcement -------------------------------------------------
def test_paid_plan_without_login_is_401():
    resp = client.post("/api/plan", json={
        "flags": {"hasAgingParent": True, "parentHasNoDocs": True},
        "memberFirstName": "Elisa", "tier": "paid",
    })
    assert resp.status_code == 401


def test_free_user_requesting_paid_is_402():
    token = _login("freeuser@example.com")
    resp = client.post("/api/plan", json={
        "flags": {"hasAgingParent": True, "parentHasNoDocs": True},
        "memberFirstName": "Elisa", "tier": "paid",
    }, headers=_auth(token))
    assert resp.status_code == 402  # upgrade required -- server-side, not client-trusted


def test_free_chat_blocked_after_quota_exhausted():
    """Free users get a small taste (3 chats). Once the monthly quota is used up,
    the next request is blocked (429). We pre-exhaust the quota via the store so
    this needs no LLM/API key."""
    email = "chatfree@example.com"
    token = _login(email)
    store = get_store()
    for _ in range(3):
        store.increment_usage(email.lower(), "chat_count")  # simulate 3 used
    resp = client.post("/api/chat", json={
        "plan": {"leadProfile": None, "actionItems": [], "businessActionItems": [], "quotes": []},
        "memberFirstName": "Test",
        "history": [{"role": "user", "content": "hi"}],
    }, headers=_auth(token))
    assert resp.status_code == 429  # quota exhausted -> upgrade prompt


def test_chat_requires_login():
    """Anonymous users can't chat -- they must sign in (free) first."""
    resp = client.post("/api/chat", json={
        "plan": {"leadProfile": None, "actionItems": [], "businessActionItems": [], "quotes": []},
        "memberFirstName": "Test",
        "history": [{"role": "user", "content": "hi"}],
    })
    assert resp.status_code == 401


def test_empty_flags_paid_user_skips_llm_and_succeeds():
    """No ANTHROPIC_API_KEY needed -- an empty plan must never reach the LLM,
    so this must succeed even with zero credentials configured."""
    email = "paidempty@example.com"
    token = _login(email)
    _grant_paid(email)
    resp = client.post("/api/plan", json={
        "flags": {}, "memberFirstName": "Test", "tier": "paid",
    }, headers=_auth(token))
    assert resp.status_code == 200
    assert resp.json()["personalized"] is None


def test_chat_rejects_empty_history():
    token = _login("chatempty@example.com")
    _grant_paid("chatempty@example.com")
    resp = client.post("/api/chat", json={
        "plan": {"leadProfile": None, "actionItems": [], "businessActionItems": [], "quotes": []},
        "memberFirstName": "Test", "history": [],
    }, headers=_auth(token))
    assert resp.status_code == 400


def test_chat_rejects_history_not_ending_in_user():
    token = _login("chatorder@example.com")
    _grant_paid("chatorder@example.com")
    resp = client.post("/api/chat", json={
        "plan": {"leadProfile": None, "actionItems": [], "businessActionItems": [], "quotes": []},
        "memberFirstName": "Test", "history": [{"role": "assistant", "content": "hi"}],
    }, headers=_auth(token))
    assert resp.status_code == 400


@pytest.mark.skipif(
    bool(os.environ.get("ANTHROPIC_API_KEY")),
    reason="only meaningful when no credentials are configured",
)
def test_paid_user_without_credentials_returns_clear_error():
    email = "paidnocreds@example.com"
    token = _login(email)
    _grant_paid(email)
    resp = client.post("/api/plan", json={
        "flags": {"hasAgingParent": True, "parentHasNoDocs": True},
        "memberFirstName": "Elisa", "tier": "paid",
    }, headers=_auth(token))
    assert resp.status_code == 502
    assert "Agent error" in resp.json()["detail"]


@pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="requires a real Anthropic API key to exercise the paid-tier LLM call",
)
def test_paid_tier_is_grounded_in_matched_action_items():
    """Smoke check only, not a rigorous grounding verifier (see
    docs/guardrails.md 'What this does NOT cover yet')."""
    email = "paidllm@example.com"
    token = _login(email)
    _grant_paid(email)
    resp = client.post("/api/plan", json={
        "flags": {"hasAgingParent": True, "parentHasNoDocs": True},
        "memberFirstName": "Elisa", "tier": "paid",
    }, headers=_auth(token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["personalized"] is not None
    assert len(data["personalized"]["steps"]) > 0
    step_texts = " ".join(s["step"] for s in data["personalized"]["steps"]).lower()
    overlap_terms = ["will", "power of attorney", "dnr", "neighbor", "safe deposit", "parent"]
    assert any(term in step_texts for term in overlap_terms)


@pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="requires a real Anthropic API key to exercise the chat LLM call",
)
def test_chat_is_grounded_in_matched_plan():
    email = "chatllm@example.com"
    token = _login(email)
    _grant_paid(email)
    plan_resp = client.post("/api/plan", json={
        "flags": {"hasAgingParent": True, "parentHasNoDocs": True},
        "memberFirstName": "Elisa", "tier": "free",
    })
    plan = plan_resp.json()["plan"]
    resp = client.post("/api/chat", json={
        "plan": plan, "memberFirstName": "Elisa",
        "history": [{"role": "user", "content": "What should I do first?"}],
    }, headers=_auth(token))
    assert resp.status_code == 200
    reply = resp.json()["reply"].lower()
    overlap_terms = ["will", "power of attorney", "dnr", "neighbor", "safe deposit", "parent"]
    assert any(term in reply for term in overlap_terms)

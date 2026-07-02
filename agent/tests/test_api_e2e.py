"""End-to-end tests against the FastAPI layer via TestClient (no dev server
needs to be running). Trial-tier and validation tests need nothing beyond
requirements.txt. The paid-tier tests are gated on ANTHROPIC_API_KEY so the
suite is runnable with or without credentials configured.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from fastapi.testclient import TestClient

from api import app

client = TestClient(app)


def test_glossary_endpoint_returns_terms():
    resp = client.get("/api/glossary")
    assert resp.status_code == 200
    terms = resp.json()
    assert len(terms) > 0
    assert all("term" in t and "shortDefinition" in t for t in terms)


def test_trial_tier_e2e():
    resp = client.post("/api/plan", json={
        "flags": {"hasAgingParent": True, "parentHasNoDocs": True},
        "memberFirstName": "Elisa",
        "tier": "trial",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["tier"] == "trial"
    assert data["plan"]["leadProfile"]["id"] == "profile_aging_parent"
    assert "personalized" not in data


def test_unknown_flag_rejected():
    resp = client.post("/api/plan", json={
        "flags": {"notARealFlag": True},
        "memberFirstName": "Test",
        "tier": "trial",
    })
    assert resp.status_code == 400


def test_invalid_tier_rejected():
    resp = client.post("/api/plan", json={
        "flags": {},
        "memberFirstName": "Test",
        "tier": "enterprise",
    })
    assert resp.status_code == 400


def test_empty_flags_paid_tier_skips_llm_and_succeeds():
    """No ANTHROPIC_API_KEY needed here -- an empty plan must never reach the
    LLM, so this must succeed even with zero credentials configured."""
    resp = client.post("/api/plan", json={
        "flags": {},
        "memberFirstName": "Test",
        "tier": "paid",
    })
    assert resp.status_code == 200
    assert resp.json()["personalized"] is None


@pytest.mark.skipif(
    bool(os.environ.get("ANTHROPIC_API_KEY")),
    reason="only meaningful when no credentials are configured",
)
def test_paid_tier_without_credentials_returns_clear_error():
    resp = client.post("/api/plan", json={
        "flags": {"hasAgingParent": True, "parentHasNoDocs": True},
        "memberFirstName": "Elisa",
        "tier": "paid",
    })
    assert resp.status_code == 502
    assert "Agent error" in resp.json()["detail"]


def test_chat_rejects_empty_history():
    resp = client.post("/api/chat", json={
        "plan": {"leadProfile": None, "actionItems": [], "businessActionItems": [], "quotes": []},
        "memberFirstName": "Test",
        "history": [],
    })
    assert resp.status_code == 400


def test_chat_rejects_history_not_ending_in_user():
    resp = client.post("/api/chat", json={
        "plan": {"leadProfile": None, "actionItems": [], "businessActionItems": [], "quotes": []},
        "memberFirstName": "Test",
        "history": [{"role": "assistant", "content": "hi"}],
    })
    assert resp.status_code == 400


@pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="requires a real Anthropic API key to exercise the chat LLM call",
)
def test_chat_is_grounded_in_matched_plan():
    """Smoke check only, same caveat as the paid-tier grounding test below --
    catches gross drift, nothing subtler."""
    plan_resp = client.post("/api/plan", json={
        "flags": {"hasAgingParent": True, "parentHasNoDocs": True},
        "memberFirstName": "Elisa",
        "tier": "trial",
    })
    plan = plan_resp.json()["plan"]

    resp = client.post("/api/chat", json={
        "plan": plan,
        "memberFirstName": "Elisa",
        "history": [{"role": "user", "content": "What should I do first?"}],
    })
    assert resp.status_code == 200
    reply = resp.json()["reply"].lower()
    overlap_terms = ["will", "power of attorney", "dnr", "neighbor", "safe deposit", "parent"]
    assert any(term in reply for term in overlap_terms)


@pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="requires a real Anthropic API key to exercise the paid-tier LLM call",
)
def test_paid_tier_is_grounded_in_matched_action_items():
    """Smoke check only, not a rigorous grounding verifier (see
    docs/guardrails.md 'What this does NOT cover yet') -- catches gross
    drift such as the model inventing unrelated content, nothing subtler."""
    resp = client.post("/api/plan", json={
        "flags": {"hasAgingParent": True, "parentHasNoDocs": True},
        "memberFirstName": "Elisa",
        "tier": "paid",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["personalized"] is not None
    assert len(data["personalized"]["steps"]) > 0
    step_texts = " ".join(s["step"] for s in data["personalized"]["steps"]).lower()
    overlap_terms = ["will", "power of attorney", "dnr", "neighbor", "safe deposit", "parent"]
    assert any(term in step_texts for term in overlap_terms)

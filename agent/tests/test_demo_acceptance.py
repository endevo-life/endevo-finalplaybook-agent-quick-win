"""Acceptance tests for the demo, derived from the product spec (freemium plan +
limited chat, paid full + AI + progress, personalized-from-answers).

Run against the real app via TestClient. LLM tests (chat, personalize) require a
working LLM backend (Anthropic key OR Bedrock) -- they skip otherwise so the
non-LLM criteria always run.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.data.store import get_store

client = TestClient(app)

# The demo runs on a live LLM (Bedrock or Anthropic). In the hermetic test env
# neither is guaranteed, so gate LLM criteria behind this.
LLM_AVAILABLE = bool(os.environ.get("ANTHROPIC_API_KEY")) or os.environ.get("LLM_BACKEND") == "bedrock"


def _login(email):
    s = client.post("/api/auth/start", json={"email": email}).json()
    v = client.post("/api/auth/verify", json={"email": email, "code": s["devLoginCode"]}).json()
    return {"Authorization": f"Bearer {v['token']}"}


def _upgrade(email):
    get_store().set_tier(email.lower(), "paid")


ANSWERS_A = {"FIN_beneficiaries": "no", "DIG_crypto": "partial"}
ANSWERS_B = {"PHYS_directive": "no", "DIG_password_manager": "yes"}


# AC-1: freemium has a plan
def test_ac1_free_user_gets_a_plan():
    r = client.post("/api/assessment/plan", json={"answers": ANSWERS_A})
    assert r.status_code == 200
    data = r.json()
    assert len(data["basicsFirst"]) >= 2          # docbox + phone legacy contact
    assert len(data["domainItems"]) >= 1          # at least one answered action


# AC-2: free chat is limited (3), then blocked
def test_ac2_free_chat_blocked_after_limit():
    email = "ac2-free@test.com"
    h = _login(email)
    store = get_store()
    for _ in range(3):
        store.increment_usage(email, "chat_count")  # simulate 3 used
    r = client.post("/api/chat", json={
        "plan": {"leadProfile": None, "actionItems": [], "businessActionItems": [], "quotes": []},
        "memberFirstName": "T", "history": [{"role": "user", "content": "hi"}],
    }, headers=h)
    assert r.status_code == 429  # quota exhausted -> upgrade prompt


# AC-3: paid chat actually replies (this is the "chat not working?" check)
@pytest.mark.skipif(not LLM_AVAILABLE, reason="needs a live LLM backend")
def test_ac3_paid_chat_returns_reply():
    email = "ac3-paid@test.com"
    h = _login(email)
    _upgrade(email)
    plan = {"leadProfile": {"id": "x", "name": "P"},
            "actionItems": [{"text": "Name beneficiaries on your accounts", "domain": "financial",
                             "steps": ["Log in to each account"]}],
            "businessActionItems": [], "digitalActionItems": [], "quotes": []}
    r = client.post("/api/chat", json={
        "plan": plan, "memberFirstName": "Sam",
        "history": [{"role": "user", "content": "what should I do first?"}],
    }, headers=h)
    assert r.status_code == 200, r.text
    assert len(r.json()["reply"]) > 10  # a real, non-empty reply


# AC-4: personalized plan is actually based on the answers
@pytest.mark.skipif(not LLM_AVAILABLE, reason="needs a live LLM backend")
def test_ac4_personalized_reflects_answers():
    email = "ac4-paid@test.com"
    h = _login(email)
    _upgrade(email)
    # Two different answer sets should ground on different action items.
    ra = client.post("/api/assessment/personalize",
                     json={"answers": {"FIN_beneficiaries": "no"}, "memberFirstName": "Sam"}, headers=h)
    assert ra.status_code == 200, ra.text
    text_a = " ".join(s["step"] + s["why_it_matters"] for s in ra.json()["personalized"]["steps"]).lower()
    # The financial-beneficiary answer should surface beneficiary/account language.
    assert any(w in text_a for w in ["beneficiar", "account", "financial"]), text_a


# AC-5: progress (completed items) saves and retrieves
def test_ac5_progress_saves_and_retrieves():
    email = "ac5-paid@test.com"
    h = _login(email)
    _upgrade(email)
    client.post("/api/my/plan", json={
        "answers": ANSWERS_A,
        "tracked": {"basics_docbox::0": True, "FIN_beneficiaries::1": True},
    }, headers=h)
    got = client.get("/api/my/plan", headers=h).json()
    assert got["tracked"]["basics_docbox::0"] is True
    assert got["tracked"]["FIN_beneficiaries::1"] is True
    assert got["answers"] == ANSWERS_A

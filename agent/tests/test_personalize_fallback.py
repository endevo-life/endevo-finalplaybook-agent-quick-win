"""The failure-fallback path: a bedrock call that raises must fall back to the
Claude path when a key is present, and re-raise when it isn't (so we don't mask a
real bedrock error with a missing-key error)."""
from app.agent import personalize


_FAKE_PLAN = {
    "leadProfile": {"id": "p", "name": "n", "urgency": "high"},
    "actionItems": [{"text": "Ask for the will.", "domain": "legal"}],
    "quotes": [],
}
_SENTINEL = object()


def test_bedrock_failure_falls_back_to_claude(monkeypatch):
    monkeypatch.setenv("LLM_BACKEND", "bedrock")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    monkeypatch.delenv("LLM_BUDGET_USD", raising=False)

    monkeypatch.setattr(personalize, "_personalize_bedrock",
                        lambda *a, **k: (_ for _ in ()).throw(ValueError("llama bad json")))
    called = {}

    def fake_claude(plan, name, signals=None):
        called["yes"] = True
        return _SENTINEL

    monkeypatch.setattr(personalize, "_personalize_anthropic", fake_claude)

    out = personalize.personalize(_FAKE_PLAN, "Sam")
    assert out is _SENTINEL
    assert called.get("yes") is True


def test_bedrock_failure_without_key_reraises(monkeypatch):
    """No Claude key -> don't mask the real bedrock error with a key error."""
    monkeypatch.setenv("LLM_BACKEND", "bedrock")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("LLM_BUDGET_USD", raising=False)

    monkeypatch.setattr(personalize, "_personalize_bedrock",
                        lambda *a, **k: (_ for _ in ()).throw(ValueError("llama down")))

    import pytest
    with pytest.raises(ValueError, match="llama down"):
        personalize.personalize(_FAKE_PLAN, "Sam")


def test_anthropic_primary_never_calls_bedrock(monkeypatch):
    monkeypatch.setenv("LLM_BACKEND", "anthropic")
    monkeypatch.setattr(personalize, "_personalize_anthropic", lambda *a, **k: _SENTINEL)
    monkeypatch.setattr(personalize, "_personalize_bedrock",
                        lambda *a, **k: (_ for _ in ()).throw(AssertionError("should not be called")))
    assert personalize.personalize(_FAKE_PLAN, "Sam") is _SENTINEL

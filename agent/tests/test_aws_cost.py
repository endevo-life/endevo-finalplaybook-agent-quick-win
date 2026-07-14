"""Cost service tests -- the estimate path (no AWS billing access) and the
fallback contract. The real Cost Explorer path isn't exercised here (no live
AWS in CI); we assert it's gated and that failures degrade to an estimate
rather than crashing the admin Cost tab."""
import importlib

from app.services import analytics, aws_cost
from app.data import events


def _fresh_events():
    events.reset_events()
    return events.get_events()


def test_estimate_is_default_source(monkeypatch):
    monkeypatch.delenv("AWS_COST_ENABLED", raising=False)
    _fresh_events()
    out = aws_cost.costs(days=30)
    assert out["source"] == "estimate"
    assert out["days"] == 30
    assert "note" in out


def test_ai_cost_tracks_llm_call_events(monkeypatch):
    monkeypatch.delenv("AWS_COST_ENABLED", raising=False)
    monkeypatch.setenv("AI_COST_PER_CALL_USD", "0.005")
    importlib.reload(aws_cost)  # pick up the per-call override
    _fresh_events()
    for _ in range(10):
        analytics.emit(analytics.PERSONALIZE, email="a@x.com")
    for _ in range(20):
        analytics.emit(analytics.CHAT, email="a@x.com")
    # signups shouldn't count as AI calls
    analytics.emit(analytics.SIGNUP, email="a@x.com")

    out = aws_cost.costs(days=30)
    assert out["totals"]["aiCalls"] == 30
    assert out["totals"]["aiCost"] == round(30 * 0.005, 4)
    ai = next(s for s in out["services"] if "Anthropic" in s["service"])
    assert ai["cost"] == out["totals"]["aiCost"]
    assert ai["billed"] is False


def test_days_is_clamped(monkeypatch):
    monkeypatch.delenv("AWS_COST_ENABLED", raising=False)
    _fresh_events()
    assert aws_cost.costs(days=9999)["days"] == 90
    assert aws_cost.costs(days=0)["days"] == 1


def test_aws_path_failure_degrades_to_estimate(monkeypatch):
    """AWS_COST_ENABLED on but the CE call blows up -> estimate + a degraded
    note, never a 500."""
    monkeypatch.setenv("AWS_COST_ENABLED", "1")
    _fresh_events()

    def boom(days):
        raise RuntimeError("no credentials")

    monkeypatch.setattr(aws_cost, "_aws_costs", boom)
    out = aws_cost.costs(days=7)
    assert out["source"] == "estimate"
    assert "degraded" in out
    assert "no credentials" in out["degraded"]

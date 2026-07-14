"""Backend-selection + budget-guard tests. The failure-fallback (bedrock ->
claude on error) is tested at the personalize() level in test_personalize_fallback."""
from app.agent import llm_router
from app.data import events
from app.services import analytics


def _fresh():
    events.reset_events()
    return events.get_events()


def test_default_primary_is_anthropic(monkeypatch):
    monkeypatch.delenv("LLM_BACKEND", raising=False)
    monkeypatch.delenv("LLM_BUDGET_USD", raising=False)
    assert llm_router.choose_backend() == "anthropic"


def test_bedrock_primary_passes_through_when_no_budget(monkeypatch):
    monkeypatch.setenv("LLM_BACKEND", "bedrock")
    monkeypatch.delenv("LLM_BUDGET_USD", raising=False)
    _fresh()
    assert llm_router.choose_backend() == "bedrock"


def test_estimated_budget_trip_routes_to_claude(monkeypatch):
    monkeypatch.setenv("LLM_BACKEND", "bedrock")
    monkeypatch.setenv("LLM_BUDGET_USD", "0.02")   # tiny cap
    monkeypatch.setenv("AI_COST_PER_CALL_USD", "0.005")
    _fresh()
    # 5 calls x $0.005 = $0.025 > $0.02 -> should flip to claude
    for _ in range(5):
        analytics.emit(analytics.PERSONALIZE, email="a@x.com")
    assert llm_router.choose_backend() == "anthropic"


def test_under_budget_stays_on_bedrock(monkeypatch):
    monkeypatch.setenv("LLM_BACKEND", "bedrock")
    monkeypatch.setenv("LLM_BUDGET_USD", "100")
    _fresh()
    for _ in range(3):
        analytics.emit(analytics.CHAT, email="a@x.com")
    assert llm_router.choose_backend() == "bedrock"


def test_budget_guard_fails_open(monkeypatch):
    """If the spend meter raises, choose_backend must NOT block -- it returns the
    primary rather than failing a member request."""
    monkeypatch.setenv("LLM_BACKEND", "bedrock")
    monkeypatch.setenv("LLM_BUDGET_USD", "0.01")

    def boom():
        raise RuntimeError("meter down")

    monkeypatch.setattr(llm_router, "_estimated_month_spend", boom)
    assert llm_router.choose_backend() == "bedrock"


def test_aws_budget_source_falls_back_to_estimate(monkeypatch):
    """LLM_BUDGET_SOURCE=aws but Cost Explorer unavailable -> uses the estimate,
    doesn't crash."""
    monkeypatch.setenv("LLM_BACKEND", "bedrock")
    monkeypatch.setenv("LLM_BUDGET_USD", "0.02")
    monkeypatch.setenv("LLM_BUDGET_SOURCE", "aws")
    monkeypatch.setenv("AI_COST_PER_CALL_USD", "0.005")
    _fresh()
    monkeypatch.setattr(llm_router, "_real_month_spend", lambda: None)  # CE down
    for _ in range(5):
        analytics.emit(analytics.PERSONALIZE, email="a@x.com")
    assert llm_router.choose_backend() == "anthropic"  # estimate still trips

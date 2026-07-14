"""Which LLM backend serves a paid call -- and when to fall back to Claude.

Policy (config-driven, all optional):

  Primary is Bedrock/Llama (cost-first) when LLM_BACKEND=bedrock. Claude is the
  safety net. A call is routed to Claude BEFORE it runs when a budget guard
  trips, and falls back to Claude AFTER a Bedrock failure at call time.

Three fallback triggers, checked cheapest-first:

  1. FAILURE (always on, real-time): a Bedrock call that errors or returns
     unparseable output is retried on Claude by the caller. Handled in
     personalize()/chat() via try/except, not here -- this module only decides
     the *starting* backend.

  2. BUDGET, estimated (immediate): estimated month-to-date Bedrock spend =
     (this month's personalize + chat count) x AI_COST_PER_CALL_USD. If it
     exceeds LLM_BUDGET_USD, start on Claude. No AWS calls -- uses the event
     stream we already track, so it reacts the same minute a spike happens.

  3. BUDGET, real billed (accurate, ~24h lagged): if LLM_BUDGET_SOURCE=aws,
     read real month-to-date Bedrock spend from Cost Explorer instead of the
     estimate. More accurate but a day behind, so it can't catch a same-day
     spike -- pair it with the estimated guard, which does.

Design note: choosing the backend must NEVER raise into a member request. Any
error in the budget check fails OPEN to the configured primary backend (better
to serve the cheap model than to 500), and the failure-fallback still protects
correctness.
"""
import os
from typing import Optional


def _per_call_usd() -> float:
    """Per-call cost estimate, read at call time so config/tests take effect
    without a module reload. Mirrors the Cost tab's AI_COST_PER_CALL_USD default
    so the budget estimate here and the admin console agree."""
    try:
        return float(os.environ.get("AI_COST_PER_CALL_USD", "0.005"))
    except ValueError:
        return 0.005


def _configured_primary() -> str:
    """The backend to use when nothing trips a guard. Cost-first default here is
    still 'anthropic' unless the operator opts into bedrock -- flipping the
    product default is a deploy-config choice (LLM_BACKEND), not a code default."""
    return os.environ.get("LLM_BACKEND", "anthropic")


def _budget_usd() -> Optional[float]:
    raw = os.environ.get("LLM_BUDGET_USD", "").strip()
    if not raw:
        return None
    try:
        v = float(raw)
        return v if v > 0 else None
    except ValueError:
        return None


def _estimated_month_spend() -> float:
    """Month-to-date Bedrock spend estimate from tracked LLM-call events."""
    from app.data.events import get_events
    from app.data.store import month_key
    from app.services import analytics

    this_month = month_key()
    calls = 0
    for e in get_events().list_events(limit=20000):
        if e.get("type") in (analytics.PERSONALIZE, analytics.CHAT):
            # month_key() of the event's timestamp; events carry ms since epoch.
            if _event_month(e.get("ts", 0)) == this_month:
                calls += 1
    return calls * _per_call_usd()


def _event_month(ts_ms: int) -> str:
    import time
    t = time.gmtime(ts_ms / 1000)
    return f"{t.tm_year:04d}-{t.tm_mon:02d}"


def _real_month_spend() -> Optional[float]:
    """Real month-to-date spend from Cost Explorer, or None if unavailable.
    Best-effort: any failure returns None so the caller falls back to the
    estimate rather than failing the request."""
    try:
        from app.services import aws_cost
        # Cost tab already knows how to pull billed $; a 31-day window covers the
        # current month, and we only need an order-of-magnitude guard here.
        data = aws_cost._aws_costs(31)
        return float(data.get("totals", {}).get("total", 0.0))
    except Exception:
        return None


def _over_budget() -> bool:
    """True when month-to-date spend exceeds LLM_BUDGET_USD. Fails OPEN (returns
    False) on any error -- never blocks a request because a meter broke."""
    budget = _budget_usd()
    if budget is None:
        return False
    try:
        if os.environ.get("LLM_BUDGET_SOURCE", "estimate").lower() == "aws":
            spend = _real_month_spend()
            if spend is None:                      # CE unavailable -> estimate
                spend = _estimated_month_spend()
        else:
            spend = _estimated_month_spend()
        return spend >= budget
    except Exception:
        return False


def choose_backend() -> str:
    """Decide the STARTING backend for a paid call. If the primary is bedrock but
    a budget guard has tripped, start on anthropic (Claude) instead."""
    primary = _configured_primary()
    if primary == "bedrock" and _over_budget():
        return "anthropic"
    return primary

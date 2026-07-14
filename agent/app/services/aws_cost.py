"""AWS cost + usage for the operator console's Cost tab.

Two sources, chosen by whether real billing access is wired:

- **estimate** (default, always available): AI/LLM spend is derived from the
  tracked `personalize` + `chat` event counts times a per-call cost, and
  infra (Lambda / DynamoDB / API Gateway) is shown as *usage counts* pulled
  from the event stream. No AWS billing permissions needed, so the tab always
  renders -- including in local dev with the in-memory store.

- **aws** (opt-in, `AWS_COST_ENABLED=1`): queries AWS Cost Explorer for real
  billed dollars grouped by service, filtered to just this app's services
  (Lambda + DynamoDB + API Gateway), plus CloudWatch for Lambda invocations
  and DynamoDB consumed capacity. Requires the Lambda role to hold
  `ce:GetCostAndUsage` + `cloudwatch:GetMetricData` (see infra/template.yaml).
  Cost Explorer bills ~$0.01 per call and its data lags ~24h -- so this path
  is gated, not default.

Every response carries `source` ("estimate" | "aws") so the UI can badge which
one an operator is looking at, and never silently presents an estimate as a bill.
"""
import os
import time
from typing import Optional

from app.services import analytics
from app.data.events import get_events

# Per-paid-LLM-call cost estimate. Sonnet 5, ~750 cached input + ~400 output
# tokens per call -> ~$0.005 (see docs/prompts.md "Cost per call"). Kept here as
# a single knob; override with AI_COST_PER_CALL_USD when pricing changes.
AI_COST_PER_CALL_USD = float(os.environ.get("AI_COST_PER_CALL_USD", "0.005"))

# The services this app actually consumes -- the Cost tab is scoped to these so
# the numbers describe *the app*, not unrelated things in the AWS account.
APP_SERVICES = [
    "AWS Lambda",
    "Amazon DynamoDB",
    "Amazon API Gateway",
]


def _day_key(ts_ms: int) -> str:
    t = time.gmtime(ts_ms / 1000)
    return f"{t.tm_year:04d}-{t.tm_mon:02d}-{t.tm_mday:02d}"


def _empty_days(days: int) -> list:
    """Zero-filled day buckets, oldest -> newest, for the daily cost chart."""
    today = time.gmtime()
    base = time.mktime((today.tm_year, today.tm_mon, today.tm_mday, 0, 0, 0, 0, 0, 0))
    out = []
    for i in range(days - 1, -1, -1):
        t = time.gmtime(base - i * 86400)
        out.append(f"{t.tm_year:04d}-{t.tm_mon:02d}-{t.tm_mday:02d}")
    return out


def costs(days: int = 30) -> dict:
    """Return cost + usage for the last `days`. Prefers real AWS billing when
    AWS_COST_ENABLED is set and the call succeeds; otherwise estimates."""
    days = max(1, min(days, 90))
    if os.environ.get("AWS_COST_ENABLED", "").lower() in ("1", "true", "yes"):
        try:
            return _aws_costs(days)
        except Exception as e:
            # Real path failed (perms/region/CE off) -- fall back to the estimate
            # rather than 500 the whole tab, and surface why.
            est = _estimate_costs(days)
            est["degraded"] = f"AWS Cost Explorer unavailable: {e}"
            return est
    return _estimate_costs(days)


# ── Estimate path (no AWS billing access) ────────────────────────────────────
def _estimate_costs(days: int) -> dict:
    """Derive AI spend from tracked LLM-call events; infra as usage counts.

    We only have real dollars for the AI calls (call count x per-call cost).
    Lambda/DynamoDB/API Gateway are reported as *usage* (counts), with $0
    estimated cost and an explicit note -- an operator sees volume, and knows
    the billed figure needs the AWS path. Honest over fake-precise."""
    day_keys = _empty_days(days)
    day_set = set(day_keys)
    daily = {d: {"ai": 0.0} for d in day_keys}

    ai_calls = 0                 # personalize + chat = the paid LLM calls
    lambda_invocations = 0       # every event is at least one request hitting Lambda
    ddb_ops = 0                  # store reads/writes are hard to count here; proxy = events

    for e in get_events().list_events(limit=20000):
        day = _day_key(e.get("ts", 0))
        etype = e.get("type")
        lambda_invocations += 1
        ddb_ops += 1
        if etype in (analytics.PERSONALIZE, analytics.CHAT):
            ai_calls += 1
            if day in day_set:
                daily[day]["ai"] += AI_COST_PER_CALL_USD

    ai_cost = round(ai_calls * AI_COST_PER_CALL_USD, 4)
    total = ai_cost  # only AI has an estimated dollar figure in this path

    services = [
        {
            "service": "Anthropic (AI agent)",
            "usage": f"{ai_calls} calls",
            "usageUnit": "LLM calls",
            "cost": ai_cost,
            "billed": False,
        },
        {
            "service": "AWS Lambda",
            "usage": f"{lambda_invocations} invocations",
            "usageUnit": "invocations",
            "cost": 0.0,
            "billed": False,
        },
        {
            "service": "Amazon DynamoDB",
            "usage": f"~{ddb_ops} ops",
            "usageUnit": "read/write ops",
            "cost": 0.0,
            "billed": False,
        },
    ]

    timeseries = [{"date": d, "ai": round(daily[d]["ai"], 4)} for d in day_keys]
    # Simple linear projection: observed daily average x 30.
    daily_avg = total / days if days else 0.0
    projected_monthly = round(daily_avg * 30, 2)

    return {
        "source": "estimate",
        "days": days,
        "totals": {
            "total": round(total, 2),
            "aiCost": ai_cost,
            "aiCalls": ai_calls,
            "projectedMonthly": projected_monthly,
            "perCallUsd": AI_COST_PER_CALL_USD,
        },
        "services": services,
        "timeseries": timeseries,
        "note": (
            "AI cost is estimated from tracked LLM calls x per-call cost. "
            "Lambda/DynamoDB show usage volume only -- enable AWS_COST_ENABLED "
            "for billed dollars."
        ),
    }


# ── AWS path (Cost Explorer + CloudWatch) ────────────────────────────────────
def _aws_costs(days: int) -> dict:
    """Real billed $ by service (Cost Explorer) + Lambda/DDB usage (CloudWatch),
    filtered to this app's services. Raises on any failure so costs() can fall
    back to the estimate."""
    import boto3

    end = time.strftime("%Y-%m-%d", time.gmtime())
    start = time.strftime("%Y-%m-%d", time.gmtime(time.time() - days * 86400))

    ce = boto3.client("ce")
    resp = ce.get_cost_and_usage(
        TimePeriod={"Start": start, "End": end},
        Granularity="DAILY",
        Metrics=["UnblendedCost"],
        Filter={"Dimensions": {"Key": "SERVICE", "Values": APP_SERVICES}},
        GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}],
    )

    per_service = {}          # service -> total $
    daily = {}                # date -> {service -> $}
    for period in resp.get("ResultsByTime", []):
        date = period["TimePeriod"]["Start"]
        day_bucket = daily.setdefault(date, {})
        for g in period.get("Groups", []):
            svc = g["Keys"][0]
            amt = float(g["Metrics"]["UnblendedCost"]["Amount"])
            per_service[svc] = per_service.get(svc, 0.0) + amt
            day_bucket[svc] = day_bucket.get(svc, 0.0) + amt

    lambda_invocations = _lambda_invocations(days)

    services = []
    for svc in APP_SERVICES:
        usage = ""
        if svc == "AWS Lambda" and lambda_invocations is not None:
            usage = f"{lambda_invocations} invocations"
        services.append({
            "service": svc,
            "usage": usage,
            "cost": round(per_service.get(svc, 0.0), 4),
            "billed": True,
        })

    total = round(sum(per_service.values()), 2)
    timeseries = [
        {"date": d, **{s: round(daily[d].get(s, 0.0), 4) for s in APP_SERVICES}}
        for d in sorted(daily)
    ]
    daily_avg = total / days if days else 0.0

    return {
        "source": "aws",
        "days": days,
        "totals": {
            "total": total,
            "projectedMonthly": round(daily_avg * 30, 2),
            "lambdaInvocations": lambda_invocations,
        },
        "services": services,
        "timeseries": timeseries,
        "note": "Billed dollars from AWS Cost Explorer (data lags ~24h).",
    }


def _lambda_invocations(days: int) -> Optional[int]:
    """Total Lambda invocations over the window via CloudWatch. Returns None if
    the metric can't be read -- usage is a nicety, not worth failing the tab."""
    try:
        import boto3
        cw = boto3.client("cloudwatch")
        now = time.time()
        resp = cw.get_metric_data(
            MetricDataQueries=[{
                "Id": "inv",
                "MetricStat": {
                    "Metric": {"Namespace": "AWS/Lambda", "MetricName": "Invocations"},
                    "Period": 86400,
                    "Stat": "Sum",
                },
                "ReturnData": True,
            }],
            StartTime=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now - days * 86400)),
            EndTime=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now)),
        )
        vals = resp["MetricDataResults"][0].get("Values", [])
        return int(sum(vals))
    except Exception:
        return None

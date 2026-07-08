"""Analytics service: emit product events and compute operator metrics.

Events are plane-tagged ("b2c") so this stream can merge into the shared B2B
operator dashboard later. Emitting is best-effort -- a metrics failure must never
break a user request, so emit() swallows errors.
"""
from app.data.events import get_events

# Event types (stable names -- the dashboard groups on these).
SIGNUP = "signup"
LOGIN = "login"
UPGRADE = "upgrade"
ASSESSMENT_COMPLETED = "assessment_completed"
PERSONALIZE = "personalize"
CHAT = "chat"
CHAT_BLOCKED = "chat_blocked"          # free user hit the 3-query cap
UPGRADE_BLOCKED = "upgrade_blocked"    # free user hit a paid gate (402)


def emit(event_type, email=None, **props):
    """Record an event. Best-effort: never raises into the caller."""
    try:
        get_events().emit(event_type, email=email, props=props or {})
    except Exception:
        pass


def _day_key(ts_ms: int) -> str:
    import time as _t
    t = _t.gmtime(ts_ms / 1000)
    return f"{t.tm_year:04d}-{t.tm_mon:02d}-{t.tm_mday:02d}"


def metrics() -> dict:
    """Aggregate the event stream into operator-dashboard numbers."""
    events = get_events().list_events(limit=5000)
    by_type = {}
    signups, upgrades = set(), set()
    # Daily activity for the time-series chart (last 14 days).
    daily = {}  # day -> {signups, upgrades, chats, assessments}
    for e in events:
        by_type[e["type"]] = by_type.get(e["type"], 0) + 1
        day = _day_key(e.get("ts", 0))
        d = daily.setdefault(day, {"signups": 0, "upgrades": 0, "chats": 0, "assessments": 0})
        if e["type"] == SIGNUP:
            d["signups"] += 1
            if e.get("email"):
                signups.add(e["email"])
        elif e["type"] == UPGRADE:
            d["upgrades"] += 1
            if e.get("email"):
                upgrades.add(e["email"])
        elif e["type"] == CHAT:
            d["chats"] += 1
        elif e["type"] == ASSESSMENT_COMPLETED:
            d["assessments"] += 1

    total_signups = len(signups)
    total_paid = len(upgrades)
    conversion = round(100 * total_paid / total_signups, 1) if total_signups else 0.0

    return {
        "totals": {
            "signups": total_signups,
            "paidUpgrades": total_paid,
            "freeToPaidConversionPct": conversion,
            "assessmentsCompleted": by_type.get(ASSESSMENT_COMPLETED, 0),
            "personalizations": by_type.get(PERSONALIZE, 0),
            "chatMessages": by_type.get(CHAT, 0),
            "chatBlocked": by_type.get(CHAT_BLOCKED, 0),
            "upgradePrompts": by_type.get(UPGRADE_BLOCKED, 0),
        },
        "eventsByType": by_type,
        "funnel": [
            {"step": "Signed up", "count": total_signups},
            {"step": "Completed assessment", "count": by_type.get(ASSESSMENT_COMPLETED, 0)},
            {"step": "Hit a paywall", "count": by_type.get(UPGRADE_BLOCKED, 0)},
            {"step": "Upgraded to paid", "count": total_paid},
        ],
        # Last 14 calendar days, oldest->newest, zero-filled for the line chart.
        "timeseries": _timeseries(daily, days=14),
    }


def _timeseries(daily: dict, days: int = 14) -> list:
    import time as _t
    today = _t.gmtime()
    base = _t.mktime((today.tm_year, today.tm_mon, today.tm_mday, 0, 0, 0, 0, 0, 0))
    out = []
    for i in range(days - 1, -1, -1):
        t = _t.gmtime(base - i * 86400)
        key = f"{t.tm_year:04d}-{t.tm_mon:02d}-{t.tm_mday:02d}"
        d = daily.get(key, {})
        out.append({
            "date": key,
            "signups": d.get("signups", 0),
            "upgrades": d.get("upgrades", 0),
            "chats": d.get("chats", 0),
            "assessments": d.get("assessments", 0),
        })
    return out


def recent_events(limit=100) -> list:
    return get_events().list_events(limit=limit)

"""Operator notifications: signup alerts and the weekly digest.

What to say lives here; how to send lives in app/data/email.py. Recipients come
from OPERATOR_EMAILS -- empty means the whole feature is inert, which is the
safe default for a dev laptop.

Best-effort by contract: every public function returns a bool and NEVER raises.
notify_signup() sits directly in the /api/auth/start request path, so a mail
failure must not cost us a signup. Same reasoning as analytics.emit().

PRIVACY -- a hard line, not a preference. Members answer questions about death,
family, and money. Operator email carries IDENTITY ONLY: address, tier,
timestamps, counts. A member's answers, plan, or narrative must never appear in
an outbound email. Feedback notifications carry what the member chose to write
to us, which is different: they wrote it in order to be read.
"""
import logging
import time

from app.config import PRODUCT_NAME, operator_emails
from app.data.email import send

log = logging.getLogger(__name__)

# Config-store key holding the last digest week we sent (idempotency watermark).
DIGEST_WATERMARK_KEY = "digest_last_sent_week"


def notify_signup(email: str, tier: str = "free", total_signups=None) -> bool:
    """Alert operators that a NEW member signed up. Returns True if the transport
    accepted it, False if unconfigured or failed. Never raises."""
    try:
        recipients = operator_emails()
        if not recipients:
            return False  # unconfigured -- inert by design
        when = _local_stamp()
        lines = [
            f"A new member just signed up for {PRODUCT_NAME}.",
            "",
            f"  Email:  {email}",
            f"  Tier:   {tier}",
            f"  When:   {when}",
        ]
        if total_signups is not None:
            lines.append(f"  Total signups to date: {total_signups}")
        lines += ["", _footer()]
        return send(
            recipients,
            f"[{PRODUCT_NAME}] New signup: {email}",
            "\n".join(lines),
        )
    except Exception as exc:
        log.warning("signup notification failed for %s: %s", email, exc)
        return False


def total_signups() -> int:
    """All-time distinct signups, for context in the signup alert ("this is our
    Nth member"). Returns 0 rather than raising if the event stream is unreadable."""
    try:
        from app.data.events import get_events
        from app.services import analytics
        seen = set()
        for e in get_events().list_events(limit=5000):
            if e.get("type") == analytics.SIGNUP:
                em = e.get("email")
                if em and em != "-":
                    seen.add(em)
        return len(seen)
    except Exception:
        return 0


def notify_feedback(entry: dict) -> bool:
    """Alert operators that a member submitted help/complaint/survey feedback.

    A complaint is subject-tagged so it can be filtered and prioritized in an
    inbox -- on a product about end-of-life planning, a member telling us the
    tone landed wrong is the most important mail we get all week.
    """
    try:
        recipients = operator_emails()
        if not recipients:
            return False
        kind = (entry.get("kind") or "help").lower()
        who = entry.get("email") or "(no email given)"
        tag = {"complaint": "COMPLAINT", "help": "Help request", "survey": "Survey"}.get(
            kind, kind.title()
        )
        lines = [
            f"{tag} submitted via {PRODUCT_NAME}.",
            "",
            f"  From:   {who}",
            f"  Kind:   {kind}",
            f"  When:   {_local_stamp(entry.get('created_at'))}",
        ]
        if entry.get("rating"):
            lines.append(f"  Rating: {entry['rating']}/5")
        if entry.get("page"):
            lines.append(f"  Page:   {entry['page']}")
        if entry.get("signed_in") is not None:
            lines.append(f"  Signed in: {'yes' if entry['signed_in'] else 'no'}")
        lines += ["", "Message:", "-" * 40, entry.get("message", ""), "-" * 40,
                  "", f"Reply directly to {who}." if entry.get("email") else "",
                  _footer()]
        return send(
            recipients,
            f"[{PRODUCT_NAME}] {tag}: {_snippet(entry.get('message', ''))}",
            "\n".join(l for l in lines if l is not None),
        )
    except Exception as exc:
        log.warning("feedback notification failed: %s", exc)
        return False


def send_weekly_digest(force: bool = False) -> dict:
    """Build and send the weekly operator digest.

    Idempotent per week: the config store holds a watermark of the last week
    sent, so a retried schedule or a double-click on the admin button does not
    double-send. `force=True` overrides (manual re-send).

    Returns a status dict -- {"sent": bool, "reason": str, "week": str, ...} --
    so the admin endpoint can report what happened. Never raises.
    """
    from app.config import DIGEST_ENABLED
    try:
        if not DIGEST_ENABLED and not force:
            return {"sent": False, "reason": "digest_disabled"}

        window = _last_week_window()
        week_key = window["key"]

        from app.data.events import get_events
        events_store = get_events()
        if not force and events_store.get_config(DIGEST_WATERMARK_KEY) == week_key:
            return {"sent": False, "reason": "already_sent", "week": week_key}

        summary = weekly_summary(window)
        recipients = operator_emails()
        if not recipients:
            return {"sent": False, "reason": "no_recipients", "week": week_key,
                    "summary": summary}

        ok = send(recipients, _digest_subject(summary, window), _digest_body(summary, window))
        if ok:
            events_store.set_config(DIGEST_WATERMARK_KEY, week_key)
        return {"sent": ok, "week": week_key, "recipients": recipients,
                "summary": summary}
    except Exception as exc:
        log.warning("weekly digest failed: %s", exc)
        return {"sent": False, "reason": f"error: {exc}"}


def weekly_summary(window=None) -> dict:
    """Aggregate one week of the event stream into digest numbers.

    Sourced from the same plane-tagged event stream the admin dashboard reads,
    so the digest and the console can never disagree.
    """
    from app.services import analytics
    from app.data.events import get_events

    window = window or _last_week_window()
    start_ms, end_ms = window["start_ms"], window["end_ms"]

    events = get_events().list_events(limit=5000)
    in_week = [e for e in events if start_ms <= e.get("ts", 0) <= end_ms]

    def _emails(evt_type):
        seen = []
        for e in in_week:
            if e.get("type") == evt_type:
                em = e.get("email")
                if em and em != "-" and em not in seen:
                    seen.append(em)
        return seen

    def _count(evt_type):
        return sum(1 for e in in_week if e.get("type") == evt_type)

    signup_emails = _emails(analytics.SIGNUP)
    upgrade_emails = _emails(analytics.UPGRADE)

    # Tier per new signup, read live from the store (a free signup may have
    # upgraded since -- the digest should show where they are now).
    from app.data.store import get_store
    store = get_store()
    signups = []
    for em in signup_emails:
        u = store.get_user(em) or {}
        signups.append({"email": em, "tier": u.get("tier", "free")})

    # Total members to date (all-time distinct signups), for context.
    all_signups = set()
    for e in events:
        if e.get("type") == analytics.SIGNUP and e.get("email") and e["email"] != "-":
            all_signups.add(e["email"])

    feedback = _feedback_in_window(start_ms, end_ms)

    n_signups = len(signups)
    n_upgrades = len(upgrade_emails)
    return {
        "signups": signups,
        "signupCount": n_signups,
        "upgrades": upgrade_emails,
        "upgradeCount": n_upgrades,
        "assessmentsCompleted": _count(analytics.ASSESSMENT_COMPLETED),
        "personalizations": _count(analytics.PERSONALIZE),
        "chatMessages": _count(analytics.CHAT),
        "upgradePrompts": _count(analytics.UPGRADE_BLOCKED),
        "conversionPct": round(100 * n_upgrades / n_signups, 1) if n_signups else 0.0,
        "totalMembersToDate": len(all_signups),
        "feedback": feedback,
    }


def _feedback_in_window(start_ms: int, end_ms: int) -> dict:
    """Feedback submitted this week, grouped by kind. Complaint messages are
    included verbatim -- they're the highest-signal item in the digest."""
    try:
        from app.data.store import get_store
        entries = get_store().list_feedback(limit=500)
    except Exception:
        return {"total": 0, "byKind": {}, "complaints": []}

    start_s, end_s = start_ms / 1000, end_ms / 1000
    in_week = [f for f in entries if start_s <= (f.get("created_at") or 0) <= end_s]
    by_kind = {}
    for f in in_week:
        k = f.get("kind", "help")
        by_kind[k] = by_kind.get(k, 0) + 1
    complaints = [
        {"email": f.get("email"), "message": _snippet(f.get("message", ""), 140)}
        for f in in_week if f.get("kind") == "complaint"
    ]
    ratings = [f["rating"] for f in in_week if f.get("rating")]
    return {
        "total": len(in_week),
        "byKind": by_kind,
        "complaints": complaints,
        "avgRating": round(sum(ratings) / len(ratings), 1) if ratings else None,
    }


# ── Digest formatting ────────────────────────────────────────────────────────
def _digest_subject(s: dict, window: dict) -> str:
    n = s["signupCount"]
    # A quiet week is information, not a reason to stay silent -- make the zero
    # explicit in the subject so nobody has to open the mail to learn nothing
    # happened.
    if n == 0:
        head = "No new signups"
    else:
        head = f"{n} new signup{'s' if n != 1 else ''}"
    if s["feedback"].get("complaints"):
        head += f" · {len(s['feedback']['complaints'])} complaint(s)"
    return f"[{PRODUCT_NAME}] Weekly summary — {head} ({window['label']})"


def _digest_body(s: dict, window: dict) -> str:
    L = [
        f"{PRODUCT_NAME} — weekly summary",
        f"Week of {window['label']} ({window['tz']})",
        "=" * 52,
        "",
        "THIS WEEK",
        f"  New signups .............. {s['signupCount']}",
        f"  Completed the playbook ... {s['assessmentsCompleted']}",
        f"  Personalized plans ....... {s['personalizations']}",
        f"  Chat messages ............ {s['chatMessages']}",
        f"  Hit a paywall ............ {s['upgradePrompts']}",
        f"  Upgraded to paid ......... {s['upgradeCount']}",
        f"  Free -> paid conversion .. {s['conversionPct']}%",
        "",
        f"  Total members to date .... {s['totalMembersToDate']}",
        "",
    ]

    if s["signups"]:
        L += ["NEW MEMBERS", ""]
        L += [f"  {m['email']}  ({m['tier']})" for m in s["signups"]]
        L += [""]
    else:
        L += ["NEW MEMBERS", "  None this week.", ""]

    if s["upgrades"]:
        L += ["UPGRADED TO PAID", ""]
        L += [f"  {em}" for em in s["upgrades"]]
        L += [""]

    fb = s["feedback"]
    if fb.get("total"):
        L += ["MEMBER FEEDBACK", ""]
        # Pad to a fixed width so the dot leaders line up like the block above,
        # whatever length the kind names are.
        for kind, n in sorted(fb["byKind"].items()):
            L.append(f"  {(kind + ' ').ljust(26, '.')} {n}")
        if fb.get("avgRating"):
            L.append(f"  {'average rating '.ljust(26, '.')} {fb['avgRating']}/5")
        if fb.get("complaints"):
            L += ["", "  Complaints (read these first):"]
            for c in fb["complaints"]:
                L.append(f"    - {c['email'] or 'anonymous'}: {c['message']}")
        L += [""]

    L += ["=" * 52, _footer()]
    return "\n".join(L)


# ── Time helpers ─────────────────────────────────────────────────────────────
def _tz():
    """The digest timezone.

    Falls back to UTC if the platform has no IANA database -- but that fallback
    shifts the Mon-Sun window by up to 8 hours, so it WARNS rather than failing
    quietly. `tzdata` is in requirements.txt precisely so this never fires on
    Lambda (whose base image ships no tz database)."""
    from app.config import DIGEST_TIMEZONE
    try:
        from zoneinfo import ZoneInfo
        return ZoneInfo(DIGEST_TIMEZONE)
    except Exception as exc:
        log.warning(
            "timezone %r unavailable (%s) -- digest window falling back to UTC, "
            "which shifts the reported week. Is tzdata installed?",
            DIGEST_TIMEZONE, exc,
        )
        from datetime import timezone
        return timezone.utc


def _last_week_window() -> dict:
    """The most recently COMPLETED Mon 00:00 -> Sun 23:59:59 week, in the digest
    timezone. Run on Monday morning, this is the week that just ended."""
    from datetime import datetime, timedelta
    tz = _tz()
    now = datetime.now(tz)
    this_monday = (now - timedelta(days=now.weekday())).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    start = this_monday - timedelta(days=7)
    end = this_monday - timedelta(microseconds=1)
    return {
        "start_ms": int(start.timestamp() * 1000),
        "end_ms": int(end.timestamp() * 1000),
        "key": start.strftime("%Y-W%V"),
        "label": f"{start.strftime('%b %-d')} – {end.strftime('%b %-d, %Y')}"
                 if not _is_windows() else
                 f"{start.strftime('%b %d')} - {end.strftime('%b %d, %Y')}",
        "tz": getattr(tz, "key", "UTC"),
    }


def _is_windows() -> bool:
    import os
    return os.name == "nt"


def _local_stamp(epoch_seconds=None) -> str:
    """Human timestamp in the digest timezone."""
    from datetime import datetime
    ts = epoch_seconds if epoch_seconds is not None else time.time()
    try:
        dt = datetime.fromtimestamp(ts, _tz())
        return dt.strftime("%b %d, %Y at %I:%M %p %Z").replace(" 0", " ")
    except Exception:
        return time.strftime("%b %d, %Y at %H:%M UTC", time.gmtime(ts))


def _snippet(text: str, limit: int = 60) -> str:
    t = " ".join((text or "").split())
    return t if len(t) <= limit else t[: limit - 1] + "…"


def _footer() -> str:
    return f"— {PRODUCT_NAME} operator notifications"

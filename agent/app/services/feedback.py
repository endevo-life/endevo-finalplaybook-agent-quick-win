"""Member feedback: help requests, complaints, and survey responses.

One endpoint serves all three because they arrive through the same door -- a
member with something to say -- and splitting them would mean three forms nobody
finds. `kind` tells operators how to triage.

Works signed-in OR anonymous. Anonymous matters here: someone who cannot log in
is exactly the person who most needs to reach us, and on a product about
end-of-life planning a member who finds the tone wrong may not want to be
identified at all.

Order of operations is deliberate: PERSIST FIRST, then notify. Email is
best-effort and can fail; the store is the system of record. Losing a complaint
because SES was misconfigured would be the worst possible failure mode.
"""
import time

from app.data.store import get_store

KINDS = ("help", "complaint", "survey")

MAX_MESSAGE_CHARS = 4000
MIN_MESSAGE_CHARS = 2

# Rate limit: submissions per email per window. Generous enough that a genuinely
# upset member can send several follow-ups, tight enough to blunt a bot.
RATE_LIMIT_MAX = 5
RATE_LIMIT_WINDOW_SECONDS = 60 * 60


class FeedbackError(ValueError):
    """Validation failure -> 422."""


class RateLimited(Exception):
    """Too many submissions in the window -> 429."""


def submit(kind, message, email=None, rating=None, page=None, signed_in=False,
           client_ip=None) -> dict:
    """Validate, persist, and notify operators. Returns the stored entry.

    Raises FeedbackError (422) or RateLimited (429). The notification itself is
    best-effort and never affects the return value -- if the member's words are
    safely stored, the submission succeeded.

    `client_ip` rate-limits the ANONYMOUS path. An anonymous survey needs no
    email, so without it there'd be no key to limit on and this public,
    unauthenticated endpoint could be driven to write rows and send mail without
    bound.
    """
    kind = (kind or "").strip().lower()
    if kind not in KINDS:
        raise FeedbackError(f"kind must be one of {', '.join(KINDS)}")

    message = (message or "").strip()
    if len(message) < MIN_MESSAGE_CHARS:
        raise FeedbackError("Please include a message.")
    if len(message) > MAX_MESSAGE_CHARS:
        raise FeedbackError(
            f"Message is too long ({len(message)} characters, max {MAX_MESSAGE_CHARS})."
        )

    rating = _clean_rating(rating)
    email = _clean_email(email)

    # An anonymous submitter must leave some way to be answered -- a help
    # request we cannot reply to helps nobody. A survey response can stay
    # anonymous, since it needs no reply.
    if not email and kind in ("help", "complaint"):
        raise FeedbackError("Please include your email so we can reply.")

    page = (page or "").strip()[:200] or None

    if email:
        _enforce_rate_limit(email)
    elif client_ip:
        # No email to key on (anonymous survey) -- fall back to the caller's IP
        # so the open endpoint still has a ceiling.
        _enforce_ip_rate_limit(client_ip)

    entry = get_store().save_feedback(
        email=email, kind=kind, message=message,
        rating=rating, page=page, signed_in=signed_in,
    )

    # Best-effort side effects: neither can fail the submission.
    try:
        from app.services import analytics
        analytics.emit("feedback", email=email, kind=kind, rating=rating)
    except Exception:
        pass
    try:
        from app.services import notifications
        notifications.notify_feedback(entry)
    except Exception:
        pass

    return entry


# Anonymous (no-email) submissions are limited per IP, in-process only. The IP is
# NEVER persisted: it's a spam ceiling, not a record we need about the member, and
# on a product this sensitive we store the minimum. Losing the counter on restart
# or spreading it across Lambda instances is an acceptable trade for that.
_ip_hits: dict[str, list] = {}
IP_RATE_LIMIT_MAX = 10


def _enforce_ip_rate_limit(client_ip: str) -> None:
    now = time.time()
    cutoff = now - RATE_LIMIT_WINDOW_SECONDS
    hits = [t for t in _ip_hits.get(client_ip, []) if t > cutoff]
    if len(hits) >= IP_RATE_LIMIT_MAX:
        _ip_hits[client_ip] = hits
        raise RateLimited("Too many submissions from this connection. Please try again later.")
    hits.append(now)
    _ip_hits[client_ip] = hits
    # Bound the dict so a spray of distinct IPs can't grow it without limit.
    if len(_ip_hits) > 2000:
        for k in [k for k, v in _ip_hits.items() if not v or v[-1] < cutoff]:
            _ip_hits.pop(k, None)


def _enforce_rate_limit(email: str) -> None:
    since = int(time.time()) - RATE_LIMIT_WINDOW_SECONDS
    try:
        recent = get_store().count_feedback_since(email, since)
    except Exception:
        return  # a counting failure must not block a genuine submission
    if recent >= RATE_LIMIT_MAX:
        raise RateLimited(
            f"You've sent {RATE_LIMIT_MAX} messages in the last hour. "
            "We've got them — we'll be in touch shortly."
        )


def _clean_rating(rating):
    if rating is None or rating == "":
        return None
    try:
        r = int(rating)
    except (TypeError, ValueError):
        raise FeedbackError("rating must be a whole number from 1 to 5")
    if not 1 <= r <= 5:
        raise FeedbackError("rating must be between 1 and 5")
    return r


def _clean_email(email):
    email = (email or "").strip().lower()
    if not email:
        return None
    if "@" not in email or "." not in email.split("@")[-1]:
        raise FeedbackError("That email address doesn't look right.")
    return email


def recent(limit: int = 100, since: int = None) -> list:
    """Feedback for the admin console, newest first."""
    try:
        return get_store().list_feedback(limit=limit, since=since)
    except Exception:
        return []

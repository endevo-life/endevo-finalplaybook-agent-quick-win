"""Email transport -- how a message is sent, never what it says.

Content lives in app/services/notifications.py; this module only moves bytes.
Same backend-selection shape as data/store/base.py and data/events.py:

- "console" -- log it and record it in memory. Sends NOTHING. The default, so a
               dev laptop or a test run can never email a real person.
- "ses"     -- AWS SES v2. Already this account's mail path (Cognito sends the
               passwordless login codes through it), so no new vendor and no new
               secret: the Lambda's IAM role grants ses:SendEmail.

NOTE: this account has SES PRODUCTION access (verified 2026-07-27), so recipients
need no verification -- only the SENDER identity (EMAIL_FROM) must be verified.
hello@endevo.life is verified; finalplaybook.com is registered as a domain
identity but its DKIM was never completed, so a @finalplaybook.com sender fails
today. A bad sender raises, which callers swallow (see the best-effort contract
below), so it looks like silence rather than an error -- check last_sends() or
the admin console. See DEPLOY.md 3d.

Best-effort contract
--------------------
send() returns True/False and NEVER raises. Callers sit in request paths
(signup) and scheduled jobs; a mail failure must not cost us a signup. This
mirrors analytics.emit(), which swallows for the same reason.
"""
import logging
import os
from typing import Optional

log = logging.getLogger(__name__)

# Console backend keeps the last N sends so tests can assert on real payloads
# without a mock library, and so /api/admin can show what would have gone out.
_MAX_RECORDED = 50


class _ConsoleEmail:
    """Logs instead of sending. Records payloads for tests and the admin view."""

    backend = "console"

    def __init__(self):
        self.sent = []  # [{to, subject, body}]

    def send(self, to: list, subject: str, body: str) -> bool:
        self.sent.append({"to": list(to), "subject": subject, "body": body})
        del self.sent[:-_MAX_RECORDED]
        log.info("[email:console] to=%s subject=%s\n%s", ", ".join(to), subject, body)
        return True


class _SesEmail:
    """AWS SES v2. Raises on failure -- send() below converts that to False."""

    backend = "ses"

    def __init__(self, region: str, sender: str):
        self.region = region
        self.sender = sender
        self.sent = []
        self._c = None

    def _client(self):
        if self._c is None:
            import boto3  # lazy: only needed when EMAIL_BACKEND=ses
            self._c = boto3.client("sesv2", region_name=self.region)
        return self._c

    def send(self, to: list, subject: str, body: str) -> bool:
        self._client().send_email(
            FromEmailAddress=self.sender,
            Destination={"ToAddresses": list(to)},
            Content={
                "Simple": {
                    "Subject": {"Data": subject, "Charset": "UTF-8"},
                    "Body": {"Text": {"Data": body, "Charset": "UTF-8"}},
                }
            },
        )
        self.sent.append({"to": list(to), "subject": subject, "body": body})
        del self.sent[:-_MAX_RECORDED]
        return True


_email = None


def get_email():
    """Singleton transport selected by EMAIL_BACKEND ("console" | "ses")."""
    global _email
    if _email is not None:
        return _email
    from app import config
    # Read the env directly (falling back to the imported default) so a test or
    # a live config change is picked up after reset_email(), not frozen at the
    # moment app.config was first imported.
    backend = os.environ.get("EMAIL_BACKEND", config.EMAIL_BACKEND).strip().lower()
    sender = os.environ.get("EMAIL_FROM", config.EMAIL_FROM).strip()
    region = os.environ.get("SES_REGION", config.SES_REGION)
    if backend == "ses":
        _email = _SesEmail(region, sender)
    elif backend == "console":
        _email = _ConsoleEmail()
    else:
        raise ValueError(
            f"Unknown EMAIL_BACKEND: {backend!r} (expected 'console' or 'ses')"
        )
    return _email


def reset_email():
    """Drop the singleton so the next get_email() re-reads config. Tests + config
    changes, same as reset_store()."""
    global _email
    _email = None


def send(to, subject: str, body: str) -> bool:
    """Send to one or more addresses. Returns True if the transport accepted it.

    Never raises -- see the best-effort contract in the module docstring. An
    empty recipient list is a no-op returning False (the feature is inert until
    OPERATOR_EMAILS is configured, which is the safe default).
    """
    recipients = [to] if isinstance(to, str) else [a for a in (to or []) if a]
    if not recipients:
        return False
    try:
        return get_email().send(recipients, subject, body)
    except Exception as exc:
        log.warning("email send failed (to=%s subject=%s): %s",
                    ", ".join(recipients), subject, exc)
        return False


def last_sends(limit: int = 20) -> list:
    """Most recent sends this process recorded, newest last. Powers tests and the
    admin console's delivery-status view."""
    try:
        return list(get_email().sent[-limit:])
    except Exception:
        return []


def backend_name() -> str:
    try:
        return get_email().backend
    except Exception:
        return "unknown"

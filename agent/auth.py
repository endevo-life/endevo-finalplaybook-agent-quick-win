"""Lightweight email-based auth.

Deliberately minimal -- no passwords. The flow is:
1. POST /api/auth/start {email}  -> creates/updates the user, mints a one-time
   login code, and (in production) emails a magic link. In dev, the code is
   returned in the response so you can log in without an email provider.
2. POST /api/auth/verify {email, code} -> exchanges the code for a session
   token (opaque, stored server-side with a TTL).
3. Every protected request sends `Authorization: Bearer <token>`; require_user()
   resolves it to an email or raises 401.

Why not JWT: sessions are server-side so we can revoke instantly and so the
paid-tier entitlement is always read fresh from the store (a user who cancels
loses access on their next request, not whenever a JWT happens to expire).

Tokens use secrets.token_urlsafe -- cryptographically strong, URL-safe.
"""
import secrets
import time
from typing import Optional

from store import get_store

SESSION_TTL_SECONDS = 60 * 60 * 24 * 30   # 30 days
LOGIN_CODE_TTL_SECONDS = 60 * 15          # 15 minutes

# One-time login codes kept in-process (short-lived; fine to lose on restart).
# email -> (code, expires_at)
_login_codes: dict[str, tuple[str, int]] = {}


def start_login(email: str) -> str:
    """Create/refresh the user and return a one-time login code. In production
    the caller emails this as a magic link; in dev it's shown to the user."""
    email = _normalize_email(email)
    store = get_store()
    if not store.get_user(email):
        store.upsert_user(email, tier="free")
    code = f"{secrets.randbelow(1_000_000):06d}"
    _login_codes[email] = (code, int(time.time()) + LOGIN_CODE_TTL_SECONDS)
    return code


def verify_login(email: str, code: str) -> str:
    """Exchange a valid login code for a session token. Raises ValueError on a
    bad/expired code."""
    email = _normalize_email(email)
    entry = _login_codes.get(email)
    if not entry or entry[0] != code or entry[1] < int(time.time()):
        raise ValueError("invalid or expired login code")
    _login_codes.pop(email, None)
    token = secrets.token_urlsafe(32)
    get_store().create_session(token, email, SESSION_TTL_SECONDS)
    return token


def logout(token: str) -> None:
    get_store().delete_session(token)


def email_from_token(token: Optional[str]) -> Optional[str]:
    if not token:
        return None
    return get_store().get_session_email(token)


def _normalize_email(email: str) -> str:
    email = (email or "").strip().lower()
    if "@" not in email or "." not in email.split("@")[-1]:
        raise ValueError("invalid email address")
    return email

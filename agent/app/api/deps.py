"""Shared FastAPI dependencies -- primarily auth (resolve a bearer token to an
email). Routes depend on `current_email` (optional/anonymous OK) or
`require_email` (401 if not signed in)."""
from typing import Optional

from fastapi import Header, HTTPException

from app.services import auth


def current_email(authorization: Optional[str] = Header(None)) -> Optional[str]:
    """Resolve a bearer token to an email, or None for anonymous requests."""
    if not authorization or not authorization.lower().startswith("bearer "):
        return None
    return auth.email_from_token(authorization.split(" ", 1)[1].strip())


def require_email(authorization: Optional[str] = Header(None)) -> str:
    email = current_email(authorization)
    if not email:
        raise HTTPException(401, "Login required")
    return email

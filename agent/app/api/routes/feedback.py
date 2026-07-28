"""Member feedback: help requests, complaints, survey responses.

Deliberately open to anonymous callers -- someone who can't sign in is exactly
the person who most needs to reach us. A signed-in caller's email comes from
their session and OVERRIDES whatever the body claims, so a submission can never
be attributed to someone else.
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request

from app.api.deps import current_email
from app.schemas.requests import FeedbackRequest
from app.services import feedback as feedback_service

router = APIRouter(prefix="/api", tags=["feedback"])


@router.get("/feedback/options")
def feedback_options():
    """Form metadata so the UI's choices and limits stay in sync with the server."""
    return {
        "kinds": [
            {"value": "help", "label": "I need help", "needsEmail": True},
            {"value": "complaint", "label": "Something's wrong", "needsEmail": True},
            {"value": "survey", "label": "Share feedback", "needsEmail": False},
        ],
        "maxMessageChars": feedback_service.MAX_MESSAGE_CHARS,
        "ratingKinds": ["survey"],
    }


@router.post("/feedback")
def submit_feedback(
    req: FeedbackRequest,
    request: Request,
    session_email: Optional[str] = Depends(current_email),
):
    # A live session is the source of truth for identity; the body's email is
    # only trusted for anonymous submissions.
    email = session_email or req.email
    try:
        entry = feedback_service.submit(
            kind=req.kind,
            message=req.message,
            email=email,
            rating=req.rating,
            page=req.page,
            signed_in=bool(session_email),
            client_ip=_client_ip(request),
        )
    except feedback_service.RateLimited as e:
        raise HTTPException(429, str(e))
    except feedback_service.FeedbackError as e:
        raise HTTPException(422, str(e))

    return {
        "ok": True,
        "id": entry.get("id"),
        "kind": entry.get("kind"),
        "message": _ack(entry.get("kind")),
    }


def _client_ip(request: Request) -> Optional[str]:
    """Caller's IP, used ONLY as an in-process rate-limit key (never stored).

    Behind API Gateway/CloudFront, request.client.host is the proxy, so the real
    caller is the FIRST entry of X-Forwarded-For -- later entries are appended by
    intermediaries and a client can forge extra ones.
    """
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip() or None
    return request.client.host if request.client else None


def _ack(kind: str) -> str:
    """What we say back. Warm and concrete, no false promises about timing --
    the same voice rule the rest of the product follows."""
    if kind == "complaint":
        return "Thank you for telling us. We've passed this straight to the team and someone will follow up."
    if kind == "help":
        return "Got it — we've received your question and someone will get back to you."
    return "Thank you — your feedback helps us make this better."

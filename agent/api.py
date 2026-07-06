"""API exposing the agent + the SaaS layer (auth, entitlements, billing) to the
React UI. The same handlers run locally (uvicorn) and in production (AWS Lambda
via Mangum -- see lambda_handler.py). Transport differs; logic is identical.

Design notes:
- The free tier still works with NO account -- POST /api/plan with tier="free"
  (or omitted) runs the pure rules engine for anonymous visitors, so the
  "try it before signing up" flow is preserved.
- Paid features (personalized plan, chat) require a logged-in user AND a live
  paid entitlement checked server-side. The client can no longer just send
  tier="paid" to get LLM output -- that's enforced in entitlements.py.
"""
import os

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

import auth
import billing
from chat_agent import ChatMessage, chat as run_chat
from entitlements import EntitlementError, entitlement_for
from orchestrator import run
from plans import PLANS, normalize_tier
from rules_engine import (
    CONTENT_LIBRARY,
    MemberContext,
    assessment_questions,
    build_domain_plan,
)

app = FastAPI(title="Final Playbook API")

# Allowed origins come from ALLOWED_ORIGINS (comma-separated) so prod can lock to
# the real domain; defaults to the Vite dev server for local work. In dev the
# Vite server hops ports (5173, 5174, ...) when several are running, so we also
# allow any localhost/127.0.0.1 port via a regex unless ALLOWED_ORIGINS is set
# explicitly (i.e. production locks it down).
_origins = os.environ.get("ALLOWED_ORIGINS", "http://localhost:5173").split(",")
_dev_default = "ALLOWED_ORIGINS" not in os.environ
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _origins if o.strip()],
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+" if _dev_default else None,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

VALID_FLAGS = set(MemberContext.__dataclass_fields__.keys())


# --- request models -----------------------------------------------------------
class PlanRequest(BaseModel):
    flags: dict[str, bool]
    memberFirstName: str
    tier: str = "free"  # client hint only; paid is verified server-side


class ChatRequest(BaseModel):
    plan: dict
    memberFirstName: str
    history: list[ChatMessage]


class AssessmentRequest(BaseModel):
    answers: dict[str, str]  # {questionId: optionValue}


class AuthStartRequest(BaseModel):
    email: str


class AuthVerifyRequest(BaseModel):
    email: str
    code: str


# --- auth dependency ----------------------------------------------------------
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


# --- public content -----------------------------------------------------------
@app.get("/api/health")
def health():
    return {"ok": True}


@app.get("/api/pricing")
def pricing():
    """Machine-readable pricing so the landing page renders from one source."""
    return {
        "plans": [
            {
                "tier": p.tier,
                "name": p.name,
                "priceUsdMonth": p.price_usd_month,
                "canPersonalize": p.can_personalize,
                "canChat": p.can_chat,
                "monthlyPersonalizeQuota": p.monthly_personalize_quota,
                "monthlyChatQuota": p.monthly_chat_quota,
            }
            for p in PLANS.values()
        ]
    }


@app.get("/api/assessment")
def get_assessment():
    """The condensed domain-assessment questions (basics-first + one high-impact
    question per domain). Deterministic and free -- no account, no LLM."""
    return assessment_questions()


@app.post("/api/assessment/plan")
def create_assessment_plan(req: AssessmentRequest):
    """Resolve a member's answers into their action plan (basics-first + one
    action per answered question, each with steps behind a UI expander). Free
    and anonymous -- pure rules, no LLM."""
    return build_domain_plan(req.answers)


@app.get("/api/glossary")
def get_glossary():
    """Grounded term definitions for UI tooltips -- sourced from the content
    library's definitionsGlossary, not invented in the frontend. See
    content-library.json _meta.status: draft, pending expert sign-off."""
    return CONTENT_LIBRARY.get("definitionsGlossary", [])


# --- auth ---------------------------------------------------------------------
@app.post("/api/auth/start")
def auth_start(req: AuthStartRequest):
    try:
        code = auth.start_login(req.email)
    except ValueError as e:
        raise HTTPException(400, str(e))
    # In production the code is emailed as a magic link and NOT returned. In dev
    # (no email provider) we return it so you can log in. Controlled by env.
    if os.environ.get("AUTH_RETURN_CODE", "true").lower() == "true":
        return {"sent": True, "devLoginCode": code}
    return {"sent": True}


@app.post("/api/auth/verify")
def auth_verify(req: AuthVerifyRequest):
    try:
        token = auth.verify_login(req.email, req.code)
    except ValueError as e:
        raise HTTPException(401, str(e))
    ent = entitlement_for(req.email)
    return {"token": token, "user": ent.snapshot()}


@app.get("/api/me")
def me(email: str = Depends(require_email)):
    return entitlement_for(email).snapshot()


@app.post("/api/auth/logout")
def auth_logout(authorization: Optional[str] = Header(None)):
    if authorization and authorization.lower().startswith("bearer "):
        auth.logout(authorization.split(" ", 1)[1].strip())
    return {"ok": True}


# --- core agent ---------------------------------------------------------------
@app.post("/api/plan")
def create_plan(req: PlanRequest, email: Optional[str] = Depends(current_email)):
    unknown = set(req.flags) - VALID_FLAGS
    if unknown:
        raise HTTPException(400, f"Unknown flags: {sorted(unknown)}")

    try:
        requested = normalize_tier(req.tier)
    except ValueError:
        raise HTTPException(400, "tier must be 'free' or 'paid'")

    # Decide whether the paid LLM path runs -- from the server-side entitlement,
    # never from the request's tier string.
    do_personalize = False
    ent = None
    if requested == "paid":
        if not email:
            raise HTTPException(401, "Log in to unlock personalized plans")
        ent = entitlement_for(email)
        try:
            ent.require_personalize()
        except EntitlementError as e:
            raise HTTPException(e.code, str(e))
        do_personalize = True

    try:
        result = run(req.flags, req.memberFirstName, personalize=do_personalize)
    except Exception as e:
        raise HTTPException(502, f"Agent error: {e}")

    if do_personalize and ent is not None:
        ent.record_personalize()  # meter only successful LLM calls
    return result


@app.post("/api/chat")
def create_chat_reply(req: ChatRequest, email: str = Depends(require_email)):
    if not req.history or req.history[-1].role != "user":
        raise HTTPException(400, "history must be non-empty and end with a user message")
    if len(req.history) > 40:
        raise HTTPException(400, "conversation too long -- please start a new one")

    ent = entitlement_for(email)
    try:
        ent.require_chat()
    except EntitlementError as e:
        raise HTTPException(e.code, str(e))

    try:
        reply = run_chat(req.plan, req.memberFirstName, req.history).model_dump()
    except Exception as e:
        raise HTTPException(502, f"Chat error: {e}")

    ent.record_chat()
    return reply


# --- billing ------------------------------------------------------------------
@app.post("/api/billing/checkout")
def billing_checkout(email: str = Depends(require_email)):
    if not billing.is_configured():
        raise HTTPException(503, "Billing is not configured on this server yet.")
    try:
        url = billing.create_checkout_session(email)
    except Exception as e:
        raise HTTPException(502, f"Checkout error: {e}")
    return {"url": url}


@app.post("/api/billing/dev-upgrade")
def billing_dev_upgrade(email: str = Depends(require_email)):
    """Unlock the paid tier WITHOUT Stripe -- for demos and early testing before
    billing is live. Guarded by ALLOW_DEV_UPGRADE so it can never be hit in
    production (Stripe's webhook is the only way to grant paid there). Lets you
    actually use and show the premium experience today."""
    if os.environ.get("ALLOW_DEV_UPGRADE", "false").lower() != "true":
        raise HTTPException(403, "Dev upgrade is disabled. Use Stripe checkout.")
    from store import get_store
    get_store().set_tier(email, "paid")
    return entitlement_for(email).snapshot()


@app.post("/api/billing/webhook")
async def billing_webhook(request: Request, stripe_signature: Optional[str] = Header(None)):
    payload = await request.body()
    try:
        return billing.handle_webhook(payload, stripe_signature)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(502, f"Webhook error: {e}")

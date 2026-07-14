"""Plan routes: the situation-profile plan (free rules / paid personalized) and
per-user saved plan + progress + chat history."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from app.agent.orchestrator import run
from app.agent.rules_engine import MemberContext
from app.api.deps import current_email, require_email
from app.data.store import get_store
from app.schemas.requests import PlanRequest, SavePlanRequest
from app.services.entitlements import EntitlementError, entitlement_for
from app.services.plans import normalize_tier

router = APIRouter(prefix="/api", tags=["plan"])

VALID_FLAGS = set(MemberContext.__dataclass_fields__.keys())


@router.post("/plan")
def create_plan(req: PlanRequest, email: Optional[str] = Depends(current_email)):
    unknown = set(req.flags) - VALID_FLAGS
    if unknown:
        raise HTTPException(400, f"Unknown flags: {sorted(unknown)}")

    try:
        requested = normalize_tier(req.tier)
    except ValueError:
        raise HTTPException(400, "tier must be 'free' or 'paid'")

    # Whether the paid LLM path runs comes from the server-side entitlement,
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


@router.get("/my/plan")
def get_my_plan(email: str = Depends(require_email)):
    """The user's saved assessment plan, progress, and chat history so they resume
    exactly where they left off (across devices)."""
    store = get_store()
    saved = store.get_plan(email) or {}
    return {
        "answers": saved.get("answers", {}),
        "plan": saved.get("plan"),
        "tracked": saved.get("tracked", {}),
        "narrative": saved.get("narrative"),
        "fields": saved.get("fields", {}),
        "chatHistory": store.get_chat_history(email),
    }


@router.post("/my/plan")
def save_my_plan(req: SavePlanRequest, email: str = Depends(require_email)):
    """Save the user's assessment answers, plan, and tracked progress."""
    try:
        get_store().save_plan(
            email,
            answers=req.answers,
            plan=req.plan,
            tracked=req.tracked,
            narrative=req.narrative,
            fields=req.fields,
        )
    except Exception as e:
        # Surface storage failures instead of silently losing the user's data.
        raise HTTPException(502, f"Could not save plan: {e}")
    return {"saved": True}

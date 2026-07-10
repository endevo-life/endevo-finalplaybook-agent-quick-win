"""Assessment routes: the condensed deterministic domain assessment (free) and
the paid personalized narrative built from a member's answers."""
from fastapi import APIRouter, Depends, HTTPException

from app.agent.personalize import personalize as run_personalize
from app.agent.rules_engine import assessment_questions, build_domain_plan
from app.api.deps import require_email
from app.schemas.requests import AssessmentPersonalizeRequest, AssessmentRequest
from app.services import analytics
from app.services.entitlements import EntitlementError, entitlement_for

router = APIRouter(prefix="/api/assessment", tags=["assessment"])


@router.get("")
def get_assessment():
    """The condensed domain-assessment questions (basics-first + one high-impact
    question per domain). Deterministic and free -- no account, no LLM."""
    return assessment_questions()


@router.post("/plan")
def create_assessment_plan(req: AssessmentRequest):
    """Resolve a member's answers into their action plan (basics-first + one
    action per answered question). Free and anonymous -- pure rules, no LLM."""
    plan = build_domain_plan(req.answers)
    analytics.emit(analytics.ASSESSMENT_COMPLETED, answered=len(req.answers or {}))
    return plan


@router.post("/personalize")
def personalize_assessment(
    req: AssessmentPersonalizeRequest, email: str = Depends(require_email)
):
    """Paid-tier: turn a member's assessment plan into a warm, personalized
    'next 7 days' narrative (the one LLM call). Gated + metered server-side."""
    ent = entitlement_for(email)
    try:
        ent.require_personalize()
    except EntitlementError as e:
        analytics.emit(analytics.UPGRADE_BLOCKED, email=email, feature="personalize", code=e.code)
        raise HTTPException(e.code, str(e))

    domain_plan = build_domain_plan(req.answers)
    # Adapt the assessment shape into the plan shape personalize() grounds on.
    # Only the member's own resolved actions/steps are sent -- never the full lib.
    action_items = [
        {"text": it["action"], "domain": it.get("domain"), "steps": it.get("steps", [])}
        for it in domain_plan["basicsFirst"] + domain_plan["domainItems"]
    ]
    if not action_items:
        return {"tier": "paid", "personalized": None}

    adapted = {
        "leadProfile": {"id": "assessment", "name": "Your Final Playbook"},
        "actionItems": action_items,
        "businessActionItems": [],
        "digitalActionItems": [],
        "quotes": [],
    }
    try:
        result = run_personalize(adapted, req.memberFirstName, signals=req.signals)
    except Exception as e:
        raise HTTPException(502, f"Agent error: {e}")

    ent.record_personalize()
    analytics.emit(analytics.PERSONALIZE, email=email)
    return {"tier": "paid", "personalized": result.model_dump()}

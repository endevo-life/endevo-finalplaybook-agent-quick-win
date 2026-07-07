"""Public, unauthenticated endpoints: health, pricing, glossary."""
from fastapi import APIRouter

from app.agent.rules_engine import CONTENT_LIBRARY
from app.services.plans import PLANS

router = APIRouter(prefix="/api", tags=["meta"])


@router.get("/health")
def health():
    return {"ok": True}


@router.get("/pricing")
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


@router.get("/glossary")
def get_glossary():
    """Grounded term definitions for UI tooltips -- sourced from the content
    library's definitionsGlossary, not invented in the frontend."""
    return CONTENT_LIBRARY.get("definitionsGlossary", [])

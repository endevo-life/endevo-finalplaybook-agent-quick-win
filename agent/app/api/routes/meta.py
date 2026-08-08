"""Public, unauthenticated endpoints: health, pricing, glossary."""
from fastapi import APIRouter

from app.agent.rules_engine import CONTENT_LIBRARY
from app.services import billing as billing_service
from app.services.plans import BILLING_INTERVALS, PLANS

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
        ],
        # How the paid tier can be bought. `available` lists the intervals with a
        # Stripe Price actually configured on this deploy -- the UI hides a toggle
        # it can't honor, rather than offering annual and 502-ing on click.
        "billingIntervals": [
            {
                "key": i.key,
                "label": i.label,
                "priceUsd": i.price_usd,
                "period": i.period,
                # What the annual plan works out to per month, for the UI's
                # "$16.58/mo billed annually" line. None for monthly itself.
                "effectiveMonthlyUsd": (
                    round(i.price_usd / 12, 2) if i.period == "year" else None
                ),
            }
            for i in BILLING_INTERVALS.values()
        ],
        "availableIntervals": billing_service.available_intervals(),
    }


@router.get("/glossary")
def get_glossary():
    """Grounded term definitions for UI tooltips -- sourced from the content
    library's definitionsGlossary, not invented in the frontend."""
    return CONTENT_LIBRARY.get("definitionsGlossary", [])

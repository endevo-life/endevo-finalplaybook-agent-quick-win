"""Plan definitions and usage limits -- the single source of truth for the
freemium/paid split. Enforced server-side (see entitlements.py); the client can
no longer just assert tier="paid" and get LLM output.

Two tiers ship today:
- "free"  : deterministic rules plan, unlimited. NO LLM personalization, NO chat.
- "paid"  : everything in free, plus the LLM "next 7 days" narrative and grounded
            follow-up chat, metered by a monthly quota.

Limits are intentionally generous but finite so a single paid account can't run
up an unbounded Anthropic bill. Numbers live here so pricing changes are a
one-file edit. See docs/pricing.md for the market-facing version.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class PlanDef:
    tier: str
    name: str
    price_usd_month: float
    can_personalize: bool          # unlock the paid LLM "next 7 days" narrative
    can_chat: bool                 # unlock grounded follow-up chat
    monthly_personalize_quota: int # LLM plan generations / month (0 = disabled)
    monthly_chat_quota: int        # chat replies / month (0 = disabled)


# The two live plans. `price_usd_month` is display-only here; the real charge is
# whatever the Stripe Price is configured for (see billing.py / DEPLOY.md).
PLANS = {
    "free": PlanDef(
        tier="free",
        name="Free",
        price_usd_month=0.0,
        can_personalize=False,
        # Free users get a small TASTE of the AI guide -- a few grounded questions
        # so they feel the value -- then it prompts upgrade. Metered server-side.
        can_chat=True,
        monthly_personalize_quota=0,
        monthly_chat_quota=3,
    ),
    "paid": PlanDef(
        tier="paid",
        name="Personalized",
        # $25/mo -- set by the business (2026-07-06). Reflects that this is
        # premium, expert-authored clinical guidance, not a generic to-do app.
        # LLM cost per user stays a few cents/month (see docs/pricing.md), so the
        # margin is very healthy.
        price_usd_month=25.0,
        can_personalize=True,
        can_chat=True,
        monthly_personalize_quota=30,   # ~30 full plan regenerations / month
        monthly_chat_quota=200,         # ~200 grounded chat replies / month
    ),
}

DEFAULT_TIER = "free"

# Backwards/forwards compatibility: the original code used "trial" for the free
# tier. Accept it as an alias so older clients and existing tests keep working.
TIER_ALIASES = {"trial": "free"}


def normalize_tier(tier: str) -> str:
    tier = (tier or DEFAULT_TIER).strip().lower()
    tier = TIER_ALIASES.get(tier, tier)
    if tier not in PLANS:
        raise ValueError(f"unknown tier: {tier!r}")
    return tier


def get_plan(tier: str) -> PlanDef:
    return PLANS[normalize_tier(tier)]

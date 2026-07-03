"""Deterministic routing engine: context flags -> matched situation profile(s) ->
prioritized, capped action items. No LLM calls happen anywhere in this file --
this is the free, zero-token layer that runs for every user on every tier.

See personalize.py for the one optional LLM call (paid tier only) that turns
this output into a personalized narrative.
"""
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

CONTENT_LIBRARY_PATH = Path(__file__).parent.parent / "knowledge-base" / "niki-content-library.json"

with open(CONTENT_LIBRARY_PATH, encoding="utf-8") as f:
    CONTENT_LIBRARY = json.load(f)

PROFILES_BY_ID = {p["id"]: p for p in CONTENT_LIBRARY["situationProfiles"]}

MAX_ACTION_ITEMS_PER_PLAN = 5  # Niki's rule: more than 5 kills momentum


@dataclass
class MemberContext:
    """Context flags used for routing. Mirrors the C1-C6 flags in the content
    library. Extend as the underlying question bank grows -- additive only."""
    hasPartner: bool = False
    hasYoungChildren: bool = False
    hasAdultChildren: bool = False
    hasAgingParent: bool = False
    parentLivesAlone: bool = False
    parentHasNoDocs: bool = False
    isSoloAger: bool = False
    isCaregiver: bool = False
    isBusinessOwner: bool = False
    postDivorce: bool = False
    newChild: bool = False
    recentMarriage: bool = False
    deathOfNamedPerson: bool = False
    hasNothingDone: bool = False
    hasSomeDone: bool = False
    hasWill: bool = False
    hasAssets: bool = False
    noTOD: bool = False
    noWill: bool = False
    # Digital assessment (D1-D3) -- each true flag pulls in its matching
    # action item from profile_digital_gap (always parallel, like business
    # owner). Flagged as an unvalidated draft addition -- see
    # niki-content-library.json.
    noLegacyContact: bool = False
    noSocialMediaPlan: bool = False
    noPasswordManager: bool = False
    # Physical (health and care) assessment (H1-H3) -- same pattern as the
    # digital flags above, pulling from profile_health_gap.
    noHealthcareProxy: bool = False
    noAdvanceDirective: bool = False
    healthcareProxyUnaware: bool = False


def _match_lead_profile(ctx: MemberContext) -> Optional[str]:
    """First matching rule wins the 'lead' slot -- mirrors Niki's stated
    priority overrides (aging parent > beneficiary audit > guardian naming >
    solo-ager TOD setup > pressure-test / clean-slate baseline)."""
    if ctx.hasAgingParent and ctx.parentHasNoDocs:
        return "profile_aging_parent"
    if ctx.postDivorce or ctx.newChild or ctx.recentMarriage or ctx.deathOfNamedPerson:
        return "profile_post_divorce_life_change"
    if ctx.hasYoungChildren and ctx.noWill:
        return "profile_young_children"
    if ctx.isSoloAger and ctx.hasAssets:
        return "profile_solo_ager"
    if ctx.hasSomeDone or ctx.hasWill:
        return "profile_pressure_test"
    if ctx.hasNothingDone:
        return "profile_clean_slate"
    return None


DIGITAL_GAP_FLAGS = ("noLegacyContact", "noSocialMediaPlan", "noPasswordManager")
HEALTH_GAP_FLAGS = ("noHealthcareProxy", "noAdvanceDirective", "healthcareProxyUnaware")

# Parallel profiles whose actionItems are individually gated by a per-item
# `flag` field (only the flags that are actually true get included), unlike
# profile_business_owner where the whole profile's items are taken as-is.
GAP_PROFILES = {
    "profile_digital_gap": ("digitalActionItems", DIGITAL_GAP_FLAGS),
    "profile_health_gap": ("healthActionItems", HEALTH_GAP_FLAGS),
}


def match_profiles(ctx: MemberContext) -> dict:
    """Business owner and gap profiles (digital, health) always run in
    parallel -- Niki treats these as separate checklists, never competing for
    priority with the lead profile."""
    lead = _match_lead_profile(ctx)
    parallel = []
    if ctx.isBusinessOwner and lead != "profile_business_owner":
        parallel.append("profile_business_owner")
    for profile_id, (_, flags) in GAP_PROFILES.items():
        if any(getattr(ctx, flag) for flag in flags):
            parallel.append(profile_id)
    return {"lead": lead, "parallel": parallel}


def build_plan(ctx: MemberContext) -> dict:
    """The full deterministic (zero-LLM) output: matched profile(s) plus
    capped, priority-ordered action items with their scripts/quotes attached."""
    matched = match_profiles(ctx)
    plan = {
        "leadProfile": None,
        "actionItems": [],
        "businessActionItems": [],
        "digitalActionItems": [],
        "healthActionItems": [],
        "quotes": [],
    }

    if matched["lead"]:
        profile = PROFILES_BY_ID[matched["lead"]]
        plan["leadProfile"] = {
            "id": profile["id"],
            "name": profile["name"],
            "urgency": profile.get("urgency"),
        }
        plan["actionItems"] = profile["actionItems"][:MAX_ACTION_ITEMS_PER_PLAN]
        if "quote" in profile:
            plan["quotes"].append(profile["quote"])
        if "quotes" in profile:
            plan["quotes"].extend(profile["quotes"])

    for pid in matched["parallel"]:
        profile = PROFILES_BY_ID[pid]
        if pid in GAP_PROFILES:
            # Each actionItem is gated on its own flag -- only include the
            # ones actually relevant to this member, not the whole profile.
            output_key, _ = GAP_PROFILES[pid]
            items = [item for item in profile["actionItems"] if getattr(ctx, item.get("flag", ""), False)]
            plan[output_key] = items[:MAX_ACTION_ITEMS_PER_PLAN]
        else:
            plan["businessActionItems"] = profile["actionItems"][:MAX_ACTION_ITEMS_PER_PLAN]

    return plan

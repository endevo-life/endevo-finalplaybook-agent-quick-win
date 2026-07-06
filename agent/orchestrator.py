"""Top-level agent entrypoint. The free tier never touches the LLM -- it returns
the rules-engine plan directly. The paid tier adds the one personalization call.

Whether the paid path runs is decided by the *caller* via `personalize=True/False`
(the API layer sets this from the user's server-side entitlement, never from a
client-supplied tier string). build_plan() itself is always free to run.
"""
from rules_engine import MemberContext, build_plan
from personalize import personalize as _personalize


def run(flags: dict, member_first_name: str, personalize: bool = False) -> dict:
    ctx = MemberContext(**flags)
    plan = build_plan(ctx)

    if not personalize:
        return {"tier": "free", "plan": plan}

    if not plan["leadProfile"] and not plan["businessActionItems"]:
        # Nothing matched -- don't send an empty plan to the LLM and risk it
        # improvising. No grounded content in, no LLM call out.
        return {"tier": "paid", "plan": plan, "personalized": None}

    personalized = _personalize(plan, member_first_name)
    return {"tier": "paid", "plan": plan, "personalized": personalized.model_dump()}

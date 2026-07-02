"""Top-level agent entrypoint. Trial tier never touches the LLM -- it returns
the rules-engine plan directly. Paid tier adds the one personalization call."""
from rules_engine import MemberContext, build_plan
from personalize import personalize


def run(flags: dict, member_first_name: str, tier: str = "trial") -> dict:
    ctx = MemberContext(**flags)
    plan = build_plan(ctx)

    if tier == "trial":
        return {"tier": "trial", "plan": plan}

    if not plan["leadProfile"] and not plan["businessActionItems"]:
        # Nothing matched -- don't send an empty plan to the LLM and risk it
        # improvising. No grounded content in, no LLM call out.
        return {"tier": tier, "plan": plan, "personalized": None}

    personalized = personalize(plan, member_first_name)
    return {"tier": tier, "plan": plan, "personalized": personalized.model_dump()}

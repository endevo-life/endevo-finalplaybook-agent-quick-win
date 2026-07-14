"""Why-now signal framing — the bridge from "what moved you to act" to how the
guide (narrative + Jesse chat) SPEAKS to this person.

The member picks these in the "Why now?" step (see the MOAT doc §1b). Until now
they only reordered the UI and were discarded. Here we give each signal a short
framing clause the LLM leads with, so a grieving person is met gently and a
business owner is met with continuity — the same facts, a different doorway in.

This is provisional, Claude-authored framing in the guide's warm, educational
voice (never advice). Niki reviews/replaces it — it lives in ONE place so she
can. Keep it additive: unknown/empty signals fall back to the neutral default.
"""

# flag -> a short second-person clause describing how to LEAD for this person.
# Written to be dropped straight into the system prompt.
SIGNAL_FRAMING = {
    "recentLossInCircle":
        "This person recently lost someone close. Lead with gentleness and "
        "acknowledgement; they already know why this matters. Skip the 'why plan' "
        "case entirely and move to what they can put in place so their own people "
        "aren't left searching.",
    "becameResponsible":
        "Someone now depends on this person (a child or a parent). Lead with the "
        "people they're responsible for — guardianship, care, and who steps in — "
        "before anything about their own affairs.",
    "settledAnEstate":
        "This person has settled an estate and seen firsthand what was missing. "
        "Lead with the executor's-eye view: the doc box, clear instructions, and "
        "access, framed as sparing their own people what they just went through.",
    "recentNearMiss":
        "A health scare or near miss brought this person here. Lead with the "
        "medical side — who can decide for them, advance directives — with calm "
        "urgency, not alarm.",
    "majorLifeChange":
        "A major life change (marriage, divorce, move, retirement, citizenship) "
        "prompted this. Lead with re-checking what's now out of date: "
        "beneficiaries, titles, and named roles that may still point to the old "
        "chapter.",
    "thresholdAge":
        "A milestone birthday nudged this person. Lead with a calm, complete "
        "sweep of the basics — no single crisis, just 'let's get the foundation "
        "in place while it's quiet.'",
    "digitalOutweighs":
        "Most of this person's life is online. Lead with digital access — "
        "accounts, photos, logins, legacy contacts — as the through-line, since "
        "that's where their life actually lives.",
    "worthProtecting":
        "This person has built something worth protecting (a home, a business, "
        "IP). Lead with continuity and clean transfer — who takes over, how it "
        "passes — before the personal basics.",
    "publicCaseShook":
        "A public story shook this person. Lead by naming the specific fear it "
        "surfaced and closing that exact gap first, so the worry becomes an "
        "action.",
    "tiredOfUnfinished":
        "This person is simply tired of an unfinished thing hanging over them. "
        "Lead by honoring that and getting one meaningful item fully done today, "
        "so momentum replaces the nagging.",
}

# Member-facing short labels (for logging / display / the plan record).
SIGNAL_LABELS = {
    "recentLossInCircle": "a loss in their circle",
    "becameResponsible": "became responsible for someone",
    "settledAnEstate": "settled an estate",
    "recentNearMiss": "a near miss",
    "majorLifeChange": "a major life change",
    "thresholdAge": "a milestone age",
    "digitalOutweighs": "digital life outweighs the paper one",
    "worthProtecting": "something worth protecting",
    "publicCaseShook": "a public case shook them",
    "tiredOfUnfinished": "tired of the unfinished thing",
}


def framing_for(signals) -> str:
    """Build the 'why now' framing block to inject into the guide's system
    prompt. Empty/unknown signals -> "" (the prompt stays neutral)."""
    if not signals:
        return ""
    clauses = [SIGNAL_FRAMING[s] for s in signals if s in SIGNAL_FRAMING]
    if not clauses:
        return ""
    labels = [SIGNAL_LABELS.get(s, s) for s in signals if s in SIGNAL_FRAMING]
    header = (
        "WHY THIS PERSON IS HERE (lead with this — it's what moved them to act): "
        + "; ".join(labels) + ".\n"
    )
    return header + "\n".join(f"- {c}" for c in clauses)

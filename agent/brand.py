"""Single source of truth for product/voice branding on the backend.

Everything that used to hard-code a specific expert's name or personal "clone"
framing now reads from here. To ship the app under a different brand, change
these values (or the matching env vars) -- no prompt or route code needs to be
touched.

The LLM is deliberately given a *neutral, unnamed* guide persona by default:
the app delivers pre-written, human-authored guidance and only ever rephrases
it. It is not impersonating any real person. If a client wants an expert's name
surfaced, set EXPERT_NAME -- but the guardrails (only rephrase provided content,
never invent advice) are identical either way.
"""
import os

# --- Product identity ---------------------------------------------------------
PRODUCT_NAME = os.environ.get("PRODUCT_NAME", "Final Playbook")

# --- Expert persona (optional) ------------------------------------------------
# Leave EXPERT_NAME empty for a neutral, unnamed guide (the market-default,
# expert-agnostic product). Set it only if a specific expert is being surfaced
# with permission. TONE_LINES are calibration-only reference lines the model may
# echo the *spirit* of -- never invented advice, just voice.
EXPERT_NAME = os.environ.get("EXPERT_NAME", "").strip()

# Neutral reference tone lines. These are voice/attitude calibration only, not
# advice, and are safe to ship without any single person's sign-off.
TONE_LINES = [
    "Plan while it's calm, not in a crisis.",
    "Small, concrete steps beat one overwhelming to-do list.",
    "This takes time and life gets busy -- there's no judgment here.",
]


def voice_descriptor() -> str:
    """How the LLM should describe whose guidance it's delivering."""
    if EXPERT_NAME:
        return f"{EXPERT_NAME}'s end-of-life planning guidance"
    return "professionally authored end-of-life planning guidance"


def tone_descriptor() -> str:
    """How the LLM should describe the *tone* to hold."""
    if EXPERT_NAME:
        return f"{EXPERT_NAME}'s direct, warm, no-judgment tone"
    return "a direct, warm, no-judgment tone"


def tone_lines_block() -> str:
    return "\n".join(f'- "{line}"' for line in TONE_LINES)

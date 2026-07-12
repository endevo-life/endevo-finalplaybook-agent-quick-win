"""Jesse's knowledge base: the educational material Jesse is ALLOWED to draw on,
beyond the member's own plan.

Before this, Jesse could only reference the member's matched plan, so it couldn't
answer general education questions ("what's the difference between a will and a
trust?"). This assembles a bounded, grounded knowledge block from:

  1. ENDevo facts (who we are, the 4-domain framework, My Final Playbook).
  2. The definitions glossary (validated + draft terms across all 4 domains).

It is STILL grounding, not open-ended: Jesse may explain these terms and facts
plainly, but must not invent laws, numbers, or advice beyond them, and must
route anything requiring a professional's judgment to a licensed pro. The
guardrail lives in the chat system prompt.

Source of truth for terms: knowledge-base/content-library.json
definitionsGlossary (Niki validates; drafts are marked validated:false).
"""
from app.agent.rules_engine import CONTENT_LIBRARY

# Who ENDevo / My Final Playbook is (from endevo.life + the ENDevo brand ref).
# Kept short and factual so Jesse can answer "what is this?" accurately.
ENDEVO_FACTS = """\
About ENDevo and My Final Playbook (facts you may state):
- ENDevo helps people plan, protect, and find peace: end-of-life and legacy
  readiness in the digital age. Slogan: "Plan. Protect. Peace." Tagline:
  "Live Fully ~ Die Ready."
- My Final Playbook is the deliverable: a complete, organized, shareable plan a
  person builds across four key areas, centered on their own beliefs/values.
- The four areas (with what each covers):
  * Legal: protect your rights and make sure your documents reflect your
    intentions (will, power of attorney, executor).
  * Financial: secure your assets and give your family clarity (accounts,
    insurance, beneficiaries).
  * Physical: address care, health, and personal needs with confidence
    (healthcare directive, final wishes).
  * Digital: organize and safeguard your online life (account access, legacy
    contacts, subscriptions).
- Beliefs sit at the center: your values, wishes, and priorities guide the rest.
- We are educators. We are NOT legal, financial, or medical advisors."""


def _glossary_block() -> str:
    """Render the glossary terms Jesse may explain, as plain 'Term: definition'
    lines. Includes draft (validated:false) terms -- they're educational, not
    advice -- so Jesse can answer common questions like will vs trust."""
    terms = CONTENT_LIBRARY.get("definitionsGlossary", [])
    lines = []
    for t in terms:
        term = t.get("term")
        d = t.get("shortDefinition") or t.get("definition")
        if term and d:
            lines.append(f"- {term}: {d}")
    if not lines:
        return ""
    return "Plain-language definitions you may explain (educational, not advice):\n" + "\n".join(lines)


def knowledge_block() -> str:
    """The full knowledge block injected into Jesse's system prompt."""
    parts = [ENDEVO_FACTS, _glossary_block()]
    return "\n\n".join(p for p in parts if p)

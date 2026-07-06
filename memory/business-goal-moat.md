---
name: business-goal-moat
description: User's stated business goal for Final Playbook — build a defensible moat and make money — and the strategy implications
metadata:
  type: project
---

User's goal (2026-07-06): "take MOAT Final Playbook, make money with this app."

**Where the real moat is (NOT the tech):**
- The tech (rules engine + one grounded LLM call) is replicable in weeks. Not a moat.
- The MOAT is **Niki's proprietary clinical routing logic + scripts**, mined from
  real client sessions (in docs/decode_finalplaybook_niki's_ip/ — gitignored PII).
  The deterministic tiered question->answer->action content, refined over 6-8
  session engagements, is the defensible asset. Competitors can copy the app
  shape; they can't copy Niki's validated content library.
- Second moat layer: proprietary content + expert sign-off = "safe to trust on a
  sensitive topic." The guardrails (never hallucinate legal/med/financial advice)
  are a trust moat if the content is validated.

**Monetization paths (both wired or scaffolded):**
1. B2C freemium: free rules/assessment (funnel, $0 to serve) -> $9/mo paid
   (LLM narrative + chat). Stripe Checkout ready. Quotas cap cost (plans.py).
2. B2B/enterprise: SAME agent, branded per-tenant via brand.py (prompt is already
   tenant-neutral). Enterprise value = SSO, seat billing, admin dashboard,
   anonymized aggregate progress. This is the higher-revenue path (employers,
   FEI/financial institutions, advisors offering it as a benefit). The prompt
   barely changes; the moneymaker is the multi-tenancy + reporting layer.

**Highest-leverage next moves toward the goal (advised):**
- Validate + expand the content library with Niki (the moat asset). Only 3 digital
  + a few situational items are wired; the full 5-domain tiered model
  (financial/physical/digital captured in content-sources/) is the product.
- Ship B2C first (Stripe live) to prove willingness-to-pay + gather usage.
- Then package B2B multi-tenant for the real revenue.

**How to apply:** when prioritizing work, weight content validation and the
B2B multi-tenant packaging over more app features — those are what defend margin
and unlock enterprise contracts. See [[deterministic-domain-model]] and
[[finalplaybook-debranded-saas]].

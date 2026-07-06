---
name: finalplaybook-debranded-saas
description: Final Playbook was de-branded from Niki's clone into a neutral SaaS product with server-side tiers, auth, billing, and AWS infra
metadata:
  type: project
---

On 2026-07-05 the Final Playbook agent repo was taken from "Niki Weiss clone"
prototype to a market-ready, expert-agnostic SaaS.

**Why:** user wanted to remove Niki's personal/clone branding everywhere, add a
freemium/paid product with real (not client-trusted) tier enforcement, auth,
Stripe billing, and AWS deploy — while keeping the $0 rules-engine free tier.

**How to apply:**
- All brand/voice text is config-driven now: `agent/brand.py` (backend prompts)
  and `frontend/src/config/branding.js` (UI). Never hard-code a product/person
  name back into prompts or components. `EXPERT_NAME` env stays blank = neutral.
- Content library was renamed `niki-content-library.json` → `content-library.json`.
  Only remaining "niki" refs are the source-provenance filename
  `niki_routing_rules_v1.html` in `_meta.source` / guardrails.md — kept as honest
  citation, not branding.
- Tier is enforced SERVER-SIDE in `agent/entitlements.py` (402 = upgrade, 429 =
  quota). `orchestrator.run()` now takes `personalize=bool`, NOT `tier=str`.
  Pricing/limits source of truth = `agent/plans.py`; UI reads `/api/pricing`.
- Persistence = `agent/store.py`, STORE_BACKEND `memory` (dev) or `dynamodb`
  (prod, single-table). Auth = `agent/auth.py` (email + opaque token, dev returns
  login code when AUTH_RETURN_CODE=true). Billing = `agent/billing.py` (Stripe
  Checkout + webhook is source of truth for tier flips).
- AWS deploy: `infra/template.yaml` (SAM: Lambda via `lambda_handler.py`/Mangum +
  HTTP API + DynamoDB). Runbook in `DEPLOY.md`. NOT yet deployed live — user runs
  it with own AWS/Stripe creds.

Local Python is `C:\Users\nimmi\AppData\Local\Programs\Python\Python312\python.exe`
(the `python`/`py` on PATH are Windows Store stubs — don't use them). 28 backend
tests pass; frontend builds clean.

# Final Playbook — Product Requirements & Specification

**Status:** Draft for review · **Audience:** Founders, legal counsel, advisors, engineering
**Last updated:** 2026-07-14 · **Owner:** ENDevo

> **Reviewer note (legal counsel):** Sections marked 🔵 **LEGAL** are written for
> counsel review. They describe the not-legal-advice positioning, the data we
> collect and store, the content-ownership model, and the billing terms — as the
> system is *actually built today*, not as aspiration. Where a control is
> partially implemented or deferred, it says so explicitly. Nothing here is a
> substitute for counsel's own review of the running product and its published
> Terms / Privacy Policy.

---

## 1. What Final Playbook is

Final Playbook is an **educational** end-of-life planning web app. A member
answers a short situational assessment; a **deterministic rules engine** (no AI)
matches their answers to proven, human-authored routing logic and returns a
prioritized action plan with word-for-word conversation scripts and plain-English
definitions. A **paid tier** adds one grounded AI call that rephrases that
already-matched plan into a warm "next 7 days" narrative, plus a grounded
follow-up chat assistant.

**The free tier never touches an AI model.** It is a pure rules engine and costs
$0 to run.

### 1.1 The core promise, and its boundary 🔵 LEGAL

- **We educate; we do not advise.** The product's stated position, shown to
  users in-product, is: *"Educate & Empower. We help you understand and take
  action. We are not legal, financial, or medical advisors."*
  (Source: `frontend/src/components/Disclaimer.jsx`.)
- The AI is **never** permitted to invent advice, documents, laws, or dollar
  figures. It may only rephrase pre-written, human-authored content. This is
  enforced structurally, not just by wording — see §6 (Guardrails).

---

## 2. Who it's for

- **Primary:** individuals (B2C) organizing their own end-of-life affairs —
  legal, financial, physical, and digital.
- **Secondary:** an operator/admin (ENDevo staff) who monitors usage, cost, and
  conversion, and can grant/revoke access for support.

---

## 3. Product tiers & terms 🔵 LEGAL (Terms / Billing)

Source of truth for all numbers: `agent/app/services/plans.py`, served to the UI
via `/api/pricing` so marketing, docs, and code cannot drift.

| | **Free** | **Personalized (Paid)** |
|---|---|---|
| **Price** | $0, forever | **$25 / month** |
| Situation assessment | ✅ | ✅ |
| Prioritized action plan (rules engine) | ✅ | ✅ |
| Conversation scripts + definitions | ✅ | ✅ |
| Download plan (PDF) | ✅ | ✅ |
| See gaps + first 2 steps | ✅ | ✅ |
| **Full plan (all actions/domains)** | Preview only (locked) | ✅ |
| **Track items / saved progress** | — | ✅ |
| **Side-by-side playbook builder** | — | ✅ |
| **AI assistant (grounded chat)** | — | ✅ |
| **AI "next 7 days" narrative** | — | ✅ |
| Account required | **No (anonymous)** | **Yes** |
| Monthly AI plan regenerations | n/a | 30 |
| Monthly AI chat replies | n/a | 200 |

**Billing terms as built:**

- Paid tier is a **$25/month subscription**, charged via **Stripe**. The real
  charge amount lives in the Stripe Price object; the app never stores card data.
- Entitlement is granted **only** by a successful Stripe payment (via Stripe's
  webhook) writing `tier == "paid"` to our store. See §7.3.
- **Quotas cap worst-case cost per account** (30 AI plan generations + 200 chat
  replies/month). Over-quota requests are refused (HTTP 429), so a single
  subscriber cannot run up an unbounded AI bill.
- **Pre-launch flag:** `ALLOW_DEV_UPGRADE` lets a logged-in user unlock paid
  **without payment** for demos. This **must be `false` in production** and is
  called out in the deploy runbook. (Legal: relevant to any "free trial" or
  promotional-access representations.)

---

## 4. User experience & flows

### 4.1 Free flow (anonymous)
1. Land → take the situational assessment (a handful of situational questions).
2. Rules engine returns the plan; user sees **basics-first steps + their single
   highest-impact action fully**, with the rest previewed but **locked**.
3. User can **download** the plan as a branded PDF.

### 4.2 Paid flow (account required)
1. Sign in (passwordless email code) → upgrade via Stripe.
2. Full plan unlocked; **track** items with saved progress; **build** each action
   side-by-side (steps, scripts, fields).
3. **AI narrative:** one grounded call rephrases the matched plan into a "next 7
   days" guide.
4. **AI chat:** grounded follow-up questions, capped by monthly quota.
5. **Progress celebrations** (in development): completing an action, sealing a
   domain, or completing the whole playbook produces earned on-screen moments
   that also print on the downloaded PDF. Celebration copy is *educational
   reassurance only* — **no dollar figures, risk percentages, or legal claims**
   (guardrail-bound; see `tasks/spec-celebrations.md`).

---

## 5. System architecture

```
Member (browser, React/Vite)                    Operator (admin.html console)
        │                                                │
        ▼                                                ▼
┌─────────────────────────── FastAPI backend ───────────────────────────┐
│  Routes (thin)  →  Services (business)  →  Agent (AI)  →  Data store    │
│  meta/auth/         auth, billing,          rules_engine   memory /     │
│  assessment/        entitlements,           (FREE, no AI)  sqlite /     │
│  plan/chat/         plans, analytics,       orchestrator   dynamodb     │
│  billing/admin      aws_cost                personalize    (7 tables)   │
│                                             chat (PAID AI)              │
└────────────────────────────────────────────────────────────────────────┘
        │                                                │
        ▼                                                ▼
  Anthropic API (paid tier only,                  AWS Cost Explorer +
   1 grounded call per action)                    CloudWatch (opt-in)
```

- **Hosting:** AWS serverless — Lambda + API Gateway + DynamoDB (SAM template in
  `infra/template.yaml`). Frontend is static (any host / Vercel).
- **Layering rule:** routes validate and delegate; business logic in services;
  AI in the agent layer; all persistence behind the store interface. No route
  touches a database directly.

---

## 6. AI guardrails 🔵 LEGAL (Liability / disclaimers)

The architecture makes hallucination and scope-creep **structurally hard**, not
just discouraged by prompt wording. Full detail: `docs/guardrails.md`.

1. **Free/trial tier has no AI at all.** There is no code path from free-tier
   input to a model call. Content that never passes through a model cannot be
   hallucinated by one. (Tested; asserts no AI key required.)
2. **The AI only ever sees already-matched, human-authored content** — the 2–5
   action items the rules engine selected, never the full content library. It
   has no ungrounded material to draw on. Enforced by the function signature,
   not just the prompt.
3. **System-prompt hard rules:** "Only use the action items, scripts, and quotes
   provided… Do not invent new advice, documents, laws, or numbers." · "If the
   material doesn't cover something, say it's outside what we can cover and
   suggest a licensed professional — do not guess." · "Never present this as
   legal, financial, or medical advice."
4. **Structured output.** The AI response is schema-validated into a fixed shape
   (`headline`, `steps[]`, `closing_note`) — it cannot add new sections the UI
   would render uncritically.
5. **Content is marked unvalidated where it is.** The knowledge base is real
   clinical logic but a **DRAFT** pending expert sign-off; `_meta.status` says so
   in plain text and must be preserved until validation completes.

**Known open risks (disclosed, not hidden):**
- **No automated post-hoc check** that the AI's output stayed grounded to its
  input. The input is small and drift is unlikely, but there is no verification
  step yet. Worth adding before scaling paid volume.
- **Opt-in open-weight backend** (`LLM_BACKEND=bedrock`) has weaker JSON-schema
  enforcement than the default Anthropic path; it is **not** the default and
  requires an explicit env change.

> **For counsel:** these guardrails support the educational-not-advisory
> position but do not, by themselves, constitute legal compliance. The published
> Terms of Service and Privacy Policy, the in-product disclaimer, and any
> state-specific unauthorized-practice-of-law considerations are counsel's call.

---

## 7. Data, privacy & security 🔵 LEGAL (Data privacy / PII)

### 7.1 What personal data we collect and store

Persisted per user (ground truth: `agent/app/data/store/`):

| Data | When | Sensitivity |
|---|---|---|
| **Email address** | On sign-in (paid only) | PII — identifier |
| Account created timestamp | On sign-in | Low |
| **Assessment answers** | On completing the assessment | Situational (family/health/asset *situation* flags, not records) |
| **Saved plan + tracked progress** | Paid, as the user works | Reflects the user's affairs |
| **AI narrative text** | Paid, on generation | Derived from the above |
| **Chat history** | Paid, per message | User's own questions |
| Stripe customer ID | On payment | Links to Stripe (no card data here) |
| Monthly usage counters | Per AI call | Low |

**What we do NOT store:** payment card numbers (held by **Stripe**), SSNs,
uploaded legal documents, or medical records. The assessment captures *situation
flags* (e.g., "has minor children", "owns a business") — not source documents.

- **Free tier is anonymous** — no account, no stored PII. Data collection begins
  only when a user signs in for the paid tier.

### 7.2 Where it lives & who can see it
- **Storage:** DynamoDB in the ENDevo AWS account (prod). Dev uses in-memory or
  local SQLite.
- **Operator access:** the admin console (§8) can view a user's tier, usage, and
  plan progress, and can grant/revoke paid or reset a quota. Access is gated by a
  shared **admin token** and an **allowlist of admin emails** — the token alone
  is insufficient once the allowlist is set. (Legal: this is internal-staff
  access to member data and should be reflected in the Privacy Policy.)

### 7.3 Billing & payment security
- All card handling is delegated to **Stripe**; the app stores only a Stripe
  customer ID. Paid status is granted **only** by Stripe's verified webhook, and
  tier is **enforced server-side** — a client cannot self-grant paid access.

### 7.4 Retention & deletion — ⚠️ gap to close before launch
- There is **no automated data-retention or user-initiated deletion flow yet.**
  Deletion is currently a manual operator action. **For counsel:** a documented
  retention period and a deletion mechanism are likely needed for the Privacy
  Policy and for any applicable privacy regime (e.g., CCPA/GDPR-style rights).

---

## 8. Admin / operator console (backend admin side)

A standalone, token-gated operator console (`frontend/public/admin.html`) reads
the admin API (`/api/admin/*`). It is separate from the member app and intended
for ENDevo staff.

### 8.1 Access control
- **Bearer admin token** (`ADMIN_TOKEN`) on every request, **plus** — when
  `ADMIN_EMAILS` is set — an allowlisted admin email. Token alone is not enough.
- Console is disabled (503) if no admin token is configured.

### 8.2 Tabs & capabilities

**Overview tab**
- Business metrics: signups, paid upgrades, free→paid conversion %, assessments
  completed, AI messages, paywall hits.
- 14-day activity chart, free-vs-paid split, conversion funnel.
- User table with per-user drill-down: tier, AI usage, plan progress; **grant /
  revoke paid**, **reset monthly quota** (support actions).

**Cost tab** (new)
- **Total spend, AI spend, AI calls, projected monthly** stat tiles.
- **Daily cost chart** (by service) and a **breakdown table**
  (service · usage · cost · % · billed-vs-estimate), with a 7/30/90-day toggle.
- **Two data sources, always labeled:**
  - **Estimate (default):** AI cost = tracked AI-call count × per-call cost
    (~$0.005); Lambda/DynamoDB shown as usage volume. Needs no AWS billing
    access — works in local dev.
  - **AWS billed $ (opt-in, `AWS_COST_ENABLED=1`):** real dollars from **AWS
    Cost Explorer**, filtered to this app's services (Lambda + DynamoDB + API
    Gateway), plus Lambda invocations from CloudWatch. Requires added IAM
    permissions; **Cost Explorer bills ~$0.01/call and lags ~24h**, so it is
    gated behind a flag, not on by default. If the live call fails it degrades
    to the estimate with a visible warning — the tab never breaks.
- A source badge means an operator always knows whether a number is **billed** or
  **estimated** — an estimate is never presented as a bill.

### 8.3 Admin API surface
```
POST /api/admin/login                      validate token (+ email if allowlisted)
GET  /api/admin/metrics                    business metrics, funnel, timeseries
GET  /api/admin/costs?days=                cost & usage (Cost tab)
GET  /api/admin/events?limit=              recent raw product events
GET  /api/admin/users                      known users + tier/usage
GET  /api/admin/users/{email}              one user: tier, usage, plan progress
POST /api/admin/users/{email}/tier         grant/revoke paid
POST /api/admin/users/{email}/reset-usage  reset monthly quotas
GET/POST /api/admin/config                 feature flags / config
```

---

## 9. Intellectual property & content ownership 🔵 LEGAL (IP)

- **The clinical content is proprietary, human-authored draft IP.** The routing
  logic, action items, conversation scripts, and definitions in
  `knowledge-base/content-library.json` are mined from real client sessions
  (Niki-authored). It is marked **DRAFT — pending expert sign-off** and must not
  be presented to end users as clinically final until that validation completes.
- **The AI does not create content — it only rephrases approved content.** By
  design (§6.2), the model is fed only already-matched, human-authored items and
  is barred from inventing new advice. This keeps generated output derivative of
  owned source material rather than novel model output.
- **Expert-agnostic by default.** The product ships with **no named person** —
  all brand/voice text is config-driven (`config.py`, `branding.js`). A specific
  expert persona is surfaced **only** by explicitly setting `EXPERT_NAME` (i.e.,
  with permission). (Legal: relevant to name/likeness/endorsement rights.)
- **Third-party services:** Anthropic (AI), AWS (hosting), Stripe (billing). Each
  processes data under its own terms; the app minimizes what it sends (the AI
  receives only the small matched plan, not the user's full record).

---

## 10. Testing & quality

- Backend: `pytest` suite (**53 passing**, 1 AI-key-gated test auto-skips)
  covering rules engine, entitlements, billing, admin, and cost service. Runs
  with no API key and the in-memory store.
- Guardrail tests assert the free tier never produces AI output and never
  requires an API key.
- Frontend: `vitest` for completion/celebration logic (**15 passing**).

---

## 11. Deployment & environments

- **Local dev:** in-memory store, no AWS, no API key needed for the free tier;
  login code returned in the response. See §12.
- **Production:** AWS SAM (`infra/template.yaml`) — Lambda + API Gateway +
  DynamoDB; Stripe for billing; static frontend host. The app runs end-to-end
  without billing configured, so a free-tier launch can precede payments.
- Full runbook: `DEPLOY.md` and `docs/GO-LIVE-runbook.md`.

---

## 12. Running it locally (for reviewers)

**Backend** (from `agent/`):
```
pip install -r requirements.txt
# minimal: free tier + admin console, no AWS, no AI key
ADMIN_TOKEN=devtoken python -m uvicorn app.main:app --port 8001
```

**Frontend** (from `frontend/`):
```
npm install
npm run dev            # http://localhost:3200
```

**Admin console:** open `frontend/public/admin.html` (served by the frontend, or
open the file with `?api=http://localhost:8001`). Sign in with the `ADMIN_TOKEN`
you set. The **Cost tab** works immediately in estimate mode.

To demo the **paid** experience without Stripe, set `ALLOW_DEV_UPGRADE=true` and
grant paid from the admin console (dev only — never in production).

---

## 13. Open items before launch (consolidated)

| # | Item | Owner | Legal-relevant |
|---|---|---|---|
| 1 | Expert sign-off on DRAFT content library | Expert / Andrea | ✅ IP / accuracy |
| 2 | Published Terms of Service | Counsel | ✅ |
| 3 | Published Privacy Policy (collection, staff access, third parties) | Counsel | ✅ |
| 4 | **Data retention + user deletion flow** (currently manual) | Eng + Counsel | ✅ |
| 5 | Automated grounding check on AI output (before scaling volume) | Eng | ✅ liability |
| 6 | Confirm `ALLOW_DEV_UPGRADE=false` + strong `ADMIN_TOKEN` in prod | Eng | ✅ |
| 7 | Niki sign-off on celebration/seal copy (no dollar/risk/legal claims) | Expert | ✅ |
| 8 | Real AWS cost integration on (`AWS_COST_ENABLED=1`) if billed $ wanted | Eng | — |

---

*This document reflects the system as built as of 2026-07-14. Sources are cited
inline by file path so any claim can be verified against the code.*

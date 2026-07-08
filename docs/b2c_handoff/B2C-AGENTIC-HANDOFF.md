# B2C My Final Playbook (Agentic) — architecture handoff

A freemium, AI-agent B2C product, built as a SEPARATE app from the B2B platform,
but sharing ONE operator/analytics dashboard. This doc is the build brief: AWS,
backend, tables, and the shared-admin design.

**Status:** not built, not hosted. This is the plan to hand to whoever builds it.
**Relationship to B2B:** separate user pool, separate data, separate experience.
Shared: the operator console + analytics, the shared control plane, the domain.

---

## 1. Product shape (what we are building)

| Tier | Playbook access | AI agent | Price |
|---|---|---|---|
| **Free** | ONE action item unlocked; the rest LOCKED | 3 queries total | $0 |
| **Paid** | Full plan: 7-day planner + all action items | Unlimited agent, with access to the member's own plan and general Q&A | subscription |

- Free is the hook: real value in one item, a locked preview of the rest, and a
  taste of the agent (3 queries), so the upgrade is obvious.
- Paid unlocks: the full personalized plan, the planner, and an unlimited agent
  that can read the member's plan ("what's my next step?", "explain a POA to me").

The CONTENT and personalization engine are the SAME as B2B (questions, milestones,
signals, the MOAT). B2C differs in packaging (gating + agent + payments), not in
the underlying plan logic. Reuse, do not fork, the content model.

---

## 2. The core architectural decision: how "separate apps, one admin" works

The clean model is **two data planes, one control/operator plane.** Nothing here
reopens the B2B locked decisions — B2C is additive alongside them.

```
                        ┌─────────────────────────────┐
                        │   SHARED CONTROL PLANE       │
                        │  (already exists for B2B)    │
                        │  - CloudFront + WAF          │
                        │  - API Gateway + HTTP Lambda │
                        │  - Operator Cognito pool     │
                        │  - Control DDB (content,      │
                        │    config, analytics stream) │
                        │  - Audit bucket, SES, etc.   │
                        └───────┬─────────────┬────────┘
                                │             │
            ┌───────────────────┘             └──────────────────┐
   ┌────────▼─────────┐                              ┌────────────▼─────────┐
   │  B2B PLANE       │                              │  B2C PLANE           │
   │  (this repo)     │                              │  (new app)           │
   │  - Tenant Cognito│                              │  - B2C Cognito pool  │
   │    pools (N)     │                              │    (ONE pool, self-  │
   │  - Per-tenant DDB│                              │    service signup)   │
   │  - Per-tenant KMS│                              │  - B2C DDB table     │
   └──────────────────┘                              │  - Stripe billing    │
                                                     └──────────────────────┘
```

**Why this shape:**
- **Separate user pools** = a B2C consumer can never appear in a corporate tenant,
  and vice versa. Different auth, different signup, different data-subject rights.
- **Shared operator pool + analytics** = ONE admin dashboard. Operators log in
  once and see both planes because both write to the SAME analytics stream and
  audit bucket. The dashboard queries across planes; the members never mix.
- **Shared content plane** = B2C reads the SAME published content bundle
  (`GET /api/v2/content`) as B2B. One place to author questions/milestones.

---

## 3. Tables (naming stays consistent with the current family)

Keep the `lro-{env}-*` family so operations, tagging, and IaC stay uniform.

| Table | Plane | Purpose | Key design |
|---|---|---|---|
| `lro-{env}-control` | shared | content bundle, config, feature flags (EXISTS) | `V2CONTENT#member`, etc. |
| `lro-{env}-tenant-{slug}` | B2B | per-tenant member data (EXISTS) | `MEMBER#{id}` / `V2#*` |
| **`lro-{env}-b2c`** (NEW) | B2C | ALL B2C consumer data, single table | see below |
| `lros-audit` / analytics stream | shared | operator dashboard source | both planes emit here |

### `lro-{env}-b2c` single-table design

B2C is one shared pool (not per-tenant), so ONE table with a user partition:

| PK | SK | Item |
|---|---|---|
| `USER#{userId}` | `PROFILE` | email, tier (free/paid), created, stripeCustomerId |
| `USER#{userId}` | `V2#STATE` | answers, flags, assigned (same shape as B2B) |
| `USER#{userId}` | `V2#PROGRESS#{milestoneId}` | status + persist-safe worksheet |
| `USER#{userId}` | `ENTITLEMENT` | tier, planExpiresAt, agentQueriesUsed, unlockedActionIds[] |
| `USER#{userId}` | `AGENT#SESSION#{id}` | agent conversation refs (NOT raw PII) |
| `USER#{userId}` | `SUB#{stripeSubId}` | subscription status mirror (from Stripe webhook) |

- **Same free-text rule as B2B:** never store names/passwords/account numbers.
  The agent works off the member's PLAN STRUCTURE, not stored sensitive text.
- **Entitlement is the gate:** the `ENTITLEMENT` item is the single source of
  truth for "free vs paid," how many agent queries are left, and which action is
  unlocked. Every gated endpoint checks it.
- Encryption: table-level KMS (a B2C CMK) is enough; no per-user CMK needed
  (consumers are not tenants, cryptographic-erase-per-tenant does not apply). A
  GDPR delete is a per-user item purge on this one table.

---

## 4. Freemium gating (where the free/paid line is enforced)

Enforce SERVER-SIDE, never trust the client:

| Gate | Rule | Enforced at |
|---|---|---|
| Action items | Free: only `unlockedActionIds[0]` returns full content; others return a LOCKED stub (title + "upgrade to unlock"). Paid: all. | plan/read endpoint reads `ENTITLEMENT.tier` |
| Agent queries | Free: reject once `agentQueriesUsed >= 3`. Paid: unlimited. | agent endpoint increments + checks `ENTITLEMENT` atomically |
| 7-day planner | Paid only. | planner endpoint checks tier |

The client shows locks/paywalls for UX, but the API is the boundary — a free user
hitting a paid endpoint gets a 402/403, always.

---

## 5. The AI agent (the paid differentiator)

- **Model:** Claude (latest — this is an Anthropic-aligned build). The agent has a
  system prompt scoped to legacy planning + the member's OWN plan structure
  (assigned milestones, completion state — never their free-text).
- **Free tier:** 3 queries, hard-capped by the `ENTITLEMENT.agentQueriesUsed`
  counter (atomic DDB update, so it cannot be raced past 3).
- **Paid tier:** unlimited; can answer "what's my next step," "explain X,"
  "reorder my plan for a divorce," grounded in the published content + their plan.
- **Data boundary:** the agent NEVER sees stored PII (there is none). It sees the
  plan skeleton + the shared content bundle. This keeps the agent useful and the
  data safe — same Tripwire-10 posture as everything else.
- Runs on the shared HTTP Lambda under `/api/b2c/agent` (or its own Lambda if
  streaming responses need it) — no new architecture, an added route.

---

## 6. Payments (Stripe — pattern already exists in B2B)

The B2B repo already has a Stripe integration (`services/api/src/routes/stripe.ts`,
webhook). Reuse it:
- Checkout for the paid tier → Stripe.
- Webhook (`/api/b2c/stripe/webhook`) updates `ENTITLEMENT.tier` = paid and
  `SUB#{id}` on `checkout.session.completed` / `customer.subscription.*`.
- On cancel/lapse → tier back to free (or a grace window). All server-side.

---

## 7. The shared admin/analytics dashboard (your key requirement)

ONE operator dashboard, both planes visible, users never mixed:

- **Auth:** operators use the EXISTING operator Cognito pool (TOTP MFA). No new
  admin login.
- **How both planes show up:** both B2B and B2C emit the SAME analytics events
  (DynamoDB Streams → Firehose → S3 → Athena, already the B2B pattern) and the
  SAME audit events. Add a `plane: 'b2b' | 'b2c'` dimension to every event.
- **Dashboard queries:** the admin UI filters by `plane` — "show B2C conversions,"
  "show B2B tenant X," or combined. Because it is one analytics store with a plane
  tag, the dashboard is one app over both.
- **What operators see for B2C:** signups, free→paid conversion, agent usage,
  action-completion funnels, churn. All from the analytics stream, no direct
  reads into member data (privacy preserved).

Result: separate experiences, separate pools, separate tables — but one place to
run the business, exactly as asked.

---

## 8. URL / hosting (roughly the same domain when live)

- B2B today: `{tenant}.enterprise.endevo.life`.
- B2C suggestion: `app.endevo.life` or `my.endevo.life` (one consumer host, since
  there is no per-tenant subdomain for consumers). Operator console stays
  `admin.endevo.life`.
- Same CloudFront + wildcard ACM cert (`*.endevo.life`, already exists). B2C is a
  new CloudFront behavior / distribution pointing at the B2C SPA bucket; the API
  is the shared API Gateway with `/api/b2c/*` routes.

---

## 9. Build order (suggested)

1. `lro-{env}-b2c` table + B2C Cognito pool (self-service signup) via CDK.
2. B2C SPA skeleton (can reuse the V2 experience components — same content model).
3. Entitlement item + gating middleware (free/paid, query counter).
4. `/api/b2c/*` routes on the shared Lambda: plan read (gated), agent, planner.
5. Stripe checkout + webhook → entitlement flips.
6. Analytics `plane` tag on every event; extend the operator dashboard with a
   plane filter.
7. CloudFront behavior + `my.endevo.life` DNS.

---

## 10. What this does NOT do (guardrails)

- Does NOT touch B2B tenant tables or pools.
- Does NOT store consumer PII beyond identity + plan structure (Tripwire 10 holds).
- Does NOT fork the content/personalization engine — B2C reads the same bundle.
- Does NOT give the free tier a way to exceed limits (server-enforced).

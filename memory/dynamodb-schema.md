---
name: dynamodb-schema
description: MyFinalPlaybook DynamoDB table naming, schema, and what's stored for free vs paid users
metadata:
  type: project
---

MyFinalPlaybook uses AWS DynamoDB (account 383423735462, us-east-1) with a
per-app prefix so it sits cleanly alongside the user's B2B tables (which use
`lro-*` and `lros-*`). Set 2026-07-06.

**Prefix:** `mfp-dev-` (MyFinalPlaybook, dev env). Configurable via DDB_TABLE_PREFIX.
Change to mfp-staging- / mfp-prod- per environment. NOT single-table — separate
tables per concern (matches the user's lros-* style; easier to browse).

**5 tables:**
- `mfp-dev-users`    PK email                -> tier(free|paid), created_at, stripe_customer_id
- `mfp-dev-sessions` PK token                -> email, expires_at (TTL enabled)
- `mfp-dev-usage`    PK email, SK month       -> personalize_count, chat_count (quota)
- `mfp-dev-plans`    PK email                -> answers, plan, tracked (per-step progress), narrative
- `mfp-dev-chat`     PK email, SK ts          -> role, content (AI chat history)

**Free vs paid storage decisions (user, 2026-07-06):**
- FREE users ARE stored (users + usage) -- they're the funnel + we meter their 3
  free AI questions. Anonymous (never-signed-in) visitors are NOT stored.
- PAID users get FULL storage: profile + tier + saved plan + per-step progress +
  chat history -> they resume exactly where they left off, across devices.

**Code:** agent/store.py DynamoStore (multi-table). Interface shared by MemoryStore
(tests) + SqliteStore (offline local). API: /api/my/plan (GET load, POST save),
chat auto-persists to mfp-dev-chat. tests/conftest.py forces STORE_BACKEND=memory
so tests never touch real AWS.

**History:** briefly used a single `final-playbook` table + a SQLite stopgap
(when the DDB create-table was blocked by the safety guard). Both removed; the
final-playbook table was deleted. See [[finalplaybook-debranded-saas]].

**Billing:** pay-per-request; ~$0/mo at dev/early-launch volume (AWS free tier).

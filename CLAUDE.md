# Final Playbook

End-of-life planning app. Members answer situational questions; a deterministic
rules engine matches proven clinical routing logic; a paid tier adds one grounded
LLM call to personalize the output in a warm, neutral guide voice. The free tier
never touches an LLM.

The product is **expert-agnostic** by default — no single person is named or
impersonated. All brand/voice text is config-driven (`agent/app/config.py`,
`frontend/src/config/branding.js`), so it can ship under any name. An expert
persona can optionally be surfaced (with permission) by setting `EXPERT_NAME`.

## Why this architecture

- **Cost:** the free tier is $0 to run (pure rules engine). The one paid-tier
  LLM call is ~$0.002-0.006 depending on model (see `docs/prompts.md`). Paid
  usage is quota-capped per user (`agent/plans.py`) so no account runs up an
  unbounded bill.
- **Trust:** this is an educational app for a sensitive topic (end-of-life
  planning) that explicitly does not give legal/financial/medical advice and
  must not hallucinate. The LLM is only ever allowed to rephrase pre-written,
  human-authored content — never to invent new advice. See `docs/guardrails.md`.
- **Content status:** the knowledge base is real clinical logic mined from
  client sessions, but is a **draft** — not yet signed off. Treat routing
  priorities and scripts as provisional. See
  `knowledge-base/content-library.json` → `_meta.status`.

## Folder structure

```
Final-Playbook/
├── CLAUDE.md                    # this file
├── DEPLOY.md                    # production deploy runbook (AWS + Stripe)
├── docs/
│   ├── development-guide.md     # how to run, extend, and modify the agent
│   ├── prompts.md               # the LLM system prompt, model choice, cost notes
│   ├── rules.md                 # human-readable routing rules reference
│   ├── guardrails.md            # hallucination/scope guardrails, how they're enforced
│   ├── pricing.md               # freemium vs paid split, limits, unit economics
│   └── testing/e2e-test-plan.md # what's covered, how to run
├── knowledge-base/
│   └── content-library.json     # Q&A, situation profiles, scripts, quotes (DRAFT)
├── infra/
│   └── template.yaml            # AWS SAM: Lambda + API Gateway + DynamoDB
├── agent/                       # layered FastAPI backend
│   ├── app/
│   │   ├── main.py              # FastAPI app factory (wires routers + CORS)
│   │   ├── config.py           # brand/voice + runtime settings (de-branding seam)
│   │   ├── api/
│   │   │   ├── deps.py         # auth dependencies (current_email / require_email)
│   │   │   └── routes/         # meta, auth, assessment, plan, chat, billing,
│   │   │                       #   feedback, admin
│   │   ├── schemas/requests.py # Pydantic request models
│   │   ├── services/           # BUSINESS logic: auth, billing, entitlements,
│   │   │                       #   plans, feedback, notifications
│   │   ├── agent/              # the AI agent: rules_engine, orchestrator,
│   │   │                       #   personalize, chat (rules = free, LLM = paid)
│   │   ├── data/email.py       # email TRANSPORT (console | ses) — no content
│   │   │                       #   services/email_template.py = brand chrome
│   │   └── data/store/         # DATA layer: base(+factory), memory, sqlite, dynamodb
│   ├── lambda_handler.py       # Mangum wrapper for AWS Lambda (imports app.main)
│   ├── demo.py                 # manual smoke test
│   ├── tests/                  # unit + e2e (conftest forces in-memory store)
│   └── requirements.txt
└── frontend/                    # Vite + React UI (landing, auth, walkthrough)
    └── src/
        ├── App.jsx
        ├── config/branding.js   # all user-facing brand text (de-branding seam)
        ├── auth/useAuth.js      # session + entitlement hook
        └── components/          # Landing, Pricing, LoginModal, ...
```

## Running it

Backend (from `agent/`):
```
pip install -r requirements.txt
python -m uvicorn app.main:app --port 8001
```
Store defaults to in-memory (`STORE_BACKEND=memory`) — no database needed for
local dev. Port 8001 is just a convention; change freely.

Frontend (from `frontend/`):
```
npm install
npm run dev
```
Then open `http://localhost:3200`. In dev the login code is returned in the
response (shown in the sign-in modal) — no email provider needed.

Paid tier requires `ANTHROPIC_API_KEY` set before starting the backend — without
it, paid-tier requests return a 502 with the underlying error rather than a raw
crash. To test paid features without Stripe, grant a user paid tier manually
(see `DEPLOY.md` §2).

## Operator notifications & member feedback

- **Signup alert:** a brand-new member triggers one email to `OPERATOR_EMAILS`.
  Returning logins send nothing.
- **Weekly digest:** EventBridge invokes the same Lambda with
  `{"job": "weekly_digest"}` on Mondays; `lambda_handler.py` dispatches on event
  shape. Idempotent per week via a watermark in the config store.
- **Feedback:** one `POST /api/feedback` serves help / complaint / survey, works
  signed-in *and* anonymous. Persisted first, emailed second. Rate-limited by
  email when identified, by IP when not — the anonymous path is public and
  writes rows + sends mail, so it always needs a ceiling.
- **Everything is best-effort** — `data/email.py`'s `send()` returns a bool and
  never raises, and `services/notifications.py` swallows. A mail failure must
  never cost a signup or lose a complaint. Same contract as `analytics.emit()`.
- **Off by default:** `EMAIL_BACKEND=console` + empty `OPERATOR_EMAILS` means no
  sends from a dev laptop or a test run. Set both to go live (see `DEPLOY.md` §3d).
- **Privacy line:** operator email carries identity only (address, tier,
  timestamps, counts). A member's answers, plan, or narrative must NEVER appear
  in an outbound email — there's a test asserting this.
- Spec: `specs/notifications-and-feedback.md`.

## Freemium / paid (enforced server-side)

- **Free:** anonymous, unlimited, rules engine only. No LLM, no chat.
- **Paid:** requires a logged-in user AND a live `tier=="paid"` entitlement in
  the store (set by the Stripe webhook). Adds the personalized narrative + chat,
  metered by monthly quotas.
- The client can no longer just send `tier="paid"` to get LLM output — the gate
  is in `entitlements.py` (402 = upgrade needed, 429 = quota exhausted). See
  `docs/pricing.md`.

## Running tests

From `agent/`:
```
pytest tests/ -v
```
Everything passes with only `requirements.txt` and no API key (118 tests, no AWS
credentials needed — `conftest.py` forces the in-memory store and the
log-only email backend so a test run can never send real mail). The
paid-tier LLM grounding tests auto-skip if no `ANTHROPIC_API_KEY` is configured.

## Deploying

See `DEPLOY.md` — AWS SAM (`infra/template.yaml`) for the backend (Lambda + API
Gateway + DynamoDB), Stripe for billing, any static host for the frontend. The
app runs end-to-end without billing configured, so a free-tier launch can go
first and payments can be turned on later.

## Conventions for future work in this repo

- **Layered structure:** routes (`app/api/routes/`) stay thin — validate + call a
  service. Business logic lives in `app/services/`, the AI in `app/agent/`, and all
  persistence behind `app/data/store/` (never touch a DB from a route).
- Never add action items, scripts, or clinical claims that aren't already in
  `content-library.json`. If a gap is found, add it to the content library first
  (and flag it as unvalidated), then wire it into `app/agent/rules_engine.py` —
  don't let the LLM improvise around a gap.
- Keep `app/agent/personalize.py`'s system prompt (built from `app/config.py`) as
  the single source of truth for tone/scope rules. If you change it, update
  `docs/prompts.md`.
- Additive only on `MemberContext` — don't repurpose an existing flag's meaning;
  the content library's flag names are load-bearing across profiles.
- Keep all user-facing brand/voice text in `app/config.py` / `branding.js`. Don't
  hard-code a product or person's name back into prompts or components.
- Pricing/limits live in `app/services/plans.py` and flow to the UI via
  `/api/pricing` — edit them there, not in the frontend.
- To add a new store backend, implement the full method set in a new
  `app/data/store/<name>.py` and register it in `base.py`'s `get_store()`.
- Notifications are three layers: transport (`app/data/email.py`), brand chrome
  (`app/services/email_template.py`), content (`app/services/notifications.py`).
  Add a new channel by implementing a backend in `email.py`; a new message by
  adding a function in `notifications.py`; restyle every message at once by
  editing `email_template.py`. Never let a send raise into a request path.
- Every notification sends **both** a plain-text and an HTML part. Text is not
  optional garnish — screen readers and spam scoring both read it, and a
  message with no text part scores worse. Keep the same facts in both.
- Email HTML has to survive Outlook (Word's engine) and Gmail: tables not
  flexbox, styles inline not in a `<style>` block, no inline SVG, 600px max.
  `tests/test_email_template.py` asserts each of these. The logo is drawn with
  table cells rather than an `<img>` because remote images are blocked by
  default in most clients and would show as an empty box on first open.
- Anything interpolated into an email template must go through `_esc()` —
  member-written feedback lands in operator mail.

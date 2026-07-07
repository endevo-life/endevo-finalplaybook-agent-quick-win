# MyFinalPlaybook

An end-of-life planning app that helps people get their digital, legal, financial,
and health affairs in order — so the people they love are never left guessing.

Members answer a few plain-language questions; a **deterministic rules engine**
(zero LLM, free) produces a prioritized action plan; a **paid tier** adds one
grounded LLM call to personalize it and an AI assistant to answer questions about
their specific plan.

> **Live Fully, Die Ready.**

---

## Why this architecture

- **Cost:** the free tier is $0 to run — it's a pure rules engine, no LLM. Only
  paid users trigger the one Claude call (~$0.002–0.006 each), and usage is
  quota-capped per account so no one runs up an unbounded bill.
- **Trust:** this is educational content on a sensitive topic. The app explicitly
  does **not** give legal/financial/medical advice, and the LLM is only ever
  allowed to *rephrase* pre-written, human-authored content — never to invent new
  advice. See [`docs/guardrails.md`](docs/guardrails.md).
- **Expert-agnostic:** no single person is named or impersonated. All brand/voice
  text is config-driven, so the product can ship under any name.

---

## Tech stack

| Layer | Tech |
|---|---|
| Frontend | Vite + React |
| Backend | FastAPI (Python 3.12), layered `app/` package |
| AI | Anthropic Claude (Sonnet for the plan narrative, Haiku for chat) |
| Auth | Passwordless email + opaque session tokens |
| Billing | Stripe Checkout + webhook |
| Data | DynamoDB (prod) · SQLite (local) · in-memory (tests) — one interface |
| Deploy | AWS Lambda + API Gateway via SAM (`infra/template.yaml`) |

---

## Project structure

```
├── agent/                       # FastAPI backend (layered)
│   ├── app/
│   │   ├── main.py             # app factory (wires routers + CORS)
│   │   ├── config.py           # brand/voice + runtime settings
│   │   ├── api/                # PRESENTATION: routes/ + deps.py
│   │   ├── schemas/            # Pydantic request models
│   │   ├── services/           # BUSINESS: auth, billing, entitlements, plans
│   │   ├── agent/              # AI AGENT: rules_engine, orchestrator, personalize, chat
│   │   └── data/store/         # DATA: base(+factory), memory, sqlite, dynamodb
│   ├── lambda_handler.py       # AWS Lambda entrypoint (Mangum)
│   ├── tests/                  # unit + e2e
│   └── requirements.txt
├── frontend/                    # Vite + React UI
├── knowledge-base/
│   └── content-library.json    # Q&A, situation profiles, scripts (DRAFT)
├── infra/template.yaml          # AWS SAM (Lambda + API Gateway + DynamoDB)
├── docs/                        # guardrails, prompts, rules, pricing, GTM
├── CLAUDE.md                    # architecture + conventions (start here)
└── DEPLOY.md                    # production deploy runbook
```

---

## Quick start

**Prerequisites:** Python 3.12, Node.js. An `ANTHROPIC_API_KEY` is only needed for
the paid tier.

### Backend (from `agent/`)

```bash
pip install -r requirements.txt
cp .env.example .env        # set ANTHROPIC_API_KEY for the paid tier (optional)
python -m uvicorn app.main:app --port 8001
```

The store defaults to in-memory for tests; for local dev set `STORE_BACKEND=sqlite`
(persists across restarts, no AWS) or `dynamodb` for the cloud tables.

### Frontend (from `frontend/`)

```bash
npm install
cp .env.example .env.local  # VITE_API_BASE_URL defaults to http://localhost:8001
npm run dev
```

Open **http://localhost:5173**. In dev, the sign-in code is shown right in the
login modal (no email provider needed).

### One-command launch (Windows)

```powershell
./start-app.ps1     # starts backend + frontend, each in its own window
```

---

## The freemium / premium split

Enforced **server-side** (`app/services/entitlements.py`) — the client can't just
claim to be paid.

| | **Free** | **Premium ($25/mo)** |
|---|---|---|
| Situation assessment + first steps | ✅ | ✅ |
| Full plan (all domains) | preview (blurred) | ✅ |
| Track items / progress | — | ✅ |
| Personalized 7-day narrative (AI) | — | ✅ |
| AI assistant (grounded chat) | 3-question taste | unlimited |
| Account required | no (anonymous) | yes |

Free users hit a `402` on paid features; over-quota paid users hit `429`. See
[`docs/pricing.md`](docs/pricing.md).

---

## Running tests

```bash
cd agent
pytest tests/ -v
```

Everything passes with only `requirements.txt` and no API key. The paid-tier LLM
tests auto-skip without an `ANTHROPIC_API_KEY`. `tests/conftest.py` forces the
in-memory store, so the suite never touches AWS.

---

## Deploying

See [`DEPLOY.md`](DEPLOY.md) — AWS SAM for the backend (Lambda + API Gateway +
DynamoDB), Stripe for billing, any static host for the frontend. The app runs
end-to-end **without** billing configured, so a free-tier launch can go first and
payments can be turned on later.

---

## Status

Pre-launch. The content library is a **DRAFT** pending expert sign-off — get that
sign-off before promoting the paid tier (see `knowledge-base/content-library.json`
→ `_meta.status`). Not legal, financial, or medical advice.

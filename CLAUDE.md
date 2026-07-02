# Final Playbook — Agent (Endevo)

End-of-life planning app for Niki Weiss (digital thanatologist). Members answer
situational questions; a deterministic rules engine matches Niki's clinical
routing logic; a paid tier adds one grounded LLM call to personalize the output
in her voice. Trial tier never touches an LLM.

## Why this architecture

- **Cost:** the trial tier is $0 to run (pure rules engine). The one paid-tier
  LLM call is ~$0.002-0.006 depending on model (see `docs/prompts.md`).
- **Trust:** this is an educational app for a sensitive topic (end-of-life
  planning) that explicitly does not give legal/financial/medical advice and
  must not hallucinate. The LLM is only ever allowed to rephrase pre-written,
  human-authored content — never to invent new advice. See `docs/guardrails.md`.
- **Content status:** the knowledge base is Niki's real clinical logic mined
  from client sessions, but is a **draft** — not yet signed off by Niki/Andrea.
  Treat routing priorities and scripts as provisional. See
  `knowledge-base/niki-content-library.json` → `_meta.status`.

## Folder structure

```
Endevo-FinalPlaybook/
├── CLAUDE.md                    # this file
├── docs/
│   ├── development-guide.md     # how to run, extend, and modify the agent
│   ├── prompts.md                # the LLM system prompt, model choice, cost notes
│   ├── rules.md                   # human-readable routing rules reference
│   ├── guardrails.md              # hallucination/scope guardrails, how they're enforced
│   └── testing/
│       └── e2e-test-plan.md       # what's covered, how to run
├── knowledge-base/
│   └── niki-content-library.json # Niki's Q&A, situation profiles, scripts, quotes (DRAFT)
├── agent/
│   ├── rules_engine.py            # zero-token routing (context flags -> plan)
│   ├── personalize.py             # the one Claude call (paid tier only)
│   ├── orchestrator.py            # run(flags, name, tier) entrypoint
│   ├── api.py                     # local FastAPI wrapper for the React UI
│   ├── demo.py                     # manual smoke test
│   ├── tests/
│   │   ├── test_rules_engine.py   # unit tests (no server, no API key needed)
│   │   └── test_api_e2e.py         # end-to-end API tests (FastAPI TestClient)
│   └── requirements.txt
└── frontend/                      # Vite + React agent-runner UI
    └── src/App.jsx
```

## Running it

Backend (from `agent/`):
```
pip install -r requirements.txt
python -m uvicorn api:app --port 8001
```
> Port 8000 was occupied by an unrelated service on the dev machine this was
> built on — 8001 is just what worked there. Change freely.

Frontend (from `frontend/`):
```
npm install
npm run dev
```
Then open `http://localhost:5173`.

Paid tier requires `ANTHROPIC_API_KEY` set (or `ant auth login`) before starting
the backend — without it, paid-tier requests return a 502 with the underlying
error message rather than a raw crash.

## Running tests

From `agent/`:
```
pytest tests/ -v
```
Unit tests need nothing installed beyond `requirements.txt`. The paid-tier
grounding test in `test_api_e2e.py` auto-skips if no API key is configured.

## Where this goes next

This repo is the **agent** only. Not yet built (intentionally deferred, see
prior conversation): user signup/auth, billing/Stripe, per-user token or query
caps, and production deployment (AWS Lambda + API Gateway + DynamoDB in place
of `api.py`'s local dev server). Build and validate the agent first; wrap it
in the SaaS product second.

## Conventions for future work in this repo

- Never add action items, scripts, or clinical claims that aren't already in
  `niki-content-library.json`. If a gap is found, add it to the content
  library first (and flag it as unvalidated), then wire it into
  `rules_engine.py` — don't let the LLM improvise around a gap.
- Keep `personalize.py`'s system prompt as the single source of truth for
  tone/scope rules. If you change it, update `docs/prompts.md` to match.
- Additive only on `MemberContext` — don't repurpose an existing flag's
  meaning; the content library's flag names are load-bearing across profiles.

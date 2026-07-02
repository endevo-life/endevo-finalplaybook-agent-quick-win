# End-to-end test plan

## Test files

| File | What it covers | Needs API key? | Needs a running server? |
|---|---|---|---|
| `agent/tests/test_rules_engine.py` | Routing logic in isolation: priority order, parallel business profile, action-item caps, empty-flags case, trial tier's zero-dependency guarantee | No | No |
| `agent/tests/test_api_e2e.py` | The FastAPI layer end to end via `TestClient` (in-process, no need to start `uvicorn`): request validation, trial tier, empty-plan paid-tier guard, and (when a key is present) a grounding smoke check on real LLM output | Partially — most tests don't; two are gated on `ANTHROPIC_API_KEY` (one runs only *without* a key, one only *with* one, so the suite always exercises one of the two paths) | No |

## Running

```
cd agent
pip install -r requirements.txt
pytest tests/ -v
```

## What "passing" means right now

As of this writing, with no `ANTHROPIC_API_KEY` configured in the dev
environment, the full suite passes with the credential-gated grounding test
skipped and its "no credentials" counterpart running instead. Before shipping
paid tier, re-run with a real key configured so
`test_paid_tier_is_grounded_in_matched_action_items` actually exercises the
model.

## Coverage gaps (known, not yet addressed)

- **No frontend automated test.** `frontend/src/App.jsx` has been verified
  by: (1) Vite serving the transformed module with no syntax errors, and
  (2) the backend contract it depends on being covered by
  `test_api_e2e.py`. It has **not** been verified by an actual browser
  interaction (clicking checkboxes, submitting, confirming the rendered
  result) — that needs to be done manually, or automated later with
  Playwright/Cypress once the UI stabilizes.
- **No load/volume testing** — irrelevant at this stage, relevant once the
  SaaS wrapper (rate limits, quotas) is built.
- **No adversarial prompt-injection testing** of the paid-tier call (e.g. a
  crafted `memberFirstName` or flag combination attempting to override the
  system prompt). Worth adding given the system prompt's constraints are
  currently only enforced by instruction, not by an independent output
  check (see `docs/guardrails.md`).

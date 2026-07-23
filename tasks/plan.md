# Plan: Launch Trust Package

Spec: `docs/specs/spec-launch-trust-package.md` (approved 2026-07-20)

## Components & dependency order

```text
A. Legal pages (independent — content + static HTML, no backend)
B. Delete account:  B1 store method → B2 service+route → B3 Settings UI
C. Trusted people:  C1 schema+store+route → C2 UI + PDF
D. Google SSO:      D1 backend verify+route → D2 login UI
```

A is fully parallel to everything. B, C, D are independent of each other but
each is internally sequential. Priority order: A, B (blockers) → C → D.

## Key technical decisions

1. **Store contract grows by one method:** `delete_user_data(email)` — removes
   the user row, all sessions for that email, all usage rows, the saved plan
   (incl. trusted people), chat history, and the stripe_customer→email mapping.
   Implemented in all three backends; MemoryStore is the canonical reference.
   - *DynamoDB wrinkle:* sessions are keyed by token, not email → delete does a
     scan-and-filter on the sessions table. Acceptable at launch scale; noted in
     the method docstring (a GSI is the scale-up path).
2. **Deletion service** (`app/services/accounts.py`): if the user has an active
   Stripe subscription, cancel it immediately (reuse `billing.py`'s Stripe client;
   cancel now, not at period end), then `delete_user_data`. Route:
   `DELETE /api/account` behind `require_email`. Idempotent — deleting an
   already-gone account returns success.
3. **Trusted people ride the plan record:** additive `people` kwarg on
   `save_plan` (list of dicts), returned by `get_plan`. Validation in the
   Pydantic schema: max 10 people; name/role required; name, role, phone, email,
   notes each ≤ 500 chars. Routes live in `plan.py` (`GET`/`PUT /api/plan/people`),
   auth required (free logged-in OK — matches spec).
4. **Google SSO, built-in auth backend only:** `POST /api/auth/google` accepts a
   Google ID token, verifies signature/audience/expiry via `google-auth` against
   `GOOGLE_CLIENT_ID` (new `config.py` setting), then issues a normal session via
   `auth_service` (same token shape as email-code login). Returns 404-equivalent
   (disabled) when `GOOGLE_CLIENT_ID` is unset. When `AUTH_BACKEND == "cognito"`,
   the endpoint stays disabled — Cognito deployments federate Google inside
   Cognito instead (documented in DEPLOY.md, out of code scope).
   Frontend: Google Identity Services script loaded only when
   `VITE_GOOGLE_CLIENT_ID` is set; button renders in LoginModal above the email
   form.
5. **Legal pages are static HTML** in `frontend/public/` with inline styles
   matching brand tokens; linked from the app footer, LoginModal, and checkout.
   Content: product-specific (localStorage-only, no cookies/analytics in-app,
   Stripe payments, Anthropic processing for paid narrative/chat, deletion
   rights incl. self-serve delete) under **ENDevo Inc.**, linking to the master
   policy at endevo.life. Both pages carry "Draft — pending review" banner until
   Niki approves, removed at deploy sign-off.

## Risks & mitigations

| Risk | Mitigation |
|---|---|
| Legal text overpromises vs. actual behavior | Text drafted strictly from code-verified behavior; Niki review gate before deploy (Boundaries: ask-first). |
| Stripe cancel fails mid-delete | Cancel first; if Stripe errors, abort deletion with a 502 and delete nothing — never leave a paying subscription attached to a deleted account. |
| PDF generation location unknown for trusted people | C2 starts with a 10-minute investigation of the download path; if PDF is generated frontend-side, people render from the same plan payload. |
| `google-auth` dependency (ask-first boundary) | Approved in spec Boundaries; pinned in requirements.txt. |
| Existing tests break | Full `pytest tests/ -v` after every task; store contract change is additive. |

## Verification checkpoints

- After B1: store unit tests green for all three backends' delete (memory + sqlite
  run in CI; dynamodb method code-reviewed, exercised in staging).
- After B2/C1/D1: route-level tests green, `pytest tests/ -v` fully green.
- After B3/C2/D2: manual walkthrough in dev (`npm run dev` + uvicorn) — delete a
  test account end-to-end, add trusted people and download the PDF, log in with
  Google (real client ID in dev).
- Final: all spec Success Criteria checked off; legal pages reviewed by Niki.

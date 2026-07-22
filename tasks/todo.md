# Tasks: Launch Trust Package

Plan: `tasks/plan.md` · Spec: `docs/specs/spec-launch-trust-package.md`
Order: A1 → B1 → B2 → B3 → C1 → C2 → D1 → D2 (A1 can run any time; B/C/D blocks are independent of each other).

## A. Legal pages

- [ ] A1: Draft + ship `privacy.html` and `terms.html`
  - Acceptance: both pages exist in `frontend/public/`, styled to brand, accurate to actual app behavior (localStorage-only, no cookies/analytics, Stripe, Anthropic, self-serve deletion), entity ENDevo Inc., link to endevo.life master policy, "Draft — pending review" banner present; footer links added in the app (Landing + main app) and in LoginModal.
  - Verify: `npm run build` succeeds; open `http://localhost:3200/privacy.html` and `/terms.html`; links reachable from footer. Niki review before deploy (banner removal is a separate sign-off).
  - Files: `frontend/public/privacy.html`, `frontend/public/terms.html`, `frontend/src/components/Landing.jsx`, `frontend/src/App.jsx`, `frontend/src/components/LoginModal.jsx`

## B. Delete my account

- [ ] B1: `delete_user_data(email)` in all three store backends
  - Acceptance: removes user, sessions (by email), usage, plan, chat, stripe map; safe no-op when nothing exists; base.py contract doc updated.
  - Verify: new `tests/test_delete_account.py` store-level cases pass (memory; sqlite via tmp file); `pytest tests/ -v` green.
  - Files: `agent/app/data/store/base.py`, `memory.py`, `sqlite.py`, `dynamodb.py`, `agent/tests/test_delete_account.py`
- [ ] B2: deletion service + `DELETE /api/account` route
  - Acceptance: cancels active Stripe subscription first (abort with 502 if Stripe errors — never orphan a live sub), then wipes store; idempotent; requires auth (401 anonymous).
  - Verify: route tests — delete paid user (Stripe mocked), delete free user, unauthenticated 401, session invalid after delete; full suite green.
  - Files: `agent/app/services/accounts.py` (new), `agent/app/api/routes/auth.py`, `agent/tests/test_delete_account.py`
- [ ] B3: Settings UI — Danger zone
  - Acceptance: "Delete my account" in Settings; confirm step requires typing DELETE; warns paid users remaining time is forfeited; on success clears localStorage token + progress keys and returns to landing.
  - Verify: manual walkthrough in dev (create → upgrade via dev flag → delete → confirm store empty via /api/me 401).
  - Files: `frontend/src/components/Settings.jsx`, `frontend/src/api/client.js`

## C. Trusted people (MVP-lite)

- [ ] C1: schema + store + routes
  - Acceptance: `TrustedPerson` Pydantic model (name+role required, ≤500 chars/field, max 10); `save_plan(..., people=...)` additive in all 3 backends; `GET/PUT /api/plan/people` behind `require_email` (free logged-in allowed); deleted by B1.
  - Verify: new `tests/test_trusted_people.py` — CRUD round-trip, validation rejects 11th person / long fields, 401 anonymous, wiped on delete; suite green.
  - Files: `agent/app/schemas/requests.py`, 3 store files, `agent/app/api/routes/plan.py`, `agent/tests/test_trusted_people.py`
- [ ] C2: UI + PDF
  - Acceptance: TrustedPeople editor (add/edit/remove, role picker: executor, POA, healthcare proxy, doctor, attorney, other) reachable from the playbook; people appear in the downloaded PDF wherever download already exists.
  - Verify: manual — add 2 people, refresh (persisted), download PDF shows them.
  - Files: `frontend/src/components/TrustedPeople.jsx` (new), `frontend/src/components/PlaybookPanel.jsx`, `frontend/src/api/client.js`, PDF generation file (locate first)

## D. Google SSO

- [ ] D1: backend verify + route
  - Acceptance: `GOOGLE_CLIENT_ID` in config; `POST /api/auth/google` verifies ID token (signature, audience, expiry) via `google-auth`, upserts user, issues standard session; 503/disabled when unset or when `AUTH_BACKEND=cognito`; `google-auth` pinned in requirements.txt.
  - Verify: tests with mocked `id_token.verify_oauth2_token` — valid → session works on /api/me; bad audience/expired → 401; unset → disabled; suite green.
  - Files: `agent/app/config.py`, `agent/app/services/auth_google.py` (new), `agent/app/api/routes/auth.py`, `agent/app/schemas/requests.py`, `agent/requirements.txt`, `agent/tests/test_google_sso.py`
- [ ] D2: login UI
  - Acceptance: "Continue with Google" renders in LoginModal only when `VITE_GOOGLE_CLIENT_ID` set (GIS script lazy-loaded); success stores the same token and refreshes entitlement; email-code flow unchanged.
  - Verify: manual with a real dev client ID; without the env var, modal is unchanged.
  - Files: `frontend/src/components/LoginModal.jsx`, `frontend/src/api/client.js`, `frontend/.env.example`

## Done means

All spec Success Criteria pass, `pytest tests/ -v` fully green (28 existing + new), legal pages signed off by Niki, DEPLOY.md updated (GOOGLE_CLIENT_ID, Cognito federation note).

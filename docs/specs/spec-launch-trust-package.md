# Spec: Launch Trust Package

**Status:** DRAFT — awaiting Niki/Nermeen approval · **Date:** 2026-07-20
**Drives:** launch blockers + trust features from `docs/competitive-pricing-2026-07.md` §5

## Objective

Make Final Playbook trustworthy enough to charge money for, in a category where
trust *is* the product. Four features, ordered by launch priority:

1. **Privacy Policy + Terms pages** (blocker) — honest, plain-English legal pages,
   publicly reachable by URL (required for Stripe live mode + Google OAuth consent
   screen verification).
2. **Delete my account** (blocker) — a member can permanently erase their account
   and every trace of their data, self-serve.
3. **Trusted people (MVP-lite)** — a member saves the key people in their plan
   (executor, POA, doctor, etc.): name, role, contact info. Private to the member;
   no sharing/permissions in this version.
4. **Google SSO** — "Sign in with Google" alongside the existing email-code login.

### User stories

- *As a visitor*, I can read exactly what data the product collects and what it
  does with it, before signing up.
- *As a member*, I can delete my account and all my data in under a minute,
  without emailing support.
- *As a member*, I can record who my trusted people are so my playbook is
  actionable, and see them in my downloaded PDF.
- *As a member (55+, password-fatigued)*, I can sign in with my Google account in
  two clicks.

## Assumptions (correct these before approving)

1. **No cookie banner is needed.** Verified: the frontend sets no cookies — only
   `localStorage` for the session token, theme, and progress (all strictly
   functional). We disclose this in the Privacy Policy instead of building a
   consent banner. If analytics are ever added, that decision reopens.
2. **Legal pages ship as static HTML** in `frontend/public/` (`/privacy.html`,
   `/terms.html`) so they're crawlable/linkable without adding a router to the
   SPA (App.jsx is view-state based, no react-router). Footer + signup/checkout
   link to them.
3. **Legal text is drafted by us for review** — accurate to what the app actually
   does, but flagged "not attorney-reviewed" until Niki signs off / counsel reads it.
4. **Delete = hard delete** across users, sessions, usage, saved plans, chat
   history, and trusted people, in all three store backends. If a Stripe
   subscription is live, we cancel it first; remaining paid time is forfeited
   (warned in the confirm step). Stripe's own records (invoices) are retained by
   Stripe per their policy — disclosed in the Privacy Policy.
5. **Trusted people live in the member's saved-plan record** (existing
   `get_plan`/`save_plan` seam) — no new tables. Available to **logged-in free
   users too** (it drives account creation; sharing/family seats stay paid-roadmap).
6. **Google SSO uses Google Identity Services** (ID-token flow): frontend button →
   ID token → backend verifies signature + audience → issues the same session
   token email-code login issues. Accounts are keyed by email, so a Google
   sign-in with the same address is the same account. New config: `GOOGLE_CLIENT_ID`
   (backend + frontend); feature hidden when unset.
7. **Additive only** — no changes to `MemberContext`, the rules engine, or the
   content library. Nothing here touches clinical logic.

## Tech Stack

Existing only: FastAPI + Pydantic (backend), Vite + React (frontend), store
abstraction (memory/sqlite/dynamodb). One new backend dependency allowed for SSO
token verification (`google-auth`) — see Boundaries.

## Commands

```text
Backend dev:   cd agent && python -m uvicorn app.main:app --port 8001
Backend tests: cd agent && pytest tests/ -v
Frontend dev:  cd frontend && npm run dev        # http://localhost:3200
Frontend build: cd frontend && npm run build
```

## Project Structure (touched by this spec)

```text
agent/app/api/routes/auth.py        → add DELETE /api/account, POST /api/auth/google
agent/app/services/                 → account deletion service; google token verify
agent/app/data/store/{memory,sqlite,dynamodb}.py → new delete_user_data(email)
agent/app/data/store/base.py        → contract doc for delete_user_data
agent/app/schemas/requests.py       → GoogleLoginRequest, TrustedPerson
agent/tests/                        → new tests per feature
frontend/public/privacy.html        → static Privacy Policy
frontend/public/terms.html          → static Terms of Use
frontend/src/components/Settings.jsx → Delete account flow (mirrors cancel-sub pattern)
frontend/src/components/LoginModal.jsx → Google button (when configured)
frontend/src/components/TrustedPeople.jsx → new; editor + list
frontend/src/api/client.js          → deleteAccount(), googleLogin(), trusted people calls
```

## Code Style

Follow the file you're editing. Reference pattern — routes stay thin, service does
the work, store does persistence:

```python
# routes/auth.py
@router.delete("/account")
def delete_account(email: str = Depends(require_email)):
    accounts.delete_account(email)          # service: Stripe cancel + store wipe
    return {"deleted": True}
```

Frontend: existing conventions — function components, `fp-` CSS classes, phase
state machines for multi-step flows (see `Settings.jsx` cancel flow).

## Testing Strategy

`pytest` in `agent/tests/`, in-memory store (conftest already forces it). No API
key needed; SSO verification tests mock the Google cert check. Required coverage:

- Delete: wipes every store surface; second call is a safe no-op; requires auth;
  sessions invalid immediately after.
- Trusted people: CRUD round-trip; free logged-in user allowed; anonymous 401;
  deleted with the account.
- Google SSO: valid mocked token → session; wrong audience/expired → 401;
  endpoint 404/disabled when `GOOGLE_CLIENT_ID` unset.
- Legal pages: exist in `frontend/public/`, linked from footer (manual check).

## Boundaries

- **Always:** run `pytest tests/ -v` before commit; keep brand text in
  `branding.js`/`config.py`; server-side enforcement for anything gated.
- **Ask first:** adding any dependency beyond `google-auth`; any change to
  Stripe webhook logic; changing the store contract beyond `delete_user_data`;
  publishing the legal pages' claims (Niki reviews text before deploy).
- **Never:** soft-delete masquerading as delete; collect new personal data not
  disclosed in the Privacy Policy; touch rules engine / content library /
  `MemberContext`; commit secrets.

## Success Criteria

1. `/privacy.html` and `/terms.html` are publicly reachable on the deployed site,
   linked in the app footer and on signup/checkout; content matches actual app
   behavior (localStorage, email codes, Stripe, Anthropic processing, deletion).
2. A logged-in member can delete their account from Settings with a typed
   confirmation ("DELETE"); afterwards their email, sessions, usage, plan, chat,
   and trusted people are gone from the store, and any live Stripe subscription
   is canceled. Verified by automated test in all — memory at minimum — backends.
3. A logged-in member (free or paid) can add/edit/remove trusted people
   (name, role, phone/email, notes ≤ 500 chars each, max 10 people) and they
   render in the downloaded PDF.
4. With `GOOGLE_CLIENT_ID` set, "Continue with Google" appears in the login modal
   and produces a working session; unset, the UI shows email-code login only and
   the endpoint is disabled.
5. All existing 28 tests still pass; new tests cover the four features.

## Resolved Decisions (Niki, 2026-07-20)

1. **Legal entity: ENDevo Inc.** Master privacy policy exists at
   `endevo.life/legal/privacy-policy` (effective 2026-02-11, contact
   `privacy@endevo.life`). Final Playbook pages are product-specific supplements
   under ENDevo Inc. that link to the master policy. Where Final Playbook is
   stricter than the master policy (no cookies, no analytics, no ad tech in this
   app), the product page says so explicitly — that's a selling point.
2. **Mid-cycle deletion: forfeit remaining paid time**, with a clear warning in
   the confirm step. No proration at launch.
3. Trusted people appear wherever the member can already download the PDF.

## Open Questions

(none — spec approved 2026-07-20, proceeding to plan)

# Acceptance Criteria — `feat/mvp-market-ready`

**Branch:** `feat/mvp-market-ready`
**Product:** My Final Playbook (B2C, free + paid $25/mo)
**Status as of 2026-07-08:** deployed to AWS dev, tested locally. Not yet merged to `main`.

This document is the acceptance criteria (AC) for everything built on this branch.
Each AC is written **Given / When / Then** so it can be checked off. Copy-paste
this whole file into a Notion page (Notion imports Markdown headings, tables, and
checkboxes natively).

---

## How to use this in Notion

1. In Notion: **New page → type `/import` → Markdown**, or just **paste** this file's
   contents into an empty page (Notion converts `#` headings, tables, and `- [ ]`
   checkboxes automatically).
2. The `- [ ]` items become real Notion checkboxes you can tick as each AC passes.
3. Link the page to the branch/PR: add a **URL property** on the page (or a callout)
   pointing to the GitHub branch:
   `https://github.com/endevo-life/endevo-finalplaybook-agent-quick-win/tree/feat/mvp-market-ready`
4. Optional: turn the "Epic" table below into a Notion **database** (paste it, then
   "Turn into database") so each epic gets its own status/owner.

---

## Epics shipped on this branch

| # | Epic | Status | Commit |
|---|---|---|---|
| E1 | Layered backend + per-user DynamoDB persistence | ✅ Done | `2509653` |
| E2 | Cognito passwordless auth (email codes) | ✅ Done | `1b5ac6d` |
| E3 | Analytics event stream + admin console | ✅ Done | `1b5ac6d` |
| E4 | Bedrock LLM backend (no API key) | ✅ Done | `d147506` |
| E5 | AWS deploy (SAM) against existing infra | ✅ Done | `f8e253e`, `e486ce8` |
| E6 | Landing explainer video (with music, subtitles) | ✅ Done | `d2b802c`, `1ff7dc9` |
| E7 | "Why now?" avoidance-breaking onboarding | ✅ Done | `3a358f2` |
| E8 | Per-scenario personalized questions (MOAT) | ✅ Done (content: DRAFT) | `0914888` |
| E9 | New-visitor vs returning-user clarity | ✅ Done | `b94ea56` |

---

## E1 — Layered backend + per-user persistence

- [ ] **Given** the app runs with `STORE_BACKEND=dynamodb`, **When** a user completes
      an assessment, **Then** their answers/plan/progress persist to their own record
      and reload on next sign-in (any device).
- [ ] **Given** three store backends (memory/sqlite/dynamodb), **When** any is
      selected, **Then** the app behaves identically (routes never touch a DB directly).
- [ ] Routes stay thin (validate + call a service); business logic in `app/services/`.

## E2 — Cognito passwordless auth

- [ ] **Given** a visitor enters their email, **When** they submit, **Then** a 6-digit
      code is emailed via Cognito + SES (no password).
- [ ] **Given** a new email, **When** they enter it, **Then** the account is created
      silently — same flow as sign-in (no separate "sign up").
- [ ] **Given** a valid code, **When** they enter it, **Then** an app session token is
      minted and they're signed in.
- [ ] **Given** an expired/wrong code, **Then** a clear error appears with a retry path.
- [ ] **KNOWN FIX NEEDED:** the `mfp-dev-auth-create` Lambda's `FROM_EMAIL` must be
      `hello@endevo.life` (a verified SES sender), not an unverified gmail, or emails
      are rejected. See Open Issues.

## E3 — Analytics + admin console

- [ ] **Given** any key action (signup, login, assessment, chat, upgrade), **When** it
      happens, **Then** an event is recorded (best-effort, never breaks the request).
- [ ] **Given** an admin with the token + an allowlisted email
      (`hello@endevo.life`, `bluesproutagency@gmail.com`), **When** they open the
      console, **Then** they see metrics, users, funnel, and can grant/revoke tier.
- [ ] **Given** a non-allowlisted email or wrong token, **Then** access is denied (401).

## E4 — Bedrock LLM backend

- [ ] **Given** `LLM_BACKEND=bedrock`, **When** a paid user generates a narrative or
      chats, **Then** the call runs via AWS Bedrock (Llama 3 8B) with no API key.
- [ ] **Given** the Lambda role, **Then** it has `bedrock:InvokeModel` permission.
- [ ] **NOTE:** Llama is weaker-grounded than Claude for this sensitive content
      (`docs/guardrails.md`). Accepted for now; revisit before scale.

## E5 — AWS deploy (SAM)

- [ ] **Given** `sam deploy`, **When** run, **Then** it provisions only the Lambda +
      HTTP API (the 7 DynamoDB tables + Cognito pool already exist, referenced by name).
- [ ] **Given** the deployed API, **When** `/api/health` is called, **Then** it returns
      `{"ok": true}`.
- [ ] **Given** `/api/assessment`, **Then** it returns the questions (rules engine loads
      the knowledge-base bundled into the Lambda package).

## E6 — Landing explainer video

- [ ] **Given** the landing page, **When** loaded, **Then** the "with music" explainer
      video plays with controls.
- [ ] **Given** the video, **Then** download is disabled and English subtitles are
      available (on by default).

## E7 — "Why now?" onboarding

- [ ] **Given** a new visitor after entering their name, **When** they continue,
      **Then** they see "What brought you here, [name]?" with 10 warm signal cards.
- [ ] **Given** the picker, **When** they tap any (multi-select) or skip, **Then** they
      proceed — no score or judgment is shown.
- [ ] **Given** picked signals, **When** the plan renders, **Then** items in the
      targeted domains lead (e.g. "digital outweighs" → digital items first).
- [ ] **Given** no signals, **Then** doc box + legacy contact still lead (universal
      baseline — the #1 gap across all sessions).

## E8 — Per-scenario personalized questions (the MOAT)

- [ ] **Given** no signals picked, **When** the assessment loads, **Then** only the 9
      universal questions appear (situational ones hidden).
- [ ] **Given** "You became responsible for someone," **Then** guardian questions
      appear and lead.
- [ ] **Given** "Something worth protecting," **Then** the business-succession question
      appears.
- [ ] **Given** "A near miss," **Then** the healthcare-proxy question appears and leads.
- [ ] **Given** the same signals + answers, **Then** the question order is identical
      every time (deterministic/auditable).
- [ ] **CONTENT CAVEAT:** the 4 scenario question clusters are `validated: false`
      DRAFTS (Claude-authored in Niki's voice). **AC not fully met until Niki signs
      off** on the clinical content.

## E9 — New-visitor vs returning-user clarity

- [ ] **Given** the landing hero, **When** viewed, **Then** the primary CTA is for new
      visitors ("start free, no account") and a separate secondary link is for
      returning users ("already made your playbook? sign in").
- [ ] **Given** the two paths, **Then** it's unambiguous which is for whom.

---

## Cross-cutting / non-functional AC

- [ ] `pytest tests/` — 39 passed, 1 skipped (green).
- [ ] `npm run build` — frontend builds with no errors.
- [ ] Free tier works fully anonymous (no login to assess + see plan).
- [ ] Paid gating enforced server-side (client can't fake `tier=paid`).
- [ ] No secrets committed (`.env` gitignored; `.env.example` uses placeholders).
- [ ] Reduced-motion respected; keyboard focus visible on new UI.

---

## Open issues (block full "done")

| Issue | Severity | Fix |
|---|---|---|
| Lambda `FROM_EMAIL` is an unverified gmail → login emails rejected | **High** | Set `FROM_EMAIL=hello@endevo.life` on `mfp-dev-auth-create` (verified SES sender) |
| Scenario questions are `validated: false` drafts | Medium | Niki reviews/signs off the 4 new clusters |
| Content library `_meta.status` still DRAFT | Medium | Clinical sign-off before promoting paid tier |
| Value-first auth reorder (anonymous-through-results) not fully wired | Low | Move email ask to after results |
| Stripe not configured (placeholder) | Low (by choice) | Add keys when billing goes live |

---

## Definition of Done (this branch → merge to `main`)

- [ ] All E1–E9 checkboxes ticked (E8 pending Niki content sign-off).
- [ ] Open issues High + Medium resolved.
- [ ] Tested end-to-end on the deployed API (not just local).
- [ ] PR opened, reviewed, merged to `main`.

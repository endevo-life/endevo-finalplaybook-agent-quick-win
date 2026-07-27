# Spec: Operator Notifications & Member Feedback

Status: **DRAFT — awaiting review**
Created: 2026-07-27
Owner: Nermeen (dev) · Sign-off: Niki

---

## Objective

Two related capabilities the app is missing before launch:

**A. Operator notifications** — the team currently has no idea when someone
signs up unless they open the admin console. We want push, not pull:

1. **Signup alert** — when a new member is created, email the operator list
   with who signed up and what tier they're on.
2. **Weekly summary** — every Monday, email the operator list a digest of the
   week: who signed up, who completed the playbook, who upgraded, conversion.

**B. Member feedback** — members have no way to ask for help, report a
problem, or tell us the product missed. A single form captures all three.

### Why now

Launch is imminent and the team is flying blind on activation. The signup
alert is the smallest thing that makes the funnel *felt* day to day; the
weekly digest is what Kara and Niki can act on without a dashboard login.
Feedback capture matters extra here because the subject matter is sensitive —
if the tone lands wrong for someone, we need to hear it directly and fast.

### Users

| User | Need |
|---|---|
| Niki (founder) | Know a real person signed up; see the week at a glance |
| Kara (marketing) | Weekly numbers for campaign feedback loops |
| Blue Sprout (agency) | Same digest for the shared ops inbox |
| Member | A way to ask for help or complain without leaving the app |

### Recipients (initial, config-driven)

```
niki@finalplaybook.com
hello@endevo.life
bluesproutagency@gmail.com
```

Set via `OPERATOR_EMAILS` (comma-separated). Never hard-coded — same rule as
every other brand/config value in this repo.

---

## Success Criteria

Specific and testable.

### A1. Signup alert
- [ ] A new user completing `POST /api/auth/start` triggers exactly **one**
      email to every address in `OPERATOR_EMAILS`.
- [ ] A **returning** user logging in triggers **zero** emails.
- [ ] The email states: email address, tier (`free`/`paid`), signup timestamp
      (US Pacific), and total signups to date.
- [ ] If SES is unreachable or misconfigured, `/api/auth/start` still returns
      200 and the user can still log in. Failure is logged, never raised.
- [ ] With `EMAIL_BACKEND=console` (default in dev/tests), nothing is sent —
      the payload is logged and recorded so tests can assert on it.

### A2. Weekly summary
- [ ] Runs Mondays 08:00 America/Los_Angeles via EventBridge Schedule.
- [ ] Covers the preceding Mon 00:00 – Sun 23:59 window.
- [ ] Reports: new signups (count + list of emails w/ tier), assessments
      completed, personalizations, chat messages, upgrades, free→paid
      conversion %, and a total-members-to-date figure.
- [ ] Sends even on a zero-activity week (silence is ambiguous; "0 signups" is
      information). Subject line makes the zero explicit.
- [ ] Manually triggerable by an operator: `POST /api/admin/digest/send`.
- [ ] Idempotent per week — re-running for an already-sent week does not
      double-send unless `force=true`.

### B. Feedback form
- [ ] `POST /api/feedback` accepts `{kind, message, email?, rating?, page?}`.
- [ ] `kind` ∈ `help` | `complaint` | `survey`. Rejects anything else with 422.
- [ ] Works **anonymous** (email required in body) **and** **logged-in**
      (email inferred from session; body email ignored).
- [ ] Persists to the store, so nothing is lost if email delivery fails.
- [ ] Emails the operator list; a `complaint` is subject-prefixed so it can be
      filtered/prioritized in an inbox.
- [ ] Rate-limited to 5 submissions per email per hour → 429.
- [ ] **Anonymous** submissions (a survey needs no email) are rate-limited by
      client IP, 10/hour → 429. Without this the public endpoint has no key to
      limit on and can be driven to write rows and send mail without bound.
      The IP is used as an in-process counter key only and is never stored.
- [ ] Message capped at 4000 chars → 422 beyond that.
- [ ] Visible from **both** the marketing surface and inside the member
      experience (see Open Question Q3).
- [ ] Submissions appear in the admin console and in the weekly digest.

---

## Tech Stack

No new runtime dependencies. `boto3` is already present (Cognito, DynamoDB,
Bedrock, Cost Explorer).

- Backend: FastAPI + Pydantic, Python 3.11 (existing)
- Email: **AWS SES v2** via `boto3` — already the delivery path for Cognito
  login codes, so no new vendor, no new secret to manage
- Scheduling: EventBridge Schedule → the existing Lambda (new invoke path)
- Persistence: existing `app/data/store/` (memory | sqlite | dynamodb)
- Frontend: Vite + React (existing)

### Why SES over SendGrid/Postmark
Already in the account and already the sender for auth codes. Adding a second
provider means a second secret, a second deliverability reputation, and a
second thing to debug at 2am. **Cost:** ~$0.10 per 1,000 emails — effectively
free at this volume.

### SES status — RESOLVED (checked live 2026-07-27)
Earlier drafts of this spec treated SES sandbox as a blocker. It isn't: the
account has **production access** (`ProductionAccessEnabled: true`, 50k/day,
`EnforcementStatus: HEALTHY`). Recipients need **no** verification — only the
**sender**.

The real constraint is narrower: `finalplaybook.com` exists as an SES domain
identity but its DKIM/DNS was never completed (`VerifiedForSendingStatus:
false`, `DkimStatus: FAILED`), so `noreply@finalplaybook.com` would fail every
send. `EMAIL_FROM` therefore defaults to **`hello@endevo.life`**, which is
verified and DKIM-signed. Finishing the domain DNS is a nice-to-have, not a
blocker.

Feedback confirmation-to-member remains **out of scope** — not for a technical
reason now, but because member email needs unsubscribe handling, CAN-SPAM
compliance, bounce/complaint processing, and voice sign-off. See Non-Goals.

---

## Architecture

Follows the repo's layered convention: routes stay thin, logic in services,
persistence behind the store.

```
POST /api/auth/start ──┐
POST /api/feedback  ───┼──→ services/notifications.py ──→ data/email.py ──→ SES
EventBridge (weekly) ──┘         (what to say)            (how to send)
                                       │
                                       └──→ services/analytics.py (existing event stream)
```

Two layers, deliberately split:

- **`app/data/email.py`** — *transport only*. Backend-selected exactly like
  `data/store/base.py` and `data/events.py`: `console` (dev/test, records to a
  list), `ses` (production). Knows nothing about signups or digests.
- **`app/services/notifications.py`** — *content*. Builds subject + body for
  each notification type, resolves the recipient list, calls the transport.
  Every public function is best-effort and never raises into a request path.

This mirrors the existing `analytics.emit()` contract, which already swallows
errors so a metrics failure can't break a user request. Same principle: **an
email failure must never cost us a signup.**

### New store methods

Added to all three backends (memory, sqlite, dynamodb) per the store contract
in `base.py`:

```
save_feedback(email, kind, message, rating, page) -> dict
list_feedback(limit=100, since=None) -> list
get_config / set_config          # already exist on the events store — reused
                                 # for the digest's last-sent watermark
```

### Files

```
NEW  agent/app/data/email.py                    transport (console | ses)
NEW  agent/app/services/notifications.py        content + recipients
NEW  agent/app/services/feedback.py             validation, rate limit, persist
NEW  agent/app/api/routes/feedback.py           POST /api/feedback
NEW  agent/tests/test_notifications.py
NEW  agent/tests/test_feedback.py
NEW  frontend/src/components/FeedbackModal.jsx
EDIT agent/app/config.py                        OPERATOR_EMAILS, EMAIL_BACKEND,
                                                EMAIL_FROM, SES_REGION, DIGEST_*
EDIT agent/app/api/routes/auth.py               fire signup notification
EDIT agent/app/api/routes/admin.py              digest send + feedback list
EDIT agent/app/main.py                          register feedback router
EDIT agent/app/data/store/{memory,sqlite,dynamodb}.py   feedback methods
EDIT agent/lambda_handler.py                    EventBridge event branch
EDIT infra/template.yaml                        SES policy, schedule, env vars
EDIT frontend/src/api/client.js                 submitFeedback()
EDIT frontend/src/components/{TopNav,Landing}.jsx       entry points
EDIT docs/  +  DEPLOY.md                        runbook: SES verification
```

---

## Commands

```
Backend dev:   cd agent && python -m uvicorn app.main:app --port 8001
Backend test:  cd agent && pytest tests/ -v
Frontend dev:  cd frontend && npm run dev          # http://localhost:3200
Frontend build:cd frontend && npm run build
Digest manual: curl -X POST localhost:8001/api/admin/digest/send \
                 -H "Authorization: Bearer $ADMIN_TOKEN"
```

---

## Configuration

All new env vars, defaulting to safe/dev values:

| Var | Default | Purpose |
|---|---|---|
| `EMAIL_BACKEND` | `console` | `console` \| `ses`. Console = log only, never sends. |
| `OPERATOR_EMAILS` | *(empty)* | Comma-separated recipients. Empty = no-op. |
| `EMAIL_FROM` | `noreply@finalplaybook.com` | SES verified sender identity |
| `SES_REGION` | `AWS_DEFAULT_REGION` or `us-east-1` | |
| `DIGEST_ENABLED` | `true` | Kill switch for the weekly job |
| `DIGEST_TIMEZONE` | `America/Los_Angeles` | Window + display timestamps |

**Default is safe:** with nothing configured, `EMAIL_BACKEND=console` and an
empty `OPERATOR_EMAILS` mean the entire feature is inert. Tests pass, local dev
sends nothing, no accidental email to real people from a dev laptop.

---

## Code Style

Matches the existing service layer — module docstring explaining *why*,
best-effort error handling, no exceptions escaping into request paths:

```python
"""Operator notifications: signup alerts and the weekly digest.

Content lives here; transport lives in app/data/email.py. Both are
best-effort by contract -- exactly like analytics.emit(). A failed send must
never cost us a signup, so every public function swallows and logs.
"""

def notify_signup(email: str, tier: str = "free") -> bool:
    """Alert operators that a new member signed up. Returns True if handed to
    the transport. Never raises."""
    try:
        recipients = operator_emails()
        if not recipients:
            return False          # unconfigured -- inert by design
        return send_email(
            to=recipients,
            subject=f"[{PRODUCT_NAME}] New signup: {email}",
            body=_signup_body(email, tier),
        )
    except Exception as exc:
        log.warning("signup notification failed for %s: %s", email, exc)
        return False
```

Conventions carried from the repo:
- Module docstrings explain the *why*, not the *what*
- Store methods added to **all three** backends, never just one
- Routes validate and delegate; no business logic, no direct store access
- No brand strings hard-coded — read `PRODUCT_NAME` from `config.py`

---

## Testing Strategy

`pytest`, tests in `agent/tests/`, `conftest.py` already forces the in-memory
store. **Everything must pass with no API key and no AWS credentials** — the
current 28-test suite does, and that property is worth protecting.

`EMAIL_BACKEND=console` records sends to an inspectable list, so tests assert
on real payloads without a network call or a mock library.

| Test | Asserts |
|---|---|
| `test_signup_sends_one_email` | New user → 1 send, correct recipients |
| `test_returning_login_sends_nothing` | Second `/auth/start` → 0 sends |
| `test_signup_email_contains_tier` | Body includes tier + timestamp |
| `test_email_failure_does_not_break_signup` | Transport raises → still 200 |
| `test_unconfigured_recipients_is_noop` | Empty `OPERATOR_EMAILS` → no send |
| `test_digest_window_and_counts` | Seeded events → correct weekly numbers |
| `test_digest_zero_activity_still_sends` | Quiet week → still delivered |
| `test_digest_idempotent_per_week` | Double-run → 1 send unless forced |
| `test_feedback_anonymous_and_authed` | Both paths persist + notify |
| `test_feedback_invalid_kind_422` | Bad `kind` rejected |
| `test_feedback_rate_limited` | 6th in an hour → 429 |
| `test_feedback_persists_when_email_fails` | Stored even if SES dies |

Target: **12+ new tests, suite stays green with zero credentials.**

Manual verification before merge:
1. `EMAIL_BACKEND=ses` against verified sandbox identities — confirm all three
   addresses actually receive the signup alert
2. Trigger the digest manually via the admin endpoint, eyeball the numbers
   against the admin dashboard
3. Submit each of the 3 feedback kinds from the UI, logged-in and anonymous

---

## Boundaries

**Always:**
- Run `pytest tests/ -v` before committing
- Keep every send best-effort — never raise into a request path
- Add new store methods to all three backends
- Read recipients/brand from `config.py`, never hard-code
- Persist feedback *before* attempting to email it

**Ask first:**
- Emailing **members** (not operators) — needs SES production access + a
  reviewed voice, and this app's tone is sensitive
- Any new dependency
- Changing the DynamoDB table set in `template.yaml`
- Adding PII beyond email address to notification bodies

**Never:**
- Put a member's plan answers or narrative in an operator email — it's
  end-of-life planning content; the signup alert gets an address and a tier,
  nothing more
- Send email from the test suite or from local dev by default
- Let an SES failure surface as a user-facing error
- Commit SES credentials (IAM role on Lambda, no keys)

### Privacy note
Members answer questions about death, family, and finances. Operator emails
carry **identity only** (email + tier + timestamps). Feedback emails carry what
the member chose to write to us. Nothing from the assessment ever leaves the
system in an email. This is a hard line, not a preference.

---

## Non-Goals (this iteration)

- Member-facing welcome email (blocked on SES production access; separate spec)
- Unsubscribe / preference management (internal recipients only)
- HTML email templates — plain text first; it's an ops alert, not a campaign
- Slack/SMS notification channels
- Per-recipient digest customization
- Replying to feedback in-app (operators reply from their inbox for now)

---

## Risks

| Risk | Impact | Mitigation |
|---|---|---|
| SES sandbox blocks delivery | High — feature silently does nothing | Verify the 3 addresses first; log every send outcome; admin console shows last-send status |
| Signup alert becomes noise at volume | Medium | Digest already covers volume; add a daily-rollup threshold if signups exceed ~20/day |
| Feedback form gets spammed | Medium | Rate limit + length cap; add a honeypot field if abused |
| Lambda cold start on the schedule | Low | Digest is async; a few seconds is irrelevant |
| Weekly job double-fires | Low | Watermark in the config store makes it idempotent |

---

## Decisions (resolved 2026-07-27)

**D1. Signup alert cadence.** ✅ **One email per signup.** Volume is low and
each signup is worth knowing about individually. Documented threshold: revisit
a daily rollup if signups exceed ~20/day.

**D2. Digest day/time.** ✅ **Monday 08:00 America/Los_Angeles** — the week's
numbers land before Monday planning.

**D3. Feedback form placement.** ✅ **Both.** A persistent "Help / Feedback"
link in `TopNav` (every screen, logged in or not) plus a footer link on
`Landing`. Rationale: a complaint most often comes from someone who is stuck,
and someone who can't log in is exactly the person who most needs to reach us.
The form adapts — logged-in submissions attach the session email automatically.

**D4. Survey scope.** ✅ Optional `rating` (1–5) **plus** free text, so one
form serves as both a quick pulse and an open comment box.

**D5. Digest includes feedback.** ✅ **Yes** — submission counts by kind, with
complaint subject lines inline. Complaints are the highest-signal item in any
given week.

**D6. SES sandbox.** ✅ **Build now, verify later.** Everything ships and
merges with `EMAIL_BACKEND=console` (fully tested, sends nothing). Niki
verifies the three operator addresses as SES identities, then flips
`EMAIL_BACKEND=ses`. Production access is only needed if we later email
members — out of scope here.

## Open Questions

**Q1. Sender address.** `noreply@finalplaybook.com` — does that domain have SES
DKIM configured, or should the initial sender be an already-verified address?
*Not blocking:* `EMAIL_FROM` is config-driven, so this is a deploy-time value,
not a code change.

---

## Implementation Order

Sequenced so each phase is independently verifiable. Detail in `tasks/todo.md`.

1. **Transport + config** — `data/email.py`, config vars, console backend, tests
2. **Signup alert** — `services/notifications.py`, wire into `auth.py`, tests
3. **Feedback backend** — store methods, service, route, tests
4. **Feedback UI** — modal + entry points, wired to the API
5. **Weekly digest** — aggregation, admin trigger, idempotency, tests
6. **Infra** — SES policy, EventBridge schedule, template env vars
7. **Docs** — DEPLOY.md SES runbook, docs/ update

Phases 1–4 ship independently of any AWS change: they're testable and
mergeable with `EMAIL_BACKEND=console`. Only phases 5–6 need SES verified.

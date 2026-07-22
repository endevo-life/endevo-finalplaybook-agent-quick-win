# Launch Plan & Audit Record — July 16, 2026

Session record: full launch-readiness audit + revenue model + meeting decisions +
ordered implementation plan. Review this, then work top-down through §8.

---

## 1. Decisions locked in (Kara & Niki meeting, 2026-07-16)

| Decision | Detail |
|---|---|
| **URL** | The B2C app ships at the **root domain `finalplaybook.com`** (not app.finalplaybook.com as GO-LIVE-runbook assumed). Existing lead-magnet page moves to a sub-path (e.g. `/main-page`) with **301 redirects** to preserve SEO. `www` redirects to root. API stays on the execute-api URL. |
| **Pricing** | **$25/month approved.** Matches `agent/app/services/plans.py:49`. Partner opportunity: offer the micro-SaaS to partners like Beacon (see `docs/moat-b2b/`). |
| **Churn** | Referral program ("recommend a friend" links, coupon codes). Kara consulting Andrea; design discussion on the Tuesday call. |
| **Team** | GHL specialist onboarding = Nermeen's central contact. Content production in Notion. Andrea (design), Jelay (content), Che (podcast). Tuesday = team ideation; Thursday = Kara/Niki 1:1. |

**Nermeen's immediate actions:** email Kara the final URL structure (proposal above);
meet Niki to approve pending items — put **content sign-off** and the **landing
voice decision** (§5) on that agenda.

---

## 2. Launch verdict

**Free tier: can launch within days** after Phase-0 fixes (§8 items 6, 11–15) +
legal pages + cert/DNS.
**Paid tier: NOT ready to charge money** — six hard blockers (§4), plus content
sign-off (§5).

---

## 3. Revenue model ($25/mo recurring)

Unit costs per paid user: Stripe ~$1.03, LLM $0.10–$0.70 worst case (quota:
30 personalizations + 200 chat/mo), AWS ~$0.05–$0.30 → **~92–95% gross margin**.

| Paid subs | MRR | ARR |
|---|---|---|
| 50 | $1,250 | $15,000 |
| 100 | $2,500 | $30,000 |
| 250 | $6,250 | $75,000 |
| 500 | $12,500 | $150,000 |
| 1,000 | $25,000 | $300,000 |

Realistic funnel: 5,000 visitors/mo → ~30% complete assessment → ~3% upgrade =
**~45 new paid/mo**. At 8%/mo churn that plateaus ~560 subs ≈ **$14K MRR / $168K ARR**.

### The completion-problem fix (churn strategy)

Core reframe: sell **"your playbook stays true"**, not "finish your playbook."
A playbook decays (divorce, moves, kids turn 18, passwords change) — the
subscription pays for keeping it current.

Levers and projected effect (illustrative, assumptions labeled):

| Scenario | Assumptions | Plateau | Revenue |
|---|---|---|---|
| A. Baseline | 45 adds/mo, 8% churn | ~560 | ~$14K MRR / $168K ARR |
| B. + Annual plan ($199/yr default) | 50% annual, 65% renew | ~780 | ~$16K MRR / $195K ARR |
| C. + Retention loop | monthly churn 8→5%, renewal 65→75% | ~1,200 | ~$25K MRR / $300K ARR |
| D. + Funnel (scripts, SEO, referral) | adds 45→65/mo | ~1,750 | ~$36K MRR / $440K ARR |

Retention loop build order: annual plan → freshness dates on seals → yearly
review engine (EventBridge + SES) → life-change re-assessment (why-now signals
un-seal domains, zero LLM) → trusted-person share → document vault (phase 2).
B2B (moat-b2b docs / Beacon) sits above all of this: institutional annual
contracts sidestep consumer churn entirely.

Referral mechanics that fit the existing code: `allow_promotion_codes=True` on
the Checkout session (coupons, zero UI); referral links = `ref` param captured
at signup → stored on user → reward on referee's first payment via the existing
Stripe webhook.

---

## 4. Payment blockers (before charging money)

1. `ALLOW_DEV_UPGRADE=true` hardcoded in prod deploy (`.github/workflows/deploy.yml:74`)
   — anyone can self-upgrade free. Must be `false`.
2. Upgrade CTA opens a **fake DemoCheckout** (prefilled 4242 card) — real Stripe
   hosted Checkout only as fallback (`frontend/src/App.jsx:82-96`,
   `frontend/src/components/DemoCheckout.jsx`). Replace with real Checkout.
3. **No working cancellation** — Settings cancel calls a dev-only downgrade that
   never touches Stripe (`agent/app/api/routes/billing.py:39-58`); no customer
   portal implemented. Stripe would keep charging with no way out.
4. **No live Stripe credentials** — `StripeSecretKey/PriceId/WebhookSecret` blank
   in `infra/template.yaml:48-61`, not passed by deploy.yml. No product/price/
   webhook exists yet. ⚠ `DEPLOY.md:30,163` still says **$9/mo** — create at $25.
5. **Webhook fails open** — no secret ⇒ unverified JSON parsed
   (`agent/app/services/billing.py:78-81`); forged POST grants paid. Fail closed.
6. **No Privacy Policy / Terms pages** — legally required (stored PII) and
   demanded by Stripe. No `/privacy` or `/terms` routes exist.

Also: rotate the weak admin token (flagged in `docs/GO-LIVE-runbook.md`), and
content sign-off (§5).

---

## 5. Security & privacy audit findings

### Critical
- **C1** Login codes returned in API response by default — `AUTH_RETURN_CODE`
  defaults `true` in `agent/app/config.py:65`; forgotten env var = account
  takeover of any email. Flip default to `false`.
- **C2** No brute-force protection on 6-digit login codes
  (`agent/app/services/auth.py:44-54`) — unlimited attempts, 15-min window.
  Add 5-attempt lockout + rate limiting.
- **C3** **No data-deletion path anywhere.** Only `delete_session` exists.
  Emails, health/financial answers, plans, chat, analytics events — all
  plaintext, keyed by email, permanent. GDPR/CCPA erasure violation. Build
  `DELETE /api/me` cascading across all 7 tables (incl. events).

### High
- Webhook fail-open (see §4.5).
- Cognito Lambda **prints live sign-in codes to CloudWatch unconditionally**
  (`infra/lambdas/auth-create/index.py:124`). Remove; scrub logs.
- **No API Gateway throttling / rate limiting anywhere** — auth + LLM endpoints
  open to abuse and cost amplification.
- CORS falls open to any localhost origin when `ALLOWED_ORIGINS` unset
  (`config.py:61`). Fail closed in prod.
- No Privacy Policy / Terms (see §4.6).

### Medium
- No security headers (HSTS/CSP/X-Frame-Options) while session token sits in
  `localStorage` for 30 days — XSS steals a month-long session. Add headers;
  consider HttpOnly cookie.
- Admin console (exposes every user's email/answers/plan) gated by one static
  token, non-constant-time compare, no lockout; `.env.example:82` ships real
  internal emails.
- DynamoDB encryption/PITR/TTL outside IaC, unverifiable; IAM allows `Scan`.

### Data inventory (for the privacy policy)
Stored (all plaintext, keyed by email, none deletable today): email, assessment
answers (health/financial/family), generated plan + typed field values, full
chat history (also sent to Anthropic API for paid chat), usage counters, Stripe
customer ID, per-email analytics events. Card data never touches the app
(Stripe-hosted). No hardcoded secrets found; entitlements properly server-side.

---

## 6. Content & tone audit (Niki's voice)

- **Nothing member-facing is signed off**: `content-library.json._meta.status` =
  DRAFT; all 27 glossary entries + all assessment questions `"validated": false`;
  why-now ordering provisional. **Niki's sign-off is the content gate.**
- **Voice split**: the Jesse system prompt
  (`agent/app/agent/prompts/jesse_system.txt`) forbids dread-framing, but
  `Landing.jsx:32` hero is *"When you're gone, will your family be locked out of
  everything?"* + a FEARS array. Decide which voice wins. Suggested no-dread
  hero: *"Make sure the people you love can find what they need. Your accounts,
  your wishes, your plan — in one place they can actually reach."*
- **Legal-advice softening needed** (these render verbatim in the free UI,
  bypassing the LLM warmth pass): "These override what your will says" (glossary
  + FIN_beneficiaries); "Do NOT name minor children directly as beneficiaries…
  assets need a trust or UTMA" (young-children specialNote) → reframe as "raise
  with an estate attorney."
- Sample rewrites in Niki's voice (8 produced in audit; representative):
  - Credit freeze: *"If you're not about to apply for anything, freezing your
    credit is a simple, free layer of protection — and you can lift it any time."*
  - Directive steps: *"Note the kinds of care you'd want or would rather skip
    (things like being kept on a breathing machine, or care focused on comfort).
    Your doctor can walk you through the specifics."*
  - Funeral keyLine: *"The kindest time to plan is now, while it's calm — not in
    the middle of grief."*
- Full reworded pass of the library: do it as a reviewable diff AFTER/alongside
  Niki's sign-off so she approves one coherent version.

---

## 7. Personalization — intention→action gaps

Strong already: per-step checkboxes, playbook builder, seals/badges, PDF export.
Gaps are at the edges:

1. No commitment capture (no "when/who" per action; calendarAnchoring rule unimplemented).
2. Zero re-engagement (no reminders/email; member who closes the tab is never contacted).
3. Guide never asks returning members "what did you finish?" (library rule says to).
4. **Conversation scripts invisible to free users** — `ActionCard.jsx` never
   renders `item.script`; highest-conversion asset hidden.
5. Sealing a domain is a dead end — no "next domain is 2 steps away" handoff.
6. Paid 7-day narrative is read-once static text, unlinked to trackable items.

Five zero-LLM-cost improvements (all deterministic, content already exists):
show scripts on free cards; add "when" + review-date fields (date-input machinery
exists); cross-answer synthesis rules in `build_domain_plan` (source: the 8
**dormant** situationProfiles — built + tested but unreachable from the live
flow); let why-now signals inject profile actions (not just reorder); next-tranche
reveal on seal.

---

## 8. Ordered implementation plan (work top-down)

### Business (this week)
1. Email Kara final URL structure (root=app, /main-page=lead magnet+301s, www→root, API on execute-api).
2. Niki meeting: content sign-off + landing voice decision.
3. Tuesday call: referral shape the webhook supports (ref param → user → reward on first payment).

### Five-minute code wins
4. DEPLOY.md: $9/mo → $25/mo (before Stripe Price creation).
5. `allow_promotion_codes=True` in Checkout (`billing.py`).

### Payment blockers
6. `ALLOW_DEV_UPGRADE=false` in deploy.yml:74.
7. Replace DemoCheckout with real Stripe hosted Checkout.
8. Stripe customer portal / real cancellation.
9. Live Stripe product/price/webhook + secrets through deploy; webhook fails closed.
10. Privacy Policy + Terms pages.

### Security criticals
11. `AUTH_RETURN_CODE` default → false (config.py:65).
12. Login-code lockout (5 attempts) + rate limiting on /api/auth/*.
13. `DELETE /api/me` cascade delete (all 7 tables incl. events).
14. Remove code `print` from auth-create Lambda; scrub CloudWatch.
15. Rotate admin token; security headers; consider HttpOnly cookie.

### Hosting at finalplaybook.com (root)
16. ACM cert (root + www, us-east-1); Route 53 ALIAS (apex can't CNAME);
    CloudFront `Aliases` + cert in `infra/frontend.yaml:38-65`.
17. /main-page routing + 301s; `AllowedOrigins`/`AppBaseUrl` →
    https://finalplaybook.com (deploy.yml:75-76); OG/Twitter tags in index.html.

### Retention & personalization (post-blockers)
18. Annual plan $199/yr default-selected (plans.py + 2nd Stripe Price + Pricing.jsx toggle).
19. Freshness dates on seals (amber after 12 mo) — completion.js.
20. Yearly review engine: review-date capture + EventBridge Lambda + SES email.
21. Life-change re-assessment via why-now signals (un-seal + inject profile actions).
22. Surface `item.script` on free ActionCards.
23. Trusted-person read-only share; document vault phase 2.

---

*Generated from the 2026-07-16 audit session (three parallel audits: security/
privacy, launch readiness, content/personalization). Cross-check against
`docs/GO-LIVE-runbook.md`, which independently flags several of the same items —
but note the runbook's app.finalplaybook.com assumption is superseded by the
root-domain decision in §1.*

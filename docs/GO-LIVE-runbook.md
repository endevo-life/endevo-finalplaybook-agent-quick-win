# Go-Live Runbook — My Final Playbook

The ordered path from working demo to a live product real people can pay for.
Each item says **who** does it (You / Me / Niki) and whether it **blocks launch**.

Current live URLs:
- App: `https://d3m7jok0qoyofy.cloudfront.net` (temporary — replaced by custom domain)
- API: `https://xlzj6dntz0.execute-api.us-east-1.amazonaws.com`

You already own **finalplaybook.com** and **endevo.life** (both SES-verified), so
no domain purchase is needed.

---

## Phase 0 — Flip the prod-safe switches (do first, ~15 min)

These are unsafe defaults left on for the demo. Close them before any real user.

| # | Item | Who | Blocks? |
|---|---|---|---|
| 0.1 | **Disable `ALLOW_DEV_UPGRADE`** — right now anyone can self-upgrade to paid for free. Set to `false` in prod (redeploy backend without it). | Me | 🔴 Yes |
| 0.2 | **Rotate the admin token** — it's `bluesprout` on a public `/admin.html`. Set a strong secret in GitHub Secrets + redeploy. | Me + You | 🔴 Yes |
| 0.3 | **Confirm SES not in sandbox** — verify login codes email to ANY address, not just verified ones. | You | 🔴 Yes |

---

## Phase 1 — Legal (required before taking money or storing PII)

You store emails + health/financial answers. Privacy Policy + Terms are legally
required and demanded by Stripe.

| # | Item | Who | Blocks? |
|---|---|---|---|
| 1.1 | **Write/approve Privacy Policy + Terms.** Use a generator (Termly, iubenda) or a lawyer. Must cover: what data you store (email, answers, plan), that it's educational-not-advice, data deletion, cookies. | You | 🔴 Yes |
| 1.2 | **Add /privacy + /terms pages** to the app + footer links. | Me (shells) | 🔴 Yes |
| 1.3 | **Disclaimer visible** ("educational only, not legal/financial/medical advice") — already in the app; confirm it's on the landing + results. | Me (verify) | 🟡 |

---

## Phase 2 — Payments (the revenue blocker)

Today the app uses a SIMULATED checkout. Real money needs Stripe.

| # | Item | Who | Blocks? |
|---|---|---|---|
| 2.1 | **Create a Stripe account** (dashboard.stripe.com). | You | 🔴 Yes |
| 2.2 | **Create a $25/mo recurring Price** → copy the `price_...` id. | You | 🔴 Yes |
| 2.3 | **Get the API keys** (`sk_test_...` first, then `sk_live_...`). | You | 🔴 Yes |
| 2.4 | **Replace demo checkout with real Stripe Checkout** + verify the webhook. | Me | 🔴 Yes |
| 2.5 | **Add the webhook endpoint** in Stripe → `https://<api>/api/billing/webhook`, events `checkout.session.completed` + `customer.subscription.deleted`. Copy `whsec_...`. | You | 🔴 Yes |
| 2.6 | **Test with a test card** (`4242...`) end to end before going live. | Me + You | 🔴 Yes |
| 2.7 | **Add a Stripe billing portal** link in Settings (real cancel/manage) — replaces the demo cancel. | Me | 🟡 |

---

## Phase 3 — Custom domain (trust + memorability)

Move off the random CloudFront URL to `app.finalplaybook.com`.

| # | Item | Who | Blocks? |
|---|---|---|---|
| 3.1 | **Request an ACM certificate** for `app.finalplaybook.com` in **us-east-1** (CloudFront requires us-east-1). | Me (command) + You (DNS) | 🟡 |
| 3.2 | **Validate the cert** — add the CNAME ACM gives you to your DNS (where finalplaybook.com is hosted). | You | 🟡 |
| 3.3 | **Add the domain as a CloudFront alternate name** + attach the cert. | Me | 🟡 |
| 3.4 | **Point DNS** — CNAME `app.finalplaybook.com` → the CloudFront domain. | You | 🟡 |
| 3.5 | **Update `ALLOWED_ORIGINS` + `APP_BASE_URL`** to the new domain, redeploy. | Me | 🟡 |

---

## Phase 4 — Content sign-off (the MOAT / liability)

| # | Item | Who | Blocks? |
|---|---|---|---|
| 4.1 | **Niki reviews the 11 draft questions + the scenario framing.** They're marked `validated: false`; the library is `_meta.status: DRAFT`. | Niki | 🔴 for PAID tier |
| 4.2 | **Niki reviews the LLM framing** (`agent/app/agent/signals.py`) — the scenario voices. | Niki | 🟡 |
| 4.3 | Flip `_meta.status` to validated once signed off. | Me | 🔴 for paid |

> The free tier can launch on the current draft (it's clearly educational); the
> **paid** tier (personalized advice) should wait for Niki's sign-off.

---

## Phase 5 — Operational readiness (know when it breaks)

| # | Item | Who | Blocks? |
|---|---|---|---|
| 5.1 | **Error monitoring** — Lambda errors → an alert (CloudWatch alarm or Sentry). | Me | 🟡 |
| 5.2 | **Review analytics** — the admin console already tracks signups/conversion; check it works at real volume. | You | 🟡 |
| 5.3 | **Backup/export** — confirm DynamoDB point-in-time recovery is on for the user tables. | Me | 🟡 |

---

## The recommended launch sequence

**Soft launch (free tier only) — fastest to real users:**
1. Phase 0 (prod-safe switches) — Me, today
2. Phase 1 (legal pages) — You approve copy, Me add pages
3. Phase 3 (domain) — nicer URL
4. Launch the FREE tier. Real people, real funnel, $0 to serve, no Stripe/Niki gate needed.

**Then turn on paid:**
5. Phase 2 (Stripe) — once you have the account
6. Phase 4 (Niki sign-off) — before promoting paid
7. Phase 5 (monitoring) — as you scale

This lets you get real users NOW on the free tier while Stripe + Niki happen in
parallel — instead of blocking the whole launch on them.

---

## What unblocks the most, fastest

If you do only three things this week:
1. **Phase 0** (I do it in 15 min — removes the unsafe demo switches)
2. **Legal pages** (you approve generator output, I wire them)
3. **Custom domain** (`app.finalplaybook.com` — you already own it)

That gets a **trustworthy, safe, free-tier product live under your own domain** —
real enough to share widely and start the funnel.

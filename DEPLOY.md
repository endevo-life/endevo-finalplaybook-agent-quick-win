# Deploy runbook — Final Playbook

Takes the app from local dev to a live, market-ready product on AWS. Nothing
here needs to run on your machine before you're ready — you execute these steps
with your own AWS/Stripe accounts. Everything is designed so the app runs
end-to-end **without** billing configured, so you can launch a free tier first
and turn on payments later.

Contents:
1. [What you provide](#1-what-you-provide) — the credentials/accounts only you can create
2. [Local dev](#2-run-it-locally-first)
3. [Deploy the backend (AWS SAM)](#3-deploy-the-backend-aws)
4. [Set up Stripe billing](#4-set-up-stripe-billing)
5. [Deploy the frontend](#5-deploy-the-frontend)
6. [Onboard real users](#6-onboard-real-users)
7. [Go-live checklist](#7-go-live-checklist)

---

## 1. What you provide

These are the things I can't create for you — they need your identity/payment:

| Item | Where | Needed for |
|---|---|---|
| AWS account + IAM user with deploy rights | aws.amazon.com | Backend + DynamoDB |
| Anthropic API key | console.anthropic.com | Paid-tier LLM calls |
| Stripe account + a $9/mo recurring Price | dashboard.stripe.com | Payments (optional at first) |
| A domain name (optional) | any registrar | Branded URL |
| Email sending (optional) | SES / Resend / Postmark | Emailing login codes in prod |

You'll also install two CLIs locally: the [AWS CLI](https://aws.amazon.com/cli/)
and the [AWS SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html).

---

## 2. Run it locally first

Backend (from `agent/`):
```bash
pip install -r requirements.txt
cp .env.example .env          # fill in ANTHROPIC_API_KEY if you want the paid tier
python -m uvicorn api:app --port 8001
```
The store defaults to `memory` — no database needed locally. Run tests with
`pytest tests/ -v` (all pass with no API key; LLM tests auto-skip).

Frontend (from `frontend/`):
```bash
npm install
cp .env.example .env.local    # VITE_API_BASE_URL defaults to http://localhost:8001
npm run dev
```
Open http://localhost:5173. Sign in with any email — in dev the 6-digit login
code is shown right in the modal (no email provider needed).

**Test the paid tier locally without Stripe:** log in, then in a Python shell in
`agent/` run:
```python
from store import get_store
get_store().set_tier("you@example.com", "paid")
```
Refresh — you're now on the paid tier. (In prod this flip is done by the Stripe
webhook instead.)

---

## 3. Deploy the backend (AWS)

The [`infra/template.yaml`](infra/template.yaml) SAM template provisions a Lambda
(the FastAPI app via Mangum), an HTTP API Gateway, and one DynamoDB table with
TTL on sessions.

```bash
cd infra
sam build
sam deploy --guided \
  --parameter-overrides \
    AnthropicApiKey=sk-ant-... \
    AllowedOrigins=https://your-frontend-domain.com \
    AppBaseUrl=https://your-frontend-domain.com
```
`--guided` walks you through stack name/region and saves your answers to
`samconfig.toml` so future deploys are just `sam deploy`.

On success SAM prints an **ApiUrl** output — copy it; the frontend needs it.

> Leave the Stripe params blank for now if you're launching free-tier-only.
> `AUTH_RETURN_CODE=true` (the default) keeps login working before you set up
> email — the code comes back in the API response. Flip it to `false` once
> email delivery is wired up.

---

## 4. Set up Stripe billing

1. In the Stripe Dashboard, create a **Product** → recurring **Price** of $9/mo.
   Copy the `price_...` ID.
2. Add a **webhook endpoint** pointing at `https://<ApiUrl>/api/billing/webhook`,
   subscribed to `checkout.session.completed` and
   `customer.subscription.deleted`. Copy the signing secret (`whsec_...`).
3. Redeploy with the Stripe params filled in:
   ```bash
   sam deploy --parameter-overrides \
     AnthropicApiKey=sk-ant-... \
     StripeSecretKey=sk_live_... \
     StripePriceId=price_... \
     StripeWebhookSecret=whsec_... \
     AllowedOrigins=https://your-frontend-domain.com \
     AppBaseUrl=https://your-frontend-domain.com
   ```
4. Test with a [Stripe test card](https://stripe.com/docs/testing) (`4242...`).
   After checkout the webhook flips the user to `paid`; the UI reflects it on the
   next `/api/me` refresh (the app does this automatically on redirect back).

**Why the webhook, not the redirect?** The redirect can be skipped or forged, so
the webhook is the source of truth for granting/revoking paid access. See
`agent/billing.py`.

---

## 5. Deploy the frontend

The frontend is a static Vite build — host it anywhere (S3+CloudFront, Vercel,
Netlify, Amplify). Set `VITE_API_BASE_URL` to the SAM **ApiUrl** at build time:

```bash
cd frontend
VITE_API_BASE_URL=https://<ApiUrl> npm run build
# deploy the dist/ folder to your host
```

Point `AllowedOrigins` and `AppBaseUrl` (step 3/4) at the frontend's real URL so
CORS and the post-checkout redirect resolve correctly.

---

## 6. Onboard real users

- **Launch free first.** The free tier needs no account and costs $0 to serve —
  it's the top of the funnel. Share the URL; people get a real plan immediately.
- **Turn on paid** once Stripe is live (step 4). The upgrade CTA in the results
  panel and pricing table then drive real checkouts.
- **Emailing login codes:** set `AUTH_RETURN_CODE=false` and add an email step in
  `agent/api.py`'s `auth_start` (send `code` as a magic link via SES/Resend
  instead of returning it). Until then, returned codes work fine for early users.
- **Watch costs:** the free tier is LLM-free; only paid users incur Anthropic
  cost, capped by the monthly quotas in `agent/plans.py`. See `docs/pricing.md`.

---

## 7. Go-live checklist

- [ ] `pytest tests/ -v` green
- [ ] `sam deploy` succeeded; `/api/health` returns `{"ok": true}`
- [ ] Frontend built with the real `VITE_API_BASE_URL`
- [ ] `ALLOWED_ORIGINS` = your frontend URL (not `localhost`)
- [ ] Content library reviewed — `_meta.status` is still **DRAFT** and flags the
      content as pending expert sign-off. **Get sign-off before promoting the
      paid tier** (this is educational, sensitive content — see `docs/guardrails.md`).
- [ ] Stripe in **live** mode (not test) with the live `price_`/`whsec_`
- [ ] Disclaimer visible ("not legal, financial, or medical advice")
- [ ] A privacy policy + terms page linked (you store emails + usage)

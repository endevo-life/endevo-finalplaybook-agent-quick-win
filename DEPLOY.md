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
| Cognito user pool + app client + custom-auth Lambda triggers | AWS Cognito console | Real auth (email login codes) |
| SES sending identity, out of sandbox | AWS SES console | Cognito emailing login codes to any address |
| Stripe account + a $9/mo recurring Price | dashboard.stripe.com | Payments (optional at first) |
| A domain name (optional) | any registrar | Branded URL |

**Auth backend: Cognito.** This app authenticates with AWS Cognito's custom-auth
flow (a Lambda trigger emails a 6-digit code; the app verifies it and mints its
own session). The Cognito pool, app client, and Lambda triggers are **not**
created by `infra/template.yaml` — provision them once, separately, then pass
their IDs to `sam deploy` as parameters (see step 3). `AUTH_BACKEND=local` still
exists as a zero-AWS fallback for local dev/tests, but production runs on
Cognito. See `agent/app/services/auth_cognito.py` for the exact flow.

You'll also install two CLIs locally: the [AWS CLI](https://aws.amazon.com/cli/)
and the [AWS SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html).

---

## 2. Run it locally first

Backend (from `agent/`):
```bash
pip install -r requirements.txt
cp .env.example .env          # fill in ANTHROPIC_API_KEY if you want the paid tier
python -m uvicorn app.main:app --port 8001
```
The store defaults to `memory` — no database needed locally (note:
`.env.example` ships `STORE_BACKEND=dynamodb` as a documentation example; leave
it unset or change it to `memory`/`sqlite` for local dev unless you actually
want to hit AWS). Run tests with `pytest tests/ -v` (all pass with no API key;
LLM tests auto-skip; the test suite always forces `STORE_BACKEND=memory` and
`AUTH_BACKEND=local` regardless of your `.env`, see `agent/tests/conftest.py`).

Frontend (from `frontend/`):
```bash
npm install
cp .env.example .env.local    # VITE_API_BASE_URL defaults to http://localhost:8001
npm run dev
```
Open http://localhost:3200. Sign in with any email — in dev the 6-digit login
code is shown right in the modal (no email provider needed).

**Test the paid tier locally without Stripe:** with `ALLOW_DEV_UPGRADE=true` in
your `.env`, log in and call the dev-upgrade endpoint (see
`agent/app/api/routes/billing.py`), or set the tier directly in a Python shell
from `agent/`:
```python
from app.data.store import get_store
get_store().set_tier("you@example.com", "paid")
```
Refresh — you're now on the paid tier. (In prod this flip is done by the Stripe
webhook instead, and `ALLOW_DEV_UPGRADE` must be `false`.)

---

## 3. Deploy the backend (AWS)

### 3a. Create the Cognito pool once (outside SAM)

`infra/template.yaml` does **not** create the Cognito user pool, app client, or
its custom-auth Lambda triggers (create/define/verify challenge) — those are
created once, by hand or with a separate script, because the trigger Lambdas
need code of their own (emailing the code via SES) that isn't part of this
FastAPI app. Once you have:

- a **user pool** with a `CUSTOM_AUTH` Lambda trigger chain wired up
- an **app client** for that pool (no client secret — the backend calls
  `initiate_auth`/`respond_to_auth_challenge` directly)
- **SES out of sandbox mode** (or every login email will fail to send to
  unverified addresses)

...note the pool ID and client ID; you'll pass them to `sam deploy` below. See
`agent/app/services/auth_cognito.py`'s module docstring for the exact API
calls the backend makes against the pool.

### 3b. Deploy the API + tables

The [`infra/template.yaml`](infra/template.yaml) SAM template provisions a
Lambda (the FastAPI app via Mangum), an HTTP API Gateway, and **seven** prefixed
DynamoDB tables (`{prefix}users/sessions/usage/plans/chat/events/config` — the
last two back the analytics/admin-config store in `agent/app/data/events.py`).

```bash
cd infra
sam build
sam deploy --guided \
  --parameter-overrides \
    AnthropicApiKey=sk-ant-... \
    AuthBackend=cognito \
    CognitoUserPoolId=us-east-1_XXXXXXXXX \
    CognitoClientId=xxxxxxxxxxxxxxxxxxxxxxxxxx \
    CognitoRegion=us-east-1 \
    AdminToken=your-strong-admin-secret \
    AllowedOrigins=https://your-frontend-domain.com \
    AppBaseUrl=https://your-frontend-domain.com
```
`--guided` walks you through stack name/region and saves your answers to
`samconfig.toml` so future deploys are just `sam deploy`.

On success SAM prints an **ApiUrl** output — copy it; the frontend needs it.

> Leave the Stripe params blank for now if you're launching free-tier-only.
> `AuthReturnCode` defaults to `"false"` in the template (prod-safe) — Cognito
> emails the code via SES instead of it coming back in the API response. Only
> set it `true` for a throwaway/demo stack.
> `AdminToken` gates `/api/admin/*` and the admin console
> (`frontend/public/admin.html`) — leave it blank to disable the admin API
> entirely, or set a strong secret to enable it.

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
`agent/app/services/billing.py`. Without `StripeWebhookSecret` set, the webhook
falls back to parsing unverified JSON — fine for local testing, but set the
real signing secret before going live in production.

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
- **Login codes are emailed by Cognito/SES**, not returned in the API response,
  once `AuthReturnCode=false` (the deploy default). No extra wiring needed
  beyond the SES sandbox exit in step 3a.
- **Watch costs:** the free tier is LLM-free; only paid users incur Anthropic
  cost, capped by the monthly quotas in `agent/app/services/plans.py`. See
  `docs/pricing.md`.

---

## 7. Go-live checklist

- [ ] `pytest tests/ -v` green
- [ ] Cognito pool + app client + Lambda triggers created, SES out of sandbox
- [ ] `sam deploy` succeeded with `AuthBackend=cognito` and real Cognito IDs;
      `/api/health` returns `{"ok": true}`
- [ ] Frontend built with the real `VITE_API_BASE_URL`
- [ ] `ALLOWED_ORIGINS` = your frontend URL (not `localhost`)
- [ ] `AdminToken` set to a strong secret (not a placeholder) if the admin
      console (`frontend/public/admin.html`) will be used in prod
- [ ] `ALLOW_DEV_UPGRADE=false` (the template default) — never true in prod
- [ ] Content library reviewed — `_meta.status` is still **DRAFT** and flags the
      content as pending expert sign-off. **Get sign-off before promoting the
      paid tier** (this is educational, sensitive content — see `docs/guardrails.md`).
- [ ] Stripe in **live** mode (not test) with the live `price_`/`whsec_`, and
      `StripeWebhookSecret` set (webhook signature verification is skipped if blank)
- [ ] Disclaimer visible ("not legal, financial, or medical advice")
- [ ] A privacy policy + terms page linked (you store emails + usage)

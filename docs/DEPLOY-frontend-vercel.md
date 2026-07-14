# Deploy the frontend to Vercel (demo URL)

Gets the React app onto an HTTPS Vercel URL, pointed at the live AWS backend.
The backend (Lambda + API Gateway) stays on AWS; only the frontend goes to Vercel.

**Live API base URL:** `https://xlzj6dntz0.execute-api.us-east-1.amazonaws.com`

---

## One-time: the CORS chicken-and-egg

The backend only accepts requests from origins in its `ALLOWED_ORIGINS` env var
(currently `http://localhost:3200`). Once the app is on Vercel, its URL must be
added there or **every API call fails with a CORS error**. But you don't know the
Vercel URL until after the first deploy. So the order is:

1. Deploy to Vercel → get the URL.
2. Add that URL to the backend's `ALLOWED_ORIGINS` (step 4 below).
3. Redeploy the backend (or update the Lambda env directly).

---

## Step 1 — Install the Vercel CLI (one time)

```powershell
npm install -g vercel
```

## Step 2 — Deploy (from the frontend folder)

```powershell
cd frontend
vercel
```

- First run: it asks you to log in (browser), then a few questions —
  **Set up and deploy?** yes · **scope** your account · **link to existing?** no ·
  **project name** `my-final-playbook` · **directory** `./` · **override settings?** no.
- It builds and gives you a **preview URL** like
  `https://my-final-playbook-xxxx.vercel.app`.

## Step 3 — Set the API URL as a Vercel env var

The app needs `VITE_API_BASE_URL` at build time. Set it, then redeploy to prod:

```powershell
vercel env add VITE_API_BASE_URL production
# paste when prompted:  https://xlzj6dntz0.execute-api.us-east-1.amazonaws.com

vercel --prod
```

`vercel --prod` gives you the stable production URL (e.g.
`https://my-final-playbook.vercel.app`). **Copy it** — you need it for CORS.

## Step 4 — Allow the Vercel URL on the backend (fixes CORS)

Replace `<VERCEL_URL>` with your real prod URL (no trailing slash):

```powershell
aws lambda update-function-configuration `
  --function-name "mfp-dev-ApiFunction-f1WA02SeuD1T" `
  --region us-east-1 `
  --environment "Variables={STORE_BACKEND=dynamodb,DDB_TABLE_PREFIX=mfp-dev-,LLM_BACKEND=bedrock,BEDROCK_REGION=us-east-1,BEDROCK_MODEL_ID=us.meta.llama3-1-8b-instruct-v1:0,AUTH_BACKEND=cognito,AUTH_RETURN_CODE=false,COGNITO_USER_POOL_ID=us-east-1_ikCfp5RAL,COGNITO_CLIENT_ID=2hsqh99bm3l6hqj9uskbtbgdgd,COGNITO_REGION=us-east-1,ADMIN_TOKEN=<YOUR_ADMIN_TOKEN>,ADMIN_EMAILS=hello@endevo.life,bluesproutagency@gmail.com,ALLOW_DEV_UPGRADE=true,PRODUCT_NAME=My Final Playbook,ALLOWED_ORIGINS=http://localhost:3200,<VERCEL_URL>,APP_BASE_URL=<VERCEL_URL>}"
```

> ⚠️ Updating the Lambda env directly REPLACES all env vars, so every var must be
> listed (above). The cleaner alternative is to redeploy via SAM with
> `AllowedOrigins` set — see `infra/deploy.ps1` and pass
> `AllowedOrigins="http://localhost:3200,<VERCEL_URL>"` and
> `AppBaseUrl="<VERCEL_URL>"`. **Redeploy via SAM is safer** — it won't drop a var.

### Safer: redeploy backend via SAM with the Vercel origin

```powershell
cd infra
# edit deploy.ps1 defaults OR pass overrides:
.\deploy.ps1 -AllowedOrigins "http://localhost:3200,<VERCEL_URL>" -AppBaseUrl "<VERCEL_URL>"
```

## Step 5 — Test the live demo

1. Open the Vercel prod URL.
2. Landing page loads, video plays.
3. Sign in with a demo account (`demo-free@endevo.life` / `demo-paid@endevo.life`) —
   the code emails via Cognito/SES.
4. If API calls fail: open DevTools → Network. A **CORS error** means step 4's
   origin doesn't exactly match the Vercel URL (check http vs https, trailing slash).

---

## Demo accounts (already created)

| Account | Tier |
|---|---|
| `demo-free@endevo.life` | free |
| `demo-paid@endevo.life` | paid |

Flip them live at `<VERCEL_URL>/admin.html` (admin token + `hello@endevo.life`).

## Redeploying the frontend later

Any change → `cd frontend && vercel --prod`. The env var and CORS stay set.

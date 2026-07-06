# Pricing & feature limits

Market-facing description of the freemium/paid split. The **source of truth**
for the actual numbers is [`agent/plans.py`](../agent/plans.py) — this doc
mirrors it. `/api/pricing` serves the same data to the landing page, so all three
stay in sync.

## Plans

| | **Free** | **Personalized** |
|---|---|---|
| **Price** | $0, forever | $25 / month |
| Situation assessment | ✅ | ✅ |
| Prioritized action plan (rules engine) | ✅ | ✅ |
| Word-for-word conversation scripts | ✅ | ✅ |
| Plain-English definitions | ✅ | ✅ |
| Download plan | ✅ | ✅ |
| See your gaps + first 2 steps | ✅ | ✅ |
| **Full plan (all actions, all domains)** | — (preview only) | ✅ |
| **Track items** (check off, saved progress) | — | ✅ |
| **Build side by side** (steps, scripts, fields) | — | ✅ |
| **AI assistant** (grounded follow-up chat) | — | ✅ |
| AI-personalized "next 7 days" narrative | — | ✅ |
| Account required | No (anonymous) | Yes |
| Monthly plan regenerations | n/a | 30 |
| Monthly chat replies | n/a | 200 |

### Free vs Premium — the split in the product

- **Free = see the gaps.** Take the assessment, see the basics-first steps and
  your single highest-impact action fully. The rest of your personalized plan is
  previewed but **locked**. No tracking, no AI, no build mode. This is the funnel:
  real value (you learn where you're exposed) before paying.
- **Premium = close the gaps.** Full plan unlocked, **item tracking** with saved
  progress, **side-by-side playbook builder** (each action with its steps/scripts/
  fields), and the **AI assistant** grounded in your own plan.

Enforcement is server-side (`entitlements.py`): free users get 402 on paid
features. During pre-launch (Stripe not live yet), `ALLOW_DEV_UPGRADE=true` lets
a logged-in user unlock Premium without payment so the experience is demoable —
this MUST be `false` in production.

## Why this split

- **Free is genuinely useful and costs us $0 to serve.** The entire free
  experience runs on the deterministic rules engine — no LLM call, no per-user
  cost. This is the acquisition funnel: people get real value before paying.
- **Paid is the one place we spend on an LLM.** The personalized narrative is a
  single grounded Claude call (~$0.002–0.006 each — see `docs/prompts.md`), and
  chat is a smaller/cheaper model. The monthly quotas cap the worst-case cost of
  any one account so a $25 subscriber can never run up an unbounded bill.

### Rough unit economics (paid tier)

At the quota ceiling (30 personalizations + 200 chat replies/month), LLM cost is
on the order of **$0.30–$0.70 per paid user per month** against $25 revenue — a
comfortable margin even before most users hit anywhere near their limits. Adjust
the quotas in `plans.py` if real usage differs.

## Enforcement (important)

Tier is **enforced server-side**, not trusted from the client:

- The free tier works anonymously — no account, the rules engine only.
- Paid features require a logged-in user **and** a live `tier == "paid"`
  entitlement in the store (set by a successful Stripe payment via the webhook).
- A free user asking for a paid feature gets **402** (upgrade required); an
  over-quota paid user gets **429** (limit reached). Neither can be bypassed by
  editing the request. See [`agent/entitlements.py`](../agent/entitlements.py).

## Changing prices or limits

1. Edit the numbers in [`agent/plans.py`](../agent/plans.py) (`PLANS`).
2. Update the Stripe **Price** object to match the new dollar amount, and set
   `STRIPE_PRICE_ID` to the new price if you created a new one.
3. This doc and the landing page update automatically from `/api/pricing`.

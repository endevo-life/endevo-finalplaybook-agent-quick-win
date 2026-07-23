# Competitive pricing analysis & launch pricing proposal

**Date:** 2026-07-20 · **Requested by:** Niki (email 2026-07-17, "Competitor analysis ENDevo — Legacy Readiness OS")
**Competitors researched:** EverSettled, DigitalLIFEBox
**Current state:** Free + Personalized $25/mo (`agent/app/services/plans.py`), no annual plan yet.

---

## 1. Competitor pricing (verified from their sites, July 2026)

### DigitalLIFEBox (digitallifebox.com) — digital-asset vault + transfer scheduling

The closest structural comparable: freemium, usage-metered tiers, add-on packs.

| Plan | Monthly | Yearly | Lifetime | Assets | Transfers | Family seats |
| --- | --- | --- | --- | --- | --- | --- |
| Basic (free) | $0 | $0 | — | 5 | 3 (immediate only) | — |
| Standard | $9.99 | $69.99 | $749.99 | 10 / 75 / 850 | 3 / 15 / 150 | 3 |
| Premium | $19.99 | $139.99 | $1,499.99 | 20 / 150 / 1,700 | 7 / 35 / 350 | 5 |

- Yearly is ~**42% off** monthly (they push annual hard).
- **Add-on packs:** 5 assets $7.99 · 5 transfers $7.99 · 20 ops/7 transfers $15.99 · 50 ops/20 transfers $39.99 · extra family member $199.99 (lifetime only). Standard gets 25% off add-ons, Premium 50%.
- Enterprise pricing "on request."
- **What they sell:** storage and transfer of digital assets. **What they don't have:** guidance, prioritized action plans, conversation scripts, an AI guide. They organize *stuff*; we organize *decisions*.

### EverSettled (eversettled.com) — post-death probate/estate settlement

- **$1,499 flat fee, billed to the estate** (no out-of-pocket for the family). AI assistant "Sage" + a dedicated human Estate Care Specialist; asset discovery, subscription cancellation, debt negotiation, all 50 states.
- **In-app self-serve upgrade: ~$199 one-time** for the "full plan" (observed inside the product by Niki, July 2026 — not published on the marketing site). So their real ladder is: free/limited entry → **$199 one-time DIY full plan** → $1,499 full-service. A $199 "full plan" price point is now *validated in this exact category* by a $5M-funded competitor.
- Just raised a **$5M seed led by Emergence Capital** (July 2026) — strong validation that this market is real and fundable.
- **Not a head-to-head competitor.** They monetize *after* death (settlement); we monetize *before* (readiness). Their $1,499 is our best marketing anchor: *"An unsettled estate costs $1,499+ to untangle. Being ready costs $199/year."* They are also a natural future partner/referral (we hand off prepared families; they hand back next-of-kin who realize they should get ready).

---

## 2. Recommended pricing

### Consumer (finalplaybook.com)

| | Free | **Personalized** |
| --- | --- | --- |
| Monthly | $0 | **$25/mo** (keep) |
| **Annual (new — primary CTA)** | — | **$199/yr** (~$16.6/mo, "save 33% — 4 months free") |

**Why:**
- $25/mo holds. DigitalLIFEBox tops out at $19.99 for a passive vault; we ship AI-personalized guidance, scripts, and tracking — a premium over them is defensible, and $25 was already the business decision (2026-07-06).
- **Annual is the plan to sell.** End-of-life planning is a "finish the project" job — monthly subscribers churn as soon as the plan feels done. Annual prepay matches how DLB discounts (~42%) without going that deep, and pairs with our progress seals/badges to justify the year.
- **$199 is now a category-validated number.** EverSettled charges ~$199 one-time in-app for their DIY "full plan." Pricing our *year* at the same $199 is easy to defend — and the comparison writes its own copy: *their $199 organizes an estate after a death; our $199 makes sure your family never needs their $1,499 service.*
- **Consider a $199 one-time framing test later.** If annual-subscription resistance shows up in real funnels ("why am I renting my own plan?"), the fallback is $199 one-time for 12 months of access with a cheap $4.99/mo "keep it updated" continuation. Same first-year revenue, softer commitment story. Don't build this for launch — just A/B the copy if conversion stalls.
- LLM cost at full quota is $0.30–0.70/user/mo, so even $199/yr keeps ~95% gross margin.

### Launch / go-to-market: Founding Member offer

For the **first 100 members** (or first 60 days, whichever first):
- **$19/mo or $149/yr — locked in for life** as long as they stay subscribed.
- Framed as founding access, not a discount: early input on features, founding badge on their playbook.
- After the window closes, list price ($25/$199) applies and is never discounted below that publicly — protects price integrity while creating real urgency.
- *Optional cash-flow lever:* a one-time **$399 Founding Lifetime** capped at 50 units. Quotas already cap per-user LLM cost, so worst-case exposure is bounded (~$8/user/yr). Skip if it complicates Stripe setup for launch.

### Retainer (B2B — the "Legacy Readiness OS" angle)

The email's comp set (Cocoon, Candidly, Bereave) are all **employer-benefit** plays — that's the retainer market: employers, financial advisors, funeral homes, senior-living communities buying readiness for their people.

| Tier | Retainer | Includes | Effective/seat |
| --- | --- | --- | --- |
| Pilot | **$500/mo** (3-mo min) | 25 member seats, partner dashboard-lite (aggregate only), co-branded landing | $20 |
| Growth | **$1,500/mo** | 100 seats, quarterly readiness report | $15 |
| White-label | custom, from **$3,000/mo** | de-branded deploy (the config seam already supports this), SSO/CSV onboarding | ~$10 |

Anchors: EverSettled bills **$1,499 per estate after death** — a partner covers 25 members for a whole year for less than the cost of two unsettled estates. Bereave and Cocoon normalize employer-paid death/grief benefits.

### Monthly vs. tiers vs. add-ons

**Recommendation: stay 2-tier (Free + Personalized) at launch. Do not add a third consumer tier. Use add-ons as the expansion path.**

- We don't have enough distinct features to ladder 3 tiers honestly; splitting would either gut Free (killing the funnel) or gut Personalized (killing the $25 story). Choice paralysis is deadly on an emotional purchase.
- DLB's model shows add-ons work in this space. Ours, in roadmap order:
  1. **Family seat** — +$10/mo or +$79/yr per additional household member. (DLB charges **$199.99** per extra member — easy win, and couples are the natural buyer.)
  2. **Printed keepsake playbook** — one-time $49–79 fulfilled print of the finished PDF (badge/seals already render there).
  3. **Expert review session** — one-time $149–199 live review with the expert persona. Doubles as the bridge into B2B retainers.
  4. Quota top-up packs only if real usage ever presses the 30/200 quotas (unlikely; don't build now).

---

## 3. What this means in the codebase (when approved)

1. `agent/app/services/plans.py` — add `price_usd_year` (199.0) to `PlanDef`; founding pricing is just different Stripe Prices, no code change.
2. Stripe: create Prices for $25/mo, $199/yr, $19/mo (founding), $149/yr (founding); archive founding Prices after the window.
3. `/api/pricing` + `docs/pricing.md` + landing pricing section pick up annual toggle.
4. Family seat / add-ons: **not in MVP** — roadmap only.

---

## 4. Go-to-market strategy & pitch

### Positioning (the one-liner)

> **Final Playbook is the proactive layer of the death-tech stack.** Everyone else
> monetizes the mess after a death (EverSettled: $1,499/estate). We're upstream —
> education-first, no dread — making families ready so the mess never happens.
> No one owns "upstream" today.

### Marketing strategy: the free tier IS the marketing

The free assessment costs $0 to serve (pure rules engine), so every piece of
content funnels into it with zero marginal cost:

1. **Education-led content in the expert voice** (warm, no-dread tone) answering the
   questions people actually search: *"how do I talk to my mom about her will,"*
   *"what happens if my dad dies without a plan."* Each piece ends at the free assessment.
2. **The "readiness score" as the shareable hook** — the assessment output is the
   lead magnet; seeing your gaps is the emotional moment that converts.
3. **Channels, in order of cost-effectiveness:** caregiver Facebook groups & forums →
   SEO on conversation-starter queries → referral partners (estate attorneys,
   financial advisors, senior-living) → paid social only after organic proves copy.
4. **The anchor line everywhere:** *"Unprepared costs $1,499+ after. Ready costs $199 now."*

### What to say to each audience

| Audience | Lead with | Proof points |
| --- | --- | --- |
| **Angel investors** | Category creation upstream of a market that just got funded downstream (EverSettled $5M seed, Emergence). We're first in "legacy readiness." | Free tier = $0 COGS funnel; paid ~95% gross margin; expert clinical routing = defensible content moat (not a GPT wrapper — deterministic engine, LLM only rephrases); white-label seam already built → B2B expansion without new product. |
| **Consumers (buyers)** | Peace of mind + the conversation scripts. *"Know exactly what to do, what to say, and in what order."* | Free score first (no signup); progress seals; $199/yr vs $1,499 cleanup. |
| **B2B demos** (employers, advisors, funeral homes) | *"Legacy readiness as a benefit"* — Cocoon/Bereave normalized employer-paid grief support; we're the pre-need version. | Live white-label moment: change one config file, their brand in 60 seconds. Aggregate readiness reporting (no individual data). $500/mo pilot < the cost of one unsettled estate. |

### Revenue potential (honest scenarios)

Assumptions: 3–5% free→paid conversion (typical freemium for high-intent tools),
blended ~$180/paid user/yr (mix of monthly + annual), ~95% gross margin.

| Scenario | Free users | Paid | Consumer ARR | B2B | Total ARR |
| --- | --- | --- | --- | --- | --- |
| Year-1 conservative | 20,000 | 600 (3%) | ~$110k | 5 pilots @ $500/mo | ~$140k |
| Year-1–2 moderate | 100,000 | 4,000 (4%) | ~$720k | 15 mixed retainers | ~$1M |
| With 3 white-labels | — | — | — | +$36k/yr each | +$100k+ |

The realistic near-term story for angels: **a credible path to ~$1M ARR on a
product that costs almost nothing to serve**, in a category a top-tier fund just
validated at the other end of the timeline.

## 5. Launch-readiness features (proposed order)

| Priority | Feature | Why / effort |
| --- | --- | --- |
| **Blocker** | Privacy policy + Terms pages | Legal necessity for a product holding sensitive family data. Static pages, small effort. |
| **Blocker** | Delete-my-account/data | Trust is the product in this category; also CCPA/GDPR hygiene. Store layer makes this a contained change (one method per backend + a route + a button). |
| High | Cookie consent | Only needed if analytics cookies ship. Recommendation: stay cookie-light (no ad pixels at launch) so the banner can be minimal — a trust win DLB already markets. |
| High | Google SSO (sign in with Google) | Cuts login friction vs email codes for the 55+ audience. Fast-follow if launch date is tight — email codes already work. |
| High | **Trusted people (MVP-lite)** | "Add people / save their info": start with saving names/roles/contact info of key people (executor, POA, doctor) *inside the member's own plan* — no sharing, no permissions, low risk, high perceived value. Full shared access = the **family seat add-on** (revenue, post-launch). |
| Medium | Recorded product demo (90s) | Script from `docs/product-video-blueprint.html`: problem (15s) → assessment (20s) → gap reveal (15s) → paid plan + AI chat (25s) → CTA (15s). One take per segment, OBS/Loom, real product, no slides. |

*Sources: digitallifebox.com/pricing (fetched 2026-07-20, prices from page + embedded plan JS), eversettled.com (+ in-app $199 upgrade observed by Niki), EverSettled $5M seed coverage (FinSMES, Law360, Seedcamp, TechFundingNews, July 2026).*

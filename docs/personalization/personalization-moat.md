# The Personalization MOAT — signals → questions

> **Source of truth for how personalization works.** Authored for the Niki +
> Nermeen design review (email, 2026-07-07). Transcribed here from
> `1-Personalization-MOAT-Plan.html` so it lives in the repo, not just an inbox.
> Reviewed BEFORE code. Extends the engine seam
> (`signal-triggered-questions-architecture.md`) with the concrete model.
>
> Status: **design review copy** — signal labels, per-question tagging, and the
> situational cluster list are pending Niki's sign-off. Do not treat as final
> clinical routing.

## 0. The claim, stated honestly

Pure show/hide is **not** the moat. If ~70% of the 40-per-domain questions are
universal (everyone makes a will, names an executor), hiding the other 30% still
shows everyone almost the same list. What makes it feel like a 1:1 session is
**three levers working together**, only one of which is show/hide:

| Lever | What it does | Engine field | Feels like |
|---|---|---|---|
| **1. REORDER** | Same questions, urgent-for-you FIRST | `priorityBoost` | "She led with exactly my problem" |
| **2. GATE** | Situational clusters appear/vanish | `showPolicy: 'ifSignal'` + `triggerSignals` | "It didn't waste my time" |
| **3. BRANCH** | Same question, answer-specific path | `QuestionOption.variants` (BUILT) | "It went deep on my actual answer" |

REORDER is the most underused and the most powerful. Niki does not hide
questions in a call — she **leads with what is on fire for you.** That is lever 1.

## 1. Two signal families (Niki's real intake)

Signals come from a TWO-PART onboarding, mirroring how Niki opens a session.

### 1a. Life-stage signals — WHO you are

`hasPartner`, `hasYoungChildren`, `hasAdultChildren`, `hasAgingParent`,
`parentHasNoDocs`, `isSoloAger`, `isCaregiver`, `isBusinessOwner`, `hasPets`,
`hasSignificantAssets`, `digitalLifeHeavy`.

These mostly GATE (a solo-ager never sees guardian questions) and set base order.

### 1b. WHY-NOW signals — what MOVED you to act (the gamified entry)

"Ten signals you are ready to start. Which is yours?" The member picks one or
more. Each sets a why-now signal that primarily REORDERS the journey toward what
that moment made urgent.

| # | The signal (member-facing) | Flag | Primarily REORDERS toward | Also GATES |
|---|---|---|---|---|
| 1 | A loss in your circle | `recentLossInCircle` | Fastest-path urgency across all domains | — |
| 2 | You became responsible for someone | `becameResponsible` | Kids→guardian / parent→caregiving lead | guardian OR caregiver |
| 3 | You settled an estate / carried someone through | `settledAnEstate` | Executor + Crucial Doc Box lead | — |
| 4 | A near miss (scare, diagnosis, hospitalization) | `recentNearMiss` | Physical + Healthcare POA lead | advance-directive |
| 5 | A major life change (marriage, divorce, move, retirement, citizenship) | `majorLifeChange` | Beneficiary audit + POA re-check lead | post-divorce re-titling |
| 6 | A new decade or threshold age (40/50/60/65) | `thresholdAge` | Gentle full sweep, no single lead | — |
| 7 | Your digital life outweighs your physical | `digitalOutweighs` | Digital domain leads the journey | inheritable-digital-assets |
| 8 | Something worth protecting (property, business, IP) | `worthProtecting` | Business + asset-transfer lead | business-succession |
| 9 | A public case shook you | `publicCaseShook` | Whichever domain the case touched | — |
| 10 | You are tired of the unfinished thing | `tiredOfUnfinished` | Their self-named worry leads | — |

Signals 6, 9, 10 are "soft" (tone/urgency only). Signals 2, 4, 5, 7, 8 are
"hard" (reorder AND add a cluster).

### 1c. Signals ADDED from real-session analysis

The transcripts + case studies surfaced gaps the 10-chart missed. Evidence-cited.

| Flag | Reads | Gates | Source |
|---|---|---|---|
| `hasSpecialNeedsDependent` | special-needs child | special-needs-trust cluster | `[CS2]` |
| `terminalDiagnosis` | terminal / hospice path | Five Wishes + healthcare-proxy depth + VSED | `[Sasha]`, `[CS3]` |
| `spousalDependency` | one partner holds all the info | ownership-transfer prompts (learn the safe combo) | `[CS3]` |
| `hasAgingParent`+`parentHasNoDocs` | caring for an unprepared parent | parent-planning cluster (leads) | `[Sasha]`, `[Ling]` |

**Baseline boost (universal #1 gap):** across ALL five case studies + both member
sessions, the most common gap was **digital access + the Crucial Doc Box** — no
one could find documents or read passwords. So `legacy_contact` and
`crucial_doc_box` carry a small boost for EVERYONE, not only digital-heavy.

**The lead rule, evidence-backed:** Niki never opens with the bank. She finds the
why-now + who-you're-responsible-for, and leads with THAT.
Order = (1) why-now signal's target → (2) responsible-for cluster → (3) base.

## 2. How a question is tagged (data change, already supported)

```
Question {
  id, domain, milestoneId, text, options[]   // existing
  showPolicy?: 'always' | 'ifSignal'         // default 'always' (universal)
  triggerSignals?: string[]                  // signals that surface OR boost this Q
  priorityBoost?: number                     // higher = leads when a trigger fires
}
```

- **Universal** (most of the 40): `always`, no triggers. Everyone sees it, in
  base order — UNLESS a why-now signal boosts it.
- **Situational**: `ifSignal` + `triggerSignals`. Only for the matching person
  (guardian → `hasYoungChildren`).
- **Boosted universal**: `always` + `triggerSignals` + `priorityBoost`. Everyone
  sees it, but it JUMPS to front when the signal fires (beneficiary audit →
  `majorLifeChange`, boost 90).

Backward compatible: no tags = today's behavior. Engine already does this
(`visibleQuestionsForDomain`, tested).

## 3. Worked example — same 4 domains, three different people

Legal has 10 questions; 7 universal, 3 situational (guardian, business
succession, post-divorce re-titling).

- **Person A — solo-ager, "tired of the unfinished thing":** GATE guardian/
  business/divorce OUT → 7 universal. Soft signal → gentle base order, self-named
  worry leads. Feels clean, calm.
- **Person B — young parent, "became responsible":** GATE guardian IN → 8.
  Guardian boosted to #1; executor #2. Feels "it knew the kids were the point."
- **Person C — business owner, divorced last year, "worth protecting":** GATE
  business + post-divorce IN → 9. Beneficiary audit #1 (divorce), business
  succession #2. Feels "it led with re-doing beneficiaries and protecting the
  company."

Same bank. Three genuinely different journeys. That is the moat.

## 4. Prioritization algorithm (deterministic, pure)

For a domain, given the member's signal set:

1. **Filter** — keep `always` + `ifSignal` whose trigger is active.
2. **Score** — `boost = max(priorityBoost of active triggers, 0)`.
3. **Sort** — boost DESC, then library order (stable → deterministic).
4. **Cross-domain lead** — a why-now signal can promote a whole DOMAIN to lead
   (signal 7 → Digital first).

Same signals + same answers → same order, every time. Auditable.

## 5. Onboarding flow (two parts, before the domains)

```
Welcome
  → Part 1: Life stage (C1–C6)  "Who is in your life?" partner/kids/parents/business/solo
  → Part 2: Why now (NEW)       "Ten signals you're ready to start. Which is yours?" (multi-pick)
  → Home (domains, ordered by the combined signals)
```

Part 2 is one screen: the 10 signals as tappable cards (multi-select). Each maps
to a flag. No score, no judgment shown.

## 6. What Niki + Nermeen decide

1. **Signal labels** — are the 10 member-facing lines in §1b right?
2. **Per-question tagging** — for each 40×4, `always` or `ifSignal`, and which
   signals boost it? (draft → Niki corrects — her judgment.)
3. **The situational clusters** — guardian, caregiver, business-succession,
   post-divorce re-titling, advance-directive, inheritable-digital. Confirm list.
4. **Cross-domain lead** — signal 7 reorders the whole journey to Digital-first,
   or just boosts within Digital? (Recommend: whole-journey lead.)

## 7. Build order (after Niki approves)

1. **Why-now onboarding step** — the 10-signal picker; sets flags.
2. **Tagging matrix** — `showPolicy` / `triggerSignals` / `priorityBoost` for all
   40×4 (needs Digital + Physical questions from Niki).
3. **Engine** — supports filter+boost; add cross-domain lead + tests.
4. **Apply tags** to the library, re-export, publish to DDB.
5. **Agentic hook (future)** — `proposeSignals(conversation)` sets flags; engine
   unchanged.

---

## Relationship to the current shipped app

The app today (`agent/app/agent/rules_engine.py`) implements a simpler version:
`MemberContext` flags → matched situation profiles → capped, ordered action
items. The three-lever model above is the **next evolution** of that engine —
REORDER (priorityBoost) and the why-now signal layer are not yet built. When
implementing, keep the existing `flag`-per-actionItem mechanism; the signal model
extends it, doesn't replace it. See `knowledge-base/content-library.json`
`situationProfiles` for what exists now.

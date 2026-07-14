# Spec: Progress Celebrations & Completion Seals

**Status:** draft — awaiting review
**Owner:** frontend
**Related:** `PlaybookPanel.jsx`, `ActionCard.jsx`, `Assessment.jsx`, `playbookPdf.js`

## Objective

Reward members for making progress so the app *feels* like it's moving their
affairs into order — turning a heavy, avoidable task into a series of small,
satisfying, visibly-earned wins.

**Three earned moments, escalating:**

1. **Action complete** — all steps of a single action are checked → the item's
   mark pops to ✓ with a soft gold glow. Lightweight, frequent.
2. **Domain sealed** — every action in a domain (Legal / Financial / Physical /
   Digital) is complete → an animated **gold wax seal stamps down**, dated
   (e.g. `LEGAL · READY · Jul 13, 2026`). Meaningful, occasional.
3. **Playbook complete** — all domains sealed → a **"My Final Playbook Complete"
   badge** with a name + date/time stamp. The big finish.

Every seal and the final badge **print on the downloaded PDF**, so the artifact
the family receives visibly shows the work was finished, and when.

**Who:** paid-tier members (free tier shows locked cards — nothing to complete).

**Why this framing, not "you saved $X":** per `docs/guardrails.md`, the app must
not invent claims or give legal/financial advice. Celebration copy is
*educational reassurance* about what completing the step accomplishes for the
member's family — never a dollar figure, risk percentage, or "you avoided
probate" claim. Copy is config-driven so Niki can sign off / edit it.

## Non-goals (this spec)

- No streaks / daily-return mechanic (deferred — tonally sensitive for this
  topic; revisit after this ships).
- No confetti (chosen against: generic, doesn't print, off-tone). Celebration
  is the **wax-seal stamp** — 0 KB CSS/SVG, on-brand with the sealed-document
  PDF, and the same visual is the printed badge.
- No 3D / Three.js / Lottie (bundle + tone cost too high for the payoff).
- No backend changes. Completion is derived from existing per-user `doneKeys`.

## Tech Stack

Vite + React (existing). Zero new dependencies. Animation = CSS keyframes +
inline SVG. Celebration copy + seal labels live in `frontend/src/config/branding.js`.

## Commands

```
Dev:    cd frontend && npm run dev          # http://localhost:3200
Build:  cd frontend && npm run build
Test:   cd frontend && npm test             # vitest
Lint:   cd frontend && npm run lint         # if configured
```

## Project Structure (what this touches)

```
frontend/src/
  lib/
    completion.js        NEW  pure helpers: actionComplete(), domainState(),
                              playbookComplete() — derive earned state from
                              items + doneKeys. Unit-tested.
    completion.test.js   NEW  vitest for the helpers (the celebration logic).
  components/
    Seal.jsx             NEW  the animated wax seal + final badge (presentational,
                              reduced-motion aware). Reused on screen AND fed to PDF.
    PlaybookPanel.jsx    EDIT render seals inline; fire the "just sealed" animation
                              once per newly-completed domain (mirrors existing
                              `justAdded` typewriter pattern).
    ActionCard.jsx       EDIT add the gold-glow ✓ pop when an action first completes.
    Assessment.jsx       EDIT (if the progress meter lives here) surface % + badge.
  config/
    branding.js          EDIT SEAL_LABELS, CELEBRATION_COPY, BADGE_COPY.
  styles/global.css      EDIT .fp-seal*, .fp-badge*, @keyframes stamp/glow,
                              prefers-reduced-motion overrides.
  lib/playbookPdf.js     EDIT render earned seals + final badge into the PDF HTML.
```

## Code Style

Derive earned state with **pure functions** — never store it; recompute from
`doneKeys` so it's always correct and needs no persistence. Matches the existing
`doneCount`/`complete` derivations in `PlaybookPanel.jsx`.

```js
// frontend/src/lib/completion.js
// All earned state is DERIVED from (items, doneKeys) — never stored.

export function actionComplete(item, doneKeys) {
  const steps = item.steps || [];
  return steps.length > 0 && steps.every((_, i) => doneKeys.has(`${item.id}::${i}`));
}

// Returns per-domain { total, done, sealed } so the UI can show progress AND
// know the exact moment a domain crosses into "sealed".
export function domainState(items, doneKeys) {
  const byDomain = {};
  for (const it of items) {
    if (it.locked || !it.domain) continue;
    const d = (byDomain[it.domain] ??= { total: 0, done: 0 });
    d.total += 1;
    if (actionComplete(it, doneKeys)) d.done += 1;
  }
  for (const d of Object.values(byDomain)) d.sealed = d.total > 0 && d.done === d.total;
  return byDomain;
}

export function playbookComplete(items, doneKeys) {
  const s = domainState(items, doneKeys);
  const domains = Object.values(s);
  return domains.length > 0 && domains.every((d) => d.sealed);
}
```

Celebration timing reuses the proven `useRef(new Set())` + `justAdded` pattern
already in `PlaybookPanel.jsx` (lines 60–69): track which domains were *already*
sealed on the previous render; when a new one appears in the sealed set, play its
stamp animation once. No animation replays on unrelated re-renders.

Copy stays out of components:

```js
// branding.js
export const SEAL_LABELS = { Legal: "Legal · Ready", Financial: "Financial · Ready",
  Physical: "Physical · Ready", Digital: "Digital · Ready" };
export const CELEBRATION_COPY = {
  action: "Done. Your family won't have to guess about this one.",
  domainSealed: (d) => `${d} affairs are in order.`,
};
export const BADGE_COPY = { title: "My Final Playbook — Complete",
  sub: "Everything your family needs, in one place." };
```

## Testing Strategy

- **vitest** unit tests for `completion.js` — the actual logic worth testing:
  - action with 0 steps is never "complete"
  - action complete only when *every* step key present
  - a domain seals only when all its non-locked actions complete
  - locked items are excluded from domain totals (free-tier items don't block)
  - playbook completes only when every domain is sealed; empty → false
- Manual / RTL check: seal animates **once** per new completion, not on every
  keystroke; reduced-motion shows the seal with no animation.
- Verify the PDF renders earned seals + badge (visual check on download).

## Boundaries

- **Always:** derive earned state (never persist a "badge" flag); keep all copy
  in `branding.js`; honor `prefers-reduced-motion`; keep celebrations paid-tier;
  run `npm run build` + tests before commit.
- **Ask first:** any dollar/risk/"you avoided X" claim in copy (guardrail — needs
  Niki sign-off); adding a dependency (we intend zero); any backend/persistence
  change; adding a streak mechanic.
- **Never:** invent a legal/financial/medical claim in celebration copy; store
  PII in a badge beyond the member's own first name + timestamp they generated;
  let a celebration block input or delay checking the next item.

## Success Criteria

1. Completing all steps of an action shows a ✓ + gold-glow pop (once), on screen.
2. Completing all actions in a domain stamps a dated seal (once), with a
   reduced-motion fallback that simply shows the seal.
3. Completing all domains awards a dated "Playbook Complete" badge on the panel.
4. The downloaded PDF shows each earned seal and the final badge, dated.
5. No new npm dependency; bundle grows < 5 KB; build + all tests pass.
6. All celebration/seal/badge text originates from `branding.js`.
7. No dollar amounts, risk percentages, or legal claims anywhere in the copy.

## Open Questions

1. **Date vs. date+time on the badge** — seals are per-day (date only); should the
   final badge include a time stamp (`Jul 13, 2026 · 3:42pm`) or date only?
   (Time makes it feel like a real "moment"; date-only is cleaner on the PDF.)
2. **Exact seal/badge copy** — the strings above are placeholders for Niki to
   approve. Is "affairs are in order" the right voice, or softer?
3. **Domain set** — confirm the canonical four domains + exact labels as they
   appear in `content-library.json` (so seal labels match the UI tags).
```
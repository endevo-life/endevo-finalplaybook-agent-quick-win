// "Why now?" signals — the avoidance-breaking entry point.
//
// SOURCE OF TRUTH: docs/personalization/personalization-moat.md §1b (the
// 10 member-facing why-now signals). This is Niki's clinical judgment — the
// labels and the domains each signal reorders toward are HERS to correct.
//
// validated: false — this is a working scaffold pending Niki's sign-off. The
// picker UX can ship on it, but the reorder weights are provisional. Do not
// present the ordering as clinically final. When Niki revises a label or a
// target, edit it HERE (one file) — nothing else needs to change.
//
// How it's used: the member picks any that fit (multi-select). Each selected
// signal contributes a `boost` to the plan items whose `domain` it targets, so
// the plan LEADS with what moved them to act (MOAT lever 1: REORDER). No score
// and no judgment is ever shown to the member.

export const WHY_NOW_VALIDATED = false;

// Each signal: member-facing label + supportive subline, the flag it sets, the
// domains it reorders toward (matched against actionItem.domain), and whether
// it's a "hard" signal (also gates a situational cluster) — kept for future
// wiring; the picker uses label/flag/reordersToward today.
export const WHY_NOW_SIGNALS = [
  {
    flag: "recentLossInCircle",
    label: "A loss in your circle",
    sub: "Someone close to you died, and it made this real.",
    reordersToward: ["legal", "financial", "digital", "physical", "communication"],
    soft: false,
  },
  {
    flag: "becameResponsible",
    label: "You became responsible for someone",
    sub: "A child, a parent, someone who now depends on you.",
    reordersToward: ["legal", "physical"],
    soft: false,
  },
  {
    flag: "settledAnEstate",
    label: "You carried someone through their ending",
    sub: "You settled an estate, and saw what was missing.",
    reordersToward: ["legal", "digital"],
    soft: false,
  },
  {
    flag: "recentNearMiss",
    label: "A near miss",
    sub: "A scare, a diagnosis, a hospital stay — a wake-up.",
    reordersToward: ["physical", "legal"],
    soft: false,
  },
  {
    flag: "majorLifeChange",
    label: "A major life change",
    sub: "Marriage, divorce, a move, retirement, citizenship.",
    reordersToward: ["financial", "legal"],
    soft: false,
  },
  {
    flag: "thresholdAge",
    label: "A new decade",
    sub: "You hit a number — 40, 50, 60, 65 — and it landed.",
    reordersToward: [],
    soft: true,
  },
  {
    flag: "digitalOutweighs",
    label: "Your digital life outweighs the paper one",
    sub: "Accounts, photos, logins — most of your life is online.",
    reordersToward: ["digital"],
    soft: false,
  },
  {
    flag: "worthProtecting",
    label: "Something worth protecting",
    sub: "A home, a business, work you built and want to pass on.",
    reordersToward: ["financial", "legal"],
    soft: false,
  },
  {
    flag: "publicCaseShook",
    label: "A story that shook you",
    sub: "A public case made you think, that could be my family.",
    reordersToward: [],
    soft: true,
  },
  {
    flag: "tiredOfUnfinished",
    label: "You're tired of the unfinished thing",
    sub: "It's been on the list too long. Today you start.",
    reordersToward: [],
    soft: true,
  },
];

// Base boost applied to any item whose domain a selected signal targets.
const SIGNAL_BOOST = 100;

// Universal baseline (MOAT doc): across every session the #1 gap was digital
// access + the Crucial Doc Box. These two lead for EVERYONE, gently, even with
// no signals picked. Matched loosely by action text / id substring.
const UNIVERSAL_LEAD = [
  { match: /doc\s?box|document|central place/i, boost: 40 },
  { match: /legacy contact/i, boost: 38 },
];

// GATE + REORDER the questions for this person (MOAT levers 2 + 1 applied to the
// assessment itself). Two steps:
//
//   1. GATE — a question with `triggerSignals` is SITUATIONAL: it only appears
//      when one of the member's picked signals matches (guardian Qs only for
//      "became responsible", succession Qs only for "worth protecting", etc.).
//      A question with no `triggerSignals` is UNIVERSAL — everyone sees it.
//   2. REORDER — among the visible questions, the ones in a domain the member's
//      signals target lead, so the assessment opens with what's urgent for them.
//
// Pure + deterministic. With no signals picked, situational questions are hidden
// and the universal set keeps its library order (today's behavior).
export function selectQuestions(questions, pickedFlags) {
  const picked = new Set(pickedFlags || []);

  // 1. GATE
  const visible = questions.filter((q) => {
    const trig = q.triggerSignals;
    if (!trig || trig.length === 0) return true;      // universal
    return trig.some((t) => picked.has(t));            // situational: needs a match
  });

  if (picked.size === 0) return visible;

  // 2. REORDER by targeted domain
  const targetedDomains = new Set();
  for (const s of WHY_NOW_SIGNALS) {
    if (picked.has(s.flag)) for (const d of s.reordersToward) targetedDomains.add(d);
  }
  const scored = visible.map((q, i) => ({
    q,
    i,
    // Situational (signal-matched) questions lead; then targeted-domain; then base.
    boost:
      (q.triggerSignals && q.triggerSignals.some((t) => picked.has(t)) ? SIGNAL_BOOST * 2 : 0) +
      (q.domain && targetedDomains.has(q.domain) ? SIGNAL_BOOST : 0),
  }));
  scored.sort((a, b) => b.boost - a.boost || a.i - b.i); // stable => deterministic
  return scored.map((s) => s.q);
}

// Back-compat alias (older name): now delegates to the gate+reorder selector.
export const orderQuestionsBySignals = selectQuestions;

// Given the picked signal flags and a flat list of plan items (each with a
// `domain` and `action`/`id`), return a NEW array sorted so the most urgent-for-
// -this-person items lead. Pure + deterministic: same signals + same items =>
// same order. Falls back to the original order when no signals are picked.
export function reorderBySignals(items, pickedFlags) {
  const picked = new Set(pickedFlags || []);
  const targetedDomains = new Set();
  for (const s of WHY_NOW_SIGNALS) {
    if (picked.has(s.flag)) for (const d of s.reordersToward) targetedDomains.add(d);
  }

  const scored = items.map((it, i) => {
    let boost = 0;
    if (it.domain && targetedDomains.has(it.domain)) boost += SIGNAL_BOOST;
    const text = `${it.action || ""} ${it.id || ""} ${it.title || ""}`;
    for (const u of UNIVERSAL_LEAD) if (u.match.test(text)) boost += u.boost;
    return { it, i, boost };
  });

  // Sort by boost DESC, then original library order (stable => deterministic).
  scored.sort((a, b) => b.boost - a.boost || a.i - b.i);
  return scored.map((s) => s.it);
}

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
    label: "Losing someone close",
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
    label: "You lost someone and handled their affairs",
    sub: "You settled an estate, and saw what was missing.",
    reordersToward: ["legal", "digital"],
    soft: false,
  },
  {
    flag: "recentNearMiss",
    label: "A near miss",
    sub: "A scare, a diagnosis, a hospital stay, a wake-up.",
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
    sub: "You hit a number, 40, 50, 60, 65, and it landed.",
    reordersToward: [],
    soft: true,
  },
  {
    flag: "digitalOutweighs",
    label: "Your digital life outweighs the paper one",
    sub: "Accounts, photos, logins, most of your life is online.",
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

// Per-signal "we heard you" clause used to build the personalized intro shown
// above the questions. Written to compound: e.g. picking "settled an estate" +
// "worth protecting" reads "You've seen what settling an estate takes, and
// you've built something worth protecting." validated:false — Niki's voice.
const SIGNAL_CLAUSE = {
  recentLossInCircle: "you know what a loss leaves behind",
  becameResponsible: "someone is counting on you now",
  settledAnEstate: "you've seen up close what settling an estate takes",
  recentNearMiss: "a scare made this suddenly real",
  majorLifeChange: "your life looks different than it did",
  thresholdAge: "you've hit a number that made you look up",
  digitalOutweighs: "most of your life now lives online",
  worthProtecting: "you've built something worth protecting",
  publicCaseShook: "a story got under your skin",
  tiredOfUnfinished: "you're done leaving this unfinished",
};

// Build a warm, compounding intro from the picked signals. One signal → one
// clause; two → joined with "and"; three+ → the first two + "and a few other
// things that brought you here." Empty when nothing's picked (caller hides it).
export function buildIntro(pickedFlags, name) {
  const clauses = (pickedFlags || [])
    .map((f) => SIGNAL_CLAUSE[f])
    .filter(Boolean);
  if (clauses.length === 0) return "";
  const who = name ? `${name}, ` : "";
  let body;
  if (clauses.length === 1) body = clauses[0];
  else if (clauses.length === 2) body = `${clauses[0]}, and ${clauses[1]}`;
  else body = `${clauses[0]}, ${clauses[1]}, and a few other things brought you here`;
  // Capitalize the first clause for a clean sentence start.
  const sentence = body.charAt(0).toUpperCase() + body.slice(1);
  return `${who}${sentence}. Here are the questions that matter most for you, we'll lead with those.`;
}

// Per-scenario question PREAMBLE (MOAT lever 3: same question, personal doorway).
// A short lead-in shown above a question when a picked signal makes it especially
// relevant — "Since a scare brought you here, ..." — so the SAME question reads
// as written for this person. Keyed by signal, then by question domain (the most
// relevant pairing wins). validated:false — Niki's voice, one place to correct.
const QUESTION_PREAMBLE = {
  recentNearMiss: {
    physical: "Since a health scare brought you here: ",
    legal: "After a scare like that, this one matters: ",
  },
  recentLossInCircle: {
    legal: "Having just been through a loss: ",
    digital: "You saw what was hard to find. So: ",
    financial: "So your people aren't left searching: ",
  },
  becameResponsible: {
    legal: "With someone depending on you now: ",
    financial: "For the people counting on you: ",
  },
  settledAnEstate: {
    legal: "Knowing what an executor needs: ",
    digital: "You know how hard access can be, so: ",
  },
  majorLifeChange: {
    financial: "After your recent change: ",
    legal: "Now that things have changed: ",
  },
  worthProtecting: {
    financial: "To protect what you've built: ",
    legal: "So what you've built passes cleanly: ",
  },
  digitalOutweighs: {
    digital: "Since most of your life is online: ",
  },
};

// Return a preamble string for a question given the picked signals, or "" if
// none applies. First matching (signal, domain) pair wins — deterministic by
// the order signals were picked.
export function questionPreamble(question, pickedFlags) {
  if (!question || !pickedFlags) return "";
  const domain = question.domain;
  for (const flag of pickedFlags) {
    const byDomain = QUESTION_PREAMBLE[flag];
    if (byDomain && byDomain[domain]) return byDomain[domain];
  }
  return "";
}

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

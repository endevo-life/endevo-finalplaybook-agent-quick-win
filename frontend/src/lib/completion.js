// Earned-progress logic for the celebration layer.
//
// All earned state (action complete, domain sealed, playbook complete) is
// DERIVED from (items, doneKeys) on every render -- never stored. That keeps it
// always-correct and needs no persistence: the same `doneKeys` that already
// drives the checklist also decides what's been earned.
//
// `doneKeys` is a Set-like with `.has(`${itemId}::${stepIndex}`)`.
// `items` are the plan items: [{ id, domain, steps[], locked }].

// An action is complete when it HAS steps and every one is checked.
// (Zero-step items can't be "completed" -- there's nothing to check.)
export function actionComplete(item, doneKeys) {
  const steps = item.steps || [];
  return steps.length > 0 && steps.every((_, i) => doneKeys.has(`${item.id}::${i}`));
}

// Per-domain tally: { [domain]: { total, done, sealed } }.
// Locked (free-tier) items and items with no domain are excluded, so a locked
// premium item never blocks a domain from sealing for a paid member.
export function domainState(items, doneKeys) {
  const byDomain = {};
  for (const it of items || []) {
    if (it.locked || !it.domain) continue;
    const d = (byDomain[it.domain] ||= { total: 0, done: 0, sealed: false });
    d.total += 1;
    if (actionComplete(it, doneKeys)) d.done += 1;
  }
  for (const d of Object.values(byDomain)) {
    d.sealed = d.total > 0 && d.done === d.total;
  }
  return byDomain;
}

// The domain keys that are fully sealed, in the order they first appear in
// `items` (stable, so seals don't reshuffle as more are earned).
export function sealedDomains(items, doneKeys) {
  const state = domainState(items, doneKeys);
  const order = [];
  for (const it of items || []) {
    if (it.domain && state[it.domain]?.sealed && !order.includes(it.domain)) {
      order.push(it.domain);
    }
  }
  return order;
}

// True only when at least one domain exists AND every domain is sealed.
export function playbookComplete(items, doneKeys) {
  const domains = Object.values(domainState(items, doneKeys));
  return domains.length > 0 && domains.every((d) => d.sealed);
}

// Overall completion fraction (0..1) across all non-locked, has-steps actions --
// drives the progress meter. Returns 0 when there's nothing trackable yet.
export function overallProgress(items, doneKeys) {
  let total = 0;
  let done = 0;
  for (const it of items || []) {
    if (it.locked || !(it.steps || []).length) continue;
    total += 1;
    if (actionComplete(it, doneKeys)) done += 1;
  }
  return total === 0 ? 0 : done / total;
}

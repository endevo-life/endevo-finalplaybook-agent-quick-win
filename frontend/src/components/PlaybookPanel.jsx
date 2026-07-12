import { useEffect, useRef, useState } from "react";
import { PLAYBOOK_NAME, PRODUCT_NAME } from "../config/branding";
import { downloadPlaybookPdf } from "../lib/playbookPdf";
import { useTypewriter } from "../lib/useTypewriter";

// Show an ISO date (2026-07-09) as a friendly "Jul 9, 2026" on the playbook.
// Leaves any non-date value untouched.
export function prettyValue(v) {
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec((v || "").trim());
  if (!m) return v;
  const d = new Date(+m[1], +m[2] - 1, +m[3]);
  if (isNaN(d)) return v;
  return d.toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });
}

// A playbook line whose title types itself in the first time it appears (i.e.
// when the member first touches that item). Later renders show it instantly.
function ItemTitle({ text, animate }) {
  const { shown, typing } = useTypewriter(text, animate);
  return (
    <span className="fp-pb-item-title">
      {shown}
      {typing && <span className="fp-pb-caret" aria-hidden="true">|</span>}
    </span>
  );
}

// The live "My Final Playbook" document panel.
//
// It assembles in real time as the member answers/checks items — the "watch it
// come together" moment. Both tiers see it build:
//   - Free: unlocked items render normally; locked (premium) items are shown
//     crossed out with a lock, so they see the SHAPE of their full playbook and
//     what upgrading completes. Download is disabled with an upgrade nudge.
//   - Paid: every item rendered; a working "Download PDF" button.
//
// Props:
//   name        — member first name (for the cover line).
//   items       — [{ id, title, action, domain, steps[], fields[], locked }].
//   doneKeys    — Set-like: has(itemId::stepIndex) → that step is checked.
//   fieldValues — { `${itemId}::${fieldKey}`: value } the member has typed.
//   isPaid      — gates the download.
//   onUpgrade   — called when a free user clicks the disabled download.
//
// The playbook starts EMPTY and fills in as the member ACTS: an item appears
// (writing itself on) the first time they check one of its steps OR type into
// one of its fields. Pure reward-for-action — the page they build is the page
// they can download.
export default function PlaybookPanel({ name, items, doneKeys, fieldValues = {}, isPaid, onUpgrade }) {
  // An item is "touched" once any step is checked or any field has a value.
  const isTouched = (it) => {
    const anyStep = (it.steps || []).some((_, i) => doneKeys.has(`${it.id}::${i}`));
    const anyField = (it.fields || []).some((f) => (fieldValues[`${it.id}::${f.key}`] || "").trim());
    return anyStep || anyField;
  };
  const shownItems = items.filter(isTouched);

  // Track which item ids have appeared, so only a NEWLY-added one types in
  // (existing lines don't re-animate on every keystroke/check).
  const seen = useRef(new Set());
  const [justAdded, setJustAdded] = useState(null);
  useEffect(() => {
    const ids = shownItems.map((it) => it.id);
    const fresh = ids.find((id) => !seen.current.has(id));
    ids.forEach((id) => seen.current.add(id));
    // prune ids no longer shown (e.g. unchecked everything)
    seen.current.forEach((id) => { if (!ids.includes(id)) seen.current.delete(id); });
    if (fresh) setJustAdded(fresh);
  }, [shownItems.map((it) => it.id).join(",")]);

  const doneCount = shownItems.filter(
    (it) => it.steps?.length && it.steps.every((_, i) => doneKeys.has(`${it.id}::${i}`))
  ).length;

  return (
    <aside className="fp-pb" aria-label={PLAYBOOK_NAME}>
      <div className="fp-pb-doc">
        <header className="fp-pb-head">
          <p className="fp-pb-kicker">{PRODUCT_NAME}</p>
          <h3 className="fp-pb-title">{name ? `${name}'s ${PLAYBOOK_NAME}` : PLAYBOOK_NAME}</h3>
          <p className="fp-pb-sub">
            {shownItems.length === 0
              ? "your blank page, start checking things off"
              : `${doneCount} of ${shownItems.length} complete`}
          </p>
        </header>

        {shownItems.length === 0 ? (
          <div className="fp-pb-empty">
            <span className="fp-pb-empty-pen" aria-hidden="true">✍️</span>
            <p>As you check items and fill in details on the left, they’ll appear
              here, building your playbook, line by line.</p>
          </div>
        ) : (
        <ol className="fp-pb-list">
          {shownItems.map((it) => {
            const steps = it.steps || [];
            const done = steps.filter((_, i) => doneKeys.has(`${it.id}::${i}`)).length;
            const complete = steps.length > 0 && done === steps.length;
            const animate = it.id === justAdded && !it.locked;
            // Field values the member entered for this item (shown on the page).
            const filled = (it.fields || [])
              .map((f) => ({ label: f.label, value: (fieldValues[`${it.id}::${f.key}`] || "").trim() }))
              .filter((f) => f.value);
            return (
              <li key={it.id} className={`fp-pb-item ${it.locked ? "locked" : ""} ${complete ? "done" : ""}`}>
                <span className="fp-pb-mark" aria-hidden="true">
                  {it.locked ? "🔒" : complete ? "✓" : "○"}
                </span>
                <span className="fp-pb-item-body">
                  <ItemTitle text={it.title || it.action} animate={animate} />
                  {it.domain && <span className="fp-pb-item-domain">{it.domain}</span>}
                  {filled.map((f) => (
                    <span key={f.label} className="fp-pb-field">
                      <span className="fp-pb-field-label">{f.label}:</span> {prettyValue(f.value)}
                    </span>
                  ))}
                  {!it.locked && steps.length > 0 && (
                    <span className="fp-pb-item-prog">{done}/{steps.length} steps</span>
                  )}
                </span>
              </li>
            );
          })}
        </ol>
        )}

        <footer className="fp-pb-foot">
          {isPaid ? (
            <button
              className="fp-btn"
              style={{ width: "100%" }}
              onClick={() => downloadPlaybookPdf({ name, items: shownItems, doneKeys, fieldValues })}
            >
              ↓ Download My Final Playbook (PDF)
            </button>
          ) : (
            <>
              <button className="fp-btn-upgrade" style={{ width: "100%" }} onClick={onUpgrade}>
                Unlock &amp; download the full playbook
              </button>
              <p className="fp-pb-foot-note">
                Free shows the shape of your plan. Unlock to complete every step and
                download it for your family.
              </p>
            </>
          )}
        </footer>
      </div>
    </aside>
  );
}

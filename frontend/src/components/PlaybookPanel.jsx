import { PLAYBOOK_NAME, PRODUCT_NAME } from "../config/branding";
import { downloadPlaybookPdf } from "../lib/playbookPdf";
import { useTypewriter } from "../lib/useTypewriter";

// The newest item's title types itself in — the "watch it write your playbook"
// moment. Earlier items render instantly.
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
//   items       — [{ id, title, action, domain, steps[], locked }] flattened,
//                 in display order; `locked` marks premium-gated items for free.
//   doneKeys    — Set-like: has(itemId::stepIndex) → that step is checked.
//   isPaid      — gates the download.
//   onUpgrade   — called when a free user clicks the disabled download.
export default function PlaybookPanel({ name, items, doneKeys, isPaid, onUpgrade }) {
  const total = items.length;
  const started = items.filter((it) => it.steps?.some((_, i) => doneKeys.has(`${it.id}::${i}`))).length;

  return (
    <aside className="fp-pb" aria-label={PLAYBOOK_NAME}>
      <div className="fp-pb-doc">
        <header className="fp-pb-head">
          <p className="fp-pb-kicker">{PRODUCT_NAME}</p>
          <h3 className="fp-pb-title">{name ? `${name}'s ${PLAYBOOK_NAME}` : PLAYBOOK_NAME}</h3>
          <p className="fp-pb-sub">{started} of {total} started · building as you go</p>
        </header>

        <ol className="fp-pb-list">
          {items.map((it, idx) => {
            const steps = it.steps || [];
            const done = steps.filter((_, i) => doneKeys.has(`${it.id}::${i}`)).length;
            const complete = steps.length > 0 && done === steps.length;
            const isLast = idx === items.length - 1; // newest item types itself in
            return (
              <li key={it.id} className={`fp-pb-item ${it.locked ? "locked" : ""} ${complete ? "done" : ""}`}>
                <span className="fp-pb-mark" aria-hidden="true">
                  {it.locked ? "🔒" : complete ? "✓" : "○"}
                </span>
                <span className="fp-pb-item-body">
                  <ItemTitle text={it.title || it.action} animate={isLast && !it.locked} />
                  {it.domain && <span className="fp-pb-item-domain">{it.domain}</span>}
                  {!it.locked && steps.length > 0 && (
                    <span className="fp-pb-item-prog">{done}/{steps.length} steps</span>
                  )}
                </span>
              </li>
            );
          })}
        </ol>

        <footer className="fp-pb-foot">
          {isPaid ? (
            <button
              className="fp-btn"
              style={{ width: "100%" }}
              onClick={() => downloadPlaybookPdf({ name, items, doneKeys })}
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

import { useState } from "react";

// Condensed action card.
//
// Free (locked=true): the card is rendered but BLURRED with a lock overlay --
//   the user sees the shape of their playbook without the content.
// Premium (locked=false): every numbered step is its own checkbox, grouped under
//   the action, so the member works through it like a real checklist. Steps auto-
//   expand for paid users so the checklist is right there. `isStepDone`/
//   `onToggleStep` drive per-step tracking; `stepKey(i)` yields a stable id.
export default function ActionCard({
  item,
  locked = false,
  isStepDone,
  onToggleStep,
  stepKey,
}) {
  const isReview = item.resultType === "review";
  const detail = isReview ? item.checklist : item.steps;
  const hasDetail = detail && detail.length > 0;
  const trackable = !locked && typeof onToggleStep === "function" && !isReview;
  // Paid: show the checklist expanded by default so it's immediately workable.
  const [open, setOpen] = useState(trackable);

  // How many of this card's steps are done (for the little per-card badge).
  const doneCount = trackable && isStepDone
    ? detail.filter((_, i) => isStepDone(stepKey(i))).length
    : 0;
  const allDone = trackable && detail.length > 0 && doneCount === detail.length;

  return (
    <div className={`fp-action-card ${item.basic ? "basic" : ""} ${isReview ? "done-review" : ""} ${allDone ? "tracked-done" : ""} ${locked ? "fp-locked-card" : ""}`}>
      <div className={locked ? "fp-locked-content" : ""}>
        {item.domain && <span className="fp-domain-tag">{item.domain}</span>}
        {item.title && <p className="fp-action-title">{item.title}</p>}
        {item.answer && <p className="fp-action-answer">Your answer: {item.answer}</p>}
        <p className="fp-action-text">{item.action}</p>

        {trackable && detail.length > 0 && (
          <span className="fp-card-progress">{doneCount}/{detail.length} steps</span>
        )}

        {hasDetail && (
          <>
            {!trackable && (
              <button className="fp-showhow" onClick={() => setOpen((o) => !o)}>
                {open ? "Hide" : isReview ? "Show checklist" : "Show me how"} {open ? "▲" : "▼"}
              </button>
            )}
            {open && (
              isReview ? (
                <ul className="fp-checklist">
                  {detail.map((c, i) => <li key={i}>{c}</li>)}
                </ul>
              ) : trackable ? (
                // Premium: each step is its own checkable row.
                <div className="fp-step-checks">
                  {detail.map((s, i) => {
                    const key = stepKey(i);
                    const done = isStepDone(key);
                    return (
                      <button
                        key={i}
                        className={`fp-step-check-row ${done ? "done" : ""}`}
                        onClick={() => onToggleStep(key)}
                      >
                        <span className={`fp-step-check-box ${done ? "done" : ""}`}>{done ? "✓" : ""}</span>
                        <span className="fp-step-check-text">{s}</span>
                      </button>
                    );
                  })}
                </div>
              ) : (
                <ol className="fp-steps-list">
                  {detail.map((s, i) => <li key={i}>{s}</li>)}
                </ol>
              )
            )}
            {open && !locked && item.fields?.length > 0 && (
              <div style={{ marginTop: 10 }}>
                {item.fields.map((f) => (
                  <div key={f.key} className="fp-field-row">
                    <label className="fp-label">{f.label}</label>
                    <input className="fp-input" placeholder={f.label} />
                  </div>
                ))}
              </div>
            )}
          </>
        )}
      </div>

      {locked && (
        <div className="fp-lock-overlay">
          <span className="fp-lock-icon">🔒</span>
        </div>
      )}
    </div>
  );
}

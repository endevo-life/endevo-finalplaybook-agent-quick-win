import { useState } from "react";

// Infer the right input type from a field's key/label, so "Date set up" gets a
// real date picker, phone fields get a tel keypad, emails an email keyboard,
// etc. Content only carries {key, label}; this keeps the UX smart without
// needing every field to declare a type.
function fieldInputType(f) {
  const s = `${f.key || ""} ${f.label || ""}`.toLowerCase();
  if (/\bdate\b|when|on\b|deadline|expir|renew/.test(s)) return "date";
  if (/phone|mobile|cell|tel\b/.test(s)) return "tel";
  if (/email|e-mail/.test(s)) return "email";
  return "text";
}

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
  fieldValues = {},
  onFieldChange,
}) {
  const isReview = item.resultType === "review";
  const detail = isReview ? item.checklist : item.steps;
  const hasDetail = detail && detail.length > 0;
  // Any unlocked card whose steps we can toggle is trackable -- including free
  // users on their "do these first" basics, so the plan never LOOKS pre-done:
  // every step is a visibly-empty checkbox the member ticks themselves.
  const trackable = !locked && typeof onToggleStep === "function";
  // Paid: show the checklist expanded by default so it's immediately workable.
  const [open, setOpen] = useState(trackable);

  // How many of this card's steps are done (for the little per-card badge).
  const doneCount = trackable && isStepDone
    ? detail.filter((_, i) => isStepDone(stepKey(i))).length
    : 0;
  const allDone = trackable && detail.length > 0 && doneCount === detail.length;

  return (
    <div className={`fp-action-card ${item.basic ? "basic" : ""} ${allDone ? "tracked-done" : ""} ${locked ? "fp-locked-card" : ""}`}>
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
              trackable ? (
                // Every unlocked step is its own checkable row (empty box until
                // the member ticks it) -- so the plan reads as "to do", never done.
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
                        <span className={`fp-step-check-box ${done ? "done" : ""}`} aria-hidden="true">{done ? "✓" : ""}</span>
                        <span className="fp-step-check-text">{s}</span>
                      </button>
                    );
                  })}
                </div>
              ) : isReview ? (
                <ul className="fp-checklist">
                  {detail.map((c, i) => <li key={i}>{c}</li>)}
                </ul>
              ) : (
                <ol className="fp-steps-list">
                  {detail.map((s, i) => <li key={i}>{s}</li>)}
                </ol>
              )
            )}
            {open && !locked && item.fields?.length > 0 && (
              <div style={{ marginTop: 10 }}>
                {item.fields.map((f) => {
                  const fk = `${item.id}::${f.key}`;
                  const type = fieldInputType(f);
                  return (
                    <div key={f.key} className="fp-field-row">
                      <label className="fp-label" htmlFor={fk}>{f.label}</label>
                      <input
                        id={fk}
                        type={type}
                        className="fp-input"
                        placeholder={type === "date" ? "" : f.label}
                        value={fieldValues[fk] || ""}
                        onChange={(e) => onFieldChange?.(fk, e.target.value)}
                      />
                    </div>
                  );
                })}
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

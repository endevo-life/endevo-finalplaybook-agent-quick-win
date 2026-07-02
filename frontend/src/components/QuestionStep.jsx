import GlossaryTerm from "./GlossaryTerm";

// Explicit (not auto-scanned) glossary wiring, scoped to the two questions
// where these terms actually appear in the real content library text.
const TERM_WIRING = {
  C2: [
    { match: "will", term: "Will" },
    { match: "power of attorney", term: "Power of attorney (financial)" },
    { match: "medical directive", term: "Power of attorney (healthcare) / medical advance directive" },
  ],
  C3: [
    { match: "will", term: "Will" },
    { match: "power of attorney", term: "Power of attorney (financial)" },
    { match: "medical directive", term: "Power of attorney (healthcare) / medical advance directive" },
  ],
};

function renderPromptText(step, glossary) {
  const wiring = TERM_WIRING[step.id];
  if (!wiring) return step.promptText;

  let parts = [step.promptText];
  wiring.forEach(({ match, term }) => {
    const next = [];
    parts.forEach((part) => {
      if (typeof part !== "string") { next.push(part); return; }
      const idx = part.toLowerCase().indexOf(match.toLowerCase());
      if (idx === -1) { next.push(part); return; }
      const before = part.slice(0, idx);
      const hit = part.slice(idx, idx + match.length);
      const after = part.slice(idx + match.length);
      if (before) next.push(before);
      next.push(
        <GlossaryTerm key={`${term}-${idx}`} term={term} glossary={glossary}>{hit}</GlossaryTerm>
      );
      if (after) next.push(after);
    });
    parts = next;
  });
  return parts;
}

export default function QuestionStep({ step, flags, onToggle, onSelectSingle, selectedLabel, glossary }) {
  const isSingle = step.type === "single";

  return (
    <div>
      <p className="fp-question-topic">{step.topic}</p>
      <p className="fp-question-text">{renderPromptText(step, glossary)}</p>
      <p className="fp-dim" style={{ marginBottom: 16 }}>
        {isSingle ? "Choose one." : "Check anything that applies — it's fine to check none."}
      </p>
      <div className="fp-choice-group">
        {step.options.map((opt) => {
          if (isSingle) {
            const checked = selectedLabel === opt.label;
            return (
              <label key={opt.label} className={`fp-choice ${checked ? "checked" : ""}`}>
                <input
                  type="radio"
                  name={step.id}
                  checked={checked}
                  onChange={() => onSelectSingle(step, opt)}
                />
                <span>{opt.label}</span>
              </label>
            );
          }
          const flagKey = Object.keys(opt.flags)[0];
          const checked = !!flags[flagKey];
          return (
            <label key={flagKey} className={`fp-choice ${checked ? "checked" : ""}`}>
              <input type="checkbox" checked={checked} onChange={() => onToggle(opt.flags)} />
              <span>{opt.label}</span>
            </label>
          );
        })}
      </div>
    </div>
  );
}

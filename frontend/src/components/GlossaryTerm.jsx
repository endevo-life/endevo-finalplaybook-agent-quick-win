import { useState } from "react";

// Inline "tap to define" term -- looks up its definition from the glossary
// list already fetched from GET /api/glossary (grounded content, nothing
// invented here). `term` must match a glossary entry's `term` field
// case-insensitively.
export default function GlossaryTerm({ term, glossary, children }) {
  const [open, setOpen] = useState(false);
  const entry = glossary?.find((g) => g.term.toLowerCase() === term.toLowerCase());

  if (!entry) return <>{children}</>;

  return (
    <span className="fp-popover-wrap">
      <button type="button" className="fp-term" onClick={() => setOpen((o) => !o)}>
        {children}
      </button>
      {open && (
        <span className="fp-popover" role="dialog">
          <p className="fp-popover-label">{entry.term}</p>
          <p className="fp-popover-def">{entry.shortDefinition}</p>
          <button type="button" className="fp-popover-close" onClick={() => setOpen(false)}>Close</button>
        </span>
      )}
    </span>
  );
}

import { useEffect, useRef, useState } from "react";

// The "feel lighter" momentum bar — gamification for BOTH tiers.
//
// Death-planning avoidance breaks through completed, celebrated action, not
// information. So this turns raw progress into a felt sense of relief: a warm
// progress meter, a count of what's been "lifted," and a rotating reassurance
// that reframes each step as weight off the member's shoulders (and their
// family's). No points, no streaks-as-pressure — just earned lightness.
//
// Props:
//   done, total — steps completed / available to this member (tier-aware; the
//                 parent passes only what this tier can actually check off).
//   tier        — "free" | "paid" (tunes the copy, not the mechanic).
//   justCompleted — increments when a step is ticked, to trigger a brief pulse.
const LINES_INPROGRESS = [
  "Every step here is one less thing your family has to figure out alone.",
  "You're doing the thing most people avoid. That counts.",
  "Small and done beats perfect and someday.",
  "This is weight coming off — yours and theirs.",
];
const LINE_START = "Start with one. The hardest part is beginning, and you already did.";
const LINE_DONE_FREE = "You've done the basics most people never do. That's real protection in place.";
const LINE_DONE_PAID = "Your playbook is complete. Your family will actually be able to use this.";

export default function Momentum({ done = 0, total = 0, tier = "free", justCompleted = 0 }) {
  const pct = total ? Math.round((done / total) * 100) : 0;
  const complete = total > 0 && done === total;
  const [pulse, setPulse] = useState(false);
  const prev = useRef(justCompleted);

  useEffect(() => {
    if (justCompleted !== prev.current) {
      prev.current = justCompleted;
      setPulse(true);
      const t = setTimeout(() => setPulse(false), 620);
      return () => clearTimeout(t);
    }
  }, [justCompleted]);

  const line = complete
    ? (tier === "paid" ? LINE_DONE_PAID : LINE_DONE_FREE)
    : done === 0
    ? LINE_START
    : LINES_INPROGRESS[done % LINES_INPROGRESS.length];

  return (
    <div className={`fp-momentum ${complete ? "complete" : ""} ${pulse ? "pulse" : ""}`}>
      <div className="fp-momentum-top">
        <span className="fp-momentum-count">
          {complete ? "All done" : `${done} of ${total} lifted`}
        </span>
        {complete && <span className="fp-momentum-badge" aria-hidden="true">✓</span>}
      </div>
      <div className="fp-momentum-track" role="progressbar" aria-valuenow={pct} aria-valuemin={0} aria-valuemax={100}>
        <div className="fp-momentum-fill" style={{ width: `${pct}%` }} />
      </div>
      <p className="fp-momentum-line">{line}</p>
    </div>
  );
}

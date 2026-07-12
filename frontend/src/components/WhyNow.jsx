import { useState } from "react";
import { WHY_NOW_SIGNALS } from "../config/whyNowSignals";
import { firstName } from "../config/branding";

// "Why now?" — the avoidance-breaking entry point (MOAT doc §1b).
//
// Reframes the ask from "plan your death" (which triggers avoidance) to "what
// brought you here?" (which honors the feeling that already got them to open the
// app). The member taps any signals that fit; the picks REORDER their plan so it
// leads with what moved them to act. No score, no judgment shown.
//
// This is a warm gate, not a quiz: skippable, multi-select, low-pressure. It
// takes ~15 seconds and makes the resulting plan feel like a 1:1 session.
export default function WhyNow({ user, picked, setPicked, onNext, onBack }) {
  const [sel, setSel] = useState(() => new Set(picked || []));
  const name = firstName(user?.name);

  function toggle(flag) {
    setSel((prev) => {
      const next = new Set(prev);
      next.has(flag) ? next.delete(flag) : next.add(flag);
      return next;
    });
  }

  function go() {
    setPicked?.([...sel]);
    onNext?.();
  }

  const count = sel.size;

  return (
    <div className="fp-page-narrow">
      <button onClick={onBack} className="fp-btn-back">← back</button>

      <h2 className="fp-h2" style={{ marginTop: 12 }}>
        {name ? `What brought you here, ${name}?` : "What brought you here?"}
      </h2>
      <p className="fp-body">
        Something moved you to start today. Tap whatever fits, we’ll lead with
        what matters most to you. There are no wrong answers, and you can pick
        more than one.
      </p>

      <div className="fp-whynow-grid" role="group" aria-label="What brought you here today">
        {WHY_NOW_SIGNALS.map((s) => {
          const on = sel.has(s.flag);
          return (
            <button
              key={s.flag}
              type="button"
              className={`fp-whynow-card${on ? " on" : ""}`}
              aria-pressed={on}
              onClick={() => toggle(s.flag)}
            >
              <span className="fp-whynow-check" aria-hidden="true">
                {on ? "✓" : ""}
              </span>
              <span className="fp-whynow-text">
                <span className="fp-whynow-label">{s.label}</span>
                <span className="fp-whynow-sub">{s.sub}</span>
              </span>
            </button>
          );
        })}
      </div>

      <div className="fp-whynow-actions">
        <button className="fp-btn" onClick={go} style={{ minWidth: 220 }}>
          {count === 0
            ? "Skip, just show me my plan →"
            : count === 1
            ? "Continue →"
            : `Continue with ${count} →`}
        </button>
        <p className="fp-whynow-reassure">
          This just orders your steps. Nothing here is shared or shown to anyone.
        </p>
      </div>
    </div>
  );
}

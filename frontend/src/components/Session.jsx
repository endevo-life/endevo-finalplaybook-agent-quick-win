import { useState } from "react";
import { STEPS } from "../data/contextQuestions";
import QuestionStep from "./QuestionStep";
import { postPlan } from "../api/client";

export default function Session({ user, flags, setFlags, glossary, onBack, onComplete }) {
  const visibleSteps = STEPS.filter((s) => !s.askIf || flags[s.askIf]);
  const [stepIndex, setStepIndex] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  // Which option label is selected per "single" (radio) step. Tracked
  // separately from `flags` because two distinct answers on the same
  // question can legitimately set the same flag value (e.g. D1's "Maybe"
  // and "No" both set noLegacyContact:true) -- deriving "selected" purely
  // from flag-matching made those options indistinguishable and unclickable.
  const [singleAnswers, setSingleAnswers] = useState({});

  const step = visibleSteps[stepIndex];
  const isLast = stepIndex === visibleSteps.length - 1;

  function toggle(optFlags) {
    const key = Object.keys(optFlags)[0];
    setFlags((f) => ({ ...f, [key]: !f[key] }));
  }

  // "single" (radio) steps: reset every flag key used anywhere on this step
  // first, then apply the selected option's flags -- robust even if options
  // target different keys, not just true/false on one shared key.
  function selectSingle(step, opt) {
    const allKeys = new Set();
    step.options.forEach((o) => Object.keys(o.flags).forEach((k) => allKeys.add(k)));
    setFlags((f) => {
      const reset = { ...f };
      allKeys.forEach((k) => { reset[k] = false; });
      return { ...reset, ...opt.flags };
    });
    setSingleAnswers((a) => ({ ...a, [step.id]: opt.label }));
  }

  async function next() {
    if (!isLast) {
      setStepIndex((i) => i + 1);
      return;
    }
    setLoading(true);
    setError("");
    try {
      const result = await postPlan({ flags, memberFirstName: user.name, tier: user.tier });
      onComplete(result);
    } catch (e) {
      setError(e.message || "Something went wrong — try again.");
    } finally {
      setLoading(false);
    }
  }

  function back() {
    if (stepIndex === 0) { onBack(); return; }
    setStepIndex((i) => i - 1);
  }

  return (
    <div className="fp-page-narrow">
      <button onClick={back} className="fp-btn-back">← back</button>

      <div className="fp-step-progress" style={{ marginTop: 12 }}>
        {visibleSteps.map((s, i) => (
          <div key={s.id} className={`fp-step-dot ${i < stepIndex ? "done" : i === stepIndex ? "active" : ""}`} />
        ))}
      </div>

      <div className="fp-card">
        <QuestionStep
          step={step}
          flags={flags}
          onToggle={toggle}
          onSelectSingle={selectSingle}
          selectedLabel={singleAnswers[step.id]}
          glossary={glossary}
        />
        {error && <p className="fp-error">{error}</p>}
        <button onClick={next} disabled={loading} className="fp-btn" style={{ width: "100%", marginTop: 8 }}>
          {loading ? "Building your plan…" : isLast ? "See my plan →" : "Next →"}
        </button>
      </div>
    </div>
  );
}

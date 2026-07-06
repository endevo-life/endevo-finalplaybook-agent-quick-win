import { useEffect, useState } from "react";
import { getAssessment, postAssessmentPlan, getPricing } from "../api/client";
import ActionCard from "./ActionCard";
import ChatWidget from "./ChatWidget";
import { PRODUCT_NAME } from "../config/branding";

// The chat backend grounds on a plan shape with actionItems/leadProfile. Adapt
// the assessment result (basicsFirst + domainItems) into that shape so a paid
// user can ask grounded questions about THIS plan, same as the other flow.
function toChatPlan(plan) {
  const items = [
    ...plan.basicsFirst.map((b) => ({ text: b.action, domain: b.domain })),
    ...plan.domainItems.map((d) => ({ text: d.action, domain: d.domain })),
  ];
  return {
    leadProfile: { id: "domain_assessment", name: "Your Final Playbook assessment" },
    actionItems: items,
    businessActionItems: [],
    digitalActionItems: [],
    quotes: [],
  };
}

// The condensed, deterministic domain assessment: a short set of high-impact
// questions (one per domain) → a light action plan (basics-first + one action
// per answer, steps tucked behind an expander). Free and anonymous — no LLM.
const TRACK_KEY = "fp_tracked_items";

export default function Assessment({ user, onBack, onUpgrade, isPaid }) {
  const [questions, setQuestions] = useState(null);
  const [idx, setIdx] = useState(0);
  const [answers, setAnswers] = useState({});
  const [plan, setPlan] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  // Premium item tracking, persisted locally so progress survives a refresh.
  const [tracked, setTracked] = useState(() => {
    try { return JSON.parse(localStorage.getItem(TRACK_KEY)) || {}; } catch { return {}; }
  });
  const [price, setPrice] = useState(25);

  useEffect(() => {
    getPricing()
      .then((p) => {
        const paid = p.plans?.find((x) => x.tier === "paid");
        if (paid?.priceUsdMonth) setPrice(paid.priceUsdMonth);
      })
      .catch(() => {});
  }, []);

  // Step-level tracking: each key is `${itemId}::${stepIndex}`.
  function toggleStep(key) {
    setTracked((prev) => {
      const next = { ...prev, [key]: !prev[key] };
      localStorage.setItem(TRACK_KEY, JSON.stringify(next));
      return next;
    });
  }
  const isStepDone = (key) => !!tracked[key];

  useEffect(() => {
    getAssessment()
      .then((d) => setQuestions(d.questions || []))
      .catch(() => setError("Couldn't load the assessment. Is the server running?"));
  }, []);

  if (error) return <div className="fp-page-narrow"><p className="fp-error">{error}</p></div>;
  if (!questions) return <div className="fp-page-narrow"><p className="fp-body">Loading…</p></div>;

  async function choose(qid, value) {
    const next = { ...answers, [qid]: value };
    setAnswers(next);
    if (idx < questions.length - 1) {
      setIdx(idx + 1);
    } else {
      setLoading(true);
      try {
        setPlan(await postAssessmentPlan(next));
      } catch (e) {
        setError(e.message || "Something went wrong.");
      } finally {
        setLoading(false);
      }
    }
  }

  // --- results view ---
  if (plan) {
    // Step-level progress (premium): count every step across every item.
    const stepKeyFor = (itemId, i) => `${itemId}::${i}`;
    const allItems = [...plan.basicsFirst, ...plan.domainItems];
    let totalSteps = 0;
    let doneSteps = 0;
    allItems.forEach((it) => {
      const steps = it.resultType === "review" ? [] : (it.steps || []);
      steps.forEach((_, i) => {
        totalSteps += 1;
        if (tracked[stepKeyFor(it.id, i)]) doneSteps += 1;
      });
    });
    const pct = totalSteps ? Math.round((doneSteps / totalSteps) * 100) : 0;

    // Free: basics shown fully; the domain plan is shown BLURRED (they see the
    // shape of their full playbook) with an unlock overlay. Premium: everything
    // interactive with per-step checkboxes.
    const renderCard = (item, locked) => (
      <ActionCard
        key={item.id}
        item={item}
        locked={locked}
        isStepDone={isStepDone}
        onToggleStep={toggleStep}
        stepKey={(i) => stepKeyFor(item.id, i)}
      />
    );

    return (
      <div className="fp-page">
        <button onClick={onBack} className="fp-btn-back">← start over</button>
        <h2 className="fp-h2" style={{ marginTop: 12 }}>
          {user?.name ? `${user.name}, here's` : "Here's"} your Final Playbook
        </h2>

        {isPaid ? (
          <>
            <p className="fp-body">
              Work through it step by step — check each off as you go. Ask the
              assistant (bottom-right) anything about a step.
            </p>
            <div className="fp-progress-bar-wrap">
              <div className="fp-progress-bar-fill" style={{ width: `${pct}%` }} />
            </div>
            <p className="fp-progress-label">{doneSteps} of {totalSteps} steps done · {pct}%</p>
          </>
        ) : (
          <p className="fp-body">
            These first two make everything else findable — do them today. Below is
            your full playbook. Unlock {PRODUCT_NAME} Premium to work through every
            step, track your progress, and get your AI guide.
          </p>
        )}

        <p className="fp-question-topic">Do these first</p>
        {plan.basicsFirst.map((b) => renderCard(b, false))}

        {plan.domainItems.length > 0 && (
          <>
            <p className="fp-question-topic" style={{ marginTop: 22 }}>Your Final Playbook</p>
            {/* Free sees these blurred; Premium sees them interactive. */}
            {plan.domainItems.map((d) => renderCard(d, !isPaid))}
          </>
        )}

        {/* Free: single unlock CTA under the blurred playbook. */}
        {!isPaid && plan.domainItems.length > 0 && (
          <div className="fp-lock-card">
            <p className="fp-lock-title">🔒 Your full playbook is ready</p>
            <p className="fp-lock-body">
              Unlock every step across your financial, digital, and physical plan —
              check items off, track your progress, and get an AI guide that walks
              you through your specific situation.
            </p>
            <button className="fp-btn-upgrade" onClick={onUpgrade}>Unlock Premium — ${price}/mo →</button>
          </div>
        )}

        {/* Chat: free users get a taste (limited queries), paid unlimited. */}
        <ChatWidget
          plan={toChatPlan(plan)}
          memberFirstName={user?.name || "there"}
          tier={isPaid ? "paid" : "free"}
          onUpgrade={onUpgrade}
        />
      </div>
    );
  }

  // --- question view (one at a time) ---
  const q = questions[idx];
  return (
    <div className="fp-page-narrow">
      <button onClick={idx === 0 ? onBack : () => setIdx(idx - 1)} className="fp-btn-back">← back</button>

      <div className="fp-step-progress" style={{ marginTop: 12 }}>
        {questions.map((_, i) => (
          <div key={i} className={`fp-step-dot ${i < idx ? "done" : i === idx ? "active" : ""}`} />
        ))}
      </div>

      <div className="fp-card">
        <span className="fp-domain-tag">{q.domain}</span>
        <p className="fp-question-text fp-assess-q">{q.question}</p>
        <div className="fp-choice-group">
          {q.options.map((o) => (
            <button
              key={o.value}
              className="fp-choice"
              disabled={loading}
              onClick={() => choose(q.id, o.value)}
            >
              <span>{o.label}</span>
            </button>
          ))}
        </div>
        {loading && <p className="fp-dim" style={{ marginTop: 12 }}>Building your plan…</p>}
      </div>
    </div>
  );
}

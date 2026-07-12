import { useEffect, useState } from "react";
import {
  getAssessment, postAssessmentPlan, postAssessmentPersonalize, getPricing,
  getMyPlan, saveMyPlan, getToken,
} from "../api/client";
import ActionCard from "./ActionCard";
import Momentum from "./Momentum";
import PlaybookPanel from "./PlaybookPanel";
import ChatWidget from "./ChatWidget";
import { PRODUCT_NAME, PLAYBOOK_NAME, firstName } from "../config/branding";
import { reorderBySignals, selectQuestions, buildIntro, questionPreamble } from "../config/whyNowSignals";

// The chat backend grounds on a plan shape with actionItems/leadProfile. Adapt
// the assessment result (basicsFirst + domainItems) into that shape so a paid
// user can ask grounded questions about THIS plan, same as the other flow.
function toChatPlan(plan) {
  // Include the steps/checklist so the AI can answer "how do I do this?" from the
  // detail we actually have -- not just the one-line action.
  const mapItem = (it) => ({
    text: it.action,
    domain: it.domain,
    steps: it.resultType === "review" ? it.checklist : it.steps,
  });
  const items = [...plan.basicsFirst.map(mapItem), ...plan.domainItems.map(mapItem)];
  return {
    leadProfile: { id: "domain_assessment", name: "My Final Playbook assessment" },
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
const FIELDS_KEY = "fp_field_values";

// Apply the "why now?" signals: reorder the situational domainItems so the plan
// LEADS with what moved this person to act (MOAT lever 1). basicsFirst is left
// untouched — those are deliberately always-first regardless of situation.
function applySignals(plan, signals) {
  if (!plan || !signals || signals.length === 0) return plan;
  return { ...plan, domainItems: reorderBySignals(plan.domainItems || [], signals) };
}

export default function Assessment({ user, signals = [], resume = false, onBack, onUpgrade, isPaid }) {
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
  // The actual info the member types into item fields (trusted person's name,
  // phone, dates, ...). Keyed `${itemId}::${fieldKey}`. This is what makes the
  // playbook a real, usable document — persisted + shown on the playbook + in PDF.
  const [fieldValues, setFieldValues] = useState(() => {
    try { return JSON.parse(localStorage.getItem(FIELDS_KEY)) || {}; } catch { return {}; }
  });
  const [price, setPrice] = useState(25);
  // Paid: the personalized 7-day narrative (LLM) generated from the answers.
  const [narrative, setNarrative] = useState(null);
  const [narrativeLoading, setNarrativeLoading] = useState(false);
  const [narrativeError, setNarrativeError] = useState("");

  async function getNarrative() {
    setNarrativeLoading(true);
    setNarrativeError("");
    try {
      const res = await postAssessmentPersonalize(answers, user?.name || "there", signals);
      setNarrative(res.personalized);
    } catch (e) {
      setNarrativeError(e.message || "Couldn't generate your personalized plan.");
    } finally {
      setNarrativeLoading(false);
    }
  }

  useEffect(() => {
    getPricing()
      .then((p) => {
        const paid = p.plans?.find((x) => x.tier === "paid");
        if (paid?.priceUsdMonth) setPrice(paid.priceUsdMonth);
      })
      .catch(() => {});
  }, []);

  // Bumped each time a step is newly checked, so Momentum can pulse/celebrate.
  const [completions, setCompletions] = useState(0);

  // Step-level tracking: each key is `${itemId}::${stepIndex}`.
  function toggleStep(key) {
    setTracked((prev) => {
      const wasDone = !!prev[key];
      const next = { ...prev, [key]: !wasDone };
      localStorage.setItem(TRACK_KEY, JSON.stringify(next));
      if (!wasDone) setCompletions((c) => c + 1); // ticking ON = a win
      return next;
    });
  }

  // Save a field value the member typed (keyed `${itemId}::${fieldKey}`). This
  // is what the playbook document actually records and can download.
  function setField(key, value) {
    setFieldValues((prev) => {
      const next = { ...prev, [key]: value };
      localStorage.setItem(FIELDS_KEY, JSON.stringify(next));
      return next;
    });
  }
  const isStepDone = (key) => !!tracked[key];

  useEffect(() => {
    getAssessment()
      // Gate + order the questions by the member's "why now?" signals: hide
      // situational questions that don't apply, lead with what's urgent for them.
      .then((d) => setQuestions(selectQuestions(d.questions || [], signals)))
      .catch(() => setError("Couldn't load the assessment. Is the server running?"));
  }, [signals]);

  // On mount for a logged-in user: restore their saved answers, plan, progress,
  // and narrative from the server so they resume where they left off (any device).
  //
  // ONLY when `resume` is set (they arrived via "Sign in" as a returning member).
  // When they came through the new-assessment flow (Why now?), we must NOT jump
  // to an old saved plan — they intend to take the questions fresh.
  useEffect(() => {
    if (!getToken() || !resume) return;
    getMyPlan()
      .then((saved) => {
        if (saved.tracked && Object.keys(saved.tracked).length) setTracked(saved.tracked);
        if (saved.fields && Object.keys(saved.fields).length) setFieldValues(saved.fields);
        if (saved.narrative) setNarrative(saved.narrative);
        // If they have a saved plan and answered questions, jump straight to it.
        if (saved.plan && saved.answers && Object.keys(saved.answers).length) {
          setAnswers(saved.answers);
          setPlan(saved.plan);
        }
      })
      .catch(() => {});
  }, [resume]);

  // Auto-save the user's plan + progress + fields + narrative to the server
  // whenever any of them change (logged-in only). Debounced 600ms so typing into
  // a field doesn't fire a request per keystroke. This is what makes "log in
  // later on any device, get it all back" work.
  useEffect(() => {
    if (!getToken() || !plan) return;
    const t = setTimeout(() => {
      saveMyPlan({ answers, plan, tracked, narrative, fields: fieldValues }).catch(() => {});
    }, 600);
    return () => clearTimeout(t);
  }, [plan, tracked, narrative, fieldValues]);

  if (error) return <div className="fp-page-narrow"><p className="fp-error">{error}</p></div>;
  if (!questions) return <div className="fp-page-narrow"><p className="fp-body">Loading…</p></div>;

  // Clear the current plan + answers and return to question #1, so the member
  // can retake the assessment (e.g. after changing their "why now?" signals).
  // Without this, a signed-in user with a saved plan is bounced straight back to
  // that plan and can never re-answer.
  function startOver() {
    setPlan(null);
    setAnswers({});
    setNarrative(null);
    setIdx(0);
  }

  async function choose(qid, value) {
    const next = { ...answers, [qid]: value };
    setAnswers(next);
    if (idx < questions.length - 1) {
      setIdx(idx + 1);
    } else {
      setLoading(true);
      try {
        setPlan(applySignals(await postAssessmentPlan(next), signals));
      } catch (e) {
        setError(e.message || "Something went wrong.");
      } finally {
        setLoading(false);
      }
    }
  }

  // --- results view ---
  if (plan) {
    const stepKeyFor = (itemId, i) => `${itemId}::${i}`;

    // Free users get a "taste": the basics PLUS the first domain item are fully
    // unlocked and checkable; the rest of the domain plan stays blurred as the
    // upgrade driver. Paid users have everything unlocked.
    const freeUnlockedDomain = isPaid ? plan.domainItems : plan.domainItems.slice(0, 1);
    const isLocked = (item, inDomain) =>
      inDomain && !isPaid && !freeUnlockedDomain.includes(item);

    // Momentum counts only what THIS tier can actually check off (never counts
    // blurred items — so the meter reflects real, earned progress).
    const countableItems = isPaid
      ? [...plan.basicsFirst, ...plan.domainItems]
      : [...plan.basicsFirst, ...freeUnlockedDomain];
    let totalSteps = 0;
    let doneSteps = 0;
    countableItems.forEach((it) => {
      const steps = it.resultType === "review" ? (it.checklist || []) : (it.steps || []);
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
        fieldValues={fieldValues}
        onFieldChange={setField}
      />
    );

    // Flattened items for the live playbook panel (right side). Basics + the
    // unlocked-for-free first domain item render normally; the rest are `locked`
    // for free (shown crossed out) and open for paid.
    const panelItems = [
      ...plan.basicsFirst.map((it) => ({ ...it, locked: false, steps: it.resultType === "review" ? it.checklist : it.steps })),
      ...plan.domainItems.map((it) => ({ ...it, locked: isLocked(it, true), steps: it.resultType === "review" ? it.checklist : it.steps })),
    ];
    const doneKeys = { has: (k) => !!tracked[k] };

    return (
      <div className="fp-page fp-results-layout">
      <div className="fp-results-main">
        <div style={{ display: "flex", gap: 16, alignItems: "center" }}>
          <button onClick={onBack} className="fp-btn-back">← home</button>
          <button onClick={startOver} className="fp-btn-back">↻ retake assessment</button>
        </div>
        <h2 className="fp-h2" style={{ marginTop: 12 }}>
          {firstName(user?.name) ? `${firstName(user.name)}, here's ${PLAYBOOK_NAME}` : `Here's ${PLAYBOOK_NAME}`}
        </h2>

        {isPaid ? (
          <>
            <p className="fp-body">
              Work through it step by step, check each off as you go. Ask the
              assistant (bottom-right) anything about a step.
            </p>
            <div className="fp-progress-bar-wrap">
              <div className="fp-progress-bar-fill" style={{ width: `${pct}%` }} />
            </div>
            <p className="fp-progress-label">{doneSteps} of {totalSteps} steps done · {pct}%</p>

            {/* Personalized 7-day narrative (the paid LLM feature). */}
            {!narrative ? (
              <div className="fp-personalized-cta">
                <div>
                  <p className="fp-personalized-cta-title">Your personalized next 7 days</p>
                  <p className="fp-personalized-cta-sub">
                    Get a warm, personal walk-through of exactly what to do this week,
                    written for your situation.
                  </p>
                </div>
                <button className="fp-btn" onClick={getNarrative} disabled={narrativeLoading}>
                  {narrativeLoading ? "Writing your plan…" : "Generate →"}
                </button>
              </div>
            ) : (
              <div className="fp-personalized">
                <p className="fp-question-topic">Your next 7 days, personalized</p>
                <h3 style={{ margin: "0 0 12px" }}>{narrative.headline}</h3>
                {narrative.steps.map((s, i) => (
                  <div key={i} style={{ marginBottom: 12 }}>
                    <p className="fp-item-text" style={{ fontWeight: 600 }}>{s.step}</p>
                    <p className="fp-dim">{s.why_it_matters}</p>
                    {s.script && <p className="fp-item-script">"{s.script}"</p>}
                  </div>
                ))}
                <p className="fp-body" style={{ marginTop: 12, marginBottom: 0 }}>{narrative.closing_note}</p>
              </div>
            )}
            {narrativeError && <p className="fp-error">{narrativeError}</p>}
          </>
        ) : (
          <p className="fp-body">
            These first two make everything else findable, do them today. Below is
            your full playbook. Unlock {PRODUCT_NAME} Premium to work through every
            step, track your progress, and get your AI guide.
          </p>
        )}

        {/* Gamified momentum, both tiers. Turns progress into felt relief. */}
        {totalSteps > 0 && (
          <Momentum done={doneSteps} total={totalSteps} tier={isPaid ? "paid" : "free"} justCompleted={completions} />
        )}

        <p className="fp-question-topic">Do these first</p>
        {plan.basicsFirst.map((b) => renderCard(b, false))}

        {plan.domainItems.length > 0 && (
          <>
            <p className="fp-question-topic" style={{ marginTop: 22 }}>{PLAYBOOK_NAME}</p>
            {/* Free: first item unlocked as a taste, the rest blurred. Paid: all. */}
            {plan.domainItems.map((d) => renderCard(d, isLocked(d, true)))}
          </>
        )}

        {/* Free: single unlock CTA under the blurred playbook. */}
        {!isPaid && plan.domainItems.length > 0 && (
          <div className="fp-lock-card">
            <p className="fp-lock-title">🔒 The rest of {PLAYBOOK_NAME} is ready</p>
            <p className="fp-lock-body">
              You've felt how the first step works. Unlock every remaining step across
              your financial, digital, and physical plan, check them off, keep your
              momentum, and get an AI guide that walks you through your situation.
            </p>
            <button className="fp-btn-upgrade" onClick={onUpgrade}>Unlock Premium, ${price}/mo →</button>
          </div>
        )}

      </div>{/* /fp-results-main */}

        {/* The live playbook document, small panel on the RIGHT. Starts empty,
            fills in as the member checks items or enters info. */}
        <PlaybookPanel
          name={firstName(user?.name)}
          items={panelItems}
          doneKeys={doneKeys}
          fieldValues={fieldValues}
          isPaid={isPaid}
          onUpgrade={onUpgrade}
        />

        {/* Chat: free users get a taste (limited queries), paid unlimited. */}
        <ChatWidget
          plan={toChatPlan(plan)}
          memberFirstName={user?.name || "there"}
          tier={isPaid ? "paid" : "free"}
          signals={signals}
          onUpgrade={onUpgrade}
        />
      </div>
    );
  }

  // --- question view (one at a time) ---
  const q = questions[idx];
  const intro = buildIntro(signals, firstName(user?.name));
  return (
    <div className="fp-page-narrow">
      <button onClick={idx === 0 ? onBack : () => setIdx(idx - 1)} className="fp-btn-back">← back</button>

      {/* Personalized, compounding intro on the first question, makes the whole
          assessment feel like it was built for THIS person's situation. */}
      {idx === 0 && intro && (
        <div className="fp-assess-intro" style={{ marginTop: 12 }}>{intro}</div>
      )}

      <div className="fp-step-progress" style={{ marginTop: 12 }}>
        {questions.map((_, i) => (
          <div key={i} className={`fp-step-dot ${i < idx ? "done" : i === idx ? "active" : ""}`} />
        ))}
      </div>

      <div className="fp-card">
        <span className="fp-domain-tag">{q.domain}</span>
        {questionPreamble(q, signals) && (
          <p className="fp-question-preamble">{questionPreamble(q, signals)}</p>
        )}
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

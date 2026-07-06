import { useState } from "react";
import { PERSONALIZED_VOICE_LABEL } from "../config/branding";

export default function Identify({ user, setUser, isPaid, onSignIn, onNext, onBack }) {
  const [err, setErr] = useState("");

  // "Personalized" is only selectable by a user with a live paid entitlement.
  // A non-entitled user clicking it is nudged to sign in / upgrade instead of
  // silently sending tier="paid" (which the server rejects with 402).
  function pickPaid() {
    if (isPaid) {
      setUser({ ...user, tier: "paid" });
    } else if (onSignIn) {
      onSignIn();
    }
  }

  function go() {
    if (!user.name.trim()) {
      setErr("Please enter your first name.");
      return;
    }
    setErr("");
    onNext();
  }

  return (
    <div className="fp-page-narrow">
      <button onClick={onBack} className="fp-btn-back">← back</button>
      <h2 className="fp-h2" style={{ marginTop: 12 }}>Let's start with your name</h2>
      <p className="fp-body">Just your first name — no account needed to try this out.</p>
      <div className="fp-card">
        <label className="fp-label">First name</label>
        <input
          className="fp-input"
          value={user.name}
          onChange={(e) => { setUser({ ...user, name: e.target.value }); setErr(""); }}
          onKeyDown={(e) => e.key === "Enter" && go()}
          placeholder="Elisa"
          autoFocus
        />

        <label className="fp-label" style={{ marginTop: 20 }}>Which plan?</label>
        <div className="fp-choice-group">
          <label className={`fp-choice ${user.tier === "trial" ? "checked" : ""}`}>
            <input
              type="radio"
              name="tier"
              checked={user.tier === "trial"}
              onChange={() => setUser({ ...user, tier: "trial" })}
            />
            <span>
              <strong>Free</strong> — rules-based plan, no AI narrative
            </span>
          </label>
          <label className={`fp-choice ${user.tier === "paid" ? "checked" : ""}`}>
            <input
              type="radio"
              name="tier"
              checked={user.tier === "paid"}
              onChange={pickPaid}
            />
            <span>
              <strong>Personalized</strong> — adds {PERSONALIZED_VOICE_LABEL}
              {!isPaid && <span className="fp-dim"> · sign in to unlock</span>}
            </span>
          </label>
        </div>

        {err && <p className="fp-error">{err}</p>}
        <button onClick={go} className="fp-btn" style={{ width: "100%", marginTop: 20 }}>
          Continue →
        </button>
      </div>
    </div>
  );
}

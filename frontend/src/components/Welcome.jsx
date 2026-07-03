import { useState } from "react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faListCheck, faShieldHalved, faHeart, faCirclePlay } from "@fortawesome/free-solid-svg-icons";
import { LOGO_URL } from "../config/branding";

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

const STEPS = [
  { icon: faListCheck, label: "Plan", body: "Answer a few quick questions and get a clear, prioritized action plan for your situation." },
  { icon: faShieldHalved, label: "Protect", body: "Cover the essentials — legal, financial, health, and digital — so nothing falls through the cracks." },
  { icon: faHeart, label: "Peace", body: "Walk away knowing your people won't be left guessing. Live fully, die ready." },
];

export default function Welcome({ user, setUser, onNext }) {
  const [err, setErr] = useState("");
  const isPaid = user.tier === "paid";

  function go() {
    if (!user.name.trim()) {
      setErr("Please enter your first name.");
      return;
    }
    if (isPaid && !EMAIL_PATTERN.test(user.email.trim())) {
      setErr("Please enter a valid email — the personalized plan needs one.");
      return;
    }
    setErr("");
    onNext();
  }

  return (
    <div className="fp-page-narrow" style={{ textAlign: "center" }}>
      {LOGO_URL ? (
        <img src={LOGO_URL} alt="Final Playbook" style={{ width: 60, height: 60, borderRadius: 16, margin: "0 auto 28px", objectFit: "contain" }} />
      ) : (
        <div className="fp-logo" style={{ width: 60, height: 60, borderRadius: 16, fontSize: 24, margin: "0 auto 28px" }}>E</div>
      )}
      <h1 className="fp-h1">My Final Playbook</h1>
      <p className="fp-body" style={{ maxWidth: 440, marginLeft: "auto", marginRight: "auto" }}>
        A calm, guided walkthrough to help you get your affairs in order — so the people you love
        are never left guessing. No jargon. Just a plan.
      </p>

      <div className="fp-video-placeholder fp-video-placeholder-image" style={{ width: 180, aspectRatio: "16 / 9", margin: "0 auto 24px" }}>
        <img src="/jesse.png" alt="" />
        <div className="fp-video-placeholder-overlay">
          <FontAwesomeIcon icon={faCirclePlay} style={{ width: 20, height: 20 }} />
        </div>
      </div>

      <div className="fp-steps-row">
        {STEPS.map((s) => (
          <div key={s.label} className="fp-step-card">
            <FontAwesomeIcon icon={s.icon} style={{ fontSize: 18, color: "var(--accent)" }} />
            <p className="fp-step-label">{s.label}</p>
            <p className="fp-step-body">{s.body}</p>
          </div>
        ))}
      </div>

      <div className="fp-card" style={{ marginTop: 24, textAlign: "left" }}>
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
            <span><strong>Free</strong> — rules-based plan, no AI narrative</span>
          </label>
          <label className={`fp-choice ${user.tier === "paid" ? "checked" : ""}`}>
            <input
              type="radio"
              name="tier"
              checked={user.tier === "paid"}
              onChange={() => setUser({ ...user, tier: "paid" })}
            />
            <span><strong>Personalized</strong> — adds a short narrative in Niki's voice</span>
          </label>
        </div>

        {isPaid && (
          <>
            <label className="fp-label" style={{ marginTop: 20 }}>Email</label>
            <input
              className="fp-input"
              type="email"
              value={user.email}
              onChange={(e) => { setUser({ ...user, email: e.target.value }); setErr(""); }}
              onKeyDown={(e) => e.key === "Enter" && go()}
              placeholder="elisa@email.com"
            />
            <p className="fp-dim" style={{ marginTop: 6 }}>We'll use this for your personalized plan and upgrade.</p>
          </>
        )}

        {err && <p className="fp-error">{err}</p>}
        <button onClick={go} className="fp-btn" style={{ width: "100%", marginTop: 20 }}>
          Get started →
        </button>
      </div>
    </div>
  );
}

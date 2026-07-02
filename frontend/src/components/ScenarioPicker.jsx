import { useState } from "react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { SCENARIOS, BUSINESS_OWNER_FLAG } from "../data/flagMap";

export default function ScenarioPicker({ user, flags, setFlags, onNext, onBack }) {
  const [pickedId, setPickedId] = useState(null);
  const [subchoiceFlags, setSubchoiceFlags] = useState({});
  const picked = SCENARIOS.find((s) => s.id === pickedId);

  function pick(scenario) {
    setPickedId(scenario.id);
    setSubchoiceFlags({});
    setFlags({ ...flags, ...scenario.baseFlags });
  }

  function toggleSubchoice(flag) {
    setSubchoiceFlags((prev) => {
      const next = { ...prev, [flag]: !prev[flag] };
      setFlags((f) => ({ ...f, ...next }));
      return next;
    });
  }

  function toggleBusinessOwner() {
    setFlags((f) => ({ ...f, [BUSINESS_OWNER_FLAG]: !f[BUSINESS_OWNER_FLAG] }));
  }

  const canContinue = picked && (!picked.needsSubchoice || Object.values(subchoiceFlags).some(Boolean));

  return (
    <div className="fp-page">
      <button onClick={onBack} className="fp-btn-back">← back</button>
      <h2 className="fp-h2" style={{ marginTop: 12 }}>What brings you here, {user.name}?</h2>
      <p className="fp-body">Pick what feels most pressing. You'll get a chance to add more detail next.</p>

      <div className="fp-card-grid">
        {SCENARIOS.map((s) => (
          <button
            key={s.id}
            onClick={() => pick(s)}
            className={`fp-scenario-card ${pickedId === s.id ? "selected" : ""}`}
          >
            <FontAwesomeIcon icon={s.icon} className="fp-scenario-icon" />
            <p className="fp-scenario-title">{s.title}</p>
            <p className="fp-scenario-sub">{s.sub}</p>
          </button>
        ))}
      </div>

      {picked?.needsSubchoice && (
        <div className="fp-card" style={{ marginTop: 16 }}>
          <p className="fp-label">{picked.subchoiceQuestion}</p>
          <div className="fp-choice-group">
            {picked.subchoiceOptions.map((opt) => (
              <label key={opt.flag} className={`fp-choice ${subchoiceFlags[opt.flag] ? "checked" : ""}`}>
                <input
                  type="checkbox"
                  checked={!!subchoiceFlags[opt.flag]}
                  onChange={() => toggleSubchoice(opt.flag)}
                />
                <span>{opt.label}</span>
              </label>
            ))}
          </div>
        </div>
      )}

      <div className="fp-toggle-row">
        <div>
          <p style={{ margin: 0, fontSize: 14, color: "var(--ink)", fontWeight: 500 }}>I also own a business</p>
          <p className="fp-dim" style={{ margin: "2px 0 0" }}>Adds a separate business-planning checklist alongside your personal plan</p>
        </div>
        <label className="fp-switch">
          <input type="checkbox" checked={!!flags[BUSINESS_OWNER_FLAG]} onChange={toggleBusinessOwner} />
          <span className="fp-switch-track"><span className="fp-switch-thumb" /></span>
        </label>
      </div>

      <button onClick={onNext} disabled={!canContinue} className="fp-btn" style={{ marginTop: 24 }}>
        Continue →
      </button>
    </div>
  );
}

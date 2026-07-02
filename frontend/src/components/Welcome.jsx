import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faBullseye, faBookOpen, faFileLines } from "@fortawesome/free-solid-svg-icons";
import { LOGO_URL } from "../config/branding";

export default function Welcome({ onStart }) {
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
      <button onClick={onStart} className="fp-btn" style={{ padding: "14px 32px", fontSize: 15 }}>
        Get started →
      </button>
      <div style={{ display: "flex", gap: 24, justifyContent: "center", marginTop: 44, flexWrap: "wrap" }}>
        {[
          [faBullseye, "Personalized to your situation"],
          [faBookOpen, "Plain-English definitions along the way"],
          [faFileLines, "Download your plan anytime"],
        ].map(([icon, text]) => (
          <div key={text} style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 8, maxWidth: 130 }}>
            <FontAwesomeIcon icon={icon} style={{ fontSize: 22, color: "var(--accent)" }} />
            <span className="fp-dim" style={{ lineHeight: 1.4 }}>{text}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

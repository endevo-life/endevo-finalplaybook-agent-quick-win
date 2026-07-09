import { PRODUCT_NAME, TAGLINE, PRIMARY_CTA } from "../config/branding";
import Pricing from "./Pricing";
import landingVideo from "../assets/video_landing/MyFinalPlaybook Video (music).mp4";

// Public marketing page. Positioning (per growth strategy): we own DIGITAL death
// — the questions nobody else answers. The product is fear reduction: turn "what
// happens to my accounts, photos, phone, money when I'm gone?" into a plan.

// High-anxiety questions — the exact hooks that convert (from the content model).
const FEARS = [
  "Who can unlock your phone if you're gone?",
  "Can your family reach your online banking — past the 2FA?",
  "What happens to your photos and a lifetime of memories?",
  "Could anyone actually access your crypto or digital wallet?",
  "Who handles your Instagram, email, and work accounts?",
  "Do your beneficiaries even know what they'd inherit?",
];

const PREMIUM = [
  ["Track every item", "Check off progress and watch your playbook come together — your plan, saved."],
  ["Build side by side", "Work through each action with the exact steps, scripts, and fields as you go."],
  ["AI assistant", "Ask anything about your situation. Grounded in your plan — never guesses, never invents."],
  ["Your full plan", "Every personalized action across all domains, prioritized for you."],
];

export default function Landing({ onStart, onSignIn, onUpgrade, isPaid }) {
  return (
    <div>
      {/* Hero — fear reduction, not feature list */}
      <div className="fp-hero">
        <p className="fp-hero-eyebrow">{PRODUCT_NAME} · Digital + Legacy Planning</p>
        <h1>When you're gone, will your family be locked out of everything?</h1>
        <p className="fp-hero-sub">
          Your phone, your accounts, your money, your memories — all behind passwords no
          one else has. {PRODUCT_NAME} turns that fear into a clear, calm plan you can
          start in minutes. <strong>{TAGLINE}</strong>
        </p>
        <div className="fp-hero-cta-row">
          <button className="fp-btn" style={{ padding: "14px 30px", fontSize: 15 }} onClick={onStart}>
            {PRIMARY_CTA} →
          </button>
          <button className="fp-btn-secondary" onClick={onSignIn}>Sign in</button>
        </div>
        <p className="fp-hero-note">Free to start · No account needed to try · Not legal, financial, or medical advice</p>
      </div>

      {/* Explainer video — "What happens to your digital life when you die" */}
      <div className="fp-section" style={{ paddingTop: 8 }}>
        <video
          className="fp-video"
          src={landingVideo}
          controls
          preload="metadata"
          playsInline
          aria-label="What happens to your digital life when you die (2 min)"
        >
          Your browser doesn’t support embedded video.
        </video>
      </div>

      {/* The fears we answer */}
      <div className="fp-section">
        <h2 className="fp-section-title">The questions no one else answers</h2>
        <p className="fp-section-lead">
          Everyone plans for the will and the funeral. Almost no one plans for the
          digital life that now outlives us. That's the gap we close.
        </p>
        <div className="fp-fear-grid">
          {FEARS.map((f) => (
            <div key={f} className="fp-fear-card">{f}</div>
          ))}
        </div>
        <div style={{ textAlign: "center", marginTop: 28 }}>
          <button className="fp-btn" style={{ padding: "13px 28px" }} onClick={onStart}>
            Find your gaps — free →
          </button>
        </div>
      </div>

      {/* How it works */}
      <div className="fp-section">
        <h2 className="fp-section-title">How it works</h2>
        <p className="fp-section-lead">Three steps. Most people get a usable plan in under five minutes.</p>
        <div className="fp-steps">
          {[
            ["1", "Answer a few questions", "Quick, plain-language questions about your digital, legal, financial, and health readiness. No jargon."],
            ["2", "Get your gaps + first steps", "We show you exactly where you're exposed and the two things to do first — free."],
            ["3", "Go Premium to finish it", "Unlock your full plan, track every item, build it side by side, and get an AI assistant for your situation."],
          ].map(([num, title, body]) => (
            <div key={num} className="fp-step-card">
              <div className="fp-step-num">{num}</div>
              <h3>{title}</h3>
              <p>{body}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Premium value */}
      <div className="fp-section">
        <h2 className="fp-section-title">Premium does the work with you</h2>
        <p className="fp-section-lead">
          Free shows you the gaps. Premium is where you actually close them.
        </p>
        <div className="fp-card-grid">
          {PREMIUM.map(([title, body]) => (
            <div key={title} className="fp-step-card">
              <h3 style={{ marginTop: 0 }}>{title}</h3>
              <p>{body}</p>
            </div>
          ))}
        </div>
      </div>

      <Pricing onUpgrade={onUpgrade} isPaid={isPaid} />

      <div className="fp-section" style={{ textAlign: "center", paddingTop: 8 }}>
        <h2 className="fp-section-title" style={{ marginBottom: 18 }}>{TAGLINE}</h2>
        <button className="fp-btn" style={{ padding: "14px 30px", fontSize: 15 }} onClick={onStart}>
          {PRIMARY_CTA} — it's free →
        </button>
      </div>
    </div>
  );
}

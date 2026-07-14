import { SEAL_LABELS, BADGE_COPY } from "../config/branding";

// The earned "wax seal" a member gets for finishing a whole domain, and the
// final "playbook complete" badge. Pure presentational -- the parent decides
// WHEN to render these (from lib/completion.js). `fresh` triggers the one-time
// stamp animation; without it the seal just shows (used on re-renders and in
// the reduced-motion / PDF cases). All motion is CSS; respects
// prefers-reduced-motion via the .fp-seal keyframes in global.css.

// A short "Jul 13, 2026" date for the seal/badge stamp.
function prettyDate(d = new Date()) {
  return d.toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });
}
// A "Jul 13, 2026 · 3:42 PM" stamp for the final badge -- makes it feel like a
// captured moment.
function prettyDateTime(d = new Date()) {
  const t = d.toLocaleTimeString(undefined, { hour: "numeric", minute: "2-digit" });
  return `${prettyDate(d)} · ${t}`;
}

// One domain seal. `domain` is the key (legal/financial/health/digital);
// `date` lets callers pass a fixed stamp (e.g. the moment it was earned).
export function DomainSeal({ domain, fresh = false, date }) {
  const label = SEAL_LABELS[domain] || domain;
  return (
    <span className={`fp-seal ${fresh ? "fp-seal-fresh" : ""}`} role="img" aria-label={`${label} — sealed`}>
      <svg className="fp-seal-ring" viewBox="0 0 48 48" aria-hidden="true">
        <circle cx="24" cy="24" r="21" className="fp-seal-disc" />
        <path d="M16 24.5l5.5 5.5L33 18.5" className="fp-seal-check" fill="none" />
      </svg>
      <span className="fp-seal-text">
        <span className="fp-seal-label">{label}</span>
        <span className="fp-seal-date">{date || prettyDate()}</span>
      </span>
    </span>
  );
}

// The final badge, awarded when every domain is sealed.
export function CompleteBadge({ name, fresh = false, when }) {
  const stamp = when || prettyDateTime();
  return (
    <div className={`fp-badge ${fresh ? "fp-badge-fresh" : ""}`} role="img"
         aria-label={`${BADGE_COPY.title} — ${stamp}`}>
      <span className="fp-badge-star" aria-hidden="true">★</span>
      <span className="fp-badge-title">{BADGE_COPY.title}</span>
      {name && <span className="fp-badge-name">{name}</span>}
      <span className="fp-badge-when">{stamp}</span>
      <span className="fp-badge-sub">{BADGE_COPY.sub}</span>
    </div>
  );
}

export { prettyDate, prettyDateTime };

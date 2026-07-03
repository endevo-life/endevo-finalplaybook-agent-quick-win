import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { DOMAINS } from "../styles/tokens";

export default function DomainSectionTeaser({ domainKey, items, onUpgradeClick }) {
  const info = DOMAINS[domainKey] || { label: "Other", color: "var(--dim)" };

  if (items.length === 0) {
    return (
      <div className="fp-domain-section" style={{ borderLeftColor: info.color }}>
        <div className="fp-domain-header">
          <span className="fp-domain-dot" style={{ background: info.color }} />
          <span className="fp-domain-label" style={{ color: info.color }}>
            {info.icon && <FontAwesomeIcon icon={info.icon} />} {info.label}
          </span>
        </div>
        <p className="fp-empty-domain">Not part of this plan</p>
      </div>
    );
  }

  // Show the first item in full as a real preview/demo of this domain's
  // guidance -- blur the rest. Gives every domain at least one genuinely
  // useful, readable item on the free tier, not just a locked count.
  const [shown, ...rest] = items;

  return (
    <div className="fp-domain-section" style={{ borderLeftColor: info.color }}>
      <div className="fp-domain-header">
        <span className="fp-domain-dot" style={{ background: info.color }} />
        <span className="fp-domain-label" style={{ color: info.color }}>
          {info.icon && <FontAwesomeIcon icon={info.icon} />} {info.label}
        </span>
        <span className="fp-domain-count-badge">{items.length}</span>
      </div>

      <div className="fp-item-row">
        <span className="fp-item-check" />
        <div>
          <p className="fp-item-text">{shown.text}</p>
          {shown.script && <p className="fp-item-script">"{shown.script}"</p>}
        </div>
      </div>

      {rest.map((item, i) => (
        <div key={i} className="fp-item-row fp-item-row-blurred">
          <span className="fp-item-check" />
          <p className="fp-item-text fp-blur-text">{item.text}</p>
        </div>
      ))}

      {rest.length > 0 && (
        <button type="button" className="fp-teaser-cta" onClick={onUpgradeClick}>
          Unlock {rest.length} more step{rest.length > 1 ? "s" : ""} in {info.label} →
        </button>
      )}
    </div>
  );
}

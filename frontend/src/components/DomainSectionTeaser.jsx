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

  return (
    <div className="fp-domain-section" style={{ borderLeftColor: info.color }}>
      <div className="fp-domain-header">
        <span className="fp-domain-dot" style={{ background: info.color }} />
        <span className="fp-domain-label" style={{ color: info.color }}>
          {info.icon && <FontAwesomeIcon icon={info.icon} />} {info.label}
        </span>
        <span className="fp-domain-count-badge">{items.length}</span>
      </div>
      {items.map((item, i) => (
        <div key={i} className="fp-item-row fp-item-row-blurred">
          <span className="fp-item-check" />
          <p className="fp-item-text fp-blur-text">{item.text}</p>
        </div>
      ))}
      <button type="button" className="fp-teaser-cta" onClick={onUpgradeClick}>
        Unlock {items.length} more step{items.length > 1 ? "s" : ""} in {info.label} →
      </button>
    </div>
  );
}

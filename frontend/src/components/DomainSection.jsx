import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { DOMAINS } from "../styles/tokens";
import ActionItemRow from "./ActionItemRow";

export default function DomainSection({ domainKey, items, doneSet, onToggleItem }) {
  const info = DOMAINS[domainKey] || { label: "Other", color: "var(--dim)", icon: null };

  return (
    <div className="fp-domain-section" style={{ borderLeftColor: info.color }}>
      <div className="fp-domain-header">
        <span className="fp-domain-dot" style={{ background: info.color }} />
        <span className="fp-domain-label" style={{ color: info.color }}>
          {info.icon && <FontAwesomeIcon icon={info.icon} />} {info.label}
        </span>
      </div>
      {items.length === 0 ? (
        <p className="fp-empty-domain">Not part of this plan</p>
      ) : (
        items.map((item) => (
          <ActionItemRow
            key={item.text}
            item={item}
            done={doneSet.has(item.text)}
            onToggle={() => onToggleItem(item.text)}
          />
        ))
      )}
    </div>
  );
}

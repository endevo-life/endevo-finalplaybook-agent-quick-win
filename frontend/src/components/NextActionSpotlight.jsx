import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { DOMAINS } from "../styles/tokens";

export default function NextActionSpotlight({ item, isPaid, totalItemCount }) {
  if (!item) return null;
  const info = DOMAINS[item.domain] || DOMAINS.legal;

  return (
    <div className="fp-spotlight" style={{ borderColor: info.color }}>
      <p className="fp-spotlight-label" style={{ color: info.color }}>
        <FontAwesomeIcon icon={info.icon} /> Your #1 priority right now
      </p>
      <p className="fp-spotlight-text">{item.text}</p>
      {item.script && <p className="fp-item-script">"{item.script}"</p>}
      {!isPaid && totalItemCount > 1 && (
        <p className="fp-spotlight-note">This is 1 of {totalItemCount} steps in your full plan.</p>
      )}
    </div>
  );
}

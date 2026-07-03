import UpgradeButton from "./UpgradeButton";

// Shared "separate checklist" teaser for business/digital/health items --
// shows the first item in full as a real demo, blurs the rest. Used instead
// of a plain locked-count box so every checklist gives a genuine preview.
export default function ChecklistTeaser({ label, items }) {
  if (!items?.length) return null;
  const [shown, ...rest] = items;

  return (
    <div className="fp-teaser-card" style={{ textAlign: "left" }}>
      <p className="fp-teaser-card-title">{label}</p>

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
        <UpgradeButton style={{ marginTop: 12 }}>
          Unlock {rest.length} more step{rest.length > 1 ? "s" : ""} →
        </UpgradeButton>
      )}
    </div>
  );
}

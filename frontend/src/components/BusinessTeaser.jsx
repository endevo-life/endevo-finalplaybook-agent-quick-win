import UpgradeButton from "./UpgradeButton";

export default function BusinessTeaser({ count }) {
  if (!count) return null;
  return (
    <div className="fp-teaser-card">
      <p className="fp-teaser-card-title">Your business checklist has {count} more step{count > 1 ? "s" : ""}</p>
      <p className="fp-teaser-card-body">Business and personal planning are separate checklists, unlock to see both.</p>
      <UpgradeButton>Unlock my business checklist →</UpgradeButton>
    </div>
  );
}

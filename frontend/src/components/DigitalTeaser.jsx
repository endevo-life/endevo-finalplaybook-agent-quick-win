import UpgradeButton from "./UpgradeButton";

export default function DigitalTeaser({ count }) {
  if (!count) return null;
  return (
    <div className="fp-teaser-card">
      <p className="fp-teaser-card-title">Your digital checklist has {count} more step{count > 1 ? "s" : ""}</p>
      <p className="fp-teaser-card-body">Legacy contacts, social media, and password access — unlock to see your steps.</p>
      <UpgradeButton>Unlock my digital checklist →</UpgradeButton>
    </div>
  );
}

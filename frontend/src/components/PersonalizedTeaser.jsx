import UpgradeButton from "./UpgradeButton";

export default function PersonalizedTeaser() {
  return (
    <div className="fp-teaser-card">
      <p className="fp-teaser-card-title">Get your next 3 days, in Niki's voice</p>
      <p className="fp-teaser-card-body">
        A short, personalized narrative walking through your plan — with word-for-word scripts for every hard conversation.
      </p>
      <UpgradeButton>Unlock my personalized plan →</UpgradeButton>
    </div>
  );
}

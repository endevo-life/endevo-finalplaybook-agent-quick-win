import { useEffect, useState } from "react";
import { getPricing } from "../api/client";

// Renders the freemium vs paid comparison from the backend /api/pricing so the
// marketing page and the server's real plan limits can never drift apart.
// Falls back to sensible defaults if the API is unreachable at page load.
const FALLBACK = {
  plans: [
    { tier: "free", name: "Free", priceUsdMonth: 0, canPersonalize: false, canChat: false,
      monthlyPersonalizeQuota: 0, monthlyChatQuota: 0 },
    { tier: "paid", name: "Personalized", priceUsdMonth: 25, canPersonalize: true, canChat: true,
      monthlyPersonalizeQuota: 30, monthlyChatQuota: 200 },
  ],
};

function FreeCard() {
  return (
    <div className="fp-price-card">
      <p className="fp-price-name">Free</p>
      <div className="fp-price-amount">$0<span> / forever</span></div>
      <p className="fp-price-desc">Everything you need to get a real, prioritized plan started — no account, no card.</p>
      <ul className="fp-price-feats">
        <li>Personalized situation assessment</li>
        <li>Prioritized action plan (rules engine)</li>
        <li>Word-for-word conversation scripts</li>
        <li>Plain-English definitions along the way</li>
        <li>Download your plan anytime</li>
        <li className="muted">AI-personalized narrative</li>
        <li className="muted">Follow-up chat about your plan</li>
      </ul>
    </div>
  );
}

function PaidCard({ plan, onUpgrade, ctaLabel }) {
  const price = plan.priceUsdMonth ? `$${plan.priceUsdMonth}` : "$25";
  return (
    <div className="fp-price-card featured">
      <span className="fp-price-badge">Most popular</span>
      <p className="fp-price-name">{plan.name || "Personalized"}</p>
      <div className="fp-price-amount">{price}<span> / month</span></div>
      <p className="fp-price-desc">Your plan, rewritten as a warm, personal next-7-days narrative — plus a guide you can ask questions.</p>
      <ul className="fp-price-feats">
        <li>Everything in Free</li>
        <li>AI-personalized "next 7 days" narrative</li>
        <li>Grounded follow-up chat about your plan</li>
        <li>Up to {plan.monthlyPersonalizeQuota || 30} plan regenerations / month</li>
        <li>Up to {plan.monthlyChatQuota || 200} chat replies / month</li>
        <li>Cancel anytime</li>
      </ul>
      <button className="fp-btn-upgrade" style={{ width: "100%" }} onClick={onUpgrade}>
        {ctaLabel}
      </button>
    </div>
  );
}

export default function Pricing({ onUpgrade, isPaid }) {
  const [pricing, setPricing] = useState(FALLBACK);

  useEffect(() => {
    getPricing().then(setPricing).catch(() => setPricing(FALLBACK));
  }, []);

  const paid = pricing.plans.find((p) => p.tier === "paid") || FALLBACK.plans[1];
  const ctaLabel = isPaid ? "You're on Personalized ✓" : "Upgrade →";

  return (
    <div className="fp-section" id="pricing">
      <h2 className="fp-section-title">Simple pricing</h2>
      <p className="fp-section-lead">
        Start free and get a real plan today. Upgrade only if you want the personalized narrative and follow-up chat.
      </p>
      <div className="fp-pricing-grid">
        <FreeCard />
        <PaidCard plan={paid} onUpgrade={isPaid ? undefined : onUpgrade} ctaLabel={ctaLabel} />
      </div>
    </div>
  );
}

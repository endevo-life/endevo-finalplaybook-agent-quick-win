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
  billingIntervals: [
    { key: "monthly", label: "Monthly", priceUsd: 25, period: "month", effectiveMonthlyUsd: null },
    { key: "annual", label: "Annual", priceUsd: 199, period: "year", effectiveMonthlyUsd: 16.58 },
  ],
  // Empty = we couldn't reach the API. We then show the toggle optimistically
  // rather than hiding annual on a transient network blip.
  availableIntervals: [],
};

// "Save 34%" -- computed, never hard-coded, so it can't drift from the prices.
function savingsPercent(monthly, annual) {
  if (!monthly || !annual) return 0;
  return Math.round((1 - annual / (monthly * 12)) * 100);
}

function IntervalToggle({ intervals, value, onChange, monthlyPrice }) {
  return (
    <div className="fp-interval-toggle" role="group" aria-label="Billing interval">
      {intervals.map((i) => {
        const save = i.period === "year" ? savingsPercent(monthlyPrice, i.priceUsd) : 0;
        return (
          <button
            key={i.key}
            type="button"
            className={`fp-interval-opt${value === i.key ? " active" : ""}`}
            aria-pressed={value === i.key}
            onClick={() => onChange(i.key)}
          >
            {i.label}
            {save > 0 && <span className="fp-interval-save">Save {save}%</span>}
          </button>
        );
      })}
    </div>
  );
}

function FreeCard() {
  return (
    <div className="fp-price-card">
      <p className="fp-price-name">Free</p>
      <div className="fp-price-amount">$0<span> / forever</span></div>
      <p className="fp-price-desc">Everything you need to get a real, prioritized plan started, no account, no card.</p>
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

function PaidCard({ plan, selected, onUpgrade, ctaLabel }) {
  const price = selected?.priceUsd ?? plan.priceUsdMonth ?? 25;
  const period = selected?.period || "month";
  const isAnnual = period === "year";
  return (
    <div className="fp-price-card featured">
      <span className="fp-price-badge">Most popular</span>
      <p className="fp-price-name">{plan.name || "Personalized"}</p>
      <div className="fp-price-amount">${price}<span> / {period}</span></div>
      {isAnnual && selected?.effectiveMonthlyUsd && (
        <p className="fp-price-sub">
          That's ${selected.effectiveMonthlyUsd}/month, billed once a year.
        </p>
      )}
      <p className="fp-price-desc">Your plan, rewritten as a warm, personal next-7-days narrative, plus a guide you can ask questions.</p>
      <ul className="fp-price-feats">
        <li>Everything in Free</li>
        <li>AI-personalized "next 7 days" narrative</li>
        <li>Grounded follow-up chat about your plan</li>
        <li>Up to {plan.monthlyPersonalizeQuota || 30} plan regenerations / month</li>
        <li>Up to {plan.monthlyChatQuota || 200} chat replies / month</li>
        <li>{isAnnual ? "A full year to work through it, at your pace" : "Cancel anytime"}</li>
      </ul>
      <button className="fp-btn-upgrade" style={{ width: "100%" }} onClick={onUpgrade}>
        {ctaLabel}
      </button>
    </div>
  );
}

export default function Pricing({ onUpgrade, isPaid }) {
  const [pricing, setPricing] = useState(FALLBACK);
  // Named billingInterval, not `interval`, so it doesn't shadow window.setInterval.
  const [billingInterval, setBillingInterval] = useState("monthly");

  useEffect(() => {
    getPricing().then(setPricing).catch(() => setPricing(FALLBACK));
  }, []);

  const paid = pricing.plans.find((p) => p.tier === "paid") || FALLBACK.plans[1];
  const allIntervals = pricing.billingIntervals?.length
    ? pricing.billingIntervals
    : FALLBACK.billingIntervals;

  // Only offer an interval this deploy can actually charge. `availableIntervals`
  // is empty when Stripe isn't configured (or the API was unreachable) -- show
  // everything then, since the button falls back to the static upgrade URL anyway.
  const available = pricing.availableIntervals?.length
    ? allIntervals.filter((i) => pricing.availableIntervals.includes(i.key))
    : allIntervals;

  // If the selected interval isn't offered, fall back to the first that is --
  // otherwise the card would price one plan and check out with another.
  const selected =
    available.find((i) => i.key === billingInterval) || available[0] || allIntervals[0];

  const monthly = allIntervals.find((i) => i.period === "month");
  const ctaLabel = isPaid ? "You're on Personalized ✓" : "Upgrade →";

  return (
    <div className="fp-section" id="pricing">
      <h2 className="fp-section-title">Simple pricing</h2>
      <p className="fp-section-lead">
        Start free and get a real plan today. Upgrade only if you want the personalized narrative and follow-up chat.
      </p>
      {available.length > 1 && (
        <IntervalToggle
          intervals={available}
          value={selected?.key}
          onChange={setBillingInterval}
          monthlyPrice={monthly?.priceUsd || paid.priceUsdMonth}
        />
      )}
      <div className="fp-pricing-grid">
        <FreeCard />
        <PaidCard
          plan={paid}
          selected={selected}
          onUpgrade={isPaid ? undefined : () => onUpgrade?.(selected?.key)}
          ctaLabel={ctaLabel}
        />
      </div>
    </div>
  );
}

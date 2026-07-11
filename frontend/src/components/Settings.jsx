import { useState } from "react";
import { cancelSubscription } from "../api/client";
import { PRODUCT_NAME } from "../config/branding";

// Account / settings modal. Shows the signed-in email + current plan, and lets
// a paid member cancel (downgrade to free). Fool-proof: a confirm step, a busy
// state, clear success/error, and it refreshes the app's entitlement so the UI
// reflects the change immediately.
function fmtDate(epochSeconds) {
  if (!epochSeconds) return "";
  return new Date(epochSeconds * 1000).toLocaleDateString(undefined, {
    year: "numeric", month: "short", day: "numeric",
  });
}

export default function Settings({ account, onClose, onChanged }) {
  const isPaid = account?.tier === "paid";
  const alreadyCanceled = isPaid && account?.canceled;
  const untilDate = fmtDate(account?.paidUntil);
  const [phase, setPhase] = useState("main"); // main | confirm | working | done | error
  const [err, setErr] = useState("");
  const [doneUntil, setDoneUntil] = useState("");

  async function doCancel() {
    setPhase("working");
    setErr("");
    try {
      const snap = await cancelSubscription();
      setDoneUntil(fmtDate(snap?.paidUntil));
      await onChanged?.(); // refresh entitlement in the app
      setPhase("done");
    } catch (e) {
      setErr(e?.message || "Couldn't cancel. Please try again.");
      setPhase("error");
    }
  }

  return (
    <div className="fp-modal-backdrop" onClick={onClose}>
      <div className="fp-modal" onClick={(e) => e.stopPropagation()} role="dialog" aria-modal="true" aria-label="Account settings">
        <button className="fp-btn-back" onClick={onClose} style={{ marginBottom: 8 }}>✕ close</button>
        <h3 className="fp-h2" style={{ marginTop: 0 }}>Account</h3>

        <div className="fp-settings-row">
          <span className="fp-settings-label">Email</span>
          <span className="fp-settings-value">{account?.email || "—"}</span>
        </div>
        <div className="fp-settings-row">
          <span className="fp-settings-label">Plan</span>
          <span className={`fp-tier-pill ${isPaid ? "paid" : ""}`}>
            {isPaid ? "Personalized" : "Free"}
          </span>
        </div>

        <div className="fp-settings-actions">
          {!isPaid && (
            <p className="fp-dim" style={{ fontSize: 13 }}>
              You're on the free plan. Unlock {PRODUCT_NAME} Premium from your playbook
              to complete every step and download it.
            </p>
          )}

          {alreadyCanceled && phase === "main" && (
            <p className="fp-dim" style={{ fontSize: 13 }}>
              Your subscription is canceled. You keep full access
              {untilDate ? ` until ${untilDate}` : " until your period ends"}, then
              you'll move to the free plan.
            </p>
          )}

          {isPaid && !alreadyCanceled && phase === "main" && (
            <button className="fp-btn-secondary" style={{ width: "100%" }} onClick={() => setPhase("confirm")}>
              Cancel subscription
            </button>
          )}

          {isPaid && phase === "confirm" && (
            <div className="fp-settings-confirm">
              <p className="fp-body" style={{ marginTop: 0 }}>
                Cancel your subscription? You'll keep full access until the end of
                your current period, then move to the free plan — no further charges.
              </p>
              <button className="fp-btn-danger" style={{ width: "100%" }} onClick={doCancel}>
                Yes, cancel my subscription
              </button>
              <button className="fp-btn-back" style={{ marginTop: 10 }} onClick={() => setPhase("main")}>
                Keep my subscription
              </button>
            </div>
          )}

          {phase === "working" && <p className="fp-body">Cancelling…</p>}

          {phase === "done" && (
            <p className="fp-body" style={{ color: "var(--teal-deep, #2E7F7B)" }}>
              ✓ Canceled. You keep full access{doneUntil ? ` until ${doneUntil}` : " until your period ends"},
              then you'll move to the free plan.
            </p>
          )}

          {phase === "error" && (
            <>
              <p className="fp-error">{err}</p>
              <button className="fp-btn-secondary" style={{ width: "100%" }} onClick={() => setPhase("confirm")}>
                Try again
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

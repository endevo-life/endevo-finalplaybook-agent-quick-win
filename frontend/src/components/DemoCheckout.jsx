import { useEffect, useState } from "react";
import { PLAYBOOK_NAME } from "../config/branding";

// Demo checkout — a realistic but SIMULATED payment for demos (no Stripe).
// Shows a card form → "processing…" → "payment successful" → unlocks paid.
// The actual tier flip is done by the caller's onConfirm (dev-upgrade / admin).
//
// This is clearly a demo: the card is prefilled with the Stripe test number and
// nothing is charged. Swap this for real Stripe Checkout before launch.
export default function DemoCheckout({ price = 25, onConfirm, onClose }) {
  const [phase, setPhase] = useState("form"); // form | processing | success | error
  const [err, setErr] = useState("");

  async function pay() {
    setPhase("processing");
    // Brief, believable processing beat.
    await new Promise((r) => setTimeout(r, 1600));
    try {
      await onConfirm(); // the real tier flip
      setPhase("success");
      await new Promise((r) => setTimeout(r, 1400));
      onClose(true); // true = upgraded
    } catch (e) {
      setErr(e?.message || "Payment couldn't be completed.");
      setPhase("error");
    }
  }

  // Close on Escape (form/error only — don't interrupt processing/success).
  useEffect(() => {
    const onKey = (e) => {
      if (e.key === "Escape" && (phase === "form" || phase === "error")) onClose(false);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [phase, onClose]);

  return (
    <div className="fp-modal-backdrop" onClick={() => (phase === "form" || phase === "error") && onClose(false)}>
      <div className="fp-modal fp-checkout" onClick={(e) => e.stopPropagation()} role="dialog" aria-modal="true" aria-label="Checkout">
        {phase === "form" && (
          <>
            <p className="fp-checkout-demo-tag">Demo checkout · no card is charged</p>
            <h3 className="fp-h2" style={{ marginTop: 6 }}>Unlock {PLAYBOOK_NAME} Premium</h3>
            <p className="fp-body">${price}/month · cancel anytime</p>

            <label className="fp-label" htmlFor="cc">Card number</label>
            <input id="cc" className="fp-input" defaultValue="4242 4242 4242 4242" inputMode="numeric" />
            <div style={{ display: "flex", gap: 12 }}>
              <div style={{ flex: 1 }}>
                <label className="fp-label" htmlFor="exp">Expiry</label>
                <input id="exp" className="fp-input" defaultValue="12 / 34" />
              </div>
              <div style={{ width: 110 }}>
                <label className="fp-label" htmlFor="cvc">CVC</label>
                <input id="cvc" className="fp-input" defaultValue="123" inputMode="numeric" />
              </div>
            </div>

            <button className="fp-btn" style={{ width: "100%", marginTop: 18 }} onClick={pay}>
              Pay ${price} →
            </button>
            <button className="fp-btn-back" style={{ marginTop: 12 }} onClick={() => onClose(false)}>Cancel</button>
          </>
        )}

        {phase === "processing" && (
          <div className="fp-checkout-status">
            <div className="fp-spinner" aria-hidden="true" />
            <p className="fp-checkout-status-text">Processing your payment…</p>
          </div>
        )}

        {phase === "success" && (
          <div className="fp-checkout-status">
            <div className="fp-checkout-check" aria-hidden="true">✓</div>
            <p className="fp-checkout-status-text">Payment successful</p>
            <p className="fp-dim">Unlocking your full playbook…</p>
          </div>
        )}

        {phase === "error" && (
          <div className="fp-checkout-status">
            <p className="fp-error" style={{ textAlign: "center" }}>{err}</p>
            <button className="fp-btn" style={{ width: "100%", marginTop: 12 }} onClick={() => setPhase("form")}>Try again</button>
            <button className="fp-btn-back" style={{ marginTop: 10 }} onClick={() => onClose(false)}>Close</button>
          </div>
        )}
      </div>
    </div>
  );
}

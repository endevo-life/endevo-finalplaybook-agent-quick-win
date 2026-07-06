import { useState } from "react";
import { UPGRADE_URL } from "../config/branding";
import { getToken, startCheckout } from "../api/client";

// Upgrade CTA. If the user is logged in and the backend has Stripe configured,
// this creates a real Checkout Session and redirects there. Otherwise it falls
// back to the static UPGRADE_URL (or asks the user to sign in first).
export default function UpgradeButton({
  children = "Upgrade →",
  className = "fp-btn-upgrade",
  style,
  onNeedLogin,
}) {
  const [busy, setBusy] = useState(false);

  async function go() {
    if (!getToken()) {
      // Not logged in -- can't attach a payment to an account yet.
      if (onNeedLogin) return onNeedLogin();
      window.open(UPGRADE_URL, "_blank", "noopener,noreferrer");
      return;
    }
    setBusy(true);
    try {
      const { url } = await startCheckout();
      window.location.href = url; // Stripe-hosted checkout
    } catch (e) {
      // Billing not configured / error -> static fallback so the button never dead-ends.
      window.open(UPGRADE_URL, "_blank", "noopener,noreferrer");
    } finally {
      setBusy(false);
    }
  }

  return (
    <button
      className={className}
      style={{ ...style, textAlign: "center" }}
      onClick={go}
      disabled={busy}
    >
      {busy ? "Redirecting…" : children}
    </button>
  );
}

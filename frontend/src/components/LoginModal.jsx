import { useState } from "react";

// Two-step email login modal. Step 1: enter email -> backend sends a 6-digit
// code (in dev it's returned and prefilled). Step 2: enter the code -> logged in.
export default function LoginModal({ auth, onClose, onLoggedIn }) {
  const [step, setStep] = useState("email"); // "email" | "code"
  const [email, setEmail] = useState("");
  const [code, setCode] = useState("");
  const [devCode, setDevCode] = useState(null);
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);

  async function sendCode() {
    setErr("");
    setBusy(true);
    try {
      const res = await auth.startLogin(email.trim());
      setDevCode(res.devLoginCode || null);
      if (res.devLoginCode) setCode(res.devLoginCode); // dev convenience
      setStep("code");
    } catch (e) {
      setErr(e.message || "Could not send a login code.");
    } finally {
      setBusy(false);
    }
  }

  async function verify() {
    setErr("");
    setBusy(true);
    try {
      const user = await auth.verifyLogin(email.trim(), code.trim());
      onLoggedIn?.(user);
      onClose();
    } catch (e) {
      setErr(e.message || "Invalid code.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="fp-modal-backdrop" onClick={onClose}>
      <div className="fp-modal" onClick={(e) => e.stopPropagation()}>
        <button className="fp-btn-back" onClick={onClose} style={{ marginBottom: 8 }}>✕ close</button>
        <h3 className="fp-h2" style={{ marginTop: 0 }}>Sign in</h3>

        {step === "email" && (
          <>
            <p className="fp-body">Enter your email and we'll send you a sign-in code. No password needed.</p>
            <label className="fp-label">Email</label>
            <input
              className="fp-input"
              type="email"
              value={email}
              autoFocus
              placeholder="you@example.com"
              onChange={(e) => setEmail(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && email.includes("@") && sendCode()}
            />
            {err && <p className="fp-error">{err}</p>}
            <button className="fp-btn" style={{ width: "100%", marginTop: 16 }}
                    disabled={busy || !email.includes("@")} onClick={sendCode}>
              {busy ? "Sending…" : "Send code →"}
            </button>
          </>
        )}

        {step === "code" && (
          <>
            <p className="fp-body">
              We sent a 6-digit code to <strong>{email}</strong>.
            </p>
            {devCode && (
              <p className="fp-dim" style={{ fontSize: 13 }}>
                Dev mode: your code is <strong>{devCode}</strong> (email delivery isn't configured on this server).
              </p>
            )}
            <label className="fp-label">Code</label>
            <input
              className="fp-input"
              value={code}
              autoFocus
              placeholder="123456"
              onChange={(e) => setCode(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && code.length >= 6 && verify()}
            />
            {err && <p className="fp-error">{err}</p>}
            <button className="fp-btn" style={{ width: "100%", marginTop: 16 }}
                    disabled={busy || code.length < 6} onClick={verify}>
              {busy ? "Verifying…" : "Sign in →"}
            </button>
            <button className="fp-btn-back" style={{ marginTop: 10 }} onClick={() => setStep("email")}>
              ← use a different email
            </button>
          </>
        )}
      </div>
    </div>
  );
}

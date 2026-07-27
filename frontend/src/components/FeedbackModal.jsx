import { useState } from "react";
import { submitFeedback } from "../api/client";

// One form for three things a member might need: help, a complaint, or general
// feedback. They arrive through the same door, so splitting them into three
// forms would just mean three things nobody finds -- `kind` is how operators
// triage on the other end.
//
// Works signed in OR anonymous. Anonymous matters: someone who can't sign in is
// exactly the person who most needs to reach us. When signed in, the backend
// takes the email from the session and ignores the field, so we hide it.

const KINDS = [
  { value: "help", label: "I need help", hint: "Something isn't working, or you're stuck." },
  { value: "complaint", label: "Something's wrong", hint: "We got something wrong, or it didn't sit right." },
  { value: "survey", label: "Share feedback", hint: "Tell us how this is going." },
];

const MAX_CHARS = 4000;

export default function FeedbackModal({ account, onClose, initialKind = "help" }) {
  const [kind, setKind] = useState(initialKind);
  const [message, setMessage] = useState("");
  const [email, setEmail] = useState("");
  const [rating, setRating] = useState(0);
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState(null);

  const signedIn = Boolean(account?.email);
  // A survey needs no reply, so it can stay anonymous. Help and complaints
  // need a return address -- same rule the server enforces.
  const needsEmail = !signedIn && kind !== "survey";
  const emailOk = !needsEmail || /\S+@\S+\.\S+/.test(email.trim());
  const canSend = message.trim().length > 1 && emailOk && !busy;

  async function send() {
    setErr("");
    setBusy(true);
    try {
      const res = await submitFeedback({
        kind,
        message: message.trim(),
        email: signedIn ? undefined : email.trim() || undefined,
        rating: kind === "survey" && rating ? rating : undefined,
        page: typeof window !== "undefined" ? window.location.pathname : undefined,
      });
      setDone(res.message || "Thank you — we've got it.");
    } catch (e) {
      setErr(e.message || "We couldn't send that. Please try again.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="fp-modal-backdrop" onClick={onClose}>
      <div
        className="fp-modal fp-modal-wide"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-label="Help and feedback"
      >
        <button className="fp-btn-back" onClick={onClose} style={{ marginBottom: 8 }}>
          ✕ close
        </button>

        {done ? (
          <>
            <h3 className="fp-h2" style={{ marginTop: 0 }}>Message sent</h3>
            <p className="fp-body">{done}</p>
            <button className="fp-btn" style={{ width: "100%", marginTop: 16 }} onClick={onClose}>
              Close
            </button>
          </>
        ) : (
          <>
            <h3 className="fp-h2" style={{ marginTop: 0 }}>How can we help?</h3>

            <label className="fp-label">What's this about?</label>
            <div className="fp-kind-list">
              {KINDS.map((k) => (
                <button
                  key={k.value}
                  type="button"
                  className={`fp-kind-option ${kind === k.value ? "selected" : ""}`}
                  onClick={() => setKind(k.value)}
                  aria-pressed={kind === k.value}
                >
                  <span className="fp-kind-label">{k.label}</span>
                  <span className="fp-kind-hint">{k.hint}</span>
                </button>
              ))}
            </div>

            {needsEmail && (
              <div style={{ marginTop: 16 }}>
                <label className="fp-label">Your email</label>
                <input
                  className="fp-input"
                  type="email"
                  value={email}
                  placeholder="you@example.com"
                  onChange={(e) => setEmail(e.target.value)}
                />
                <p className="fp-dim" style={{ fontSize: 12.5, marginTop: 6 }}>
                  So we can write back.
                </p>
              </div>
            )}

            {kind === "survey" && (
              <div style={{ marginTop: 16 }}>
                <label className="fp-label">How useful has this been so far? (optional)</label>
                <div className="fp-rating" role="group" aria-label="Rating out of 5">
                  {[1, 2, 3, 4, 5].map((n) => (
                    <button
                      key={n}
                      type="button"
                      className={`fp-rating-star ${rating >= n ? "on" : ""}`}
                      onClick={() => setRating(rating === n ? 0 : n)}
                      aria-label={`${n} out of 5`}
                      aria-pressed={rating === n}
                    >
                      ★
                    </button>
                  ))}
                </div>
              </div>
            )}

            <div style={{ marginTop: 16 }}>
              <label className="fp-label">
                {kind === "complaint" ? "What happened?" : "Your message"}
              </label>
              <textarea
                className="fp-input fp-textarea"
                value={message}
                rows={5}
                maxLength={MAX_CHARS}
                autoFocus
                placeholder={
                  kind === "complaint"
                    ? "Tell us what went wrong — we read every one of these."
                    : kind === "help"
                    ? "What are you stuck on?"
                    : "What's working, and what isn't?"
                }
                onChange={(e) => setMessage(e.target.value)}
              />
              <p className="fp-dim" style={{ fontSize: 12.5, marginTop: 6, textAlign: "right" }}>
                {message.length}/{MAX_CHARS}
              </p>
            </div>

            {err && <p className="fp-error">{err}</p>}

            <button
              className="fp-btn"
              style={{ width: "100%", marginTop: 12 }}
              disabled={!canSend}
              onClick={send}
            >
              {busy ? "Sending…" : "Send →"}
            </button>

            {signedIn && (
              <p className="fp-dim" style={{ fontSize: 12.5, marginTop: 10, textAlign: "center" }}>
                Sending as {account.email}
              </p>
            )}
          </>
        )}
      </div>
    </div>
  );
}

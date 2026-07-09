export default function Identify({ user, setUser, isPaid, onNext, onBack }) {
  // Just a warm "what should we call you?" — tier is set by the member's account
  // (server-side entitlement), never chosen here, so there's no plan picker.
  function go() {
    onNext(); // name is optional; greetings fall back gracefully without it
  }

  return (
    <div className="fp-page-narrow">
      <button onClick={onBack} className="fp-btn-back">← back</button>
      <h2 className="fp-h2" style={{ marginTop: 12 }}>What should we call you?</h2>
      <p className="fp-body">
        We'll use your first name to keep things personal. That's it — no account
        setup, and you're already signed in.
      </p>
      <div className="fp-card">
        <label className="fp-label" htmlFor="fp-firstname">First name</label>
        <input
          id="fp-firstname"
          className="fp-input"
          value={user.name}
          onChange={(e) => setUser({ ...user, name: e.target.value })}
          onKeyDown={(e) => e.key === "Enter" && go()}
          placeholder="Elisa"
          autoFocus
        />
        <button onClick={go} className="fp-btn" style={{ width: "100%", marginTop: 20 }}>
          Continue →
        </button>
      </div>
    </div>
  );
}

import { useEffect, useState } from "react";
import TopNav from "./components/TopNav";
import Disclaimer from "./components/Disclaimer";
import Landing from "./components/Landing";
import Welcome from "./components/Welcome";
import Identify from "./components/Identify";
import WhyNow from "./components/WhyNow";
import ScenarioPicker from "./components/ScenarioPicker";
import Session from "./components/Session";
import ResultsPanel from "./components/ResultsPanel";
import Assessment from "./components/Assessment";
import LoginModal from "./components/LoginModal";
import { getGlossary, startCheckout, devUpgrade, getToken } from "./api/client";
import { useAuth } from "./auth/useAuth";
import { firstName } from "./config/branding";

export default function App() {
  // landing | welcome | identify | scenarios | session | results
  const [route, setRoute] = useState("landing");
  const [user, setUser] = useState({ name: "", tier: "free" });
  const [flags, setFlags] = useState({});
  // "Why now?" signals (flags) — set by the WhyNow picker, used to REORDER the
  // assessment plan so it leads with what moved this person to act.
  const [signals, setSignals] = useState([]);
  const [result, setResult] = useState(null);
  const [glossary, setGlossary] = useState([]);
  const [showLogin, setShowLogin] = useState(false);
  // When true, a successful login should immediately resume the upgrade flow
  // (user clicked Upgrade while logged out).
  const [pendingUpgrade, setPendingUpgrade] = useState(false);
  // When true, a successful login should start the assessment flow (user clicked
  // "Get My Final Playbook" while logged out). Even the FREE experience requires
  // an account so the AI-guide taste works and progress persists per user.
  const [pendingStart, setPendingStart] = useState(false);

  const auth = useAuth();

  useEffect(() => {
    getGlossary().then(setGlossary).catch(() => setGlossary([]));
  }, []);

  // The effective tier is always the server-side entitlement, never a client
  // toggle -- so a free user can't self-select "paid" and get LLM output.
  useEffect(() => {
    setUser((u) => ({ ...u, tier: auth.isPaid ? "paid" : "free" }));
  }, [auth.isPaid]);

  // Return from Stripe Checkout: refresh entitlement so the UI reflects the
  // (webhook-driven) upgrade, and clean the URL.
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get("checkout")) {
      auth.refresh();
      window.history.replaceState({}, "", window.location.pathname);
    }
  }, [auth]);

  function restart() {
    setUser({ name: "", tier: auth.isPaid ? "paid" : "free" });
    setFlags({});
    setResult(null);
    setRoute("landing");
  }

  // The actual upgrade action (assumes the user is logged in).
  async function doUpgrade() {
    try {
      // Preferred path: real Stripe Checkout when billing is configured.
      const { url } = await startCheckout();
      window.location.href = url;
      return;
    } catch (e) {
      // 503 = billing not configured yet. Fall back to the dev unlock so the
      // premium experience is still usable/demoable before Stripe is live.
      if (e.status === 503) {
        try {
          await devUpgrade();
          await auth.refresh(); // reflect paid tier in the UI immediately
          return;
        } catch (devErr) {
          // Surface the real reason instead of silently opening a placeholder.
          alert("Upgrade failed: " + (devErr.message || "unknown error") +
                "\n(Dev upgrade may be disabled — set ALLOW_DEV_UPGRADE=true.)");
          return;
        }
      }
      // Any other error: tell the user rather than dead-ending.
      alert("Couldn't start checkout: " + (e.message || "unknown error"));
    }
  }

  // Start the (free) assessment. Requires an account first: the free tier still
  // needs a logged-in user for the AI-guide taste and per-user progress. If not
  // signed in, open the login modal and resume into the flow on success.
  function startFlow() {
    if (!getToken()) {
      setPendingStart(true);
      setShowLogin(true);
      return;
    }
    setRoute("identify");
  }

  function handleUpgrade() {
    // Must be logged in to attach the upgrade to an account. If not, open the
    // login modal and remember to resume the upgrade once they're in.
    if (!getToken()) {
      setPendingUpgrade(true);
      setShowLogin(true);
      return;
    }
    doUpgrade();
  }

  // Called by the login modal on success. Route based on WHY they signed in:
  //   - pendingUpgrade → continue straight into checkout
  //   - pendingStart   → they clicked "Get My Final Playbook": begin the flow
  //   - plain "Sign in" (returning user) → go to their playbook. The Assessment
  //     screen restores their saved plan on mount; if they have none, it shows
  //     the questions. Either way we skip Identify — a signed-in user is known,
  //     so we don't re-ask their name or make them "pick a plan" (tier comes
  //     from their account, server-side).
  function handleLoggedIn(loggedInUser) {
    setShowLogin(false);
    // Seed the display name from their email so greetings work without Identify.
    if (loggedInUser?.email && !user.name) {
      setUser((u) => ({ ...u, name: firstName(loggedInUser.email) }));
    }
    if (pendingUpgrade) {
      setPendingUpgrade(false);
      doUpgrade();
      return;
    }
    if (pendingStart) {
      // They clicked "Get My Final Playbook": run the full new-user flow
      // (name → why now → questions).
      setPendingStart(false);
      setRoute("identify");
      return;
    }
    // Plain "Sign in" — a returning member. Skip the intro; go straight to their
    // playbook. Assessment restores their saved plan on mount, or shows the
    // questions if they have none. We don't re-ask their name or plan.
    setRoute("assessment");
  }

  return (
    <div style={{ minHeight: "100vh" }}>
      <TopNav
        route={route}
        user={user}
        account={auth.account}
        onHome={restart}
        onSignIn={() => setShowLogin(true)}
        onSignOut={auth.logout}
      />
      <Disclaimer />

      {route === "landing" && (
        <Landing
          onStart={startFlow}
          onSignIn={() => setShowLogin(true)}
          onUpgrade={handleUpgrade}
          isPaid={auth.isPaid}
        />
      )}

      {route === "welcome" && <Welcome onStart={startFlow} />}

      {route === "identify" && (
        <Identify
          user={user}
          setUser={setUser}
          onNext={() => setRoute("whyNow")}
          onBack={() => setRoute("landing")}
        />
      )}

      {route === "whyNow" && (
        <WhyNow
          user={user}
          picked={signals}
          setPicked={setSignals}
          onNext={() => setRoute("assessment")}
          onBack={() => setRoute("identify")}
        />
      )}

      {route === "assessment" && (
        <Assessment
          user={user}
          signals={signals}
          isPaid={auth.isPaid}
          onUpgrade={handleUpgrade}
          onBack={() => setRoute("landing")}
        />
      )}

      {route === "scenarios" && (
        <ScenarioPicker
          user={user}
          flags={flags}
          setFlags={setFlags}
          onNext={() => setRoute("session")}
          onBack={() => setRoute("identify")}
        />
      )}

      {route === "session" && (
        <Session
          user={user}
          flags={flags}
          setFlags={setFlags}
          glossary={glossary}
          onBack={() => setRoute("scenarios")}
          onComplete={(planResult) => { setResult(planResult); setRoute("results"); }}
        />
      )}

      {route === "results" && result && (
        <ResultsPanel
          user={user}
          account={auth.account}
          result={result}
          onUpgrade={handleUpgrade}
          onRestart={restart}
        />
      )}

      {showLogin && (
        <LoginModal
          auth={auth}
          onClose={() => { setShowLogin(false); setPendingUpgrade(false); setPendingStart(false); }}
          onLoggedIn={handleLoggedIn}
        />
      )}
    </div>
  );
}

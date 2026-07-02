import { useEffect, useState } from "react";
import TopNav from "./components/TopNav";
import Disclaimer from "./components/Disclaimer";
import Welcome from "./components/Welcome";
import Identify from "./components/Identify";
import ScenarioPicker from "./components/ScenarioPicker";
import Session from "./components/Session";
import ResultsPanel from "./components/ResultsPanel";
import { getGlossary } from "./api/client";

export default function App() {
  const [route, setRoute] = useState("welcome"); // welcome | identify | scenarios | session | results
  const [user, setUser] = useState({ name: "", tier: "trial" });
  const [flags, setFlags] = useState({});
  const [result, setResult] = useState(null);
  const [glossary, setGlossary] = useState([]);

  useEffect(() => {
    getGlossary().then(setGlossary).catch(() => setGlossary([]));
  }, []);

  function restart() {
    setUser({ name: "", tier: "trial" });
    setFlags({});
    setResult(null);
    setRoute("welcome");
  }

  return (
    <div style={{ minHeight: "100vh" }}>
      <TopNav route={route} user={user} onHome={restart} />
      <Disclaimer />

      {route === "welcome" && <Welcome onStart={() => setRoute("identify")} />}

      {route === "identify" && (
        <Identify user={user} setUser={setUser} onNext={() => setRoute("scenarios")} onBack={() => setRoute("welcome")} />
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
        <ResultsPanel user={user} result={result} onRestart={restart} />
      )}
    </div>
  );
}

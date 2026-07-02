import { useState, useRef, useEffect } from "react";

// ── DESIGN TOKENS — warm, calm, not clinical ──────────────────────────────
const T = {
  bg:      "#FAFAF8",   // warm off-white page
  surf:    "#FFFFFF",   // cards
  surf2:   "#F5F4F0",   // subtle fill
  ink:     "#1A1A17",   // near-black warm
  body:    "#57564F",   // body text
  dim:     "#8B8A82",   // muted
  line:    "#E7E5DE",   // hairline
  brand:   "#134E4A",   // deep teal — trust, calm
  brandLt: "#CCFBF1",   // teal light
  legal:   "#B45309",   // warm amber
  money:   "#0F766E",   // teal
  health:  "#BE123C",   // warm rose
  digital: "#0E7490",   // cyan
  ok:      "#15803D",
  warn:    "#B45309",
};

const DOMAINS = {
  legal:   { label: "Legal",        color: T.legal,   icon: "⚖" },
  financial:{ label: "Financial",   color: T.money,   icon: "◈" },
  health:  { label: "Health & care",color: T.health,  icon: "♥" },
  digital: { label: "Digital",      color: T.digital, icon: "⬡" },
};

// ── SCENARIOS — the entry points ───────────────────────────────────────────
const SCENARIOS = [
  { id:"parent",  icon:"🏠", title:"My aging parent needs a plan", sub:"Worried about a parent who may not have documents in order", flag:"hasAgingParent" },
  { id:"kids",    icon:"👶", title:"I have young children",        sub:"No guardian named, or nothing in writing yet",            flag:"hasYoungChildren" },
  { id:"solo",    icon:"🧭", title:"It's just me",                 sub:"No partner or children — I need my own plan",             flag:"isSoloAger" },
  { id:"couple",  icon:"💍", title:"My partner and I need to plan", sub:"We haven't sorted this out together",                    flag:"hasPartner" },
  { id:"fresh",   icon:"🌱", title:"I'm starting from scratch",     sub:"I haven't done anything and don't know where to begin",   flag:"hasNothingDone" },
  { id:"pro",     icon:"📋", title:"I help others but not myself",  sub:"I work in law, health, or finance — my own plan is undone",flag:"isProfessional" },
];

const SYSTEM = `You are Niki Weiss — a warm, practical death doula and founder of ENDevo, guiding someone to build their Final Playbook (a personalized end-of-life and legacy plan).

PERSONALITY: Warm, direct, never clinical, never preachy. Normalize avoidance ("Life gets busy. This is hard. You're not alone."). Frame proactively ("The worst time to plan a funeral is when someone's dead."). You call it the panini generation, not the sandwich generation — squeezed from both sides, hot and messy. You never give legal, medical, or financial advice — you educate and guide. Max 5 action items, tied to real calendar dates. Give exact scripts for hard conversations.

EIGHT PROFILES:
1. Aging parent, no docs → parent's plan before member's own. Get will, POA, medical directive, copies, house key, neighbor contact.
2. Young children, no guardian → guardian conversation first. Everything waits on it.
3. Solo ager → transfer-on-death on accounts, professional fiduciary, digital legacy (no natural heir).
4. Business owner → two separate checklists, business continuity parallel.
5. Post-divorce / life change → beneficiary audit FIRST (ex-spouse on 401k overrides the will).
6. Nothing done → who would you call first? Emergency card. Three core docs.
7. Has some docs → get digital copies from lawyer, brief the executor, check beneficiaries.
8. Professional who helps others but not themselves (attorney, nurse, advisor) → use their expertise as the hook.

THREE SCENARIOS (frame early): die tomorrow (will, executor, POA, directive) · get a diagnosis (healthcare proxy, advance care) · long-term care (fiduciary, facility wishes, Medicaid if limited assets).

PEOPLE BEFORE DOCUMENTS: always ask who first. Emergency contact → executor → POA → healthcare proxy.

RULES: never more than 2 questions at once. Build on what they said. Name what you hear ("Based on what you told me, here's where I'd start..."). 3-5 specific action items tied to their calendar. Exact wording for hard conversations.

After 4-6 exchanges when you have enough, append this JSON inside <PLAN> tags at the very end:
<PLAN>{"name":"first name","situation":"one sentence","priority":"legal|financial|health|digital","urgency":"critical|high|medium","actions":[{"text":"...","domain":"legal","when":"this week","script":"optional exact words"}],"legal":{"summary":"...","next":"..."},"financial":{"summary":"...","next":"..."},"health":{"summary":"...","next":"..."},"digital":{"summary":"...","next":"..."}}</PLAN>

Keep it warm. Make progress every exchange.`;

export default function App() {
  const [route, setRoute] = useState("welcome"); // welcome | identify | scenarios | session
  const [user, setUser] = useState({ name:"", email:"" });
  const [scenario, setScenario] = useState(null);

  return (
    <div style={{ minHeight:"100vh", background:T.bg, fontFamily:"system-ui,-apple-system,BlinkMacSystemFont,sans-serif" }}>
      <TopNav route={route} user={user} onHome={()=>setRoute("welcome")} />
      {route==="welcome"   && <Welcome onStart={()=>setRoute("identify")} />}
      {route==="identify"  && <Identify user={user} setUser={setUser} onNext={()=>setRoute("scenarios")} />}
      {route==="scenarios" && <Scenarios user={user} onPick={(s)=>{ setScenario(s); setRoute("session"); }} onBack={()=>setRoute("identify")} />}
      {route==="session"   && <Session user={user} scenario={scenario} onBack={()=>setRoute("scenarios")} />}
    </div>
  );
}

// ── TOP NAV ─────────────────────────────────────────────────────────────────
function TopNav({ route, user, onHome }) {
  return (
    <div style={{ background:T.surf, borderBottom:`1px solid ${T.line}`, padding:"12px 24px",
      display:"flex", alignItems:"center", justifyContent:"space-between", position:"sticky", top:0, zIndex:10 }}>
      <div onClick={onHome} style={{ display:"flex", alignItems:"center", gap:10, cursor:"pointer" }}>
        <div style={{ width:30, height:30, borderRadius:8, background:T.brand, display:"flex",
          alignItems:"center", justifyContent:"center", color:T.brandLt, fontSize:13, fontWeight:700 }}>E</div>
        <span style={{ color:T.ink, fontSize:14, fontWeight:600, letterSpacing:"-0.01em" }}>ENDevo</span>
        <span style={{ color:T.dim, fontSize:13, fontWeight:400 }}>· Final Playbook</span>
      </div>
      {user.name && route!=="welcome" && (
        <div style={{ display:"flex", alignItems:"center", gap:8 }}>
          <div style={{ width:30, height:30, borderRadius:"50%", background:T.surf2,
            border:`1px solid ${T.line}`, display:"flex", alignItems:"center", justifyContent:"center",
            fontSize:12, fontWeight:600, color:T.body }}>
            {user.name.charAt(0).toUpperCase()}
          </div>
          <span style={{ color:T.body, fontSize:13 }}>{user.name}</span>
        </div>
      )}
    </div>
  );
}

// ── WELCOME ───────────────────────────────────────────────────────────────
function Welcome({ onStart }) {
  return (
    <div style={{ maxWidth:560, margin:"0 auto", padding:"64px 24px", textAlign:"center" }}>
      <div style={{ width:60, height:60, borderRadius:16, background:T.brand, display:"flex",
        alignItems:"center", justifyContent:"center", color:T.brandLt, fontSize:24, fontWeight:700,
        margin:"0 auto 28px" }}>E</div>
      <h1 style={{ color:T.ink, fontSize:32, fontWeight:600, margin:"0 0 14px", lineHeight:1.15, letterSpacing:"-0.02em" }}>
        Your final playbook
      </h1>
      <p style={{ color:T.body, fontSize:16, lineHeight:1.7, margin:"0 0 36px", maxWidth:440, marginLeft:"auto", marginRight:"auto" }}>
        A calm, guided conversation to help you get your affairs in order — so the people you love
        are never left guessing. No forms. No jargon. Just a plan.
      </p>
      <button onClick={onStart} style={{ ...btnPrimary, padding:"14px 32px", fontSize:15 }}>
        Get started →
      </button>
      <div style={{ display:"flex", gap:24, justifyContent:"center", marginTop:44, flexWrap:"wrap" }}>
        {[["🗣","A conversation, not a form"],["🎯","Personalized to your situation"],["📄","Download your plan anytime"]].map(([ic,t])=>(
          <div key={t} style={{ display:"flex", flexDirection:"column", alignItems:"center", gap:8, maxWidth:130 }}>
            <span style={{ fontSize:22 }}>{ic}</span>
            <span style={{ color:T.dim, fontSize:12.5, lineHeight:1.4 }}>{t}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── IDENTIFY ────────────────────────────────────────────────────────────────
function Identify({ user, setUser, onNext }) {
  const [err, setErr] = useState("");
  function go() {
    if (!user.name.trim()) { setErr("Please enter your first name."); return; }
    setErr(""); onNext();
  }
  return (
    <div style={{ maxWidth:440, margin:"0 auto", padding:"56px 24px" }}>
      <h2 style={{ color:T.ink, fontSize:24, fontWeight:600, margin:"0 0 8px", letterSpacing:"-0.01em" }}>
        Let's start with your name
      </h2>
      <p style={{ color:T.body, fontSize:14.5, lineHeight:1.6, margin:"0 0 28px" }}>
        No password needed. Your email lets you save and return to your plan later.
      </p>
      <div style={cardStyle}>
        <label style={labelStyle}>First name</label>
        <input value={user.name} onChange={e=>{ setUser({...user, name:e.target.value}); setErr(""); }}
          onKeyDown={e=>e.key==="Enter"&&go()} placeholder="Elisa" style={inputStyle} autoFocus />
        <label style={{ ...labelStyle, marginTop:16 }}>Email <span style={{ color:T.dim, fontWeight:400 }}>(optional)</span></label>
        <input value={user.email} onChange={e=>setUser({...user, email:e.target.value})}
          onKeyDown={e=>e.key==="Enter"&&go()} placeholder="elisa@email.com" type="email" style={inputStyle} />
        {err && <p style={{ color:T.health, fontSize:12.5, marginTop:10 }}>{err}</p>}
        <button onClick={go} style={{ ...btnPrimary, width:"100%", marginTop:20 }}>Continue →</button>
        <p style={{ color:T.dim, fontSize:12, textAlign:"center", marginTop:12 }}>
          Free to start · takes 10–15 minutes
        </p>
      </div>
    </div>
  );
}

// ── SCENARIOS ─────────────────────────────────────────────────────────────
function Scenarios({ user, onPick, onBack }) {
  return (
    <div style={{ maxWidth:720, margin:"0 auto", padding:"48px 24px" }}>
      <button onClick={onBack} style={backStyle}>← back</button>
      <h2 style={{ color:T.ink, fontSize:24, fontWeight:600, margin:"12px 0 6px", letterSpacing:"-0.01em" }}>
        What brings you here, {user.name}?
      </h2>
      <p style={{ color:T.body, fontSize:14.5, lineHeight:1.6, margin:"0 0 28px" }}>
        Pick what feels most pressing. Your advisor will start there — you can cover everything else too.
      </p>
      <div style={{ display:"grid", gridTemplateColumns:"repeat(auto-fit,minmax(220px,1fr))", gap:14 }}>
        {SCENARIOS.map(s=>(
          <button key={s.id} onClick={()=>onPick(s)} style={scenarioCard}
            onMouseEnter={e=>{ e.currentTarget.style.borderColor=T.brand; e.currentTarget.style.transform="translateY(-2px)"; }}
            onMouseLeave={e=>{ e.currentTarget.style.borderColor=T.line; e.currentTarget.style.transform="translateY(0)"; }}>
            <span style={{ fontSize:26, marginBottom:10, display:"block" }}>{s.icon}</span>
            <p style={{ color:T.ink, fontSize:15, fontWeight:600, margin:"0 0 5px", lineHeight:1.3 }}>{s.title}</p>
            <p style={{ color:T.dim, fontSize:12.5, margin:0, lineHeight:1.5 }}>{s.sub}</p>
          </button>
        ))}
      </div>
    </div>
  );
}

// ── SESSION (split view: chat + live playbook) ─────────────────────────────
function Session({ user, scenario, onBack }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [plan, setPlan] = useState(null);
  const [err, setErr] = useState("");
  const [mobileTab, setMobileTab] = useState("chat");
  const endRef = useRef(null);
  const taRef = useRef(null);

  useEffect(()=>{ endRef.current?.scrollIntoView({ behavior:"smooth" }); }, [messages, loading]);
  useEffect(()=>{ start(); }, []);

  async function callClaude(msgs) {
    const res = await fetch("https://api.anthropic.com/v1/messages", {
      method:"POST", headers:{ "Content-Type":"application/json" },
      body: JSON.stringify({ model:"claude-sonnet-4-6", max_tokens:1000, system:SYSTEM,
        messages: msgs.map(m=>({ role:m.role, content:m.content })) }),
    });
    if (!res.ok) throw new Error("api");
    const d = await res.json();
    return d.content?.[0]?.text || "";
  }

  function start() {
    const opener = `Hi ${user.name}, I'm really glad you're here. Most people avoid this — the fact that you showed up already puts you ahead.\n\nYou mentioned "${scenario.title.toLowerCase()}." Tell me a bit more about your situation — what's going on, and what's worrying you most right now?`;
    setMessages([{ role:"assistant", content:opener }]);
  }

  async function send() {
    if (!input.trim() || loading) return;
    const text = input.trim(); setInput("");
    const next = [...messages, { role:"user", content:text }];
    setMessages(next); setLoading(true); setErr("");
    try {
      const raw = await callClaude(next);
      const pm = raw.match(/<PLAN>([\s\S]*?)<\/PLAN>/);
      if (pm) { try { setPlan(JSON.parse(pm[1].trim())); } catch(e){} }
      const disp = raw.replace(/<PLAN>[\s\S]*?<\/PLAN>/g, "").trim();
      setMessages([...next, { role:"assistant", content:disp }]);
    } catch(e) { setErr("Connection issue — try again."); setMessages(next); }
    setLoading(false);
  }

  function download() {
    if (!plan) return;
    const L = ["MY FINAL PLAYBOOK","=================",`Name: ${user.name}`,
      `Situation: ${plan.situation}`,`Priority: ${DOMAINS[plan.priority]?.label||plan.priority}`,"",
      "ACTION ITEMS","------------",
      ...(plan.actions||[]).map((a,i)=>{
        const p=[`${i+1}. [${(DOMAINS[a.domain]?.label||a.domain).toUpperCase()}] ${a.text}`];
        if(a.when)p.push(`   When: ${a.when}`); if(a.script)p.push(`   Say: "${a.script}"`);
        return p.join("\n");
      }),"","BY DOMAIN","---------",
      ...["legal","financial","health","digital"].map(d=>{
        const s=plan[d]; if(!s)return "";
        return `${DOMAINS[d].label.toUpperCase()}\n  Status: ${s.summary||"—"}\n  Next: ${s.next||"—"}\n`;
      }),"","Generated by ENDevo · endevo.life"];
    const b=new Blob([L.join("\n")],{type:"text/plain"});
    const u=URL.createObjectURL(b); const a=document.createElement("a");
    a.href=u; a.download=`final-playbook-${user.name.toLowerCase()}.txt`; a.click();
  }

  return (
    <div style={{ maxWidth:1100, margin:"0 auto", padding:"16px 16px 0", height:"calc(100vh - 55px)", display:"flex", flexDirection:"column" }}>
      <div style={{ display:"flex", alignItems:"center", justifyContent:"space-between", marginBottom:12 }}>
        <button onClick={onBack} style={backStyle}>← change focus</button>
        {/* mobile tab switch */}
        <div style={{ display:"flex", gap:4, background:T.surf2, borderRadius:8, padding:3 }} className="mobile-tabs">
          {[["chat","Conversation"],["plan","My plan"]].map(([k,l])=>(
            <button key={k} onClick={()=>setMobileTab(k)} style={{
              padding:"5px 12px", borderRadius:6, border:"none", cursor:"pointer", fontSize:12, fontWeight:500,
              background: mobileTab===k?T.surf:"transparent", color: mobileTab===k?T.ink:T.dim }}>{l}</button>
          ))}
        </div>
      </div>

      <div style={{ display:"grid", gridTemplateColumns:"1fr 360px", gap:16, flex:1, minHeight:0 }} className="session-grid">
        {/* CHAT */}
        <div style={{ display:"flex", flexDirection:"column", background:T.surf, border:`1px solid ${T.line}`,
          borderRadius:14, overflow:"hidden", minHeight:0 }}
          data-pane="chat" className={mobileTab==="chat"?"pane-active":"pane-hidden"}>
          <div style={{ flex:1, overflowY:"auto", padding:"18px 18px 0" }}>
            {messages.map((m,i)=>(
              <div key={i} style={{ display:"flex", justifyContent: m.role==="user"?"flex-end":"flex-start",
                gap:9, marginBottom:16, alignItems:"flex-start" }}>
                {m.role==="assistant" && <div style={avatarStyle}>N</div>}
                <div style={ m.role==="user"?userBubble:agentBubble }>
                  {m.content.split("\n").map((l,j,arr)=>(<span key={j}>{l}{j<arr.length-1&&<br/>}</span>))}
                </div>
              </div>
            ))}
            {loading && (
              <div style={{ display:"flex", gap:9, marginBottom:16, alignItems:"flex-start" }}>
                <div style={avatarStyle}>N</div>
                <div style={{ ...agentBubble, display:"flex", gap:4, padding:"14px 18px" }}>
                  {[0,1,2].map(i=>(<span key={i} className="typing-dot" style={{ animationDelay:`${i*0.15}s` }}/>))}
                </div>
              </div>
            )}
            {err && <p style={{ color:T.health, fontSize:12.5, textAlign:"center", padding:"6px" }}>{err}</p>}
            <div ref={endRef}/>
          </div>
          <div style={{ padding:"12px 14px", borderTop:`1px solid ${T.line}`, display:"flex", gap:9, alignItems:"flex-end" }}>
            <textarea ref={taRef} value={input} onChange={e=>setInput(e.target.value)}
              onKeyDown={e=>{ if(e.key==="Enter"&&!e.shiftKey){ e.preventDefault(); send(); } }}
              placeholder="Type your response..." rows={2} disabled={loading}
              style={{ flex:1, background:T.surf2, border:`1px solid ${T.line}`, borderRadius:10,
                padding:"10px 13px", fontSize:14, color:T.ink, outline:"none", resize:"none",
                fontFamily:"inherit", lineHeight:1.5 }} />
            <button onClick={send} disabled={loading||!input.trim()} style={{ ...btnPrimary,
              padding:"10px 18px", opacity: (loading||!input.trim())?0.4:1, height:42 }}>Send</button>
          </div>
        </div>

        {/* PLAYBOOK */}
        <div style={{ background:T.surf, border:`1px solid ${T.line}`, borderRadius:14, overflowY:"auto", padding:"18px 16px" }}
          data-pane="plan" className={mobileTab==="plan"?"pane-active":"pane-hidden"}>
          <p style={{ color:T.dim, fontSize:11, fontWeight:700, letterSpacing:"0.06em", textTransform:"uppercase", margin:"0 0 14px" }}>
            Your playbook
          </p>
          {!plan ? (
            <div>
              <p style={{ color:T.dim, fontSize:13, lineHeight:1.6, marginBottom:16 }}>
                Your plan builds here as you talk. Keep going — your advisor is learning your situation.
              </p>
              {Object.entries(DOMAINS).map(([k,d])=>(
                <div key={k} style={{ display:"flex", alignItems:"center", gap:10, padding:"9px 0", borderBottom:`1px solid ${T.surf2}` }}>
                  <div style={{ width:8, height:8, borderRadius:"50%", background:d.color+"40" }}/>
                  <span style={{ color:T.dim, fontSize:13 }}>{d.label}</span>
                </div>
              ))}
            </div>
          ) : (
            <div style={{ display:"flex", flexDirection:"column", gap:16 }}>
              <div style={{ background:T.surf2, borderRadius:10, padding:"12px 14px" }}>
                <p style={{ color:T.dim, fontSize:10, fontWeight:700, letterSpacing:"0.06em", textTransform:"uppercase", margin:"0 0 5px" }}>Your situation</p>
                <p style={{ color:T.ink, fontSize:13, lineHeight:1.5, margin:0 }}>{plan.situation}</p>
                {plan.urgency==="critical" && <span style={{ display:"inline-block", marginTop:8, background:"#FEF3C7", color:"#92400E", fontSize:11, fontWeight:600, padding:"2px 8px", borderRadius:4 }}>⚠ Time-sensitive</span>}
              </div>
              {plan.actions?.length>0 && (
                <div>
                  <p style={{ color:T.dim, fontSize:10, fontWeight:700, letterSpacing:"0.06em", textTransform:"uppercase", margin:"0 0 10px" }}>Action items</p>
                  {plan.actions.map((a,i)=>(
                    <div key={i} style={{ display:"flex", gap:10, padding:"9px 0", borderBottom:`1px solid ${T.surf2}` }}>
                      <div style={{ width:22, height:22, borderRadius:6, background:(DOMAINS[a.domain]?.color||T.dim)+"1A",
                        color:DOMAINS[a.domain]?.color||T.dim, fontSize:11, fontWeight:700, display:"flex",
                        alignItems:"center", justifyContent:"center", flexShrink:0, marginTop:1 }}>{i+1}</div>
                      <div style={{ flex:1 }}>
                        <p style={{ color:T.ink, fontSize:13, lineHeight:1.45, margin:"0 0 2px" }}>{a.text}</p>
                        {a.when && <p style={{ color:T.dim, fontSize:11, margin:0 }}>{a.when}</p>}
                        {a.script && <p style={{ color:T.money, fontSize:11, fontStyle:"italic", margin:"3px 0 0", lineHeight:1.4 }}>"{a.script}"</p>}
                      </div>
                    </div>
                  ))}
                </div>
              )}
              <div>
                <p style={{ color:T.dim, fontSize:10, fontWeight:700, letterSpacing:"0.06em", textTransform:"uppercase", margin:"0 0 10px" }}>Your domains</p>
                {["legal","financial","health","digital"].map(d=>{
                  const info=plan[d]; const c=DOMAINS[d].color; const first=d===plan.priority;
                  return (
                    <div key={d} style={{ border:`1.5px solid ${first?c:T.line}`, borderRadius:8, padding:"10px 12px", marginBottom:8 }}>
                      <div style={{ display:"flex", alignItems:"center", gap:8, marginBottom:3 }}>
                        <div style={{ width:8, height:8, borderRadius:"50%", background:c }}/>
                        <span style={{ color:c, fontSize:12.5, fontWeight:600 }}>{DOMAINS[d].label}</span>
                        {first && <span style={{ background:c+"1A", color:c, fontSize:9, fontWeight:700, padding:"1px 6px", borderRadius:3 }}>Start here</span>}
                      </div>
                      <p style={{ color:T.body, fontSize:12, margin:0, lineHeight:1.4 }}>{info?.next||"To be explored"}</p>
                    </div>
                  );
                })}
              </div>
              <button onClick={download} style={{ ...btnPrimary, width:"100%" }}>Download my playbook ↓</button>
            </div>
          )}
        </div>
      </div>

      <style>{`
        @keyframes blink { 0%,80%,100%{opacity:0.2} 40%{opacity:1} }
        .typing-dot { width:6px; height:6px; border-radius:50%; background:${T.dim}; display:inline-block; animation:blink 1.2s infinite; }
        .mobile-tabs { display:none; }
        .pane-hidden { display:flex; }
        @media (max-width: 820px) {
          .session-grid { grid-template-columns:1fr !important; }
          .mobile-tabs { display:flex !important; }
          .pane-hidden { display:none !important; }
          .pane-active { display:flex !important; }
        }
      `}</style>
    </div>
  );
}

// ── STYLE PRIMITIVES ─────────────────────────────────────────────────────
const btnPrimary = { background:T.brand, color:T.brandLt, border:"none", borderRadius:10,
  padding:"12px 20px", fontSize:14, fontWeight:600, cursor:"pointer", fontFamily:"inherit", letterSpacing:"0.01em" };
const cardStyle = { background:T.surf, border:`1px solid ${T.line}`, borderRadius:14, padding:"24px 22px" };
const labelStyle = { color:T.body, fontSize:12.5, fontWeight:500, display:"block", marginBottom:6 };
const inputStyle = { width:"100%", background:T.surf2, border:`1px solid ${T.line}`, borderRadius:9,
  padding:"11px 14px", fontSize:14, color:T.ink, outline:"none", boxSizing:"border-box", fontFamily:"inherit", display:"block" };
const backStyle = { background:"none", border:"none", color:T.dim, fontSize:13, cursor:"pointer", padding:0, fontFamily:"inherit" };
const scenarioCard = { background:T.surf, border:`1px solid ${T.line}`, borderRadius:14, padding:"20px 18px",
  cursor:"pointer", textAlign:"left", transition:"all 0.15s ease", fontFamily:"inherit" };
const avatarStyle = { width:30, height:30, borderRadius:"50%", background:T.brand, color:T.brandLt,
  fontSize:12, fontWeight:700, display:"flex", alignItems:"center", justifyContent:"center", flexShrink:0, marginTop:2 };
const agentBubble = { background:T.surf2, borderRadius:"4px 14px 14px 14px", padding:"12px 15px",
  maxWidth:"78%", fontSize:14, color:T.ink, lineHeight:1.65 };
const userBubble = { background:T.brand, color:"#F0FDFA", borderRadius:"14px 4px 14px 14px",
  padding:"12px 15px", maxWidth:"75%", fontSize:14, lineHeight:1.6 };

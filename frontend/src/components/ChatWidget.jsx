import { useEffect, useRef, useState } from "react";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faPaperPlane, faXmark, faLock } from "@fortawesome/free-solid-svg-icons";
import { postChat } from "../api/client";
import { LOGO_URL } from "../config/branding";

const FREE_QUERY_LIMIT = 3;
const STORAGE_KEY = "fp_chat_query_count";

export default function ChatWidget({ plan, memberFirstName, tier, signals, onUpgrade }) {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([]); // [{role, content}]
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const isPaid = tier === "paid";
  const [queryCount, setQueryCount] = useState(() =>
    isPaid ? 0 : Number(localStorage.getItem(STORAGE_KEY) || 0)
  );
  const capped = !isPaid && queryCount >= FREE_QUERY_LIMIT;
  const scrollRef = useRef(null);

  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [messages, loading]);

  async function send() {
    if (!input.trim() || loading || capped) return;
    const nextHistory = [...messages, { role: "user", content: input.trim() }];
    setMessages(nextHistory);
    setInput("");
    setLoading(true);
    setError(null);
    try {
      const { reply } = await postChat({ plan, memberFirstName, history: nextHistory, signals });
      setMessages([...nextHistory, { role: "assistant", content: reply }]);
      if (!isPaid) {
        const next = queryCount + 1;
        setQueryCount(next);
        localStorage.setItem(STORAGE_KEY, String(next));
      }
    } catch (e) {
      // 401 = must sign in first; 402/429 = out of free questions -> upgrade.
      if (e.status === 401) {
        setError("Sign in (free) to ask Jesse.");
      } else if (e.status === 402 || e.status === 429) {
        setQueryCount(FREE_QUERY_LIMIT); // flip to the upgrade state
        localStorage.setItem(STORAGE_KEY, String(FREE_QUERY_LIMIT));
      } else {
        setError(e.message || "Something went wrong, try again.");
      }
      // roll back the optimistic user message on error
      setMessages(messages);
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <button className={`fp-chat-fab ${open ? "open" : "jesse"}`} onClick={() => setOpen((o) => !o)} aria-label={open ? "Close Jesse" : "Ask Jesse"}>
        {open ? <FontAwesomeIcon icon={faXmark} /> : <img src={LOGO_URL} alt="" className="fp-chat-fab-jesse" />}
      </button>
      {open && (
        <div className="fp-chat-panel">
          <div className="fp-chat-header">
            <img src={LOGO_URL} alt="" className="fp-chat-header-jesse" />
            <div className="fp-chat-header-text">
              <p>Jesse Guide</p>
              <span className="fp-chat-header-sub">{isPaid ? "Here to walk you through it" : "Ask about your plan"}</span>
            </div>
            {!isPaid && <span className="fp-chat-quota">{Math.min(queryCount, FREE_QUERY_LIMIT)}/{FREE_QUERY_LIMIT} free</span>}
          </div>
          <div className="fp-chat-messages" ref={scrollRef}>
            {messages.length === 0 && (
              <p className="fp-chat-empty">
                {isPaid
                  ? "Hi, I'm Jesse. Ask me anything about your plan, I'll walk you through any step, grounded only in what's here."
                  : "Hi, I'm Jesse. Ask me a question about your plan, free includes 3, upgrade for unlimited."}
                {" "}We're educators, not legal, financial, or medical advisors.
              </p>
            )}
            {messages.map((m, i) => (
              <div key={i} className={`fp-chat-bubble fp-chat-bubble-${m.role}`}>{m.content}</div>
            ))}
            {loading && <div className="fp-chat-bubble fp-chat-bubble-assistant">…</div>}
          </div>
          {error && <p className="fp-error" style={{ padding: "0 14px" }}>{error}</p>}
          {capped ? (
            <div className="fp-chat-capped">
              <FontAwesomeIcon icon={faLock} />
              <p>You've used your 3 free questions. Upgrade for unlimited time with Jesse.</p>
              <button className="fp-btn-upgrade" style={{ width: "100%" }} onClick={onUpgrade}>Upgrade →</button>
            </div>
          ) : (
            <div className="fp-chat-input-row">
              <input
                className="fp-chat-input"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && send()}
                placeholder="Type a question…"
                disabled={loading}
              />
              <button className="fp-chat-send" onClick={send} disabled={loading || !input.trim()} aria-label="Send">
                <FontAwesomeIcon icon={faPaperPlane} />
              </button>
            </div>
          )}
        </div>
      )}
    </>
  );
}

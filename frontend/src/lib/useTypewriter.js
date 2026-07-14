import { useEffect, useRef, useState } from "react";

// Type `text` out character-by-character when `active` is true. Returns the
// currently-typed substring + whether it's still typing (for a cursor). Respects
// prefers-reduced-motion (shows the full text instantly). Pure client polish.
export function useTypewriter(text, active, speed = 22) {
  const [shown, setShown] = useState(active ? "" : text);
  const rafText = useRef(text);

  useEffect(() => {
    rafText.current = text;
    const reduce = window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
    if (!active || reduce || !text) {
      setShown(text);
      return;
    }
    setShown("");
    let i = 0;
    const id = setInterval(() => {
      i += 1;
      setShown(text.slice(0, i));
      if (i >= text.length) clearInterval(id);
    }, speed);
    return () => clearInterval(id);
  }, [text, active, speed]);

  return { shown, typing: active && shown.length < text.length };
}

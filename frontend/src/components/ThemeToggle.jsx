import { useState } from "react";

// Compact Classic | ENDevo theme switch for the top nav. Classic (B2C,
// gold/navy/off-white) is the default; ENDevo (B2B navy/orange) is optional.
// Applies instantly and remembers the choice (localStorage, read in main.jsx).
export default function ThemeToggle() {
  const [theme, setThemeState] = useState(
    () => (localStorage.getItem("fp_theme") === "b2b" ? "b2b" : "b2c")
  );
  function set(next) {
    setThemeState(next);
    localStorage.setItem("fp_theme", next);
    if (next === "b2b") document.documentElement.setAttribute("data-theme", "b2b");
    else document.documentElement.removeAttribute("data-theme");
  }
  return (
    <div className="fp-theme-switch" role="group" aria-label="Theme">
      <button className={`fp-theme-opt ${theme === "b2c" ? "on" : ""}`} onClick={() => set("b2c")}>
        Classic
      </button>
      <button className={`fp-theme-opt ${theme === "b2b" ? "on" : ""}`} onClick={() => set("b2b")}>
        ENDevo
      </button>
    </div>
  );
}

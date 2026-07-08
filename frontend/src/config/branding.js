// Single source of truth for all user-facing brand text and links.
// Change these to re-skin the product -- no component code needs editing.
// Anything that used to hard-code a specific expert's name or personal
// "clone" framing now reads from here.

// Product + company identity ------------------------------------------------
export const PRODUCT_NAME = "MyFinalPlaybook";
export const COMPANY_NAME = "MyFinalPlaybook";     // shown in the top-left nav
export const TAGLINE = "Live Fully, Die Ready.";

// The member-facing name of the deliverable. ALWAYS "My Final Playbook" (never
// "Your Final Playbook") -- it's the member's own document. Use this everywhere
// the plan is referred to, and PRIMARY_CTA for the main call-to-action button.
export const PLAYBOOK_NAME = "My Final Playbook";
export const PRIMARY_CTA = "Get My Final Playbook";

// A safe display first name. Never shows a raw email as the name: if we only
// have an email, use the part before "@"; strip anything that looks like an
// address. Falls back to empty so callers can render a name-less heading.
export function firstName(raw) {
  const v = (raw || "").trim();
  if (!v) return "";
  const base = v.includes("@") ? v.split("@")[0] : v;
  // take the first word, title-case it, drop digits/punctuation noise
  const word = base.split(/[\s._-]+/).filter(Boolean)[0] || "";
  const clean = word.replace(/[^a-zA-Z]/g, "");
  if (!clean) return "";
  return clean.charAt(0).toUpperCase() + clean.slice(1);
}

// The personalized (paid) narrative is delivered in a neutral guide voice, not
// any named person's voice. This string is used everywhere the UI describes
// what the paid tier adds.
export const PERSONALIZED_VOICE_LABEL = "a warm, personalized narrative";

// Jesse's logo (the Day-of-the-Dead mascot), imported so Vite bundles + hashes
// it. If it ever fails to load, TopNav/Welcome fall back to the letter badge.
import jesseLogo from "../assets/jesse_final.png";
export const LOGO_URL = jesseLogo;
export const LOGO_LETTER = "M"; // fallback badge if the image can't load

// Checkout / upgrade. When Stripe is configured, the UpgradeButton calls the
// backend to create a Checkout session and redirects; UPGRADE_URL is only the
// static fallback used if the backend checkout endpoint is unavailable.
export const UPGRADE_URL = "https://example.com/final-playbook/upgrade";

// Single source of truth for all user-facing brand text and links.
// Change these to re-skin the product -- no component code needs editing.
// Anything that used to hard-code a specific expert's name or personal
// "clone" framing now reads from here.

// Product + company identity ------------------------------------------------
export const PRODUCT_NAME = "MyFinalPlaybook";
export const COMPANY_NAME = "MyFinalPlaybook";     // shown in the top-left nav
export const TAGLINE = "Live Fully, Die Ready.";

// The personalized (paid) narrative is delivered in a neutral guide voice, not
// any named person's voice. This string is used everywhere the UI describes
// what the paid tier adds.
export const PERSONALIZED_VOICE_LABEL = "a warm, personalized narrative";

// Jesse's logo. Drop the image at frontend/public/logo.png (or .jpg/.svg) and
// it loads from "/logo.png". If the file isn't present yet, TopNav/Welcome fall
// back to the letter badge below (so the UI never shows a broken image).
export const LOGO_URL = "/logo.png";
export const LOGO_LETTER = "M"; // fallback badge until the logo file is in place

// Checkout / upgrade. When Stripe is configured, the UpgradeButton calls the
// backend to create a Checkout session and redirects; UPGRADE_URL is only the
// static fallback used if the backend checkout endpoint is unavailable.
export const UPGRADE_URL = "https://example.com/final-playbook/upgrade";

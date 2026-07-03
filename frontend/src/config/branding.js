// Set to a real path (e.g. "/logo.png" served from public/, or an imported
// asset) once the client provides the final logo file. Until then, LOGO_URL
// stays null and TopNav/Welcome fall back to the existing letter-badge.
export const LOGO_URL = null;

// Set to a YouTube/Vimeo embed URL (e.g. "https://www.youtube.com/embed/XXXX")
// once the intro/walkthrough video is ready. Until then, Welcome.jsx shows a
// "coming soon" placeholder instead. If you have a direct video FILE instead
// of a hosted link, swap the <iframe> in Welcome.jsx for a <video> tag.
export const INTRO_VIDEO_URL = null;

// Real ENDevo wordmark (light-background/navy-text version -- matches the
// footer's white background). A dark-bg white-text variant also exists
// (logo_v2_with_white_text.png) for future use on dark surfaces if needed.
export const FOOTER_LOGO_URL = "/endevo-logo.png";

// Placeholder -- swap for the real payment/checkout link once available.
// Opens in a new tab (see UpgradeButton.jsx) so users never lose their
// in-progress plan.
export const UPGRADE_URL = "https://example.com/final-playbook/upgrade";

// TEMPORARY demo flag: when true, every member sees the full paid experience
// regardless of which tier they picked -- full domain lists, the AI
// personalized narrative, unlimited chat, and the download button. This also
// makes Session.jsx send tier="paid" to the backend on every plan request,
// so it DOES trigger real LLM calls (real cost) even for "Free" signups.
// Set to true only for demos -- real freemium/paid gating (with the improved
// free-tier preview: one real item per domain/checklist, blurred rest, 3
// free chat questions) is the normal state.
export const UNLOCK_FREEMIUM = false;

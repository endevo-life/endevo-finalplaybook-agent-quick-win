// API base URL comes from the Vite env (VITE_API_BASE_URL) so the same build
// points at localhost in dev and the API Gateway URL in production. Falls back
// to the local dev server.
const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8001";

// --- session token (persisted so a refresh keeps you logged in) --------------
const TOKEN_KEY = "fp_token";
export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}
export function setToken(token) {
  if (token) localStorage.setItem(TOKEN_KEY, token);
  else localStorage.removeItem(TOKEN_KEY);
}

function authHeaders() {
  const t = getToken();
  return t ? { Authorization: `Bearer ${t}` } : {};
}

async function request(path, { method = "GET", body } = {}) {
  const res = await fetch(`${BASE_URL}${path}`, {
    method,
    headers: {
      ...(body ? { "Content-Type": "application/json" } : {}),
      ...authHeaders(),
    },
    body: body ? JSON.stringify(body) : undefined,
  });
  const data = await res.json().catch(() => null);
  if (!res.ok) {
    const err = new Error(data?.detail || `Request failed (${res.status})`);
    err.status = res.status;
    throw err;
  }
  return data;
}

// --- agent -------------------------------------------------------------------
export function postPlan({ flags, memberFirstName, tier }) {
  return request("/api/plan", { method: "POST", body: { flags, memberFirstName, tier } });
}

export async function getGlossary() {
  try {
    return await request("/api/glossary");
  } catch {
    return [];
  }
}

export function postChat({ plan, memberFirstName, history }) {
  return request("/api/chat", { method: "POST", body: { plan, memberFirstName, history } });
}

// --- pricing / marketing -----------------------------------------------------
export function getPricing() {
  return request("/api/pricing");
}

// --- domain assessment (condensed, deterministic, free) ----------------------
export function getAssessment() {
  return request("/api/assessment");
}
export function postAssessmentPlan(answers) {
  return request("/api/assessment/plan", { method: "POST", body: { answers } });
}
// Paid: turn the assessment into a personalized 7-day narrative (one LLM call).
export function postAssessmentPersonalize(answers, memberFirstName) {
  return request("/api/assessment/personalize", {
    method: "POST",
    body: { answers, memberFirstName },
  });
}

// Per-user saved plan: answers, generated plan, tracked progress, narrative,
// and chat history. Restores a logged-in user's session across devices.
export function getMyPlan() {
  return request("/api/my/plan");
}
export function saveMyPlan({ answers, plan, tracked, narrative }) {
  return request("/api/my/plan", { method: "POST", body: { answers, plan, tracked, narrative } });
}

// --- auth --------------------------------------------------------------------
export function authStart(email) {
  return request("/api/auth/start", { method: "POST", body: { email } });
}
export function authVerify(email, code) {
  return request("/api/auth/verify", { method: "POST", body: { email, code } });
}
export function getMe() {
  return request("/api/me");
}
export function authLogout() {
  return request("/api/auth/logout", { method: "POST" });
}

// --- billing -----------------------------------------------------------------
export function startCheckout() {
  return request("/api/billing/checkout", { method: "POST" });
}
// Dev-only unlock (no Stripe). Backend gates this behind ALLOW_DEV_UPGRADE.
export function devUpgrade() {
  return request("/api/billing/dev-upgrade", { method: "POST" });
}

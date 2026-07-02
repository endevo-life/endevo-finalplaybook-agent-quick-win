const BASE_URL = "http://localhost:8001";

export async function postPlan({ flags, memberFirstName, tier }) {
  const res = await fetch(`${BASE_URL}/api/plan`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ flags, memberFirstName, tier }),
  });
  const data = await res.json().catch(() => null);
  if (!res.ok) {
    throw new Error(data?.detail || `Request failed (${res.status})`);
  }
  return data;
}

export async function getGlossary() {
  const res = await fetch(`${BASE_URL}/api/glossary`);
  if (!res.ok) return [];
  return res.json();
}

export async function postChat({ plan, memberFirstName, history }) {
  const res = await fetch(`${BASE_URL}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ plan, memberFirstName, history }),
  });
  const data = await res.json().catch(() => null);
  if (!res.ok) {
    throw new Error(data?.detail || `Request failed (${res.status})`);
  }
  return data; // { reply: string }
}

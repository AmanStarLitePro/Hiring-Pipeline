const SERVER_BACKEND_URL =
  process.env.BACKEND_URL || "http://127.0.0.1:8000";

export const API_BASE_URL =
  typeof window === "undefined" ? SERVER_BACKEND_URL : "/api/backend";

async function request(path, options = {}) {
  const url = `${API_BASE_URL}${path}`;
  console.log(`[API Request] Fetching: ${url}`);

  const response = await fetch(url, {
    headers: {
      Accept: "application/json",
      ...(options.body ? { "Content-Type": "application/json" } : {}),
      ...options.headers,
    },
    ...options,
  });

  if (!response.ok) {
    const detail = await response.text();
    console.error(`[API Error] Path: ${path} | Status: ${response.status}`, detail);
    throw new Error(
      detail || `Backend request failed with status ${response.status}`
    );
  }

  if (response.status === 204) return null;
  const data = await response.json();
  console.log(`[API Response] Path: ${path} | Data:`, data);
  return data;
}

function unwrapList(payload, keys = []) {
  if (Array.isArray(payload)) return payload;

  for (const key of keys) {
    if (Array.isArray(payload?.[key])) return payload[key];
  }

  return [];
}

export function normalizeCandidates(payload) {
  if (!payload) return [];
  if (Array.isArray(payload)) return payload;
  if (Array.isArray(payload.records)) return payload.records;
  if (payload.id && payload.name) return [payload];
  if (typeof payload === "object") return payload;
  return [];
}

export function normalizeHistory(payload) {
  return unwrapList(payload, ["history", "events", "data"]);
}

export function normalizeAuditLogs(payload) {
  return unwrapList(payload, ["audit_logs", "logs", "results", "data"]);
}

export async function getCandidates() {
  const payload = await request("/hiring/candidates");
  return normalizeCandidates(payload);
}

export async function searchCandidates(query) {
  const payload = await request("/hiring/search", {
    method: "POST",
    body: JSON.stringify({ query }),
  });
  return normalizeCandidates(payload);
}

export async function addCandidate(candidateData) {
  return await request("/hiring/candidates", {
    method: "POST",
    body: JSON.stringify(candidateData),
  });
}

export async function getCandidateHistory(id) {
  const payload = await request(
    `/hiring/candidates/${encodeURIComponent(id)}/history`
  );
  console.log("[getCandidateHistory RAW] Payload received:", payload);
  
  return {
    ...payload,
    history: normalizeHistory(payload),
  };
}

export async function getAuditLogs(candidateId) {
  const query = candidateId
    ? `?candidate_id=${encodeURIComponent(candidateId)}`
    : "";
  const payload = await request(`/hiring/audit_logs${query}`);
  return normalizeAuditLogs(payload);
}
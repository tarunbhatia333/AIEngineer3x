import { authHeaders } from "./keys.js";

// In production (Vercel), the frontend and API share an origin (see vercel.json
// rewrites), so a relative "" base is correct. In local dev, the Vite server
// (5173) and FastAPI (8787) are separate origins, so default to localhost.
const API_BASE = import.meta.env.VITE_API_BASE ?? (import.meta.env.PROD ? "" : "http://localhost:8787");

async function handle(res) {
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch {
      /* ignore parse errors */
    }
    throw new Error(detail);
  }
  return res.json();
}

export async function getCollections() {
  return handle(await fetch(`${API_BASE}/api/collections`, { headers: authHeaders() }));
}

export async function activateCollection(name) {
  return handle(
    await fetch(`${API_BASE}/api/collections/${encodeURIComponent(name)}/activate`, {
      method: "POST",
      headers: authHeaders(),
    })
  );
}

export async function deleteCollection(name) {
  return handle(
    await fetch(`${API_BASE}/api/collections/${encodeURIComponent(name)}`, {
      method: "DELETE",
      headers: authHeaders(),
    })
  );
}

export async function reingestDefault() {
  return handle(
    await fetch(`${API_BASE}/api/ingest/default`, { method: "POST", headers: authHeaders() })
  );
}

export async function uploadDocument(file) {
  const formData = new FormData();
  formData.append("file", file);
  return handle(
    await fetch(`${API_BASE}/api/ingest/upload`, {
      method: "POST",
      headers: authHeaders(),
      body: formData,
    })
  );
}

export async function runQuery(question, collection) {
  return handle(
    await fetch(`${API_BASE}/api/query`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...authHeaders() },
      body: JSON.stringify({ question, collection }),
    })
  );
}

export async function checkHealth() {
  return handle(await fetch(`${API_BASE}/api/health`));
}

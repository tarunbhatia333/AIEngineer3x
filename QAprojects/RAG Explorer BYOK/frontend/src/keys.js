const STORAGE_KEY = "rag-explorer-byok-keys";

function readAll() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY)) || {};
  } catch {
    return {};
  }
}

export function getKeys() {
  const stored = readAll();
  return {
    groq: stored.groq || "",
    openai: stored.openai || "",
    pinecone: stored.pinecone || "",
  };
}

export function saveKeys({ groq, openai, pinecone }) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify({ groq, openai, pinecone }));
}

export function clearKeys() {
  localStorage.removeItem(STORAGE_KEY);
}

export function hasAllKeys() {
  const { groq, openai, pinecone } = getKeys();
  return Boolean(groq && openai && pinecone);
}

export function authHeaders() {
  const { groq, openai, pinecone } = getKeys();
  const headers = {};
  if (groq) headers["X-Groq-Key"] = groq;
  if (openai) headers["X-OpenAI-Key"] = openai;
  if (pinecone) headers["X-Pinecone-Key"] = pinecone;
  return headers;
}

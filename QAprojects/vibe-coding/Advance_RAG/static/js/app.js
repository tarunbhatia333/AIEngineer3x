/* Shared helpers used by upload.html, ingest.html, chunks.html, chat.html */

/**
 * Streams a text/event-stream response from a POST endpoint (fetch's
 * ReadableStream, not EventSource, since EventSource can't POST a body).
 * Parses "event: X\ndata: {...}\n\n" blocks and calls handlers[eventName].
 *
 * `body` may be a plain object (sent as JSON) or a FormData instance (sent
 * as multipart, e.g. when re-attaching a File — browser sets its own
 * Content-Type with the multipart boundary, so no header is set for that case).
 */
async function streamSSE(url, body, handlers) {
  const isFormData = body instanceof FormData;
  const resp = await fetch(url, {
    method: "POST",
    headers: isFormData ? {} : { "Content-Type": "application/json" },
    body: isFormData ? body : JSON.stringify(body),
  });
  if (!resp.ok) {
    const err = await resp.json().catch(() => ({ error: resp.statusText }));
    if (handlers.error) handlers.error(err);
    return;
  }
  const reader = resp.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    let sep;
    while ((sep = buffer.indexOf("\n\n")) !== -1) {
      const block = buffer.slice(0, sep);
      buffer = buffer.slice(sep + 2);
      const eventMatch = block.match(/^event: (.+)$/m);
      const dataMatch = block.match(/^data: (.+)$/m);
      if (!eventMatch || !dataMatch) continue;
      const eventName = eventMatch[1].trim();
      let data = {};
      try { data = JSON.parse(dataMatch[1]); } catch (e) { /* ignore */ }
      if (handlers[eventName]) handlers[eventName](data);
      if (handlers._any) handlers._any(eventName, data);
    }
  }
}

/** Renders a fixed sequence of pipeline stages into #tracker-list, then lets
 * setStageStatus() flip each <li>'s class as SSE events arrive. */
function renderTracker(stages) {
  const list = document.getElementById("tracker-list");
  if (!list) return;
  list.innerHTML = stages
    .map((s) => `<li class="stage" data-stage="${s.key}"><span class="dot"></span>${s.label}</li>`)
    .join("");
}

function setStageStatus(key, status) {
  const el = document.querySelector(`.stage[data-stage="${key}"]`);
  if (!el) return;
  el.classList.remove("active", "done", "error");
  if (status) el.classList.add(status);
}

function escapeHtml(str) {
  return String(str)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

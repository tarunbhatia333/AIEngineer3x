const SECTIONS = ["linkedin", "medium"];

function el(id) {
  return document.getElementById(id);
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str || "";
  return div.innerHTML;
}

function skeletonCardsHtml() {
  return Array.from({ length: 3 })
    .map(
      () => `
      <div class="option-card skeleton">
        <div class="skel-line"></div>
        <div class="skel-line short"></div>
      </div>`
    )
    .join("");
}

function renderOptionCards(section, options) {
  const container = el(`options-${section}-cards`);
  if (!options.length) {
    container.innerHTML = `<p style="color:var(--gray);font-size:13px;">No items available right now — try refreshing, or use the custom topic field below.</p>`;
    return;
  }
  container.innerHTML = options
    .map(
      (opt) => `
      <div class="option-card" data-id="${opt.id}" data-section="${section}">
        <span class="option-card__headline">${escapeHtml(opt.headline)}</span>
        <span class="option-card__meta">${escapeHtml(opt.source)} &middot; ${escapeHtml(opt.time_ago)}</span>
        <button type="button" class="option-card__select btn">SELECT &rarr;</button>
      </div>`
    )
    .join("");

  container.querySelectorAll(".option-card__select").forEach((btn) => {
    btn.addEventListener("click", () => {
      const card = btn.closest(".option-card");
      generateFromOption(card.dataset.section, card.dataset.id);
    });
  });
}

async function fetchOptions(section, force) {
  const panel = el(`options-${section}`);
  const cards = el(`options-${section}-cards`);
  panel.hidden = false;
  cards.innerHTML = skeletonCardsHtml();

  const refreshBtn = el(`refresh-${section}`);
  if (refreshBtn) refreshBtn.classList.add("is-spinning");

  try {
    const resp = await fetch(`/fetch-options/${section}${force ? "?force=true" : ""}`);
    const data = await resp.json();
    renderOptionCards(section, data.options || []);
    el(`options-${section}-updated`).textContent = "Updated just now";
  } catch (err) {
    cards.innerHTML = `<p style="color:#ff9a9a;font-size:13px;">Failed to load options: ${escapeHtml(String(err))}</p>`;
  } finally {
    if (refreshBtn) refreshBtn.classList.remove("is-spinning");
  }
}

function showLoading(section) {
  const out = el(`output-${section}`);
  out.hidden = false;
  out.innerHTML = `
    <div class="output__spinner">
      <div class="spin-icon"></div>
      <p>Generating your ${section === "medium" ? "article" : "post"}...</p>
    </div>`;
}

function showError(section, message) {
  const out = el(`output-${section}`);
  out.hidden = false;
  out.innerHTML = `<div class="output__error">${escapeHtml(message)}</div>`;
}

function renderResult(section, data) {
  const out = el(`output-${section}`);
  out.hidden = false;

  const noteHtml = data.note
    ? `<div class="output__note">${escapeHtml(data.note)}</div>`
    : "";

  let bodyHtml;
  let tagsHtml;
  if (section === "linkedin") {
    bodyHtml = `<h3>Caption</h3><p class="output__text">${escapeHtml(data.caption)}</p>`;
    tagsHtml = `<h3>Hashtags</h3><p class="output__tags">${escapeHtml((data.hashtags || []).join(" "))}</p>`;
  } else {
    bodyHtml = `
      <h3>Title</h3><p class="output__text">${escapeHtml(data.title)}</p>
      <h3>Intro</h3><p class="output__text">${escapeHtml(data.intro)}</p>
      <h3>Article</h3><p class="output__text">${escapeHtml(data.body_markdown)}</p>`;
    tagsHtml = `<h3>Tags</h3><p class="output__tags">${escapeHtml((data.tags || []).join(", "))}</p>`;
  }

  const promptBoxHtml = data.manual_image_prompt
    ? `
      <div class="output__prompt-box">
        <h3>Copy image prompt</h3>
        <p class="output__prompt-hint">AI image generation didn't produce an image this time — paste this prompt into ChatGPT, Gemini, or DALL-E to generate it yourself.</p>
        <textarea class="output__prompt-text" readonly rows="4">${escapeHtml(data.manual_image_prompt)}</textarea>
        <button type="button" class="btn copy-btn" data-target="prompt-${section}">COPY PROMPT</button>
      </div>`
    : "";

  out.innerHTML = `
    ${noteHtml}
    <div class="output__content">
      <div class="output__image-wrap">
        <img class="output__image" src="${data.image_url}" alt="Generated ${section} preview">
      </div>
      <div class="output__details">
        ${bodyHtml}
        ${tagsHtml}
        ${promptBoxHtml}
        <div class="output__downloads">
          <a class="btn" href="${data.image_url}" download="${data.image_filename}">DOWNLOAD IMAGE</a>
          <button type="button" class="btn" id="download-text-btn">DOWNLOAD TEXT</button>
        </div>
      </div>
    </div>`;

  const downloadTextBtn = out.querySelector("#download-text-btn");
  if (downloadTextBtn) {
    downloadTextBtn.addEventListener("click", () => {
      const blob = new Blob([data.text_body || ""], { type: "text/plain;charset=utf-8" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = data.text_filename;
      a.click();
      URL.revokeObjectURL(url);
    });
  }

  const copyBtn = out.querySelector(".copy-btn");
  if (copyBtn) {
    copyBtn.addEventListener("click", () => {
      const textarea = out.querySelector(".output__prompt-text");
      navigator.clipboard.writeText(textarea.value);
      copyBtn.textContent = "COPIED!";
      setTimeout(() => (copyBtn.textContent = "COPY PROMPT"), 1500);
    });
  }
}

async function generateFromOption(section, optionId) {
  showLoading(section);
  try {
    const resp = await fetch(`/generate/${section}/${optionId}`, { method: "POST" });
    const data = await resp.json();
    if (!resp.ok) {
      showError(section, data.error || "Generation failed.");
      return;
    }
    renderResult(section, data);
  } catch (err) {
    showError(section, String(err));
  }
}

function readFileAsDataUrl(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.onerror = reject;
    reader.readAsDataURL(file);
  });
}

async function generateFromCustom(section) {
  const input = el(`custom-input-${section}`);
  const topic = input.value.trim();
  if (!topic) {
    showError(section, "Please enter a topic to generate content about.");
    return;
  }

  const fileInput = el(`custom-image-${section}`);
  const file = fileInput && fileInput.files[0];

  showLoading(section);
  try {
    const body = { topic };
    if (file) {
      body.reference_image = await readFileAsDataUrl(file);
    }

    const resp = await fetch(`/generate/${section}/custom`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const data = await resp.json();
    if (!resp.ok) {
      showError(section, data.error || "Generation failed.");
      return;
    }
    renderResult(section, data);
  } catch (err) {
    showError(section, String(err));
  }
}

function setupReferenceUpload(section) {
  const fileInput = el(`custom-image-${section}`);
  const dropZone = el(`custom-image-${section}-drop`);
  const preview = el(`custom-image-${section}-preview`);
  const clearBtn = el(`custom-image-${section}-clear`);
  if (!fileInput) return;

  async function showFile(file) {
    if (!file || !file.type.startsWith("image/")) return;
    // Reflect the chosen/dropped/pasted file in the <input> so generateFromCustom() picks it up.
    const dt = new DataTransfer();
    dt.items.add(file);
    fileInput.files = dt.files;

    preview.querySelector("img").src = await readFileAsDataUrl(file);
    preview.hidden = false;
  }

  fileInput.addEventListener("change", () => showFile(fileInput.files[0]));

  clearBtn.addEventListener("click", () => {
    fileInput.value = "";
    preview.hidden = true;
  });

  if (dropZone) {
    ["dragenter", "dragover"].forEach((evt) =>
      dropZone.addEventListener(evt, (e) => {
        e.preventDefault();
        dropZone.classList.add("is-dragover");
      })
    );
    ["dragleave", "drop"].forEach((evt) =>
      dropZone.addEventListener(evt, (e) => {
        e.preventDefault();
        dropZone.classList.remove("is-dragover");
      })
    );
    dropZone.addEventListener("drop", (e) => {
      const file = e.dataTransfer.files && e.dataTransfer.files[0];
      if (file) showFile(file);
    });

    dropZone.addEventListener("paste", (e) => {
      const item = Array.from(e.clipboardData.items || []).find((i) => i.type.startsWith("image/"));
      if (item) showFile(item.getAsFile());
    });
  }
}

SECTIONS.forEach((section) => {
  el(`btn-${section}`).addEventListener("click", () => fetchOptions(section, false));
  el(`refresh-${section}`).addEventListener("click", () => fetchOptions(section, true));
  el(`btn-custom-${section}`).addEventListener("click", () => generateFromCustom(section));
  setupReferenceUpload(section);
});

const output = document.getElementById("output");
const spinner = document.getElementById("spinner");
const errorBox = document.getElementById("error-box");
const outputContent = document.getElementById("output-content");
const promptBox = document.getElementById("prompt-box");
const promptText = document.getElementById("prompt-text");
const logsBox = document.getElementById("logs-box");
const logsText = document.getElementById("logs-text");

const outputImage = document.getElementById("output-image");
const outputCaption = document.getElementById("output-caption");
const outputHashtags = document.getElementById("output-hashtags");
const outputNote = document.getElementById("output-note");
const imagePromptBox = document.getElementById("image-prompt-box");
const imagePromptText = document.getElementById("image-prompt-text");
const downloadImage = document.getElementById("download-image");
const downloadText = document.getElementById("download-text");

const allButtons = () => document.querySelectorAll(".action-card, .custom__btn");

function setLoading(isLoading) {
  allButtons().forEach((btn) => (btn.disabled = isLoading));
  output.hidden = false;
  spinner.hidden = !isLoading;
  if (isLoading) {
    errorBox.hidden = true;
    promptBox.hidden = true;
    outputContent.hidden = true;
    logsBox.hidden = true;
  }
}

function showLogs(logs) {
  if (logs && logs.length) {
    logsText.value = logs.join("\n");
    logsBox.hidden = false;
  } else {
    logsBox.hidden = true;
  }
}

function showError(message, isQuota, manualPrompt, logs) {
  errorBox.hidden = false;
  errorBox.classList.toggle("output__error--quota", Boolean(isQuota));
  errorBox.textContent = `${isQuota ? "⏳" : "⚠"} ${message}`;
  outputContent.hidden = true;

  if (manualPrompt) {
    promptText.value = manualPrompt;
    promptBox.hidden = false;
  } else {
    promptBox.hidden = true;
  }

  showLogs(logs);
}

function showResult(data) {
  outputImage.src = data.image_url;
  outputCaption.textContent = data.caption || "";
  outputHashtags.textContent = (data.hashtags || []).join(" ");

  if (data.note) {
    outputNote.textContent = `ℹ️ ${data.note}`;
    outputNote.hidden = false;
  } else {
    outputNote.hidden = true;
  }

  if (data.manual_image_prompt) {
    imagePromptText.value = data.manual_image_prompt;
    imagePromptBox.hidden = false;
  } else {
    imagePromptBox.hidden = true;
  }

  downloadImage.href = `/download/image/${data.image_filename}`;
  downloadText.href = `/download/text/${data.text_filename}`;

  errorBox.hidden = true;
  promptBox.hidden = true;
  outputContent.hidden = false;

  showLogs(data.logs);

  output.scrollIntoView({ behavior: "smooth", block: "start" });
}

function setupCopyButton(button) {
  const targetId = button.getAttribute("data-target");
  const target = document.getElementById(targetId);
  const originalLabel = button.textContent;

  button.addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(target.value);
    } catch (err) {
      target.select();
      document.execCommand("copy");
    }
    button.textContent = "✅ COPIED!";
    setTimeout(() => {
      button.textContent = originalLabel;
    }, 1500);
  });
}

document.querySelectorAll(".output__copy-btn").forEach(setupCopyButton);

async function generate(endpoint, body) {
  setLoading(true);
  try {
    const response = await fetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body || {}),
    });

    const data = await response.json();

    if (!response.ok) {
      showError(
        data.error || "Something went wrong while generating content.",
        Boolean(data.quota_exceeded),
        data.manual_prompt,
        data.logs
      );
      return;
    }

    showResult(data);
  } catch (err) {
    showError(err.message, false);
  } finally {
    setLoading(false);
  }
}

// ---------------------------------------------------------------------------
// Two-step selection flow: News / Match Preview / Match Review
// ---------------------------------------------------------------------------

const SECTIONS = ["news", "preview", "review"];
const AUTO_REFRESH_MS = 60 * 60 * 1000; // 1 hour

function cardMeta(section, option) {
  if (section === "news") {
    return { icon: "📰", title: option.headline, meta: `${option.source} · ${option.time_ago}` };
  }
  if (section === "preview") {
    return {
      icon: "⚽",
      title: `${option.home_team} vs ${option.away_team}`,
      meta: `${option.competition} · ${option.kickoff}`,
    };
  }
  return {
    icon: "📊",
    title: `${option.home_team} ${option.score} ${option.away_team}`,
    meta: option.competition,
  };
}

function renderSkeletons(section) {
  const cardsEl = document.getElementById(`options-${section}-cards`);
  cardsEl.innerHTML = "";
  for (let i = 0; i < 3; i++) {
    const skeleton = document.createElement("div");
    skeleton.className = "skeleton-card";
    cardsEl.appendChild(skeleton);
  }
}

function renderOptions(section, options) {
  const cardsEl = document.getElementById(`options-${section}-cards`);
  cardsEl.innerHTML = "";

  if (!options.length) {
    const empty = document.createElement("p");
    empty.className = "options-panel__empty";
    empty.textContent = "No trending items right now — try refreshing.";
    cardsEl.appendChild(empty);
    return;
  }

  options.forEach((option) => {
    const { icon, title, meta } = cardMeta(section, option);
    const card = document.createElement("div");
    card.className = "option-card";
    card.innerHTML = `
      <div class="option-card__icon">${icon}</div>
      <div class="option-card__headline">${title}</div>
      <div class="option-card__meta">${meta}</div>
      <button type="button" class="option-card__select btn btn--gold">SELECT →</button>
    `;
    card.querySelector(".option-card__select").addEventListener("click", () => {
      generate(`/generate/${section}/${option.id}`);
    });
    cardsEl.appendChild(card);
  });
}

function formatUpdated(lastUpdated) {
  const seconds = Math.max((Date.now() / 1000) - lastUpdated, 0);
  if (seconds < 60) return "Updated just now";
  const minutes = Math.round(seconds / 60);
  if (minutes < 60) return `Updated ${minutes} min${minutes !== 1 ? "s" : ""} ago`;
  const hours = Math.round(minutes / 60);
  return `Updated ${hours} hour${hours !== 1 ? "s" : ""} ago`;
}

async function loadOptions(section, { force = false, showSkeletons = true } = {}) {
  const panel = document.getElementById(`options-${section}`);
  panel.hidden = false;

  if (showSkeletons) {
    renderSkeletons(section);
  }

  try {
    const response = await fetch(`/fetch-options/${section}${force ? "?force=true" : ""}`);
    const data = await response.json();
    if (!response.ok) {
      renderOptions(section, []);
      return;
    }
    renderOptions(section, data.options || []);
    document.getElementById(`options-${section}-updated`).textContent = formatUpdated(data.last_updated);
  } catch (err) {
    renderOptions(section, []);
  }
}

SECTIONS.forEach((section) => {
  document.getElementById(`btn-${section}`).addEventListener("click", () => {
    loadOptions(section, { force: false, showSkeletons: true });
  });

  const refreshBtn = document.getElementById(`refresh-${section}`);
  refreshBtn.addEventListener("click", async () => {
    refreshBtn.classList.add("refresh-icon--spinning");
    await loadOptions(section, { force: true, showSkeletons: false });
    refreshBtn.classList.remove("refresh-icon--spinning");
  });

  setInterval(() => {
    const panel = document.getElementById(`options-${section}`);
    if (!panel.hidden) {
      loadOptions(section, { force: true, showSkeletons: false });
    }
  }, AUTO_REFRESH_MS);
});

document.getElementById("btn-custom").addEventListener("click", () => {
  const prompt = document.getElementById("custom-input").value.trim();
  if (!prompt) {
    showError("Please enter a topic to generate content about.", false);
    return;
  }
  generate("/generate/custom", { prompt });
});

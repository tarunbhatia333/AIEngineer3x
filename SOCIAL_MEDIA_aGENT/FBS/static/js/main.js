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

document.getElementById("btn-news").addEventListener("click", () => {
  generate("/generate/news");
});

document.getElementById("btn-preview").addEventListener("click", () => {
  generate("/generate/preview");
});

document.getElementById("btn-review").addEventListener("click", () => {
  generate("/generate/review");
});

document.getElementById("btn-custom").addEventListener("click", () => {
  const prompt = document.getElementById("custom-input").value.trim();
  if (!prompt) {
    showError("Please enter a topic to generate content about.", false);
    return;
  }
  generate("/generate/custom", { prompt });
});

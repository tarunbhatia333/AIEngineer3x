# QA Content Agent

One-click LinkedIn & Medium content generator for QA / Test Automation / AI agents in QA /
vibe coding / n8n topics.

**🔗 Live app: [https://qa-content-agent.vercel.app](https://qa-content-agent.vercel.app)**

Generate branded, ready-to-post content — images, captions/articles, and hashtags/tags —
sourced from real, current QA/automation news, all from a single black-and-orange dashboard.

---

## Features

- 💼 **LinkedIn Post** — scrapes trending QA/automation/AI-agent items, suggests 3 real
  options to post about, and generates a branded image + practitioner-voice caption + hashtags
- ✍️ **Medium Article** — same suggestion flow, generates a longer-form SEO-aware article
  (title + intro + ~600–900 word body) + cover image + tags
- 🖼️ **Reference image upload** — optionally attach an image (click, drag-and-drop, or
  paste/Ctrl+V) to the custom-topic box to use as a visual base for the generated graphic
- ⬇ **One-Click Download** — download the generated image (.png) and caption/article text
  (.txt) directly from the dashboard
- 🔎 **"Image generated via" label** — every result shows which provider actually produced
  the image (OpenAI, Gemini, or Hugging Face), so it's never a mystery

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11+, Flask, deployed serverless on Vercel |
| Content Generation | Groq (Llama 3.3 70B) → OpenAI (GPT-4o) → Gemini, automatic fallback chain |
| Image Generation | OpenAI `gpt-image-1` → Gemini (`gemini-2.5-flash-image`) → Hugging Face (`black-forest-labs/FLUX.1-schnell`) → PIL placeholder |
| Image Compositing | Pillow (PIL) — composed images returned as inline base64 (no disk persistence, serverless-friendly) |
| Source Data | `feedparser` (Ministry of Testing, Selenium, TestGuild, Applitools, n8n RSS) + dev.to API + Hacker News Algolia API + Reddit RSS + GitHub search API |
| Frontend | HTML5, CSS3 (black `#0D0D0D` + orange `#FF6B00` theme), Vanilla JS |
| Env Management | `python-dotenv` (local) / Vercel project environment variables (production) |

### AI provider fallback chains

- **Text/content generation**: Groq (`llama-3.3-70b-versatile`) → OpenAI (`gpt-4o`) → Gemini
  (`gemini-2.0-flash`). A `QuotaExceededError` is raised only if every configured provider is
  exhausted, with the raw prompt surfaced for manual use.
- **Image generation**: OpenAI (`gpt-image-1`) → Gemini (`gemini-2.5-flash-image`) → Hugging
  Face Inference API (`black-forest-labs/FLUX.1-schnell`) → PIL-drawn placeholder. The
  provider that actually succeeded is returned to the UI and shown under the image.
- **Reference-image upload**: tried via OpenAI's `images.edit` first, then Gemini's
  multimodal image+text input; dropped gracefully (not an error) if neither tier is
  available, falling through to plain text-to-image.

See `SKILL.md` for the full architecture writeup.

---

## Project Structure

```
QA_content_creator/
│
├── app.py                        # Main Flask application
├── api/index.py                  # Vercel serverless entrypoint (exposes `app`)
├── vercel.json                   # Rewrites all routes to api/index.py
├── .env.example                  # Template for required environment variables
├── .gitignore
├── requirements.txt
│
├── agents/
│   ├── __init__.py               # Shared SYSTEM_PROMPT/VOICE_GUIDELINES + multi-provider generate_content()
│   ├── linkedin_agent.py         # build_prompt(item=None, custom_topic=None) for LinkedIn posts
│   └── medium_agent.py           # build_prompt(item=None, custom_topic=None) for Medium articles
│
├── image_gen/
│   ├── __init__.py
│   ├── image_generator.py        # OpenAI -> Gemini -> Hugging Face image fallback chain
│   └── image_composer.py         # PIL-based compositing + text-based brand lockup
│
├── scrapers/
│   ├── __init__.py
│   └── qa_scraper.py             # RSS/dev.to/HN/Reddit/GitHub source aggregation
│
├── templates/
│   └── index.html                # Main dashboard HTML (Jinja2)
│
├── static/
│   ├── css/style.css             # Black/orange dashboard styles
│   └── js/main.js                # AJAX handlers, drag-drop/paste upload, download triggers
│
├── files/                        # Original planning docs (build prompt + blueprint)
├── SKILL.md                      # As-built architecture reference
└── QA_Content_Agent.agent.md     # Agent role/domain description
```

---

## Setup Instructions (local development)

```bash
# 1. Navigate to the project
cd QA_content_creator

# 2. Create a virtual environment
python -m venv venv
venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Add your API keys to .env (see Environment Variables below)

# 5. Run the app
python app.py

# 6. Open your browser
# http://localhost:5050
```

---

## How to Use

1. **SUGGEST POSTS** (LinkedIn) — fetches 3 real, current QA/automation items to pick from.
   Click **SELECT →** on one to generate a branded image + caption + hashtags.
2. **SUGGEST ARTICLES** (Medium) — same flow, generates a longer-form article + cover image
   + tags instead.
3. **Custom topic** — type any QA/automation topic into the text box under either section
   and click **GENERATE FROM TOPIC**. Optionally attach a reference image first.
4. Use **DOWNLOAD IMAGE** and **DOWNLOAD TEXT** to save the output locally.

---

## Environment Variables

| Variable | Description |
|---|---|
| `OPENAI_API_KEY` | Used for GPT-4o content generation (fallback) and `gpt-image-1` image generation (primary) |
| `GEMINI_API_KEY` | Optional. Fallback for text and image generation if OpenAI hits its rate limit/quota |
| `GROQ_API_KEY` | Optional. Used first for content generation (`llama-3.3-70b-versatile`) to save OpenAI credits |
| `HUGGINGFACE_API_KEY` | Optional. Third-tier image fallback via FLUX.1-schnell on Hugging Face's Inference API |
| `FLASK_SECRET_KEY` | Secret key used by Flask for session security |

A ready-to-fill template is provided in `.env.example`. In production, these are set as
Vercel project environment variables instead of a committed `.env` file.

> ⚠️ **Never commit your `.env` file or share your API keys publicly.**

---

## Deployment

Deployed on Vercel's Python serverless runtime at **https://qa-content-agent.vercel.app**.
`vercel.json` rewrites every route to `api/index.py`; Vercel auto-detects the Flask `app`
object and handles `static/`/`templates/` with zero extra config. Generated images are
returned as inline base64 data URLs rather than saved to disk, since Vercel's serverless
filesystem doesn't persist files between invocations.

---

## Credits

QA Content Agent — for QA/test-automation/AI-in-QA practitioners.

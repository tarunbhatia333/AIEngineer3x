---
name: qa-content-agent
description: One-click content generator for QA/Test-Automation/AI-in-QA topics, producing branded LinkedIn posts and Medium articles. Adapted from the content-gen-app blueprint (FBS football reference implementation). Two independent buttons/flows — "LinkedIn Post" and "Medium Article" — each with its own suggestion pool, refresh, and custom-topic input with optional reference-image upload. Live at https://qa-content-agent.vercel.app.
---

# QA Content Agent — Architecture (as built)

Reference architecture: `SOCIAL_MEDIA_aGENT/FBS` (football news -> Instagram posts).
Same 5-piece skeleton, same two-step generation flow, same anti-hallucination and
fallback-chain principles. Domain swapped to **QA / Test Automation / AI agents in QA /
vibe coding / n8n workflows**, platforms swapped to **LinkedIn + Medium**, brand theme
swapped to **black + orange**. Deployed serverless on Vercel.

## Core architecture

```
app.py                       Flask routes + two-step generate flow + in-memory options cache
api/index.py                  Vercel serverless entrypoint, exposes `app` for the Python runtime
agents/
  __init__.py                 shared GUIDELINES constant (brand + "sound human" rules) + generate_content()
  linkedin_agent.py            build_prompt(item=None, custom_topic=None) for LinkedIn posts
  medium_agent.py              build_prompt(item=None, custom_topic=None) for Medium articles
scrapers/qa_scraper.py        pulls REAL current QA/automation/AI-agent/n8n items — never let GPT invent facts
image_gen/
  image_generator.py           OpenAI gpt-image-1 -> Gemini -> Hugging Face (FLUX.1-schnell) fallback chain
  image_composer.py            PIL: fit AI image to canvas + text-based brand lockup (no logo file needed)
templates/ + static/          dashboard UI: 2 action cards -> options panel -> generated preview
vercel.json                   rewrites all routes to api/index.py; Vercel auto-detects the Flask `app`
```

## The two-step generation flow — TWO independent instances

There is **no shared "section" picker** like FBS's News/Preview/Review. There are exactly
two top-level buttons on the dashboard, each running its own full flow:

**"SUGGEST POSTS" (LinkedIn)**
1. Click -> backend pulls a pool of real, current QA/automation/AI-agent/vibe-coding/n8n
   items (see Scraper sources below), `random.sample(pool, min(3, len(pool)))`, caches by
   uuid, returns as 3 lightweight option cards (headline, source, time-ago) with a visible
   **SELECT →** button. No GPT/image call yet.
2. User clicks SELECT -> `POST /generate/linkedin/<id>` -> full pipeline: `linkedin_agent
   .build_prompt(item) -> generate_content() -> generate_image() -> compose_linkedin_post()`.
3. Refresh icon re-samples the pool (`force=true`); skeleton cards while loading.
4. A **custom-topic** textarea sits below the cards (free-text QA/automation topic, bypasses
   the pool) with its own "GENERATE FROM TOPIC" button, plus an optional **reference-image
   upload** (click, drag-and-drop, or paste/Ctrl+V) used as a visual base for the image.

**"SUGGEST ARTICLES" (Medium)**
Identical shape, separate pool/sample/cache/pick cycle, its own custom-topic field +
reference-image upload. The agent differs (longer-form, SEO title, article draft instead of
a short caption) and the image differs (article cover, not feed graphic) — see Domain knobs.

Both buttons reuse the same `scrapers/qa_scraper.py` pool.

## Scraper sources (QA / automation / AI-in-QA / vibe coding / n8n)

Fail-soft to `[]` per source on network error — never let one dead feed break the pool.

- Ministry of Testing, Selenium, TestGuild, Applitools, n8n blog RSS feeds
- dev.to public API, filtered by tags: `testing`, `qa`, `automation`, `ai`, `playwright`, `selenium`
- Hacker News (Algolia API), queried for: "test automation", "AI agent QA", "vibe coding", "Selenium", "Playwright", "n8n"
- Reddit RSS (read-only `.rss` feeds): r/QualityAssurance, r/softwaretesting, r/selenium, r/n8n, r/automation
- GitHub search API for topics: `selenium`, `playwright`, `test-automation`, `ai-agents`, `n8n`

`_time_ago` / `_source_name` helpers format cards as "2h ago · github.com".

## Anti-hallucination grounding

- Pass the picked item's `raw_data` dict straight into `build_prompt(item)` — any version
  number, stat, tool name, or quote in the output must trace back to this dict.
- For the custom-topic path, `build_prompt(custom_topic=...)` injects a LIVE DATA SNAPSHOT
  block built from the scraper's most recent items (`_live_data_snapshot()` in each agent
  file) instead of faking a scraped item — the model is told any specific fact must come
  from the snapshot or be phrased as general/timeless advice.

## "Sounds human, not AI"

The shared `VOICE_GUIDELINES` constant in `agents/__init__.py` instructs the model to avoid
stock AI openers, em-dash overuse (max 1), emoji stacking, and templated CTAs — and to use
first-person practitioner framing, one concrete grounded detail, mixed sentence length, and
contractions. Includes a one-shot example of the target voice.

## Image generation — as actually implemented

- **Fallback chain (in order): OpenAI `gpt-image-1` → Gemini (`gemini-2.5-flash-image`) →
  Hugging Face Inference API (`black-forest-labs/FLUX.1-schnell`) → PIL-drawn placeholder.**
  Each tier is tried only if the prior one errors (rate limit, billing limit, quota,
  moderation block). `generate_image()` returns `(image_bytes, provider_label)` and the
  label is shown to the user in the UI under the generated image ("Image generated via:
  Hugging Face (black-forest-labs/FLUX.1-schnell)").
- **Reference-image upload**: if the user attaches an image in the custom-topic box, it's
  tried first via OpenAI's `images.edit` (image + prompt), then Gemini's multimodal
  image+text input. If neither tier is available/working, the reference is dropped (not an
  error) and generation continues as plain text-to-image — Hugging Face's endpoint has no
  image-input support.
- **No disk persistence**: composed images are returned as inline `data:image/png;base64,...`
  URLs in the JSON response, not saved to `output/` and served from a file route — required
  because Vercel's serverless filesystem is ephemeral per-invocation. Text downloads are
  built client-side from a Blob in `main.js`, not a server route either.
- **Palette/aesthetic**: near-black `#0D0D0D` + orange `#FF6B00`, tech-editorial (terminal/
  code fragments, line art, geometric shapes), no stock photos or realistic people.
- **Canvases**: LinkedIn 1080×1350 (4:5), Medium 1200×630. Both use `_fit_with_padding`
  (never crop) plus a small PIL-drawn text-based brand lockup (no logo image file needed).
- **Hard image failure**: surfaces the raw image prompt in a copy-to-clipboard box in the UI
  (`manual_image_prompt` in the response) — caption/article text is still always returned.
- **Text-model fallback chain**: Groq Llama 3.3 → GPT-4o → Gemini text → typed
  `QuotaExceededError` with the raw prompt shown for manual use.

## Domain knobs (filled in)

| Knob | LinkedIn Post | Medium Article |
|---|---|---|
| Image canvas | 1080×1350 (4:5 feed) | 1200×630 (article cover) |
| "Full graphic" baked text | Hook headline | Title only |
| Caption/body tone | Practitioner voice, ~150–200 words | SEO-aware title + intro + ~600–900 word body (Markdown) |
| Tags | 3–5 LinkedIn hashtags | 5 lowercase Medium tags |
| Reference image upload | Yes (click / drag-drop / paste) | Yes (click / drag-drop / paste) |

## Deployment

Deployed on Vercel's Python serverless runtime — **https://qa-content-agent.vercel.app**.
`vercel.json` rewrites every route to `api/index.py`, which imports the Flask `app` object;
Vercel's zero-config Python detection handles `static/`/`templates/` automatically (no
`includeFiles` config needed). Env vars (`OPENAI_API_KEY`, `GEMINI_API_KEY`, `GROQ_API_KEY`,
`HUGGINGFACE_API_KEY`, `FLASK_SECRET_KEY`) are set in the Vercel project's production
environment, not committed to the repo.

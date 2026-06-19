---
name: content-gen-app
description: Blueprint for building a one-click social/content generation web app (Flask + GPT + image model) for any topic and any platform — e.g. football Instagram posts (FootBro Show, reference implementation), QA/test-automation LinkedIn + Medium posts (QA Content Agent, second reference implementation), Twitter/X threads. Use when the user wants to scaffold or extend a "pick a real source item -> auto-generate branded post" tool.
---

# Content-Gen App Blueprint

Reference implementations:
- `SOCIAL_MEDIA_aGENT/FBS` (football news -> Instagram posts for @thefootbroshow)
- `QAProject/QAProject/QA_content_creator` (QA/automation news -> LinkedIn posts + Medium
  articles, deployed at https://qa-content-agent.vercel.app — see its `SKILL.md` for the
  as-built writeup, including a 3-tier image fallback chain and serverless-specific
  adaptations like inline base64 images instead of disk persistence)

Copy this architecture, swap the **domain knobs** in the table below, and the same app
works for a different topic/platform.

## Core architecture (always the same 5 pieces)

```
app.py                  Flask routes + the two-step generate flow + in-memory options cache
agents/
  __init__.py            shared GUIDELINES constant + generate_content() (GPT call w/ fallback chain)
  <type>_agent.py         one file per content type, build_prompt(item=None) -> GPT user prompt string
scrapers/<domain>_scraper.py   pulls REAL current data (RSS/API) — never let GPT invent facts
image_gen/
  image_generator.py      calls image model (gpt-image-1 primary, Gemini image fallback)
  image_composer.py       PIL: fit AI image to final canvas + brand lockup (logo/handle)
templates/ + static/      dashboard UI: action cards -> options panel -> generated preview
```

## The two-step generation flow (always the same UX)

1. User clicks "Generate" under a content-type section (e.g. News / Preview / Review).
2. Backend scrapes/fetches a **pool** of real current items, randomly samples 3
   (`random.sample(pool, min(3, len(pool)))` — never deterministically slice the same top-3,
   or the refresh button will look broken), caches them keyed by a uuid `id`, returns them as
   lightweight option cards (no GPT/image call yet — cheap and fast).
3. User picks one card -> `POST /generate/<type>/<id>` looks the cached item back up by id and
   runs the full pipeline: `build_prompt(item) -> generate_content() -> generate_image() ->
   compose_*_post() -> save`.
4. Manual refresh re-samples from the pool (`force=true`); an auto-refresh timer (e.g. 1hr)
   does the same silently if the panel is open. Always show skeleton cards while loading.

This pattern generalizes directly: "3 trending LinkedIn discussion topics", "3 candidate
Medium article angles from today's RSS", "3 tweet-worthy headlines" — same fetch -> sample ->
cache-by-id -> pick -> generate shape regardless of topic or platform.

## Anti-hallucination grounding (always required)

GPT's training data goes stale. Any agent that needs specific facts (a score, a stat, a launch
date, a quote) must receive them as **structured real data already fetched by your scraper**,
never rely on GPT's memory:
- Pass the picked item's `raw_data` dict straight into `build_prompt(item)`.
- For free-form/custom topics with no single picked item, inject a "LIVE DATA SNAPSHOT" block
  built from your scraper's most recent N items (see `agents/custom_agent.py::_live_data_snapshot`
  for the exact pattern) and instruct GPT: *"your training knowledge may be outdated; any
  specific fact must come only from this snapshot; write around it if the fact isn't there."*

## Image generation (always the same two-tier approach)

- **Primary**: one image-model call per post where the model bakes ALL on-image text
  (headline, stat bullets, leaderboard/table) directly into the graphic — write the literal
  text verbatim in the prompt (`'bold text reading "X 3-1 Y"'`), don't just describe it
  abstractly. Real named people -> "stylized lookalike cartoon/caricature", never a realistic
  photo of an identifiable person (moderation-safe). See `agents/__init__.py::FULL_GRAPHIC_GUIDELINES`.
- **Compose, don't crop**: fit the generated image onto the exact target canvas with
  letterbox/pad (`_fit_with_padding`), not crop-to-fill — cropping cuts off baked-in text near
  edges. Reserve a clear strip (e.g. bottom ~130px) in the prompt for your logo/handle lockup,
  drawn with PIL afterward.
- **Fallback chain**: image model A (e.g. gpt-image-1) -> on quota/rate-limit, image model B
  (e.g. Gemini image) -> on total failure, fall back to a PIL-composited placeholder (flat
  brand-color background + headline + bullet list drawn with PIL) so the app never hard-fails.
- **Text-model fallback chain**: same idea — primary (GPT-4o) -> secondary (Groq Llama) ->
  tertiary (Gemini text) -> raise a typed `QuotaExceededError` only if all are exhausted, and
  surface the raw prompt so the user can paste it elsewhere manually.

## Domain knobs to change per new app

| Knob | Football/Instagram (reference) | LinkedIn example | Medium example |
|---|---|---|---|
| Scraper sources | ESPN scoreboard JSON, Goal/ESPN/BBC/Sky/Guardian RSS | Industry news RSS, company blog RSS, trending-topics API | Niche-topic RSS, arXiv/HN/Reddit API |
| Content types (agents) | News / Preview / Review / Custom | Industry-news take / Personal-milestone post / Custom | Listicle / Deep-dive / Opinion / Custom |
| Image canvas size | 1080x1350 (4:5 portrait) | 1200x627 (link-share) or 1080x1080 (square) | 1200x630 (article cover) |
| Brand visual theme | Dark green #0a1f0a + gold #ffd700, Bebas Neue headlines | Match the user's LinkedIn banner colors | Match the publication's cover style |
| Caption tone/length | Punchy, opinionated, ~150 words | Professional, hook + insight + CTA, ~200 words | Long-form intro paragraph, SEO-aware title |
| "Full graphic" baked text | Score lines + leaderboard table | Stat callout + quote card | Pull-quote + title card |
| Hashtags/tags count | Top 5 | 3-5 LinkedIn hashtags | 5 Medium tags |

## Build checklist for a new instance

1. Write `scrapers/<domain>_scraper.py`: functions that return lists of dicts with real,
   structured, current data (fail-soft to `[]` on network error). Add small presentation
   helpers (`_time_ago`, `_source_name`) if the UI needs "2 hours ago / Source.com" labels.
2. Write `agents/__init__.py`: `<DOMAIN>_GUIDELINES` constant (the brand/canvas/text-baking
   rules) + shared `generate_content()` with the model fallback chain.
3. Write one `agents/<type>_agent.py` per content type: `build_prompt(item=None)` that falls
   back to the scraper's "most relevant item" when called with no argument, and references the
   guidelines constant for the image-prompt instruction.
4. Write/adapt `image_gen/image_generator.py` (model + size + quality="high") and
   `image_gen/image_composer.py` (`compose_full_graphic_post` using `_fit_with_padding`, plus a
   PIL-drawn `compose_<platform>_post` fallback).
5. Wire `app.py`: `SECTION_FETCHERS` (sample-from-pool functions), `PROMPT_BUILDERS`,
   `/fetch-options/<section>`, `/generate/<section>/<id>`, `/generate/custom`, the shared
   `_generate()` helper (branch on whether the AI image succeeded).
6. Build `templates/index.html` + `static/js/main.js` + `static/css/style.css`: action cards ->
   options panel (skeleton -> real cards -> refresh icon) -> generated preview with
   caption/hashtags/downloads, matching the new brand theme.
7. Test: force-refresh twice and confirm options actually change; generate once per content
   type and confirm baked-in image text matches the picked item's real data, not invented facts.

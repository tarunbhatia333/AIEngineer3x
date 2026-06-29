---
name: qa-content-agent
description: Blueprint for a one-click content generator for QA/Test-Automation/AI-in-QA topics, producing branded LinkedIn posts and Medium articles. Adapted from the content-gen-app blueprint (FBS football reference implementation). Two independent buttons/flows instead of three: "LinkedIn Post" and "Medium Article", each with its own suggestion pool, refresh, and custom-topic input.
---

# QA Content Agent — Build Blueprint

Reference architecture: `SOCIAL_MEDIA_aGENT/FBS` (football news -> Instagram posts).
Same 5-piece skeleton, same two-step generation flow, same anti-hallucination and
fallback-chain principles. Domain swapped to **QA / Test Automation / AI agents in QA /
vibe coding / n8n workflows**, platforms swapped to **LinkedIn + Medium**, brand theme
swapped to **black + orange**.

## Core architecture (unchanged shape, renamed folder)

```
app.py                       Flask routes + two-step generate flow + in-memory options cache
agents/
  __init__.py                 shared GUIDELINES constant (brand + "sound human" rules) + generate_content()
  linkedin_agent.py            build_prompt(item=None) for LinkedIn posts
  medium_agent.py              build_prompt(item=None) for Medium articles
scrapers/qa_scraper.py        pulls REAL current QA/automation/AI-agent/n8n items — never let GPT invent facts
image_gen/
  image_generator.py           gpt-image-1 primary, Gemini image fallback
  image_composer.py            PIL: fit AI image to canvas + brand lockup (logo/handle)
templates/ + static/          dashboard UI: 2 action cards -> options panel -> generated preview
```

## The two-step generation flow — TWO independent instances, not three

There is **no shared "section" picker** like FBS's News/Preview/Review. There are exactly
two top-level buttons on the dashboard, each running its own full flow:

**Button 1 — "Generate LinkedIn Post"**
1. Click -> backend pulls a pool of real, current QA/automation/AI-agent/vibe-coding/n8n
   items (see Scraper sources below), `random.sample(pool, min(3, len(pool)))`, caches by
   uuid, returns as 3 lightweight option cards (title, source, snippet, age). No GPT/image
   call yet.
2. User picks a card -> `POST /generate/linkedin/<id>` -> full pipeline: `linkedin_agent
   .build_prompt(item) -> generate_content() -> generate_image() -> compose_linkedin_post()
   -> save`.
3. Refresh icon re-samples the pool (`force=true`); skeleton cards while loading.
4. A **Custom Topic** text field sits below the cards (free-text QA/automation topic,
   bypasses the pool, still goes through the same pipeline + "sound human" guidelines).

**Button 2 — "Generate Medium Article"**
Identical shape, separate pool/sample/cache/pick cycle, its own Custom Topic field. The
agent differs (longer-form, SEO title, article draft instead of a short caption) and the
image differs (article cover, not feed graphic) — see Domain knobs table.

Both buttons can reuse the same `scrapers/qa_scraper.py` pool (same raw items), but each
agent frames/samples it differently — LinkedIn wants "hot take in the next 10 minutes"
items, Medium wants "deep enough to write 800+ words" items. Keep two separate
`build_prompt()` files even though the scraper is shared.

## Scraper sources (QA / automation / AI-in-QA / vibe coding / n8n)

Fail-soft to `[]` per source on network error — never let one dead feed break the pool.

- Ministry of Testing blog RSS
- Selenium official blog RSS (`selenium.dev/blog`)
- Applitools / TestGuild blogs (RSS)
- Playwright blog + GitHub releases (new features = good post fodder)
- n8n blog RSS + n8n community forum (workflow-automation angle, incl. QA-for-n8n-workflows)
- dev.to public API, filtered by tags: `testing`, `qa`, `automation`, `ai`, `playwright`,
  `selenium`
- Hacker News (Algolia API), queried for: "test automation", "AI agent QA", "vibe coding",
  "Selenium", "Playwright", "n8n"
- Reddit RSS (read-only `.rss` feeds): r/QualityAssurance, r/softwaretesting, r/selenium,
  r/n8n, r/automation
- GitHub Trending / GitHub API for topics: `selenium`, `playwright`, `test-automation`,
  `ai-agents`, `n8n`

Add small presentation helpers (`_time_ago`, `_source_name`) exactly like FBS, so cards can
show "2h ago · Ministry of Testing".

## Anti-hallucination grounding (unchanged principle)

- Pass the picked item's `raw_data` dict straight into `build_prompt(item)` — any version
  number, stat, tool name, or quote in the output must trace back to this dict.
- For Custom Topic (no picked item), inject a "LIVE DATA SNAPSHOT" block built from the
  scraper's most recent N relevant items, same pattern as FBS's `custom_agent.py
  ::_live_data_snapshot`. Instruct GPT explicitly: *"your training knowledge may be
  outdated; any specific tool version, statistic, or claim must come only from this
  snapshot or be phrased as general/timeless advice — never invent a number."*
- QA audiences spot fake specifics fast (wrong Selenium version, made-up benchmark numbers,
  a "study found X%" with no source) — treat this guardrail as harder-required than in FBS,
  not optional.

## "Sounds human, not AI" — required for this app (new vs. FBS)

LinkedIn/Medium audiences in tech are unusually good at spotting AI-generated copy. The
`GUIDELINES` constant must explicitly instruct the model to avoid this, and the prompt
should give a few-shot example of the target voice (a real practitioner's LinkedIn post),
not just a list of rules.

**Avoid:**
- Stock AI openers: "In today's fast-paced world...", "Let's dive in", "Unlock the power
  of...", "Game-changer", "It's not just X, it's Y"
- Heavy em-dash usage — keep to at most one per post
- Emoji stacking (max 1, often zero — this is a dev/QA audience, not lifestyle content)
- Generic closing CTA repeated every time ("What are your thoughts?" on every single post)
- Perfectly uniform sentence length / corporate-smooth rhythm
- Hashtag stuffing inside the body text — hashtags belong at the end only

**Use:**
- First-person, practitioner framing ("Spent this morning debugging a flaky Playwright
  test and—") rather than third-person announcer voice
- One concrete, specific detail (a real error message shape, a real tool name + version
  from the grounding data, a real number) to anchor the post in reality
- Mixed sentence length: a short punchy line next to a longer explanatory one
- A varied, topic-specific closing line/question each time, not a template
- Contractions throughout ("it's", "didn't", "you'll")

## Image generation (black + orange theme, two canvas sizes)

- **Palette**: near-black background (`#0D0D0D`–`#111111`) + orange accent
  (`#FF6B00`–`#FF7A00`), clean bold sans-serif (Space Grotesk / Inter / Sora style)
  for any baked headline text.
- **Aesthetic**: tech-editorial, not cartoonish — terminal/code-snippet fragments,
  abstract circuit or network line art, geometric shapes, minimal icons. No stock-photo
  people, no realistic photos of named individuals. Should look credible on a QA
  professional's LinkedIn feed, not like a meme.
- **LinkedIn canvas**: 1080×1350 (4:5 feed post) — bake in a short hook headline and, where
  the content is cheatsheet/listicle-style, 2–4 short bullet lines (e.g. "3 Playwright
  locator strategies") written verbatim in the image prompt, not described abstractly.
  Reserve a bottom strip (~130px) for the brand lockup (logo/handle), drawn with PIL after
  the AI image returns.
- **Medium canvas**: 1200×630 (standard article cover) — simpler: title text only, no
  bullet list (the article body carries the detail). Same palette/lockup treatment.
- **Compose, don't crop**: `_fit_with_padding` onto the exact canvas, same as FBS — cropping
  cuts off baked-in text near the edges.
- **Fallback chain**: gpt-image-1 -> Gemini image -> PIL-composited placeholder (flat brand
  background + headline + bullets/title drawn with PIL).
- **"Generate elsewhere" fallback (required, same UX as FBS)**: if every image tier fails,
  surface the exact image prompt in a copy-to-clipboard box in the UI so the user can paste
  it into an external image tool (DALL-E web UI, Midjourney, etc.) and upload the result
  back in manually. Never hard-fail the whole post — caption/hashtags/article text should
  still be deliverable even with no image.
- **Text-model fallback chain**: GPT-4o -> Groq Llama -> Gemini text -> typed
  `QuotaExceededError`, with the raw prompt shown to the user to paste elsewhere manually
  (same pattern as the image fallback).

## Domain knobs (filled in)

| Knob | LinkedIn Post | Medium Article |
|---|---|---|
| Scraper sources | shared `qa_scraper.py` pool (see above) | same pool, sampled for "deep enough" items |
| Image canvas | 1080×1350 (4:5 feed) | 1200×630 (article cover) |
| Brand theme | Black `#0D0D0D` + Orange `#FF6B00`, tech-editorial line art | same palette, more minimal/editorial |
| "Full graphic" baked text | Hook headline + 2–4 bullet cheatsheet lines | Title only |
| Caption/body tone | Practitioner voice, hook + insight + CTA, ~150–200 words, human-sounding (see above) | SEO-aware title + long-form intro paragraph + outline/draft, ~600–900 words |
| Tags | Top 3–5 LinkedIn hashtags (rotate from a QA/automation tag pool) | 5 Medium tags (lowercase, e.g. `software-testing`, `test-automation`, `ai`, `automation`, `qa`) |
| Custom topic input | Yes, separate field under LinkedIn section | Yes, separate field under Medium section |

## Build checklist for this instance

1. `scrapers/qa_scraper.py`: functions returning lists of dicts with real, structured,
   current QA/automation/AI-agent/n8n data, fail-soft to `[]` per source.
2. `agents/__init__.py`: `QA_GUIDELINES` constant (brand/canvas/text-baking rules **plus**
   the "sounds human" voice rules and a short few-shot example post) + shared
   `generate_content()` with the model fallback chain.
3. `agents/linkedin_agent.py`: `build_prompt(item=None)`, falls back to the scraper's most
   relevant item when called with no argument (custom topic path), references
   `QA_GUIDELINES`.
4. `agents/medium_agent.py`: same shape, longer-form prompt, SEO title instruction.
5. `image_gen/image_generator.py` (model + per-section size + quality="high") and
   `image_gen/image_composer.py` (`compose_linkedin_post`, `compose_medium_post`, both using
   `_fit_with_padding`, plus PIL-drawn fallbacks for each).
6. Wire `app.py`: two independent route pairs —
   `/fetch-options/linkedin`, `/generate/linkedin/<id>`, `/generate/linkedin/custom` and
   `/fetch-options/medium`, `/generate/medium/<id>`, `/generate/medium/custom` — plus the
   shared `_generate()` helper (branch on whether the AI image succeeded; surface the raw
   prompt in the UI on total image failure).
7. `templates/index.html` + `static/js/main.js` + `static/css/style.css`: two clearly
   separate sections ("LinkedIn Post" / "Medium Article"), each with action button ->
   skeleton cards -> real cards -> refresh icon -> custom-topic field -> generated preview
   (image + caption/article + tags + download + "copy image prompt" fallback button), in the
   black/orange theme.
8. Test: force-refresh both sections twice and confirm options actually change; generate
   once per section and confirm (a) baked-in image text matches the picked item's real data,
   never invented facts, and (b) the generated caption/article reads like a practitioner
   wrote it, not like templated AI copy.

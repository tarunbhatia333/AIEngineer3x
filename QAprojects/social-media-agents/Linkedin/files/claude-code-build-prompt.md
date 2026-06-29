# Prompt for Claude Code

Paste everything below this line into a Claude Code chat in your new project folder.

---

I'm building a one-click content generator web app, same overall architecture as a Flask
project I already built called FBS (a football news -> Instagram content agent: scrape
real data -> show 3 picks -> generate a branded image + caption + hashtags with GPT-4o /
DALL-E). I've attached the adapted blueprint for this new app as `qa-content-agent-SKILL.md`
— read it fully before writing any code, it defines the architecture, the two content
flows, the anti-hallucination rules, the "sound human" copy rules, and the image style.

**New project, new domain, new platforms:**
- Topic: QA / Test Automation / Selenium / Playwright / AI agents in QA / vibe coding /
  n8n workflows for QA — trending news, ideas, and cheatsheet-style content from this space.
- Platforms: LinkedIn and Medium, as **two completely separate buttons/flows** (not a
  shared 3-option picker like FBS had News/Preview/Review). Each button has its own
  suggestion pool, refresh, and custom-topic field.
- Brand theme: black (`#0D0D0D`) + orange (`#FF6B00`) throughout the UI and the generated
  images. Tech-editorial visual style (terminal/code fragments, line art, geometric
  shapes) — not cartoonish, this audience is software professionals.
- Stack: same as FBS — Python, Flask, OpenAI (GPT-4o for text, gpt-image-1 for images),
  Pillow for compositing. Reuse the same fallback-chain pattern FBS uses for both text and
  image generation (so the app never hard-fails).

**Project location:** create the new project at
`D:\VS code projects\Project\QA_CONTENT_AGENT\QCA\` (adjust if you've already set up a
different folder — tell me before you start if so).

**What I need from you, in order:**

1. Read `qa-content-agent-SKILL.md` in full and confirm you understand the two-flow
   architecture (LinkedIn Post button + Medium Article button, each independent, each with
   its own scraper sampling / refresh / custom-topic field) before writing code.
2. Scaffold the folder structure exactly as laid out in the blueprint's "Core architecture"
   section.
3. Build `scrapers/qa_scraper.py` first, pulling from the sources listed in the blueprint
   (Ministry of Testing, Selenium blog, Applitools/TestGuild, Playwright blog + GitHub
   releases, n8n blog/community, dev.to API by tag, Hacker News Algolia API, relevant
   subreddit RSS, GitHub Trending). Each source function should fail-soft to `[]` on error —
   show me the working scraper output (printed sample items) before moving on.
4. Build `agents/__init__.py` with the shared `QA_GUIDELINES` constant. This needs to
   encode BOTH the brand/image rules AND the "sounds human, not AI" copywriting rules from
   the blueprint — give me a couple of example sentences of what to avoid (AI-cliché
   openers, em-dash overuse, emoji stacking, templated CTAs) and what to aim for
   (practitioner voice, contractions, one concrete specific detail, varied sentence length).
5. Build `agents/linkedin_agent.py` and `agents/medium_agent.py` per the blueprint's prompt
   shape — `build_prompt(item=None)` in each, falling back to a "most relevant recent item"
   when called with no item (the custom-topic path), and injecting a LIVE DATA SNAPSHOT
   block for grounding when there's no single picked item.
6. Build `image_gen/image_generator.py` and `image_gen/image_composer.py` with
   `compose_linkedin_post` (1080×1350) and `compose_medium_post` (1200×630), both using
   fit-with-padding (never crop), brand lockup drawn with PIL, and the gpt-image-1 ->
   Gemini image -> PIL-placeholder fallback chain.
7. Wire `app.py` with the two independent route pairs described in the blueprint's build
   checklist, plus the "copy image prompt for external generation" fallback in the API
   response when image generation totally fails (this needs to surface all the way to the
   UI, not just get logged).
8. Build the frontend (`templates/index.html`, `static/js/main.js`, `static/css/style.css`)
   in the black/orange theme: two clearly separated sections (LinkedIn Post / Medium
   Article), each with: button -> skeleton cards while loading -> 3 real option cards with
   refresh icon -> custom-topic text field -> generated preview panel (image, caption or
   article text, hashtags/tags, download button, and a "copy prompt" button that only
   appears if AI image generation failed).
9. After scaffolding, walk me through the `.env` setup — I only need to provide a real
   `OPENAI_API_KEY`; `FLASK_SECRET_KEY` can be any string I invent myself. Tell me if any
   other env vars are needed for the fallback models (Groq/Gemini) and let me decide
   whether to wire those up now or skip them and rely on the OpenAI tier only for v1.
10. Once it runs locally, walk me through testing both flows: force-refresh each section
    twice and confirm the 3 suggested items actually change, then generate one real post on
    each platform and check (a) the image text matches real scraped data, not invented
    facts, and (b) the caption/article reads like a person wrote it.

Ask me clarifying questions before step 2 if anything in the blueprint is ambiguous for
your implementation — don't guess on the architecture, the domain knobs are all decided
already, but implementation details (e.g. exact RSS parsing library, exact card data shape)
are yours to choose unless I've specified them above.

# FootBro Show — Social Media Content Agent

One-click Instagram & YouTube content generator for **@thefootbroshow**.

Generate branded, ready-to-post Instagram content — images, captions, and hashtags — for football news, match previews, match reviews, and custom topics, all from a single dashboard.

---

## Features

- ⚽ **Football News** — scrapes trending football news and generates a branded post (image + caption + hashtags)
- 👁 **Match Preview** — generates pre-match hype content for today's big fixtures
- 📊 **Match Review** — generates post-match reaction content for recently completed games
- ✏️ **Custom Content** — type any football topic and generate a branded post on demand
- 🖼 **Auto Image Generation** — AI-generated artwork composited with FootBro Show branding, stats overlay, and logo watermark
- ⬇ **One-Click Download** — download the generated image (.png) and caption + hashtags (.txt) directly from the dashboard

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11+, Flask |
| Content Generation | Groq (Llama 3.3 70B) → OpenAI (GPT-4o) → Gemini, automatic fallback chain |
| Image Generation | OpenAI `gpt-image-1` → Gemini (`gemini-2.5-flash-image`) fallback |
| Image Compositing | Pillow (PIL) |
| News & Match Data | `feedparser` (RSS: Goal, ESPN, BBC, Sky Sports, The Guardian) + ESPN public scoreboard API |
| Frontend | HTML5, CSS3 (dark green football theme), Vanilla JS |
| Env Management | `python-dotenv` |
| Export | PIL save to PNG + text file |

### AI provider fallback chain

- **Text/content generation**: tries **Groq** (`llama-3.3-70b-versatile`, free/fast) first to preserve OpenAI credits, then falls back to **OpenAI** (`gpt-4o`), then to **Gemini** (`gemini-2.0-flash`) if OpenAI's rate limit/quota is hit. A `QuotaExceededError` is raised only if every configured provider is exhausted.
- **Image generation**: tries **OpenAI** (`gpt-image-1`) first, then falls back to **Gemini** (`gemini-2.5-flash-image`) on rate limit/quota errors.
- Any provider errors encountered along the way are surfaced in the dashboard's error/debug log section.

---

## Project Structure

```
FBS/
│
├── app.py                        # Main Flask application
├── .env                          # API keys (gitignored — see .env.example)
├── .env.example                  # Template for required environment variables
├── .gitignore
├── requirements.txt              # Python dependencies
├── run.bat / start_footbro.bat   # Windows launch scripts
│
├── agents/
│   ├── __init__.py               # Shared SYSTEM_PROMPT + multi-provider generate_content()
│   ├── news_agent.py             # Football news -> post content generator
│   ├── match_preview_agent.py    # Match preview generator
│   ├── match_review_agent.py     # Match review generator
│   └── custom_agent.py           # Custom prompt content generator
│
├── image_gen/
│   ├── __init__.py
│   ├── image_generator.py        # OpenAI/Gemini image generation
│   └── image_composer.py         # PIL-based image compositing (headline band, bullets, logo)
│
├── scrapers/
│   ├── __init__.py
│   └── football_scraper.py       # RSS news + ESPN scoreboard fixtures/results scraper
│
├── assets/
│   ├── logo.png                  # FootBro Show logo
│   ├── logo_small.png            # Small watermark version
│   ├── sample1.png, sample2.png, sample3.png  # Reference layout mockups
│   └── fonts/                    # Optional custom fonts (falls back to system fonts if empty)
│
├── templates/
│   └── index.html                # Main dashboard HTML (Jinja2)
│
├── static/
│   ├── css/
│   │   └── style.css             # Dashboard styles
│   └── js/
│       └── main.js               # AJAX handlers, download triggers
│
└── output/                       # All generated content saved here (gitignored, except .gitkeep)
    ├── images/
    └── text/
```

---

## Setup Instructions

```bash
# 1. Navigate to the project
cd "D:\VS code projects\Project\SOCIAL_MEDIA_aGENT\FBS"

# 2. Create a virtual environment
python -m venv venv
venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Add your API keys to .env (see Environment Variables below)

# 5. Place your FootBro Show logo at:
#    assets/logo.png

# 6. Run the app
python app.py

# 7. Open your browser
# http://localhost:5000
```

---

## How to Use

1. **📰 Football News** — click GENERATE to scrape the latest trending football news, write a fan-voice caption, generate a matching AI image, and produce 5 SEO hashtags.
2. **👁 Match Preview** — click GENERATE to fetch today's top fixtures and produce hype pre-match content, key stats, and an AI image.
3. **📊 Match Review** — click GENERATE to fetch a recently completed match and produce reaction-style post-match content with key stats.
4. **✏️ Custom Content** — type any football-related topic into the text box and click GENERATE CONTENT to produce a fully branded post on that topic.

After generation, the **Output Preview Area** shows the 1080×1350 image, caption, and hashtags. Use the **DOWNLOAD IMAGE** and **DOWNLOAD CAPTION+TAGS** buttons to save the files locally.

### Where output files are saved

All generated content is automatically saved to:

```
output/images/footbro_{type}_{timestamp}.png
output/text/footbro_{type}_{timestamp}.txt
```

---

## Environment Variables

Create a `.env` file in the project root with the following variables:

| Variable | Description |
|---|---|
| `GROQ_API_KEY` | Your Groq API key. Used first for content generation (`llama-3.3-70b-versatile`) to save OpenAI credits. Optional — if unset, OpenAI is used directly |
| `OPENAI_API_KEY` | Your OpenAI API key, used for GPT-4o content generation (fallback) and `gpt-image-1` image generation |
| `GEMINI_API_KEY` | Your Google Gemini API key. Optional fallback used automatically for text and image generation if the OpenAI account hits its rate limit / daily quota |
| `FLASK_SECRET_KEY` | Secret key used by Flask for session security |
| `OUTPUT_DIR` | Absolute path to the folder where generated images and text files are saved |
| `LOGO_PATH` | Absolute path to the FootBro Show logo used for image watermarking |

A ready-to-fill template is provided in `.env.example` — copy it to `.env` and fill in your keys.

> ⚠️ **Never share your `.env` file publicly.** It contains your private API keys — do not commit it to version control or post it anywhere (including chats, issues, or screenshots). If a key is ever exposed, rotate it immediately from your OpenAI/Google AI dashboard.

---

## Output Format

- **Image**: 1080×1350 PNG (4:5 Instagram portrait) — top portion is AI-generated artwork with a "BREAKING" headline band, bottom portion is a dark green "KEY HIGHLIGHTS" overlay with stat bullets, FootBro Show logo badge, and `@thefootbroshow` handle
- **Text**: `.txt` file containing the generated caption followed by the top 5 hashtags
- **Save location**: all files are written to the `output/` folder (`output/images/` and `output/text/`)

### Data grounding & fallbacks

- All stat bullets are grounded in real scraped data (RSS news, or ESPN fixture/result data) — the AI is instructed to never invent player names, scores, or stats, and never output placeholder text like `[Player Name]`.
- `football_scraper.py` uses a multi-source, multi-date fallback chain (RSS feeds → recent ESPN results → upcoming ESPN fixtures) so real data is available for almost every run.
- If, in the rare case, no live data can be fetched at all, `stats_bullets` falls back to a single branded CTA — **"Follow @thefootbroshow for more football news & stats"** — instead of an error-style message.

---

## Credits

**The FootBro Show** | [@thefootbroshow](https://instagram.com/thefootbroshow)

Football conversations. Real opinions. For fans, by fans. ⚽

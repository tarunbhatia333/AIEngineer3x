"""FootBro Content Agent — main Flask application.

One-click social media content generation for @thefootbroshow:
football news, match previews, match reviews, and custom prompts —
each producing a branded 1080x1350 image, caption, and top 5 hashtags.
"""
import os
import random
import time
from pathlib import Path
from uuid import uuid4

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request, send_from_directory

from agents import QuotaExceededError, build_full_prompt, generate_content
from agents.custom_agent import build_prompt as build_custom_prompt
from agents.match_preview_agent import build_prompt as build_preview_prompt
from agents.match_review_agent import build_prompt as build_review_prompt
from agents.news_agent import build_prompt as build_news_prompt
from image_gen.image_composer import compose_full_graphic_post, compose_instagram_post
from image_gen.image_generator import generate_image
from scrapers.football_scraper import (
    _source_name,
    _time_ago,
    get_latest_news,
    get_recent_results,
    get_today_fixtures,
)

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = Path(os.environ.get("OUTPUT_DIR") or (BASE_DIR / "output"))
IMAGES_DIR = OUTPUT_DIR / "images"
TEXT_DIR = OUTPUT_DIR / "text"
LOGO_PATH = os.environ.get("LOGO_PATH") or str(BASE_DIR / "assets" / "logo.png")

IMAGES_DIR.mkdir(parents=True, exist_ok=True)
TEXT_DIR.mkdir(parents=True, exist_ok=True)

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "footbro_secret_2024")


@app.route("/")
def dashboard():
    return render_template("index.html")


OPTIONS_TTL = 3600  # seconds — auto-refresh window for each section's options
options_cache = {"news": None, "preview": None, "review": None}


def _sample(pool, count=3):
    """Pick `count` distinct items at random so repeated refreshes can surface
    different real items from the pool instead of always the same top N."""
    return random.sample(pool, min(count, len(pool)))


def _news_options():
    return [
        {
            "id": uuid4().hex,
            "headline": a["headline"],
            "source": _source_name(a["source_url"]),
            "time_ago": _time_ago(a["published_parsed"]),
            "raw_data": a,
        }
        for a in _sample(get_latest_news(limit=12))
    ]


def _preview_options():
    return [
        {
            "id": uuid4().hex,
            "home_team": f["home_team"],
            "away_team": f["away_team"],
            "competition": f["competition"],
            "kickoff": f["date"],
            "raw_data": f,
        }
        for f in _sample(get_today_fixtures())
    ]


def _review_options():
    return [
        {
            "id": uuid4().hex,
            "home_team": r["home_team"],
            "away_team": r["away_team"],
            "score": f"{r['home_score']}-{r['away_score']}",
            "competition": r["competition"],
            "raw_data": r,
        }
        for r in _sample(get_recent_results())
    ]


SECTION_FETCHERS = {"news": _news_options, "preview": _preview_options, "review": _review_options}
PROMPT_BUILDERS = {
    "news": build_news_prompt,
    "preview": build_preview_prompt,
    "review": build_review_prompt,
}


@app.route("/fetch-options/<section>", methods=["GET"])
def fetch_options(section):
    if section not in SECTION_FETCHERS:
        return jsonify({"error": "Unknown section"}), 404

    force = request.args.get("force") == "true"
    entry = options_cache.get(section)
    now = time.time()

    if force or not entry or (now - entry["last_updated"] >= OPTIONS_TTL):
        entry = {"data": SECTION_FETCHERS[section](), "last_updated": now}
        options_cache[section] = entry

    public_options = [{k: v for k, v in o.items() if k != "raw_data"} for o in entry["data"]]
    return jsonify({"options": public_options, "last_updated": entry["last_updated"]})


@app.route("/generate/<section>/<option_id>", methods=["POST"])
def generate_from_option(section, option_id):
    if section not in SECTION_FETCHERS:
        return jsonify({"error": "Unknown section"}), 404

    entry = options_cache.get(section)
    option = next((o for o in (entry or {}).get("data", []) if o["id"] == option_id), None)
    if not option:
        return jsonify({"error": "This option has expired — please refresh and pick again."}), 410

    return _generate(section, PROMPT_BUILDERS[section](option["raw_data"]))


@app.route("/generate/custom", methods=["POST"])
def generate_custom():
    data = request.get_json(silent=True) or {}
    prompt = (data.get("prompt") or "").strip()
    if not prompt:
        return jsonify({"error": "Please enter a topic to generate content about."}), 400
    return _generate("custom", build_custom_prompt(prompt))


@app.route("/output/images/<path:filename>")
def serve_image(filename):
    return send_from_directory(IMAGES_DIR, filename)


@app.route("/download/image/<path:filename>")
def download_image(filename):
    return send_from_directory(IMAGES_DIR, filename, as_attachment=True)


@app.route("/download/text/<path:filename>")
def download_text(filename):
    return send_from_directory(TEXT_DIR, filename, as_attachment=True)


def _generate(post_type, user_prompt):
    """Run a content agent, generate + compose the image, save outputs, return JSON."""
    logs = []
    try:
        content = generate_content(user_prompt, logs=logs)
    except QuotaExceededError as exc:
        return jsonify({
            "error": str(exc),
            "quota_exceeded": True,
            "manual_prompt": build_full_prompt(user_prompt),
            "logs": logs,
        }), 429
    except Exception as exc:
        logs.append(f"Content generation failed: {exc}")
        return jsonify({"error": f"Content generation failed: {exc}", "logs": logs}), 500

    caption = content.get("caption", "")
    hashtags = content.get("hashtags", [])
    bullets = content.get("stats_bullets", [])
    fun_facts = content.get("fun_facts", [])
    image_prompt = content.get("image_prompt", "")
    headline = content.get("headline", "")

    ai_image_source = None
    note = None
    manual_image_prompt = None
    if image_prompt:
        try:
            ai_image_source = generate_image(image_prompt, logs=logs)
        except QuotaExceededError:
            note = "AI image quota reached for today — used a placeholder image instead. Copy the image prompt below to generate it manually."
            manual_image_prompt = image_prompt
        except Exception as exc:
            logs.append(f"Image generation failed: {exc}")
            ai_image_source = None

    if ai_image_source:
        composed = compose_full_graphic_post(ai_image_source, LOGO_PATH)
    else:
        composed = compose_instagram_post(
            None, bullets, LOGO_PATH, headline=headline, fun_facts=fun_facts
        )

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    image_filename = f"footbro_{post_type}_{timestamp}.png"
    text_filename = f"footbro_{post_type}_{timestamp}.txt"

    composed.save(IMAGES_DIR / image_filename, "PNG")
    (TEXT_DIR / text_filename).write_text(
        caption.strip() + "\n\n" + " ".join(hashtags), encoding="utf-8"
    )

    return jsonify({
        "image_url": f"/output/images/{image_filename}",
        "image_filename": image_filename,
        "text_filename": text_filename,
        "headline": headline,
        "caption": caption,
        "hashtags": hashtags,
        "stats_bullets": bullets,
        "fun_facts": fun_facts,
        "image_generated": ai_image_source is not None,
        "note": note,
        "manual_image_prompt": manual_image_prompt,
        "logs": logs,
    })


if __name__ == "__main__":
    app.run(debug=True, port=5000)

"""QA Content Agent — main Flask application.

One-click branded content generation for QA/test-automation/AI-in-QA/vibe
coding/n8n topics: two fully independent flows, LinkedIn Post and Medium
Article, each with its own suggestion pool, refresh, and custom-topic field.
"""
import base64
import os
import random
import time
from io import BytesIO
from uuid import uuid4

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request

from agents import QuotaExceededError, build_full_prompt, generate_content
from agents.linkedin_agent import build_prompt as build_linkedin_prompt
from agents.medium_agent import build_prompt as build_medium_prompt
from image_gen.image_composer import compose_linkedin_post, compose_medium_post
from image_gen.image_generator import generate_image
from scrapers.qa_scraper import _source_name, _time_ago, get_item_pool

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "qa_content_agent_secret")


@app.route("/")
def dashboard():
    return render_template("index.html")


OPTIONS_TTL = 3600  # seconds — auto-refresh window for each section's options
options_cache = {"linkedin": None, "medium": None}


def _sample(pool, count=3):
    """Pick `count` distinct items at random so repeated refreshes can surface
    different real items from the pool instead of always the same top N."""
    return random.sample(pool, min(count, len(pool)))


def _build_options():
    return [
        {
            "id": uuid4().hex,
            "headline": item["headline"],
            "source": _source_name(item["source_url"]),
            "time_ago": _time_ago(item["published_parsed"]),
            "raw_data": item,
        }
        for item in _sample(get_item_pool(limit=40))
    ]


SECTION_FETCHERS = {"linkedin": _build_options, "medium": _build_options}
PROMPT_BUILDERS = {"linkedin": build_linkedin_prompt, "medium": build_medium_prompt}


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


@app.route("/generate/<section>/custom", methods=["POST"])
def generate_custom(section):
    if section not in SECTION_FETCHERS:
        return jsonify({"error": "Unknown section"}), 404

    data = request.get_json(silent=True) or {}
    topic = (data.get("topic") or "").strip()
    if not topic:
        return jsonify({"error": "Please enter a topic to generate content about."}), 400

    reference_image = _decode_data_url(data.get("reference_image"))

    return _generate(section, PROMPT_BUILDERS[section](custom_topic=topic), reference_image=reference_image)


def _decode_data_url(data_url):
    """Decode a `data:image/...;base64,...` URL (from a file upload) into raw bytes."""
    if not data_url or "," not in data_url:
        return None
    try:
        return base64.b64decode(data_url.split(",", 1)[1])
    except Exception:
        return None


def _generate(section, user_prompt, reference_image=None):
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

    image_prompt = content.get("image_prompt", "")
    image_size = "1024x1536" if section == "linkedin" else "1536x1024"

    ai_image_source = None
    note = None
    manual_image_prompt = None
    if image_prompt:
        try:
            ai_image_source = generate_image(
                image_prompt, reference_image=reference_image, size=image_size, logs=logs
            )
        except QuotaExceededError:
            note = "AI image quota reached for today — used a placeholder image instead. Copy the image prompt below to generate it manually."
            manual_image_prompt = image_prompt
        except Exception as exc:
            logs.append(f"Image generation failed: {exc}")
            ai_image_source = None
            note = "AI image generation failed — used a placeholder image instead. Copy the image prompt below to generate it manually."
            manual_image_prompt = image_prompt

    timestamp = time.strftime("%Y%m%d_%H%M%S")

    if section == "linkedin":
        headline = content.get("headline", "")
        caption = content.get("caption", "")
        hashtags = content.get("hashtags", [])
        composed = compose_linkedin_post(ai_image_source, headline=headline)
        text_body = caption.strip() + "\n\n" + " ".join(hashtags)
        response_payload = {
            "headline": headline,
            "caption": caption,
            "hashtags": hashtags,
        }
    else:
        title = content.get("title", "")
        intro = content.get("intro", "")
        body_markdown = content.get("body_markdown", "")
        tags = content.get("tags", [])
        composed = compose_medium_post(ai_image_source, title=title)
        text_body = f"# {title}\n\n{intro}\n\n{body_markdown}\n\nTags: " + ", ".join(tags)
        response_payload = {
            "title": title,
            "intro": intro,
            "body_markdown": body_markdown,
            "tags": tags,
        }

    buffer = BytesIO()
    composed.save(buffer, "PNG")
    image_data_url = "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode("ascii")

    return jsonify({
        **response_payload,
        "image_url": image_data_url,
        "image_filename": f"qca_{section}_{timestamp}.png",
        "text_filename": f"qca_{section}_{timestamp}.txt",
        "text_body": text_body,
        "image_generated": ai_image_source is not None,
        "note": note,
        "manual_image_prompt": manual_image_prompt,
        "logs": logs,
    })


if __name__ == "__main__":
    app.run(debug=True, port=5050)

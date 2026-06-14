"""FootBro Content Agent — main Flask application.

One-click social media content generation for @thefootbroshow:
football news, match previews, match reviews, and custom prompts —
each producing a branded 1080x1350 image, caption, and top 5 hashtags.
"""
import os
import time
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request, send_from_directory

from agents import QuotaExceededError, build_full_prompt, generate_content
from agents.custom_agent import build_prompt as build_custom_prompt
from agents.match_preview_agent import build_prompt as build_preview_prompt
from agents.match_review_agent import build_prompt as build_review_prompt
from agents.news_agent import build_prompt as build_news_prompt
from image_gen.image_composer import compose_instagram_post
from image_gen.image_generator import generate_image

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


@app.route("/generate/news", methods=["POST"])
def generate_news():
    return _generate("news", build_news_prompt())


@app.route("/generate/preview", methods=["POST"])
def generate_preview():
    return _generate("preview", build_preview_prompt())


@app.route("/generate/review", methods=["POST"])
def generate_review():
    return _generate("review", build_review_prompt())


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

    composed = compose_instagram_post(ai_image_source, bullets, logo_path=LOGO_PATH, headline=headline)

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
        "caption": caption,
        "hashtags": hashtags,
        "stats_bullets": bullets,
        "image_generated": ai_image_source is not None,
        "note": note,
        "manual_image_prompt": manual_image_prompt,
        "logs": logs,
    })


if __name__ == "__main__":
    app.run(debug=True, port=5000)

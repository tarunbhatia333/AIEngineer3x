"""PIL-based compositing for QA Content Agent posts — black/orange theme.

Two pairs of compositors, one per platform:
  - compose_linkedin_post: 1080x1350 (4:5). If an AI image came back, just
    fit it to canvas and overlay the brand lockup. If image generation
    failed entirely, draw a PIL placeholder graphic instead so the post is
    still deliverable.
  - compose_medium_post: 1200x630 article cover, same two paths.

Always fit-with-padding, never crop — cropping would cut off baked-in
headline/bullet text near the source image's edges.
"""
import os
import re
from io import BytesIO

import requests
from PIL import Image, ImageDraw, ImageFont

LINKEDIN_W, LINKEDIN_H = 1080, 1350
MEDIUM_W, MEDIUM_H = 1200, 630

BLACK = (13, 13, 13)
ORANGE = (255, 107, 0)
WHITE = (245, 245, 245)
GRAY = (60, 60, 60)

BRAND_NAME = "QA CONTENT AGENT"

FONT_CANDIDATES = [
    "C:/Windows/Fonts/segoeuib.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
]
BODY_FONT_CANDIDATES = [
    "C:/Windows/Fonts/segoeui.ttf",
    "C:/Windows/Fonts/arial.ttf",
]

_EMOJI_RE = re.compile(
    "[\U0001F000-\U0001FFFF\U00002600-\U000027BF\U0001F1E6-\U0001F1FF]+",
    flags=re.UNICODE,
)


def _strip_emoji(text):
    return re.sub(r"\s{2,}", " ", _EMOJI_RE.sub("", text or "")).strip()


def _load_font(candidates, size):
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue
    return ImageFont.load_default()


def _wrap_text(draw, text, font, max_width):
    words = text.split()
    lines, cur = [], ""
    for word in words:
        trial = f"{cur} {word}".strip()
        if draw.textlength(trial, font=font) <= max_width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def _load_ai_image(source):
    if not source:
        return None
    try:
        if isinstance(source, bytes):
            return Image.open(BytesIO(source)).convert("RGB")
        if source.startswith("http://") or source.startswith("https://"):
            resp = requests.get(source, timeout=30)
            resp.raise_for_status()
            return Image.open(BytesIO(resp.content)).convert("RGB")
        return Image.open(source).convert("RGB")
    except Exception:
        return None


def _fit_with_padding(img, target_w, target_h, bg_color):
    """Resize `img` to fit fully inside target_w x target_h without
    cropping, centered on a `bg_color` canvas — never cuts off baked-in
    headline/bullet text near the source image's edges."""
    src_ratio = img.width / img.height
    target_ratio = target_w / target_h
    if src_ratio > target_ratio:
        new_w = target_w
        new_h = round(new_w / src_ratio)
    else:
        new_h = target_h
        new_w = round(new_h * src_ratio)
    resized = img.resize((new_w, new_h), Image.LANCZOS)

    canvas = Image.new("RGB", (target_w, target_h), color=bg_color)
    canvas.paste(resized, ((target_w - new_w) // 2, (target_h - new_h) // 2))
    return canvas


def _draw_brand_lockup(draw, canvas_w, y_center):
    """Draw a simple text-based brand lockup: an orange tick + wordmark."""
    font = _load_font(FONT_CANDIDATES, 26)
    text_w = draw.textlength(BRAND_NAME, font=font)
    bar_w = 22
    gap = 14
    total_w = bar_w + gap + text_w
    start_x = (canvas_w - total_w) / 2

    draw.rectangle(
        [(start_x, y_center - 14), (start_x + bar_w, y_center + 14)],
        fill=ORANGE,
    )
    draw.text((start_x + bar_w + gap, y_center - 13), BRAND_NAME, font=font, fill=WHITE)


# ---------------------------------------------------------------------------
# LinkedIn (1080x1350)
# ---------------------------------------------------------------------------

def compose_linkedin_post(ai_image_source, headline=None, bullets=None):
    """Compose the final 1080x1350 LinkedIn post and return a PIL Image."""
    canvas = Image.new("RGB", (LINKEDIN_W, LINKEDIN_H), color=BLACK)

    ai_img = _load_ai_image(ai_image_source)
    if ai_img:
        canvas = _fit_with_padding(ai_img, LINKEDIN_W, LINKEDIN_H, BLACK)
    else:
        canvas = _placeholder_linkedin(headline, bullets)

    draw = ImageDraw.Draw(canvas)
    draw.rectangle([(0, LINKEDIN_H - 90), (LINKEDIN_W, LINKEDIN_H)], fill=BLACK)
    draw.rectangle([(0, LINKEDIN_H - 92), (LINKEDIN_W, LINKEDIN_H - 88)], fill=ORANGE)
    _draw_brand_lockup(draw, LINKEDIN_W, LINKEDIN_H - 45)
    return canvas


def _placeholder_linkedin(headline, bullets):
    """PIL-only fallback graphic when every image-generation tier fails."""
    canvas = Image.new("RGB", (LINKEDIN_W, LINKEDIN_H), color=BLACK)
    draw = ImageDraw.Draw(canvas)

    draw.rectangle([(0, 0), (LINKEDIN_W, 8)], fill=ORANGE)

    font_hl = _load_font(FONT_CANDIDATES, 56)
    hl = _strip_emoji(headline or "QA / TEST AUTOMATION")
    y = 160
    for line in _wrap_text(draw, hl, font_hl, LINKEDIN_W - 140)[:4]:
        draw.text((70, y), line, font=font_hl, fill=WHITE)
        y += 66

    y += 40
    draw.rectangle([(70, y), (LINKEDIN_W - 70, y + 3)], fill=ORANGE)
    y += 40

    font_bullet = _load_font(BODY_FONT_CANDIDATES, 30)
    for item in (bullets or [])[:4]:
        text = item.lstrip("-•").strip()
        if not text:
            continue
        lines = _wrap_text(draw, text, font_bullet, LINKEDIN_W - 180)[:2]
        draw.ellipse([(70, y + 10), (84, y + 24)], fill=ORANGE)
        for line in lines:
            draw.text((104, y), line, font=font_bullet, fill=WHITE)
            y += 38
        y += 16

    return canvas


# ---------------------------------------------------------------------------
# Medium (1200x630)
# ---------------------------------------------------------------------------

def compose_medium_post(ai_image_source, title=None):
    """Compose the final 1200x630 Medium article cover and return a PIL Image."""
    canvas = Image.new("RGB", (MEDIUM_W, MEDIUM_H), color=BLACK)

    ai_img = _load_ai_image(ai_image_source)
    if ai_img:
        canvas = _fit_with_padding(ai_img, MEDIUM_W, MEDIUM_H, BLACK)
    else:
        canvas = _placeholder_medium(title)

    draw = ImageDraw.Draw(canvas)
    draw.rectangle([(0, MEDIUM_H - 64), (MEDIUM_W, MEDIUM_H)], fill=BLACK)
    draw.rectangle([(0, MEDIUM_H - 66), (MEDIUM_W, MEDIUM_H - 62)], fill=ORANGE)
    _draw_brand_lockup(draw, MEDIUM_W, MEDIUM_H - 32)
    return canvas


def _placeholder_medium(title):
    """PIL-only fallback cover when every image-generation tier fails."""
    canvas = Image.new("RGB", (MEDIUM_W, MEDIUM_H), color=BLACK)
    draw = ImageDraw.Draw(canvas)

    draw.rectangle([(0, 0), (MEDIUM_W, 8)], fill=ORANGE)

    font_title = _load_font(FONT_CANDIDATES, 48)
    text = _strip_emoji(title or "QA / TEST AUTOMATION")
    lines = _wrap_text(draw, text, font_title, MEDIUM_W - 160)[:3]
    total_h = len(lines) * 58
    y = (MEDIUM_H - total_h) / 2 - 30
    for line in lines:
        draw.text((80, y), line, font=font_title, fill=WHITE)
        y += 58

    return canvas

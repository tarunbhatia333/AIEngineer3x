"""PIL-based compositing of the final 1080x1350 Instagram post (4:5 portrait).

Layout:
  - Photo section (1080x670): AI-generated image (or placeholder if unavailable)
  - Headline band (1080x140): "BREAKING" badge + bold news-style headline
  - Gold accent separator line
  - Bottom section (1080x540): dark green overlay with "KEY HIGHLIGHTS" stats
  - Bottom lockup bar: @thefootbroshow handle + circular FootBro Show logo badge
"""
import os
import re
from io import BytesIO

import requests
from PIL import Image, ImageChops, ImageDraw, ImageFont

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS_DIR = os.path.join(BASE_DIR, "assets", "fonts")

CANVAS_WIDTH = 1080
CANVAS_HEIGHT = 1350
PHOTO_HEIGHT = 600
HEADLINE_HEIGHT = 140
TOP_HEIGHT = PHOTO_HEIGHT + HEADLINE_HEIGHT
BOTTOM_HEIGHT = CANVAS_HEIGHT - TOP_HEIGHT

DARK_GREEN = (10, 31, 10)
GOLD = (255, 215, 0)
WHITE = (255, 255, 255)
RED = (214, 40, 40)

LOGO_BG = (33, 36, 41)

# Fallback chain for the bold display font (header), then for body/bullet text.
HEADER_FONT_CANDIDATES = [
    os.path.join(FONTS_DIR, "BebasNeue.ttf"),
    "C:/Windows/Fonts/impact.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
]
BODY_FONT_CANDIDATES = [
    os.path.join(FONTS_DIR, "Inter-Bold.ttf"),
    os.path.join(FONTS_DIR, "Inter.ttf"),
    "C:/Windows/Fonts/arialbd.ttf",
    "C:/Windows/Fonts/arial.ttf",
]

# Emoji / pictographic ranges that the header & body fonts above can't render
# (they show up as "tofu" □ glyphs) — stripped from any text drawn on the image.
_EMOJI_PATTERN = re.compile(
    "["
    "\U0001F000-\U0001FFFF"
    "\U00002600-\U000027BF"
    "\U00002190-\U000021FF"
    "\U00002300-\U000023FF"
    "\U00002B00-\U00002BFF"
    "\U0000FE00-\U0000FE0F"
    "\U0000200D"
    "]+",
    flags=re.UNICODE,
)


def _strip_emoji(text):
    """Remove emoji/pictographic characters the post fonts can't render."""
    cleaned = _EMOJI_PATTERN.sub("", text or "")
    return re.sub(r"\s{2,}", " ", cleaned).strip()


def _load_font(candidates, size):
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue
    return ImageFont.load_default()


def _load_ai_image(source):
    """Load the AI-generated image from raw bytes, a URL, or a local file path."""
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


def _crop_to_fit(img, target_w, target_h):
    """Center-crop and resize an image to exactly target_w x target_h."""
    src_ratio = img.width / img.height
    target_ratio = target_w / target_h

    if src_ratio > target_ratio:
        new_height = img.height
        new_width = int(new_height * target_ratio)
        left = (img.width - new_width) // 2
        img = img.crop((left, 0, left + new_width, new_height))
    else:
        new_width = img.width
        new_height = int(new_width / target_ratio)
        top = (img.height - new_height) // 2
        img = img.crop((0, top, new_width, top + new_height))

    return img.resize((target_w, target_h), Image.LANCZOS)


def _wrap_text(draw, text, font, max_width):
    words = text.split()
    lines = []
    current = ""
    for word in words:
        trial = f"{current} {word}".strip()
        if draw.textlength(trial, font=font) <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def _load_logo_badge(logo_path, size):
    """Crop the FootBro Show logo to a clean circular badge of `size`x`size`.

    logo.png is a fully opaque rectangle with a dark background around a
    circular badge — center-crop to a square, color-key out the dark
    background, then intersect with a circular mask for crisp edges.
    """
    logo = Image.open(logo_path).convert("RGBA")
    side = min(logo.width, logo.height)
    left = (logo.width - side) // 2
    top = (logo.height - side) // 2
    badge = logo.crop((left, top, left + side, top + side)).resize((size, size), Image.LANCZOS)

    tolerance = 35
    pixels = badge.getdata()
    keyed = []
    for r, g, b, a in pixels:
        if (
            abs(r - LOGO_BG[0]) <= tolerance
            and abs(g - LOGO_BG[1]) <= tolerance
            and abs(b - LOGO_BG[2]) <= tolerance
        ):
            keyed.append((r, g, b, 0))
        else:
            keyed.append((r, g, b, a))
    badge.putdata(keyed)

    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, size, size), fill=255)
    badge.putalpha(ImageChops.multiply(badge.getchannel("A"), mask))

    return badge


def compose_instagram_post(ai_image_source, bullets, logo_path=None, handle="@thefootbroshow", headline=None):
    """Compose the final 1080x1350 branded Instagram post and return a PIL Image."""
    canvas = Image.new("RGB", (CANVAS_WIDTH, CANVAS_HEIGHT), color=DARK_GREEN)
    draw = ImageDraw.Draw(canvas)

    # --- Photo section: AI-generated image (or placeholder) ---
    ai_img = _load_ai_image(ai_image_source)
    if ai_img:
        ai_img = _crop_to_fit(ai_img, CANVAS_WIDTH, PHOTO_HEIGHT)
        canvas.paste(ai_img, (0, 0))
    else:
        draw.rectangle([(0, 0), (CANVAS_WIDTH, PHOTO_HEIGHT)], fill=(20, 50, 20))
        placeholder_font = _load_font(HEADER_FONT_CANDIDATES, 36)
        msg = "FOOTBRO SHOW"
        w = draw.textlength(msg, font=placeholder_font)
        draw.text(((CANVAS_WIDTH - w) / 2, PHOTO_HEIGHT / 2 - 20), msg, font=placeholder_font, fill=GOLD)

    # --- Headline band: "BREAKING" badge + bold news-style headline ---
    draw.rectangle([(0, PHOTO_HEIGHT), (CANVAS_WIDTH, TOP_HEIGHT)], fill=DARK_GREEN)

    headline = _strip_emoji(headline)
    if headline:
        badge_box = (60, PHOTO_HEIGHT + 14, 60 + 130, PHOTO_HEIGHT + 46)
        draw.rounded_rectangle(badge_box, radius=6, fill=RED)
        font_badge = _load_font(BODY_FONT_CANDIDATES, 18)
        badge_text = "BREAKING"
        bw = draw.textlength(badge_text, font=font_badge)
        draw.text(
            (badge_box[0] + (130 - bw) / 2, badge_box[1] + 7),
            badge_text,
            font=font_badge,
            fill=WHITE,
        )

        font_headline = _load_font(HEADER_FONT_CANDIDATES, 36)
        max_text_width = CANVAS_WIDTH - 120
        y = PHOTO_HEIGHT + 54
        for line in _wrap_text(draw, headline, font_headline, max_text_width)[:2]:
            draw.text((60, y), line, font=font_headline, fill=WHITE)
            y += 40

    # --- Gold accent separator line ---
    draw.rectangle([(0, TOP_HEIGHT - 4), (CANVAS_WIDTH, TOP_HEIGHT + 4)], fill=GOLD)

    # --- Bottom section: dark overlay (already the canvas background) ---
    draw.rectangle([(0, TOP_HEIGHT), (CANVAS_WIDTH, CANVAS_HEIGHT)], fill=DARK_GREEN)
    draw.rectangle([(0, TOP_HEIGHT - 4), (CANVAS_WIDTH, TOP_HEIGHT + 4)], fill=GOLD)

    # --- Header ---
    font_header = _load_font(HEADER_FONT_CANDIDATES, 46)
    draw.text((60, TOP_HEIGHT + 30), "KEY HIGHLIGHTS", font=font_header, fill=GOLD)

    # --- Bullet stats ---
    font_bullet = _load_font(BODY_FONT_CANDIDATES, 26)
    max_text_width = CANVAS_WIDTH - 120
    line_height = 32
    bullet_gap = 10
    max_y = CANVAS_HEIGHT - 130
    y = TOP_HEIGHT + 95
    for bullet in bullets[:5]:
        text = _strip_emoji(bullet)
        if not text:
            continue
        if not text.startswith("•"):
            text = f"• {text}"
        lines = _wrap_text(draw, text, font_bullet, max_text_width)[:2]
        if y + line_height * len(lines) > max_y:
            break
        for line in lines:
            draw.text((60, y), line, font=font_bullet, fill=WHITE)
            y += line_height
        y += bullet_gap

    # --- Bottom lockup: @handle + circular logo badge, centered as a group ---
    font_handle = _load_font(BODY_FONT_CANDIDATES, 30)
    badge_size = 90
    ring_pad = 5
    gap = 24

    text_w = draw.textlength(handle, font=font_handle)
    text_bbox = font_handle.getbbox(handle)
    text_h = text_bbox[3] - text_bbox[1]

    badge_dia = badge_size + ring_pad * 2
    group_w = text_w + gap + badge_dia
    start_x = (CANVAS_WIDTH - group_w) / 2
    center_y = CANVAS_HEIGHT - 65

    draw.text((start_x, center_y - text_h / 2 - text_bbox[1]), handle, font=font_handle, fill=GOLD)

    badge_x = start_x + text_w + gap
    if logo_path and os.path.exists(logo_path):
        try:
            badge = _load_logo_badge(logo_path, badge_size)
            ring_box = (
                badge_x,
                center_y - badge_dia / 2,
                badge_x + badge_dia,
                center_y + badge_dia / 2,
            )
            draw.ellipse(ring_box, outline=GOLD, width=4)
            canvas.paste(badge, (int(badge_x + ring_pad), int(center_y - badge_size / 2)), badge)
        except Exception:
            pass

    return canvas

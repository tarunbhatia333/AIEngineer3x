"""PIL-based compositing of the final 1080x1350 Instagram post (4:5 portrait).

Two compositors:
  - compose_full_graphic_post: the AI image already bakes in all headline/
    bullet/table text (see agents.FULL_GRAPHIC_GUIDELINES) — just crop/resize
    it to the canvas and overlay the real logo + handle lockup.
  - compose_instagram_post: fallback used when no AI image was generated —
    draws a placeholder/photo, headline band, "KEY HIGHLIGHTS" and "DID YOU
    KNOW?" bullet sections, and the handle + logo lockup with PIL.
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
BOTTOM_HEIGHT = CANVAS_HEIGHT - TOP_HEIGHT   # 610 px
LOGO_ZONE_TOP = CANVAS_HEIGHT - 130         # reserve bottom 130 px for handle/logo

DARK_GREEN = (10, 31, 10)
GOLD = (255, 215, 0)
WHITE = (255, 255, 255)
RED = (214, 40, 40)

LOGO_BG = (33, 36, 41)

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
EMOJI_FONT_CANDIDATES = [
    "C:/Windows/Fonts/seguiemj.ttf",
    "C:/Windows/Fonts/seguisym.ttf",
]

# Characters the header/body fonts cannot render — handled by the emoji font.
_EMOJI_RE = re.compile(
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
    cleaned = _EMOJI_RE.sub("", text or "")
    return re.sub(r"\s{2,}", " ", cleaned).strip()


def _load_font(candidates, size):
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue
    return ImageFont.load_default()


def _load_emoji_font(size):
    """Load an emoji-capable font; returns None if none found."""
    for path in EMOJI_FONT_CANDIDATES:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue
    return None


# ---------------------------------------------------------------------------
# Mixed emoji+text helpers
# ---------------------------------------------------------------------------

def _mixed_length(draw, text, reg_font, em_font):
    """Measure pixel width of text that may contain emoji."""
    parts = _EMOJI_RE.split(text)
    emojis = _EMOJI_RE.findall(text)
    total = 0.0
    for i, seg in enumerate(parts):
        if seg:
            total += draw.textlength(seg, font=reg_font)
        if i < len(emojis):
            try:
                total += draw.textlength(emojis[i], font=em_font or reg_font)
            except Exception:
                total += 22 * len(emojis[i])
    return total


def _wrap_mixed(draw, text, reg_font, em_font, max_width):
    """Word-wrap text that may contain emoji."""
    words = text.split()
    lines, cur = [], ""
    for word in words:
        trial = f"{cur} {word}".strip()
        if _mixed_length(draw, trial, reg_font, em_font) <= max_width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def _draw_mixed_line(draw, text, xy, reg_font, em_font, fill):
    """Render one line of mixed emoji+regular text."""
    x, y = xy
    parts = _EMOJI_RE.split(text)
    emojis = _EMOJI_RE.findall(text)
    for i, seg in enumerate(parts):
        if seg:
            draw.text((x, y), seg, font=reg_font, fill=fill)
            x += draw.textlength(seg, font=reg_font)
        if i < len(emojis):
            font = em_font or reg_font
            em = emojis[i]
            try:
                draw.text((x, y), em, font=font, fill=fill)
                x += draw.textlength(em, font=font)
            except Exception:
                pass


# ---------------------------------------------------------------------------
# Bullet-block renderer
# ---------------------------------------------------------------------------

def _draw_bullets(
    draw, items, start_y, reg_font, em_font,
    icon_color, icon_shape,
    max_y, left_margin=60, indent=94,
    line_h=28, gap=9,
):
    """Draw a list of bullets with a colored icon prefix. Returns final y."""
    max_text_w = CANVAS_WIDTH - indent - 60
    y = start_y
    for item in (items or []):
        text = item.lstrip("•").strip()
        if not text:
            continue
        lines = _wrap_mixed(draw, text, reg_font, em_font, max_text_w)[:2]
        block_h = line_h * len(lines)
        if y + block_h > max_y:
            break

        # Icon: diamond (gold) or circle (red)
        icon_cx = left_margin + 10
        icon_cy = y + line_h // 2
        r = 8
        if icon_shape == "circle":
            draw.ellipse(
                [(icon_cx - r, icon_cy - r), (icon_cx + r, icon_cy + r)],
                fill=icon_color,
            )
        else:  # diamond
            draw.polygon(
                [
                    (icon_cx, icon_cy - r),
                    (icon_cx + r, icon_cy),
                    (icon_cx, icon_cy + r),
                    (icon_cx - r, icon_cy),
                ],
                fill=icon_color,
            )

        for j, line in enumerate(lines):
            _draw_mixed_line(draw, line, (indent, y + j * line_h), reg_font, em_font, WHITE)

        y += block_h + gap
    return y


# ---------------------------------------------------------------------------
# Image loading helpers
# ---------------------------------------------------------------------------

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


def _crop_to_fit(img, target_w, target_h):
    src_ratio = img.width / img.height
    target_ratio = target_w / target_h
    if src_ratio > target_ratio:
        new_h = img.height
        new_w = int(new_h * target_ratio)
        left = (img.width - new_w) // 2
        img = img.crop((left, 0, left + new_w, new_h))
    else:
        new_w = img.width
        new_h = int(new_w / target_ratio)
        top = (img.height - new_h) // 2
        img = img.crop((0, top, new_w, top + new_h))
    return img.resize((target_w, target_h), Image.LANCZOS)


def _fit_with_padding(img, target_w, target_h, bg_color):
    """Resize `img` to fit fully inside target_w x target_h without cropping,
    centered on a `bg_color` canvas — unlike `_crop_to_fit`, this never cuts
    off baked-in headline/leaderboard text near the source image's edges."""
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


def _load_logo_badge(logo_path, size):
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


# ---------------------------------------------------------------------------
# Bottom handle + logo lockup
# ---------------------------------------------------------------------------

def _draw_handle_lockup(canvas, draw, logo_path, handle):
    """Draw the centered @handle + circular logo badge near the bottom of canvas."""
    font_handle = _load_font(BODY_FONT_CANDIDATES, 30)
    badge_size = 90
    ring_pad = 5
    gap_px = 24

    text_w = draw.textlength(handle, font=font_handle)
    text_bbox = font_handle.getbbox(handle)
    text_h = text_bbox[3] - text_bbox[1]

    badge_dia = badge_size + ring_pad * 2
    group_w = text_w + gap_px + badge_dia
    start_x = (CANVAS_WIDTH - group_w) / 2
    center_y = CANVAS_HEIGHT - 65

    draw.text(
        (start_x, center_y - text_h / 2 - text_bbox[1]),
        handle, font=font_handle, fill=GOLD,
    )

    badge_x = start_x + text_w + gap_px
    if logo_path and os.path.exists(logo_path):
        try:
            badge = _load_logo_badge(logo_path, badge_size)
            ring_box = (
                badge_x, center_y - badge_dia / 2,
                badge_x + badge_dia, center_y + badge_dia / 2,
            )
            draw.ellipse(ring_box, outline=GOLD, width=4)
            canvas.paste(badge, (int(badge_x + ring_pad), int(center_y - badge_size / 2)), badge)
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Main compositors
# ---------------------------------------------------------------------------

def compose_full_graphic_post(ai_image_source, logo_path=None, handle="@thefootbroshow"):
    """Crop/resize an AI-generated full graphic to the 1080x1350 canvas.

    The AI image is expected to already contain all headline/bullet/table
    text baked in (see agents.FULL_GRAPHIC_GUIDELINES) — this just fits it
    to the post canvas and overlays the real logo + handle lockup on top.
    """
    canvas = Image.new("RGB", (CANVAS_WIDTH, CANVAS_HEIGHT), color=DARK_GREEN)

    ai_img = _load_ai_image(ai_image_source)
    if ai_img:
        canvas = _fit_with_padding(ai_img, CANVAS_WIDTH, CANVAS_HEIGHT, DARK_GREEN)

    draw = ImageDraw.Draw(canvas)
    _draw_handle_lockup(canvas, draw, logo_path, handle)
    return canvas


def compose_instagram_post(
    ai_image_source,
    bullets,
    logo_path=None,
    handle="@thefootbroshow",
    headline=None,
    fun_facts=None,
):
    """Compose the final 1080x1350 branded Instagram post and return a PIL Image."""
    canvas = Image.new("RGB", (CANVAS_WIDTH, CANVAS_HEIGHT), color=DARK_GREEN)
    draw = ImageDraw.Draw(canvas)

    # ------------------------------------------------------------------ photo
    ai_img = _load_ai_image(ai_image_source)
    if ai_img:
        ai_img = _crop_to_fit(ai_img, CANVAS_WIDTH, PHOTO_HEIGHT)
        canvas.paste(ai_img, (0, 0))
    else:
        draw.rectangle([(0, 0), (CANVAS_WIDTH, PHOTO_HEIGHT)], fill=(20, 50, 20))
        ph_font = _load_font(HEADER_FONT_CANDIDATES, 36)
        msg = "FOOTBRO SHOW"
        w = draw.textlength(msg, font=ph_font)
        draw.text(((CANVAS_WIDTH - w) / 2, PHOTO_HEIGHT / 2 - 20), msg, font=ph_font, fill=GOLD)

    # --------------------------------------------------------------- headline band
    draw.rectangle([(0, PHOTO_HEIGHT), (CANVAS_WIDTH, TOP_HEIGHT)], fill=DARK_GREEN)
    hl_text = _strip_emoji(headline or "")
    if hl_text:
        badge_box = (60, PHOTO_HEIGHT + 14, 190, PHOTO_HEIGHT + 46)
        draw.rounded_rectangle(badge_box, radius=6, fill=RED)
        font_badge = _load_font(BODY_FONT_CANDIDATES, 18)
        bw = draw.textlength("BREAKING", font=font_badge)
        draw.text(
            (badge_box[0] + (130 - bw) / 2, badge_box[1] + 7),
            "BREAKING", font=font_badge, fill=WHITE,
        )
        font_hl = _load_font(HEADER_FONT_CANDIDATES, 36)
        y = PHOTO_HEIGHT + 54
        for line in _wrap_text(draw, hl_text, font_hl, CANVAS_WIDTH - 120)[:2]:
            draw.text((60, y), line, font=font_hl, fill=WHITE)
            y += 40

    # ------------------------------------------------------------ gold separator
    draw.rectangle([(0, TOP_HEIGHT - 4), (CANVAS_WIDTH, TOP_HEIGHT + 4)], fill=GOLD)

    # ------------------------------------------------------------ bottom panel
    draw.rectangle([(0, TOP_HEIGHT), (CANVAS_WIDTH, CANVAS_HEIGHT)], fill=DARK_GREEN)
    draw.rectangle([(0, TOP_HEIGHT - 4), (CANVAS_WIDTH, TOP_HEIGHT + 4)], fill=GOLD)

    LEFT = 60
    INDENT = 94
    LINE_H = 29
    GAP = 9
    font_section = _load_font(HEADER_FONT_CANDIDATES, 40)
    font_bullet = _load_font(BODY_FONT_CANDIDATES, 23)
    em_font = _load_emoji_font(23)

    y = TOP_HEIGHT + 18

    # ---- Section 1 : KEY HIGHLIGHTS ----
    draw.text((LEFT, y), "KEY HIGHLIGHTS", font=font_section, fill=GOLD)
    y += 43
    draw.rectangle([(LEFT, y), (CANVAS_WIDTH - LEFT, y + 2)], fill=GOLD)
    y += 10

    # cap section 1 so section 2 always has at least 190 px
    sec1_max_y = LOGO_ZONE_TOP - 215
    y = _draw_bullets(
        draw, (bullets or [])[:4], y,
        font_bullet, em_font, GOLD, "diamond",
        max_y=sec1_max_y, left_margin=LEFT, indent=INDENT,
        line_h=LINE_H, gap=GAP,
    )

    # ---- full-width gold divider ----
    y += 12
    draw.rectangle([(36, y), (CANVAS_WIDTH - 36, y + 3)], fill=GOLD)
    y += 16

    # ---- Section 2 : DID YOU KNOW? ----
    draw.text((LEFT, y), "DID YOU KNOW?", font=font_section, fill=RED)
    y += 43
    draw.rectangle([(LEFT, y), (CANVAS_WIDTH - LEFT, y + 2)], fill=RED)
    y += 10

    # Fall back to extra stats bullets if no fun_facts returned
    facts = (fun_facts or []) or (bullets or [])[4:]
    _draw_bullets(
        draw, facts[:4], y,
        font_bullet, em_font, RED, "circle",
        max_y=LOGO_ZONE_TOP, left_margin=LEFT, indent=INDENT,
        line_h=LINE_H, gap=GAP,
    )

    # --------------------------------------------------------- bottom lockup
    _draw_handle_lockup(canvas, draw, logo_path, handle)

    return canvas

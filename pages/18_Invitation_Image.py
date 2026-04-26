# -*- coding: utf-8 -*-
"""
Σελίδα 18 — Πρόσκληση Εργασιών Σ∴ Στ∴ ΑΚΡΟΠΟΛΙΣ 84 — Luxury Mode

Δημιουργεί PNG πρόσκληση με:
- luxury parchment background
- καθαρό ασπρόμαυρο κορυμβωτό πλαίσιο
- εσωτερικό premium πλαίσιο
- μεγάλη καθαρή φωτογραφία Ακρόπολης με elegant frame
- σωστή υποστήριξη του τεκτονικού συμβόλου ∴ με DejaVu Sans
- σφραγίδα της Στοάς ανάμεσα στον Σεβάσμιο και τον Γραμματέα
- μικρή σφραγίδα/δαφνινο στεφάνι ως bullet στην ημερήσια διάταξη
- editable ημερήσια διάταξη, ομιλητής, θέμα, επόμενες συνεδρίες

Προτεινόμενα assets:
assets/acropolis-photo.jpg
assets/symbol_top.png
assets/symbol_center.png     # Σφραγίδα / δαφνινο στεφάνι της Στοάς
assets/symbol_corner.png

requirements.txt:
Pillow
"""

import sys
sys.path.append("..")

import io
import os
import random
from typing import List, Tuple, Optional

import streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps, ImageEnhance

try:
    from modules.database import init_db
    init_db()
except Exception:
    pass

st.set_page_config(page_title="Πρόσκληση Εργασιών", page_icon="🖼️", layout="wide")

# ══════════════════════════════════════════════════════════════
# ΣΤΑΘΕΡΕΣ
# ══════════════════════════════════════════════════════════════
PAGE_W, PAGE_H = 1240, 2050
NAVY = (18, 26, 63)
NAVY_SOFT = (29, 39, 78)
GOLD = (155, 130, 77)
GOLD_DARK = (120, 96, 52)
BLACK = (5, 5, 5)
WHITE = (255, 255, 255)
OFFWHITE = (250, 249, 246)
PARCHMENT = (248, 244, 235)
PARCHMENT_DARK = (226, 215, 190)

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS = os.path.join(BASE, "fonts")
ASSETS = os.path.join(BASE, "assets")

# ══════════════════════════════════════════════════════════════
# ΓΡΑΜΜΑΤΟΣΕΙΡΕΣ — DejaVu Sans για σωστό ∴
# ══════════════════════════════════════════════════════════════
def _fp(name: str) -> Optional[str]:
    path = os.path.join(FONTS, name)
    return path if os.path.exists(path) else None


def font(size: int, bold: bool = False, italic: bool = False) -> ImageFont.ImageFont:
    """DejaVu Sans by default. Υποστηρίζει σωστά το ∴."""
    if bold:
        path = _fp("DejaVuSans-Bold.ttf") or _fp("DejaVuSerif-Bold.ttf")
    elif italic:
        path = _fp("DejaVuSans-Oblique.ttf") or _fp("DejaVuSerif-Italic.ttf")
    else:
        path = _fp("DejaVuSans.ttf") or _fp("DejaVuSerif.ttf")
    return ImageFont.truetype(path, size=size) if path else ImageFont.load_default()

# ══════════════════════════════════════════════════════════════
# TEXT HELPERS
# ══════════════════════════════════════════════════════════════
def tw(draw: ImageDraw.ImageDraw, text: str, fnt: ImageFont.ImageFont) -> int:
    b = draw.textbbox((0, 0), str(text), font=fnt)
    return b[2] - b[0]


def th(draw: ImageDraw.ImageDraw, text: str, fnt: ImageFont.ImageFont) -> int:
    b = draw.textbbox((0, 0), str(text), font=fnt)
    return b[3] - b[1]


def wrap(draw: ImageDraw.ImageDraw, text: str, fnt: ImageFont.ImageFont, max_w: int) -> List[str]:
    words = str(text or "").split()
    lines, cur = [], ""
    for word in words:
        test = word if not cur else f"{cur} {word}"
        if tw(draw, test, fnt) <= max_w:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def center(draw: ImageDraw.ImageDraw, y: int, text: str, fnt: ImageFont.ImageFont,
           fill=NAVY, max_w: Optional[int] = None, lsp: int = 6) -> int:
    if not text:
        return y
    lines = [text] if not max_w else wrap(draw, text, fnt, max_w)
    for line in lines:
        w = tw(draw, line, fnt)
        draw.text(((PAGE_W - w) / 2, y), line, font=fnt, fill=fill)
        y += th(draw, line, fnt) + lsp
    return y


def center_at(draw: ImageDraw.ImageDraw, cx: int, y: int, text: str, fnt: ImageFont.ImageFont, fill=NAVY) -> None:
    w = tw(draw, text, fnt)
    draw.text((cx - w / 2, y), text, font=fnt, fill=fill)


def left(draw: ImageDraw.ImageDraw, x: int, y: int, text: str, fnt: ImageFont.ImageFont,
         fill=NAVY, max_w: Optional[int] = None, lsp: int = 6) -> int:
    lines = [text] if not max_w else wrap(draw, text, fnt, max_w)
    for line in lines:
        draw.text((x, y), line, font=fnt, fill=fill)
        y += th(draw, line, fnt) + lsp
    return y

# ══════════════════════════════════════════════════════════════
# ASSET HELPERS
# ══════════════════════════════════════════════════════════════
def load_asset(name: str) -> Optional[bytes]:
    path = os.path.join(ASSETS, name)
    if os.path.exists(path):
        with open(path, "rb") as f:
            return f.read()
    return None


def paste_asset(
    img: Image.Image,
    asset_bytes: Optional[bytes],
    x: int,
    y: int,
    max_w: int,
    max_h: int,
    monochrome: bool = False,
    invert: bool = False,
    opacity: float = 1.0,
) -> bool:
    if not asset_bytes:
        return False
    try:
        icon = Image.open(io.BytesIO(asset_bytes)).convert("RGBA")
        if monochrome:
            gray = ImageOps.grayscale(icon)
            if invert:
                gray = ImageOps.invert(gray)
            icon = Image.merge("RGBA", (gray, gray, gray, icon.getchannel("A")))
        if opacity < 1.0:
            a = icon.getchannel("A")
            a = a.point(lambda p: int(p * opacity))
            icon.putalpha(a)
        icon.thumbnail((max_w, max_h), Image.LANCZOS)
        px = x + (max_w - icon.width) // 2
        py = y + (max_h - icon.height) // 2
        img.alpha_composite(icon, (px, py))
        return True
    except Exception:
        return False

# ══════════════════════════════════════════════════════════════
# LUXURY BACKGROUND
# ══════════════════════════════════════════════════════════════
def create_luxury_background() -> Image.Image:
    """Δημιουργεί ελαφρύ parchment / luxury paper background."""
    bg = Image.new("RGBA", (PAGE_W, PAGE_H), PARCHMENT + (255,))
    pix = bg.load()
    random.seed(84)
    for _ in range(12000):
        x = random.randrange(0, PAGE_W)
        y = random.randrange(0, PAGE_H)
        delta = random.randrange(-7, 8)
        r = max(0, min(255, PARCHMENT[0] + delta))
        g = max(0, min(255, PARCHMENT[1] + delta))
        b = max(0, min(255, PARCHMENT[2] + delta))
        pix[x, y] = (r, g, b, 255)

    # subtle center glow
    overlay = Image.new("RGBA", (PAGE_W, PAGE_H), (255, 255, 255, 0))
    od = ImageDraw.Draw(overlay)
    od.ellipse((-250, 120, PAGE_W + 250, PAGE_H - 80), fill=(255, 255, 255, 48))
    overlay = overlay.filter(ImageFilter.GaussianBlur(90))
    bg.alpha_composite(overlay)
    return bg

# ══════════════════════════════════════════════════════════════
# FALLBACK SYMBOLS (χρησιμοποιούνται ΜΟΝΟ για corners/top)
# ══════════════════════════════════════════════════════════════
def draw_sq_compass(draw: ImageDraw.ImageDraw, cx: int, cy: int, size: int, color=WHITE, show_g: bool = True) -> None:
    s = size
    lw = max(2, s // 9)
    top = (cx, cy - int(s * 0.78))
    left_foot = (cx - int(s * 0.65), cy + int(s * 0.62))
    right_foot = (cx + int(s * 0.65), cy + int(s * 0.62))
    draw.line([top, left_foot], fill=color, width=lw)
    draw.line([top, right_foot], fill=color, width=lw)
    draw.ellipse([top[0] - lw, top[1] - lw, top[0] + lw, top[1] + lw], fill=color)

    arm = int(s * 0.86)
    y0 = cy + int(s * 0.38)
    draw.line([(cx - arm // 2, y0), (cx, cy - int(s * 0.08)), (cx + arm // 2, y0)], fill=color, width=lw)
    draw.line([(cx - arm // 2, y0), (cx + arm // 2, y0)], fill=color, width=lw)

    if show_g:
        f = font(max(12, int(s * 0.45)), bold=True)
        center_at(draw, cx, cy - int(s * 0.12), "G", f, color)


def draw_wreath_symbol(draw: ImageDraw.ImageDraw, cx: int, cy: int, size: int, color=NAVY) -> None:
    import math
    s = size
    for side in [-1, 1]:
        for i in range(12):
            angle = math.radians(110 + i * 11 if side == -1 else 70 - i * 11)
            px = cx + int(side * (s * 0.78) * math.cos(angle))
            py = cy + int((s * 0.92) * math.sin(angle))
            draw.ellipse([px - 5, py - 3, px + 5, py + 3], outline=color, width=2)
    draw_sq_compass(draw, cx, cy, int(s * 0.68), color)

# ══════════════════════════════════════════════════════════════
# ΔΙΑΚΟΣΜΗΤΙΚΑ
# ══════════════════════════════════════════════════════════════
def rule(draw: ImageDraw.ImageDraw, y: int, x1: int, x2: int, color=NAVY) -> None:
    draw.line([(x1, y), (x2, y)], fill=color, width=2)
    cx = (x1 + x2) // 2
    ds = 6
    draw.polygon([(cx, y - ds), (cx + ds, y), (cx, y + ds), (cx - ds, y)], fill=color)


def ornament(draw: ImageDraw.ImageDraw, y: int, x1: int, x2: int, color=NAVY) -> None:
    cx = (x1 + x2) // 2
    draw.line([(x1, y), (cx - 46, y)], fill=color, width=2)
    draw.line([(cx + 46, y), (x2, y)], fill=color, width=2)
    for off in [-34, -15, 15, 34]:
        ox = cx + off
        ds = 5
        draw.polygon([(ox, y - ds), (ox + ds * 2, y), (ox, y + ds), (ox - ds * 2, y)], outline=color, width=2)


def luxury_section_label(draw: ImageDraw.ImageDraw, y: int, text: str, fnt: ImageFont.ImageFont) -> int:
    """Luxury cartouche για section title."""
    w = tw(draw, text, fnt) + 70
    h = th(draw, text, fnt) + 22
    x1 = (PAGE_W - w) // 2
    y1 = y - 8
    x2 = x1 + w
    y2 = y1 + h
    draw.rounded_rectangle([x1, y1, x2, y2], radius=4, fill=(252, 250, 244), outline=NAVY, width=1)
    draw.line([(x1 - 150, y1 + h // 2), (x1 - 15, y1 + h // 2)], fill=GOLD_DARK, width=1)
    draw.line([(x2 + 15, y1 + h // 2), (x2 + 150, y1 + h // 2)], fill=GOLD_DARK, width=1)
    center_at(draw, PAGE_W // 2, y, text, fnt, NAVY)
    return y2 + 12

# ══════════════════════════════════════════════════════════════
# ΠΛΑΙΣΙΟ
# ══════════════════════════════════════════════════════════════
def draw_diamond_border(img: Image.Image, corner_bytes: Optional[bytes] = None) -> None:
    draw = ImageDraw.Draw(img)
    W, H = PAGE_W, PAGE_H
    draw.rectangle([0, 0, W - 1, H - 1], fill=BLACK)

    corner = 92
    draw.rectangle([corner, corner, W - corner, H - corner], fill=PARCHMENT)

    ds = 30
    step = ds * 2

    def diamond(cx, cy, s):
        return [(cx, cy - s), (cx + s, cy), (cx, cy + s), (cx - s, cy)]

    x = corner + ds
    idx = 0
    while x <= W - corner - ds:
        fill = WHITE if idx % 2 == 0 else BLACK
        for cy in [ds + 8, H - ds - 8]:
            pts = diamond(x, cy, ds)
            draw.polygon(pts, fill=fill)
            draw.polygon(pts, outline=BLACK if fill == WHITE else WHITE, width=1)
        x += step
        idx += 1

    y = corner + ds
    idx = 0
    while y <= H - corner - ds:
        fill = WHITE if idx % 2 == 0 else BLACK
        for cx in [ds + 8, W - ds - 8]:
            pts = diamond(cx, y, ds)
            draw.polygon(pts, fill=fill)
            draw.polygon(pts, outline=BLACK if fill == WHITE else WHITE, width=1)
        y += step
        idx += 1

    for gx, gy in [(0, 0), (W - corner, 0), (0, H - corner), (W - corner, H - corner)]:
        draw.rectangle([gx, gy, gx + corner, gy + corner], fill=BLACK, outline=WHITE, width=2)
        if not paste_asset(img, corner_bytes, gx + 11, gy + 11, corner - 22, corner - 22):
            draw_sq_compass(draw, gx + corner // 2, gy + corner // 2, 32, WHITE)

    m = 112
    draw.rectangle([m, m, W - m, H - m], outline=BLACK, width=5)
    draw.rectangle([m + 10, m + 10, W - m - 10, H - m - 10], outline=NAVY, width=2)
    draw.rectangle([m + 18, m + 18, W - m - 18, H - m - 18], outline=(206, 190, 150), width=1)

    # corner ticks inside
    t = 24
    for x1, y1, sx, sy in [(m + 22, m + 22, 1, 1), (W - m - 22, m + 22, -1, 1), (m + 22, H - m - 22, 1, -1), (W - m - 22, H - m - 22, -1, -1)]:
        draw.line([(x1, y1), (x1 + sx * t, y1)], fill=NAVY, width=2)
        draw.line([(x1, y1), (x1, y1 + sy * t)], fill=NAVY, width=2)

# ══════════════════════════════════════════════════════════════
# ΦΩΤΟΓΡΑΦΙΑ ΑΚΡΟΠΟΛΗΣ
# ══════════════════════════════════════════════════════════════
def process_acropolis(photo_bytes: bytes, box_w: int, box_h: int) -> Image.Image:
    photo = Image.open(io.BytesIO(photo_bytes)).convert("L")
    pw, ph = photo.size

    # Αφαίρεση κάτω caption/υπογραφής.
    photo = photo.crop((0, 0, pw, int(ph * 0.81)))
    pw, ph = photo.size

    target_ratio = box_w / box_h
    src_ratio = pw / ph

    if src_ratio > target_ratio:
        new_w = int(ph * target_ratio)
        left = max(0, (pw - new_w) // 2)
        photo = photo.crop((left, 0, left + new_w, ph))
    else:
        new_h = int(pw / target_ratio)
        top = max(0, int((ph - new_h) * 0.10))
        photo = photo.crop((0, top, pw, top + new_h))

    photo = photo.resize((box_w, box_h), Image.LANCZOS)
    photo = ImageOps.autocontrast(photo, cutoff=1)
    photo = ImageEnhance.Contrast(photo).enhance(1.20)
    photo = ImageEnhance.Sharpness(photo).enhance(1.30)

    rgba = photo.convert("RGBA")

    mask = Image.new("L", (box_w, box_h), 0)
    md = ImageDraw.Draw(mask)
    md.rounded_rectangle([0, 0, box_w, box_h], radius=18, fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(5))

    # soft bottom fade, not too strong
    alpha = mask.copy()
    fade_start = int(box_h * 0.88)
    for yy in range(fade_start, box_h):
        t = (yy - fade_start) / max(1, box_h - fade_start)
        val = int(255 * (1 - 0.28 * t))
        for xx in range(box_w):
            alpha.putpixel((xx, yy), min(alpha.getpixel((xx, yy)), val))

    rgba.putalpha(alpha)
    return rgba


def draw_photo_frame(draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int) -> None:
    """Luxury frame γύρω από τη φωτογραφία."""
    pad = 13
    outer = [x - pad, y - pad, x + w + pad, y + h + pad]
    mount = [x - 7, y - 7, x + w + 7, y + h + 7]
    inner = [x - 2, y - 2, x + w + 2, y + h + 2]

    draw.rounded_rectangle(outer, radius=16, fill=(255, 254, 249), outline=NAVY, width=2)
    draw.rounded_rectangle(mount, radius=12, outline=GOLD_DARK, width=2)
    draw.rounded_rectangle(inner, radius=8, outline=BLACK, width=2)

    c = 28
    for sx, sy in [(outer[0], outer[1]), (outer[2], outer[1]), (outer[0], outer[3]), (outer[2], outer[3])]:
        if sx == outer[0] and sy == outer[1]:
            draw.line([(sx, sy + c), (sx, sy), (sx + c, sy)], fill=NAVY, width=2)
        elif sx == outer[2] and sy == outer[1]:
            draw.line([(sx - c, sy), (sx, sy), (sx, sy + c)], fill=NAVY, width=2)
        elif sx == outer[0] and sy == outer[3]:
            draw.line([(sx, sy - c), (sx, sy), (sx + c, sy)], fill=NAVY, width=2)
        else:
            draw.line([(sx - c, sy), (sx, sy), (sx, sy - c)], fill=NAVY, width=2)

# ══════════════════════════════════════════════════════════════
# ΚΥΡΙΑ ΓΕΝΝΗΤΡΙΑ
# ══════════════════════════════════════════════════════════════
def create_invitation(
    meeting_date: str,
    meeting_time: str,
    degree: str,
    venue: str,
    agenda_items: List[str],
    speaker: str,
    topic: str,
    next_sessions: List[Tuple[str, str]],
    master: str,
    secretary: str,
    photo_bytes: Optional[bytes] = None,
    symbol_top_bytes: Optional[bytes] = None,
    symbol_center_bytes: Optional[bytes] = None,
    symbol_corner_bytes: Optional[bytes] = None,
    seal_bytes: Optional[bytes] = None,
) -> bytes:
    img = create_luxury_background()
    draw_diamond_border(img, corner_bytes=symbol_corner_bytes)
    draw = ImageDraw.Draw(img)

    INNER_X = 150
    TEXT_W = PAGE_W - INNER_X * 2

    # Fonts compact luxury
    f_top = font(40, bold=True)
    f_header = font(24)
    f_lodge = font(28, bold=True)
    f_title = font(48, bold=True)
    f_body = font(23)
    f_body_b = font(23, bold=True)
    f_section = font(23, bold=True)
    f_agenda = font(20, bold=True)
    f_small = font(18)
    f_small_b = font(18, bold=True)
    f_sig = font(19)
    f_sig_name = font(16, bold=True)
    f_next = font(18)

    # Header
    y = 140
    y = center(draw, y, "Ε∴ Δ∴ Τ∴ Μ∴ Α∴ Τ∴ Σ∴", f_top, NAVY, lsp=14)
    y = center(draw, y, "Εν Ονόματι και Υπό την Αιγίδα", f_header, NAVY, lsp=6)
    y = center(draw, y, "της Μεγάλης Στοάς της Ελλάδος", f_header, NAVY, lsp=6)
    y = center(draw, y, "των Αρχαίων Ελευθέρων και Αποδεδεγμένων Τεκτόνων", f_header, NAVY, max_w=TEXT_W, lsp=16)
    ornament(draw, y + 8, x1=475, x2=765)
    y += 34

    y = center(draw, y, "Σ∴ Στ∴ «ΑΚΡΟΠΟΛΙΣ» υπ' αριθμόν 84", f_lodge, NAVY, lsp=10)
    y = center(draw, y, "εν Αν∴ Αθηνών", f_lodge, NAVY, lsp=26)

    # Top right symbol — optional asset
    if symbol_top_bytes:
        paste_asset(img, symbol_top_bytes, PAGE_W - INNER_X - 78, 150, 92, 92)
    else:
        draw_sq_compass(draw, PAGE_W - INNER_X - 25, 205, 44, NAVY)

    # Photo
    photo_x = INNER_X - 42
    photo_y = y + 18
    photo_w = PAGE_W - photo_x * 2
    photo_h = 440
    raw_photo = photo_bytes or load_asset("acropolis-photo.jpg")

    draw_photo_frame(draw, photo_x, photo_y, photo_w, photo_h)
    if raw_photo:
        try:
            ph_img = process_acropolis(raw_photo, photo_w, photo_h)
            img.alpha_composite(ph_img, (photo_x, photo_y))
        except Exception:
            draw.rounded_rectangle([photo_x, photo_y, photo_x + photo_w, photo_y + photo_h], radius=10, fill=(220, 220, 220, 255))
    else:
        draw.rounded_rectangle([photo_x, photo_y, photo_x + photo_w, photo_y + photo_h], radius=10, fill=(220, 220, 220, 255))

    draw = ImageDraw.Draw(img)
    y = photo_y + photo_h + 46

    # ── Τίτλος με γενναίο breathing space ────────────────────────
    y = center(draw, y, "ΠΡΟΣΚΛΗΣΗ ΣΕ ΕΡΓΑΣΙΕΣ", f_title, NAVY, lsp=6)
    y += 16
    ornament(draw, y + 6, x1=420, x2=820)
    y += 38
    # ─────────────────────────────────────────────────────────────

    # Meeting details
    y = center(draw, y, f"Την {meeting_date} και ώρα {meeting_time},", f_body_b, NAVY, max_w=TEXT_W, lsp=10)
    y = center(draw, y, "θα πραγματοποιηθούν οι Εργασίες της Σεπτής Στοάς μας", f_body, NAVY, max_w=TEXT_W, lsp=10)
    y = center(draw, y, f"εις Βαθμόν {degree},", f_body, NAVY, max_w=TEXT_W, lsp=12)
    y = center(draw, y, venue, f_body, NAVY, max_w=TEXT_W, lsp=10)

    y += 14
    y = luxury_section_label(draw, y, "ΗΜΕΡΗΣΙΑ ΔΙΑΤΑΞΙΣ", f_section)
    y += 6

    # ── Agenda bullets ────────────────────────────────────────────
    bullet_x = INNER_X + 70
    text_x = bullet_x + 48
    for item in agenda_items:
        if symbol_center_bytes:
            paste_asset(img, symbol_center_bytes, bullet_x - 12, y - 2, 28, 28, opacity=0.92)
        else:
            draw_wreath_symbol(draw, bullet_x, y + 10, 16, GOLD_DARK)
        y = left(draw, text_x, y, item.upper(), f_agenda, NAVY, max_w=TEXT_W - 80, lsp=4)
        y += 10   # ← κενό ανάμεσα στα agenda items
    # ─────────────────────────────────────────────────────────────

    y += 14

    # Speaker / Topic
    if speaker.strip():
        y = center(draw, y, f"Ομιλητής: {speaker.strip()}", f_small, NAVY, max_w=TEXT_W, lsp=8)
    else:
        y = center(draw, y, "Ομιλητής: ________________________________", f_small, NAVY, lsp=8)

    if topic.strip():
        y = center(draw, y, f"Θέμα: «{topic.strip()}»", f_small, NAVY, max_w=TEXT_W, lsp=10)
    else:
        y = center(draw, y, "Θέμα: «__________________________________»", f_small, NAVY, lsp=10)

    ornament(draw, y + 6, x1=480, x2=760)
    y += 32

    # Closing
    para = (
        "Η παρουσία σας θα λαμπρύνει τις Εργασίες της Στοάς μας και θα αποτελέσει "
        "ιδιαίτερη χαρά και τιμή για το Πλήρωμα του Εργαστηρίου μας και τον "
        "Αδελφό Σεβάσμιο ιδιαιτέρως."
    )
    y = center(draw, y, para, f_small, NAVY, max_w=TEXT_W, lsp=8)
    y += 6
    y = center(draw, y, "Μετά το πέρας των Εργασιών θα ακολουθήσει Ποτήριον Αγάπης.", f_small, NAVY, max_w=TEXT_W, lsp=10)
    y = center(draw, y, "Με τον τριπλό αδελφικό ασπασμό,", f_small, NAVY, lsp=22)

    # ── Signatures ────────────────────────────────────────────────
    sig_y = y + 8
    sig_lx = INNER_X + 170
    sig_rx = PAGE_W - INNER_X - 170
    center_at(draw, sig_lx, sig_y, "Ο Σεβάσμιος", f_sig, NAVY)
    center_at(draw, sig_rx, sig_y, "Ο Γραμματεύς", f_sig, NAVY)

    line_y = sig_y + 80
    draw.line([(sig_lx - 130, line_y), (sig_lx + 130, line_y)], fill=NAVY, width=2)
    draw.line([(sig_rx - 130, line_y), (sig_rx + 130, line_y)], fill=NAVY, width=2)

    if master.strip():
        center_at(draw, sig_lx, line_y + 10, master.strip().upper(), f_sig_name, NAVY)
    if secretary.strip():
        center_at(draw, sig_rx, line_y + 10, secretary.strip().upper(), f_sig_name, NAVY)
    # ─────────────────────────────────────────────────────────────

    # ── Κεντρική σφραγίδα — αποκλειστικά akropolis-seal.png ─────
    symbol_box_w, symbol_box_h = 190, 150
    symbol_x = (PAGE_W - symbol_box_w) // 2
    symbol_y = sig_y + 3
    paste_asset(img, seal_bytes, symbol_x, symbol_y, symbol_box_w, symbol_box_h)
    # ─────────────────────────────────────────────────────────────

    y = line_y + 100
    if master.strip() or secretary.strip():
        y += 14

    # Next sessions box
    box_x1 = INNER_X - 18
    box_x2 = PAGE_W - INNER_X + 18
    box_y1 = min(max(y + 20, 1760), PAGE_H - 290)
    box_h = 60 + len(next_sessions[:4]) * 36 + 24
    box_y2 = min(box_y1 + box_h, PAGE_H - 160)

    draw.rounded_rectangle([box_x1, box_y1, box_x2, box_y2], radius=12, outline=BLACK, width=2, fill=(255, 254, 249))
    draw.rounded_rectangle([box_x1 + 5, box_y1 + 5, box_x2 - 5, box_y2 - 5], radius=10, outline=NAVY, width=1)
    draw.rounded_rectangle([box_x1 + 9, box_y1 + 9, box_x2 - 9, box_y2 - 9], radius=8, outline=(206, 190, 150), width=1)

    header_y = box_y1 + 18
    center_at(draw, PAGE_W // 2, header_y, "ΕΠΟΜΕΝΕΣ ΣΥΝΕΔΡΙΕΣ", font(22, bold=True), NAVY)
    rule(draw, header_y + 36, x1=box_x1 + 110, x2=box_x2 - 110)

    row_y = header_y + 50
    for dt, deg in next_sessions[:4]:
        cal_x = box_x1 + 105
        draw.rectangle([cal_x, row_y + 2, cal_x + 18, row_y + 22], outline=NAVY, width=2)
        draw.line([(cal_x, row_y + 8), (cal_x + 18, row_y + 8)], fill=NAVY, width=2)
        draw.text((box_x1 + 138, row_y), dt, font=f_next, fill=NAVY)
        draw.text((box_x1 + 515, row_y), f"Βαθμός: {deg}", font=f_next, fill=NAVY)
        row_y += 36

    if box_y2 + 22 < PAGE_H - 118:
        ornament(draw, box_y2 + 20, x1=480, x2=760)

    # Export
    out = Image.new("RGB", (PAGE_W, PAGE_H), WHITE)
    out.paste(img, mask=img.split()[3])
    buf = io.BytesIO()
    out.save(buf, format="PNG", optimize=True)
    buf.seek(0)
    return buf.read()

# ══════════════════════════════════════════════════════════════
# STREAMLIT UI
# ══════════════════════════════════════════════════════════════
st.markdown("# 🖼️ Πρόσκληση Εργασιών — Σ∴ Στ∴ ΑΚΡΟΠΟΛΙΣ 84")
st.caption("Luxury mode · Συμπληρώνετε τα στοιχεία και δημιουργείται πρόσκληση PNG έτοιμη για αποστολή ή εκτύπωση.")

with st.sidebar:
    st.markdown("## 📎 Assets")
    photo_up = st.file_uploader("Φωτογραφία Ακρόπολης", type=["jpg", "jpeg", "png"])
    symbol_top_up = st.file_uploader("Σύμβολο επάνω δεξιά", type=["jpg", "jpeg", "png"], key="top_symbol")
    symbol_center_up = st.file_uploader("Σφραγίδα Ακρόπολης / κεντρικό σύμβολο", type=["jpg", "jpeg", "png"], key="center_symbol")
    symbol_corner_up = st.file_uploader("Σύμβολο γωνιών", type=["jpg", "jpeg", "png"], key="corner_symbol")
    st.caption("Αν δεν ανεβάσετε, χρησιμοποιούνται όσα υπάρχουν στον φάκελο assets/.")

c1, c2 = st.columns(2)

with c1:
    meeting_date = st.text_input("Ημερομηνία", "Πέμπτη, 30 Απριλίου 2026")
    meeting_time = st.text_input("Ώρα", "20:00")
    degree = st.selectbox("Βαθμός", ["Μαθητού", "Εταίρου", "Διδασκάλου"])
    venue = st.text_area(
        "Τόπος",
        "στο Τεκτονικό Μέγαρο Αθηνών\n(Αχαρνών 19-21 & Σουρμελή, Τ.Κ. 104 39, Αθήνα).",
        height=80,
    ).replace("\n", " ")

with c2:
    master = st.text_input("Σεβάσμιος", "")
    secretary = st.text_input("Γραμματεύς", "")
    speaker = st.text_input("Ομιλητής", "")
    topic = st.text_input("Θέμα Ομιλίας", "")

st.markdown("---")
agenda_raw = st.text_area(
    "Ημερήσια Διάταξη — ένα θέμα ανά γραμμή",
    "Εγκατάσταση Αξιωματικών\nΟμιλία",
    height=90,
)
agenda_items = [x.strip() for x in agenda_raw.splitlines() if x.strip()]

st.markdown("### Επόμενες Συνεδρίες")
n1, n2 = st.columns(2)
with n1:
    nd1 = st.text_input("1η ημερομηνία", "Πέμπτη 14 Μαΐου 2026")
    nb1 = st.selectbox("1ος βαθμός", ["Μαθητού", "Εταίρου", "Διδασκάλου"], key="nb1")
with n2:
    nd2 = st.text_input("2η ημερομηνία", "Πέμπτη 4 Ιουνίου 2026")
    nb2 = st.selectbox("2ος βαθμός", ["Μαθητού", "Εταίρου", "Διδασκάλου"], key="nb2")

next_s = []
if nd1.strip():
    next_s.append((nd1.strip(), nb1))
if nd2.strip():
    next_s.append((nd2.strip(), nb2))

# Auto-load fallback assets
photo_bytes = photo_up.getvalue() if photo_up else load_asset("acropolis-photo.jpg")
symbol_top_bytes = symbol_top_up.getvalue() if symbol_top_up else load_asset("symbol_top.png")
symbol_center_bytes = symbol_center_up.getvalue() if symbol_center_up else load_asset("symbol_center.png")
seal_bytes = load_asset("akropolis-seal.png")
symbol_corner_bytes = symbol_corner_up.getvalue() if symbol_corner_up else load_asset("symbol_corner.png")

st.markdown("---")
if st.button("🎨 Δημιουργία Πρόσκλησης PNG", type="primary", use_container_width=True):
    with st.spinner("Δημιουργία luxury πρόσκλησης…"):
        png = create_invitation(
            meeting_date=meeting_date,
            meeting_time=meeting_time,
            degree=degree,
            venue=venue,
            agenda_items=agenda_items,
            speaker=speaker,
            topic=topic,
            next_sessions=next_s,
            master=master,
            secretary=secretary,
            photo_bytes=photo_bytes,
            symbol_top_bytes=symbol_top_bytes,
            symbol_center_bytes=symbol_center_bytes,
            symbol_corner_bytes=symbol_corner_bytes,
            seal_bytes=seal_bytes,
        )
    st.session_state["inv_png"] = png
    st.success("✅ Έτοιμο!")

if "inv_png" in st.session_state:
    st.image(st.session_state["inv_png"], use_container_width=True)
    st.download_button(
        "⬇️ Λήψη PNG",
        data=st.session_state["inv_png"],
        file_name="prosklisi_akropolis_84_luxury.png",
        mime="image/png",
        use_container_width=True,
    )

with st.expander("ℹ️ Οδηγίες assets"):
    st.markdown("""
    Προαιρετικά βάλτε στον φάκελο `assets/`:

    ```txt
    assets/acropolis-photo.jpg
    assets/symbol_top.png
    assets/symbol_center.png   ← PNG transparent, min 800×800
    assets/symbol_corner.png
    ```

    Το `symbol_center.png` χρησιμοποιείται:
    - **ανάμεσα** στον Σεβάσμιο και τον Γραμματέα (κεντρική σφραγίδα)
    - **ως bullet** στην Ημερήσια Διάταξη

    ⚠️ Αν δεν υπάρχει `symbol_center.png`, η κεντρική σφραγίδα **παραλείπεται** (δεν σχεδιάζεται fallback).
    Για τέλεια ποιότητα: PNG με **διαφανές φόντο**, τουλάχιστον **800×800 px**.
    """)


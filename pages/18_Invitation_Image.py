# -*- coding: utf-8 -*-
"""
Σελίδα 18 — Δημιουργία Πρόσκλησης Εργασιών ως εικόνα PNG

Δημιουργεί πρόσκληση τύπου αφίσας με:
- κορυμβωτό/σκακιέρα ασπρόμαυρο πλαίσιο
- φωτογραφία Ακρόπολης χωρίς τα κάτω γράμματα
- editable στοιχεία συνεδρίας
- ημερήσια διάταξη
- επόμενες συνεδρίες
- download PNG

Βάλτε την αρχική φωτογραφία στο:
assets/acropolis-photo.jpg
ή ανεβάστε τη χειροκίνητα από τη σελίδα.

requirements.txt:
Pillow
"""

import sys
sys.path.append("..")

import io
import os
from datetime import date
from typing import List, Tuple

import streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageFilter

try:
    from modules.database import init_db
    init_db()
except Exception:
    pass

st.set_page_config(page_title="Πρόσκληση Εργασιών", page_icon="🖼️", layout="wide")

# ══════════════════════════════════════════════════════════════
# CONFIG
# ══════════════════════════════════════════════════════════════
NAVY = "#121a3f"
GOLD = "#9b824d"
BLACK = "#050505"
WHITE = "#ffffff"
LIGHT_BG = "#fbfaf7"

PAGE_W = 1240
PAGE_H = 1800

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT_DIR = os.path.join(BASE_DIR, "fonts")
ASSET_DIR = os.path.join(BASE_DIR, "assets")
DEFAULT_ACROPOLIS = os.path.join(ASSET_DIR, "acropolis-photo.jpg")
DEFAULT_SEAL = os.path.join(ASSET_DIR, "akropolis-seal.png")

# ══════════════════════════════════════════════════════════════
# FONT HELPERS
# ══════════════════════════════════════════════════════════════
def font_path(*names: str) -> str | None:
    for name in names:
        path = os.path.join(FONT_DIR, name)
        if os.path.exists(path):
            return path
    return None


def get_font(size: int, bold: bool = False, italic: bool = False):
    # IMPORTANT:
    # Χρησιμοποιούμε DejaVu Sans γιατί υποστηρίζει το τεκτονικό σύμβολο ∴.
    # Το DejaVu Serif συχνά το αφήνει κενό, άρα φαίνεται σαν "Σ Στ" αντί για "Σ∴ Στ∴".
    if bold:
        path = font_path("DejaVuSans-Bold.ttf", "DejaVuSerif-Bold.ttf")
    elif italic:
        path = font_path("DejaVuSans-Oblique.ttf", "DejaVuSerif-Italic.ttf")
    else:
        path = font_path("DejaVuSans.ttf", "DejaVuSerif.ttf")

    if path:
        return ImageFont.truetype(path, size=size)

    # fallback
    return ImageFont.load_default()

# ══════════════════════════════════════════════════════════════
# DRAW HELPERS
# ══════════════════════════════════════════════════════════════
def text_bbox(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont):
    return draw.textbbox((0, 0), text, font=font)


def text_width(draw, text, font):
    b = text_bbox(draw, text, font)
    return b[2] - b[0]


def text_height(draw, text, font):
    b = text_bbox(draw, text, font)
    return b[3] - b[1]


def draw_center(draw, y: int, text: str, font, fill=NAVY, max_width=None, line_spacing=8):
    if not text:
        return y

    if max_width is None:
        w = text_width(draw, text, font)
        draw.text(((PAGE_W - w) / 2, y), text, font=font, fill=fill)
        return y + text_height(draw, text, font) + line_spacing

    lines = wrap_text(draw, text, font, max_width)
    for line in lines:
        w = text_width(draw, line, font)
        draw.text(((PAGE_W - w) / 2, y), line, font=font, fill=fill)
        y += text_height(draw, line, font) + line_spacing
    return y


def draw_left(draw, x: int, y: int, text: str, font, fill=NAVY, max_width=None, line_spacing=8):
    if not max_width:
        draw.text((x, y), text, font=font, fill=fill)
        return y + text_height(draw, text, font) + line_spacing

    lines = wrap_text(draw, text, font, max_width)
    for line in lines:
        draw.text((x, y), line, font=font, fill=fill)
        y += text_height(draw, line, font) + line_spacing
    return y


def wrap_text(draw, text: str, font, max_width: int) -> List[str]:
    words = text.split()
    lines = []
    current = ""

    for word in words:
        test = word if not current else current + " " + word
        if text_width(draw, test, font) <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word

    if current:
        lines.append(current)
    return lines


def draw_rule(draw, y: int, x1=250, x2=990, fill=NAVY):
    draw.line((x1, y, x2, y), fill=fill, width=2)
    mid = (x1 + x2) // 2
    draw.ellipse((mid - 5, y - 5, mid + 5, y + 5), outline=fill, width=2)
    draw.line((mid - 35, y, mid - 12, y), fill=fill, width=2)
    draw.line((mid + 12, y, mid + 35, y), fill=fill, width=2)


def draw_checker_border(img: Image.Image):
    draw = ImageDraw.Draw(img)

    # Καθαρό εξωτερικό πλαίσιο
    draw.rectangle((0, 0, PAGE_W - 1, PAGE_H - 1), outline=BLACK, width=6)

    margin = 42
    border = 34
    step = 32

    # Κορυμβωτό ασπρόμαυρο μοτίβο — πιο αραιό και καθαρό
    for x in range(margin + 20, PAGE_W - margin - 20, step):
        i = (x - margin) // step
        fill = BLACK if i % 2 == 0 else WHITE
        pts_top = [(x, 18), (x + 16, 18 + border), (x + 32, 18), (x + 16, 18 - border)]
        pts_bottom = [(x, PAGE_H - 18), (x + 16, PAGE_H - 18 - border), (x + 32, PAGE_H - 18), (x + 16, PAGE_H - 18 + border)]
        draw.polygon(pts_top, fill=fill, outline=BLACK)
        draw.polygon(pts_bottom, fill=fill, outline=BLACK)

    for y in range(margin + 20, PAGE_H - margin - 20, step):
        i = (y - margin) // step
        fill = BLACK if i % 2 == 0 else WHITE
        pts_left = [(18, y), (18 + border, y + 16), (18, y + 32), (18 - border, y + 16)]
        pts_right = [(PAGE_W - 18, y), (PAGE_W - 18 - border, y + 16), (PAGE_W - 18, y + 32), (PAGE_W - 18 + border, y + 16)]
        draw.polygon(pts_left, fill=fill, outline=BLACK)
        draw.polygon(pts_right, fill=fill, outline=BLACK)

    # Λευκό εσωτερικό πεδίο και διπλό πλαίσιο
    draw.rectangle((96, 86, PAGE_W - 96, PAGE_H - 86), fill=LIGHT_BG)
    draw.rectangle((96, 86, PAGE_W - 96, PAGE_H - 86), outline=BLACK, width=4)
    draw.rectangle((114, 104, PAGE_W - 114, PAGE_H - 104), outline=NAVY, width=2)

    # Corner symbols
    box = 92
    for x, y in [(8, 8), (PAGE_W - box - 8, 8), (8, PAGE_H - box - 8), (PAGE_W - box - 8, PAGE_H - box - 8)]:
        draw.rectangle((x, y, x + box, y + box), fill=BLACK, outline=WHITE, width=2)
        draw_symbol_square_compass(draw, x + box // 2, y + box // 2 + 2, 34, WHITE)


def draw_symbol_square_compass(draw, cx: int, cy: int, size: int, fill=NAVY):
    # simple geometric square & compass style symbol
    s = size
    draw.line((cx - s, cy + s // 2, cx, cy - s, cx + s, cy + s // 2), fill=fill, width=3)
    draw.line((cx - s, cy + s // 2, cx + s, cy + s // 2), fill=fill, width=3)
    draw.line((cx - s // 2, cy + s, cx, cy, cx + s // 2, cy + s), fill=fill, width=3)
    try:
        f = get_font(max(16, size // 2), bold=True)
        tw = text_width(draw, "G", f)
        draw.text((cx - tw / 2, cy - 8), "G", font=f, fill=fill)
    except Exception:
        pass


def draw_seal_or_placeholder(img: Image.Image, x: int, y: int, size: int, seal_bytes=None):
    draw = ImageDraw.Draw(img)
    if seal_bytes:
        try:
            seal = Image.open(io.BytesIO(seal_bytes)).convert("RGBA")
            seal.thumbnail((size, size), Image.LANCZOS)
            img.alpha_composite(seal, (x, y))
            return
        except Exception:
            pass

    if os.path.exists(DEFAULT_SEAL):
        try:
            seal = Image.open(DEFAULT_SEAL).convert("RGBA")
            seal.thumbnail((size, size), Image.LANCZOS)
            img.alpha_composite(seal, (x, y))
            return
        except Exception:
            pass

    # placeholder seal
    draw.ellipse((x, y, x + size, y + size), outline=NAVY, width=4)
    draw.ellipse((x + 12, y + 12, x + size - 12, y + size - 12), outline=NAVY, width=2)
    f1 = get_font(16, bold=True)
    f2 = get_font(34, bold=True)
    draw_centered_at(draw, x + size // 2, y + 18, "Σ∴Στ∴ ΑΚΡΟΠΟΛΙΣ", f1, NAVY)
    draw_centered_at(draw, x + size // 2, y + size // 2 - 18, "Α", f2, NAVY)
    draw_centered_at(draw, x + size // 2, y + size - 36, "ΥΠ' ΑΡΙΘ. 84", f1, NAVY)


def draw_centered_at(draw, cx, y, text, font, fill):
    w = text_width(draw, text, font)
    draw.text((cx - w / 2, y), text, font=font, fill=fill)


def add_acropolis_photo(img: Image.Image, photo_bytes=None):
    draw = ImageDraw.Draw(img)
    photo = None

    if photo_bytes:
        try:
            photo = Image.open(io.BytesIO(photo_bytes)).convert("L")
        except Exception:
            photo = None

    if photo is None and os.path.exists(DEFAULT_ACROPOLIS):
        try:
            photo = Image.open(DEFAULT_ACROPOLIS).convert("L")
        except Exception:
            photo = None

    x, y, w, h = 150, 430, 940, 360

    if photo is None:
        draw.rectangle((x, y, x + w, y + h), fill="#dddddd", outline=GOLD, width=2)
        f = get_font(28, italic=True)
        draw_centered_at(draw, PAGE_W // 2, y + h // 2 - 20, "[Φωτογραφία Ακρόπολης]", f, NAVY)
        return

    # crop bottom strip with letters/signature from source photo
    pw, ph = photo.size
    crop_bottom = int(ph * 0.86)
    photo = photo.crop((0, 0, pw, crop_bottom))

    # cover crop to target box
    target_ratio = w / h
    src_ratio = photo.width / photo.height
    if src_ratio > target_ratio:
        new_w = int(photo.height * target_ratio)
        left = (photo.width - new_w) // 2
        photo = photo.crop((left, 0, left + new_w, photo.height))
    else:
        new_h = int(photo.width / target_ratio)
        top = max(0, (photo.height - new_h) // 2)
        photo = photo.crop((0, top, photo.width, top + new_h))

    photo = photo.resize((w, h), Image.LANCZOS).convert("RGBA")

    # soft vignette mask
    mask = Image.new("L", (w, h), 0)
    md = ImageDraw.Draw(mask)
    md.rounded_rectangle((0, 0, w, h), radius=28, fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(16))

    # fade bottom slightly
    alpha = mask
    photo.putalpha(alpha)

    img.alpha_composite(photo, (x, y))

# ══════════════════════════════════════════════════════════════
# MAIN GENERATOR
# ══════════════════════════════════════════════════════════════
def create_invitation_png(
    meeting_date: str,
    meeting_time: str,
    degree: str,
    venue: str,
    agenda_items: List[str],
    speaker: str,
    topic: str,
    next_sessions: List[Tuple[str, str]],
    worshipful_master: str,
    secretary: str,
    photo_bytes=None,
    seal_bytes=None,
) -> bytes:
    img = Image.new("RGBA", (PAGE_W, PAGE_H), LIGHT_BG)
    draw = ImageDraw.Draw(img)

    draw_checker_border(img)

    # fonts
    f_top = get_font(42, bold=True)
    f_header = get_font(25)
    f_lodge = get_font(28, bold=True)
    f_title = get_font(50, bold=True)
    f_body = get_font(26)
    f_body_bold = get_font(26, bold=True)
    f_mid = get_font(25, bold=True)
    f_small = get_font(21)
    f_small_bold = get_font(21, bold=True)
    f_tiny = get_font(17)

    y = 125
    y = draw_center(draw, y, "Ε∴Δ∴Τ∴Μ∴Α∴Τ∴Σ∴", f_top, NAVY, line_spacing=12)
    y = draw_center(draw, y, "Εν Ονόματι και Υπό την Αιγίδα", f_header, NAVY, line_spacing=5)
    y = draw_center(draw, y, "της Μεγάλης Στοάς της Ελλάδος", f_header, NAVY, line_spacing=5)
    y = draw_center(draw, y, "των Αρχαίων Ελευθέρων και Αποδεδεγμένων Τεκτόνων", f_header, NAVY, line_spacing=18)

    draw_rule(draw, y + 5, x1=470, x2=770)
    y += 28

    y = draw_center(draw, y, "Σ∴ Στ∴ «ΑΚΡΟΠΟΛΙΣ» υπ’ αριθμόν 84", f_lodge, NAVY, line_spacing=6)
    y = draw_center(draw, y, "εν Αν∴ Αθηνών", f_lodge, NAVY, line_spacing=22)

    # seal and simple symbol top
    draw_seal_or_placeholder(img, 135, 145, 105, seal_bytes=seal_bytes)
    draw_symbol_square_compass(draw, 1040, 220, 50, NAVY)

    # photo
    add_acropolis_photo(img, photo_bytes=photo_bytes)

    y = 815
    y = draw_center(draw, y, "ΠΡΟΣΚΛΗΣΗ ΣΕ ΕΡΓΑΣΙΕΣ", f_title, NAVY, line_spacing=4)
    draw_rule(draw, y + 6, x1=455, x2=785)
    y += 34

    # Event info with centered text
    y = draw_center(draw, y, f"Την {meeting_date} και ώρα {meeting_time},", f_body, NAVY, max_width=860, line_spacing=8)
    y = draw_center(draw, y, "θα πραγματοποιηθούν οι Εργασίες της Σεπτής Στοάς μας", f_body, NAVY, max_width=860, line_spacing=8)
    y = draw_center(draw, y, f"εις Βαθμόν {degree},", f_body, NAVY, max_width=860, line_spacing=14)
    y = draw_center(draw, y, venue, f_body, NAVY, max_width=860, line_spacing=14)

    y += 10
    draw_rule(draw, y + 10, x1=300, x2=940)
    y += 24
    y = draw_center(draw, y, "ΗΜΕΡΗΣΙΑ ΔΙΑΤΑΞΙΣ", f_mid, NAVY, line_spacing=22)

    # agenda
    x_ag = 285
    for item in agenda_items:
        draw_symbol_square_compass(draw, x_ag - 34, y + 10, 12, GOLD)
        y = draw_left(draw, x_ag, y, item.upper(), f_small_bold, NAVY, max_width=680, line_spacing=12)

    y += 4
    if speaker.strip():
        y = draw_center(draw, y, f"Ομιλητής: {speaker}", f_small, NAVY, max_width=760, line_spacing=8)
    else:
        y = draw_center(draw, y, "Ομιλητής: ________________________________", f_small, NAVY, line_spacing=8)

    if topic.strip():
        y = draw_center(draw, y, f"Θέμα: «{topic}»", f_small, NAVY, max_width=760, line_spacing=10)
    else:
        y = draw_center(draw, y, "Θέμα: «__________________________________»", f_small, NAVY, line_spacing=10)

    draw_rule(draw, y + 5, x1=455, x2=785)
    y += 28

    # closing paragraph
    paragraph = (
        "Η παρουσία σας θα λαμπρύνει τις Εργασίες της Στοάς μας και θα αποτελέσει "
        "ιδιαίτερη χαρά και τιμή για το Πλήρωμα του Εργαστηρίου μας και τον Αδελφό Σεβάσμιο ιδιαιτέρως."
    )
    y = draw_center(draw, y, paragraph, f_small, NAVY, max_width=760, line_spacing=7)
    y += 6
    y = draw_center(draw, y, "Μετά το πέρας των Εργασιών θα ακολουθήσει Ποτήριον Αγάπης.", f_small, NAVY, max_width=760, line_spacing=10)
    y = draw_center(draw, y, "Με τον τριπλό αδελφικό ασπασμό,", f_small, NAVY, max_width=760, line_spacing=18)

    # signatures
    sig_y = y + 8
    draw_centered_at(draw, 300, sig_y, "Ο Σεβάσμιος", f_small, NAVY)
    draw_centered_at(draw, 940, sig_y, "Ο Γραμματεύς", f_small, NAVY)
    draw.line((210, sig_y + 58, 430, sig_y + 58), fill=NAVY, width=2)
    draw.line((810, sig_y + 58, 1030, sig_y + 58), fill=NAVY, width=2)

    if worshipful_master.strip():
        draw_centered_at(draw, 320, sig_y + 68, worshipful_master, f_tiny, NAVY)
    if secretary.strip():
        draw_centered_at(draw, 920, sig_y + 68, secretary, f_tiny, NAVY)

    draw_symbol_square_compass(draw, PAGE_W // 2, sig_y + 55, 40, NAVY)

    # next sessions box
    box_x1, box_y1 = 225, 1608
    box_x2, box_y2 = PAGE_W - 225, 1738
    draw.rounded_rectangle((box_x1, box_y1, box_x2, box_y2), radius=10, outline=BLACK, width=2, fill="#ffffff")
    draw_rule(draw, box_y1 + 28, x1=275, x2=965)
    draw_centered_at(draw, PAGE_W // 2, box_y1 + 12, "ΕΠΟΜΕΝΕΣ ΣΥΝΕΔΡΙΕΣ", f_mid, NAVY)

    row_y = box_y1 + 58
    for dt, deg in next_sessions[:3]:
        # calendar icon
        draw.rectangle((box_x1 + 105, row_y + 4, box_x1 + 125, row_y + 26), outline=NAVY, width=2)
        draw.line((box_x1 + 105, row_y + 11, box_x1 + 125, row_y + 11), fill=NAVY, width=2)
        draw.text((box_x1 + 150, row_y), dt, font=f_small, fill=NAVY)
        draw.text((box_x1 + 500, row_y), f"Βαθμός: {deg}", font=f_small, fill=NAVY)
        row_y += 34

    draw_rule(draw, 1752, x1=455, x2=785)

    # flatten white background for PNG
    out = Image.new("RGB", img.size, WHITE)
    out.paste(img, mask=img.split()[3])

    buf = io.BytesIO()
    out.save(buf, format="PNG", optimize=True)
    buf.seek(0)
    return buf.read()

# ══════════════════════════════════════════════════════════════
# STREAMLIT UI
# ══════════════════════════════════════════════════════════════
st.markdown("# 🖼️ Δημιουργία Πρόσκλησης Εργασιών")
st.caption("Συμπληρώνετε τα στοιχεία και το app δημιουργεί έτοιμη εικόνα PNG όπως το δείγμα.")

with st.sidebar:
    st.markdown("## ⚙️ Assets")
    st.caption("Αν δεν ανεβάσετε φωτογραφία, το app ψάχνει για `assets/acropolis-photo.jpg`.")
    photo_upload = st.file_uploader("Φωτογραφία Ακρόπολης", type=["jpg", "jpeg", "png"])
    seal_upload = st.file_uploader("Σφραγίδα / Logo Στοάς", type=["jpg", "jpeg", "png"])

col1, col2 = st.columns(2)

with col1:
    meeting_date = st.text_input("Ημερομηνία", "Πέμπτη, 30 Απριλίου 2026")
    meeting_time = st.text_input("Ώρα", "20:00")
    degree = st.selectbox("Βαθμός", ["Μαθητού", "Εταίρου", "Διδασκάλου"], index=0)
    venue = st.text_area(
        "Τόπος",
        "στο Τεκτονικό Μέγαρο Αθηνών\n(Αχαρνών 19-21 & Σουρμελή, Τ.Κ. 104 39, Αθήνα).",
        height=80,
    ).replace("\n", " ")

with col2:
    speaker = st.text_input("Ομιλητής", "")
    topic = st.text_input("Θέμα Ομιλίας", "")
    worshipful_master = st.text_input("Σεβάσμιος", "")
    secretary = st.text_input("Γραμματεύς", "")

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
    next_1_date = st.text_input("1η επόμενη ημερομηνία", "Πέμπτη 14 Μαΐου 2026")
    next_1_degree = st.selectbox("1ος βαθμός", ["Μαθητού", "Εταίρου", "Διδασκάλου"], index=0, key="n1deg")
with n2:
    next_2_date = st.text_input("2η επόμενη ημερομηνία", "Πέμπτη 4 Ιουνίου 2026")
    next_2_degree = st.selectbox("2ος βαθμός", ["Μαθητού", "Εταίρου", "Διδασκάλου"], index=0, key="n2deg")

next_sessions = []
if next_1_date.strip():
    next_sessions.append((next_1_date.strip(), next_1_degree))
if next_2_date.strip():
    next_sessions.append((next_2_date.strip(), next_2_degree))

st.markdown("---")

generate = st.button("🎨 Δημιουργία Πρόσκλησης PNG", type="primary", use_container_width=True)

if generate:
    with st.spinner("Δημιουργία εικόνας πρόσκλησης…"):
        png_bytes = create_invitation_png(
            meeting_date=meeting_date,
            meeting_time=meeting_time,
            degree=degree,
            venue=venue,
            agenda_items=agenda_items,
            speaker=speaker,
            topic=topic,
            next_sessions=next_sessions,
            worshipful_master=worshipful_master,
            secretary=secretary,
            photo_bytes=photo_upload.getvalue() if photo_upload else None,
            seal_bytes=seal_upload.getvalue() if seal_upload else None,
        )

    st.session_state["invitation_png"] = png_bytes
    st.success("✅ Η πρόσκληση δημιουργήθηκε.")

if "invitation_png" in st.session_state:
    st.image(st.session_state["invitation_png"], caption="Προεπισκόπηση Πρόσκλησης", use_container_width=True)
    st.download_button(
        "⬇️ Λήψη Πρόσκλησης PNG",
        data=st.session_state["invitation_png"],
        file_name="prosklisi_akropolis_84.png",
        mime="image/png",
        use_container_width=True,
    )

with st.expander("ℹ️ Οδηγίες εγκατάστασης"):
    st.markdown("""
    ### 1. Αρχείο σελίδας
    Αποθηκεύστε αυτό το αρχείο ως:

    ```txt
    pages/18_Πρόσκληση_Εργασιών.py
    ```

    ### 2. requirements.txt
    Προσθέστε:

    ```txt
    Pillow
    ```

    ### 3. Assets
    Δημιουργήστε φάκελο:

    ```txt
    assets/
    ```

    και βάλτε μέσα τη φωτογραφία ως:

    ```txt
    assets/acropolis-photo.jpg
    ```

    Προαιρετικά βάλτε και σφραγίδα:

    ```txt
    assets/akropolis-seal.png
    ```

    ### 4. Fonts
    Αν υπάρχουν ήδη τα DejaVu fonts στον φάκελο `fonts/`, θα τα χρησιμοποιήσει αυτόματα.
    Διαφορετικά θα χρησιμοποιηθεί fallback γραμματοσειρά.
    """)

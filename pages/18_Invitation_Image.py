# -*- coding: utf-8 -*-
"""
Σελίδα 18 — Πρόσκληση Εργασιών Σ∴ Στ∴ ΑΚΡΟΠΟΛΙΣ 84 — Luxury Mode
- acropolis.jpg (σωστό όνομα asset)
- ΔΕΝ έχει σφραγίδα ούτε γραμμές υπογραφών
"""

import sys
sys.path.append("..")

import io
import os
from typing import List, Tuple, Optional

import streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps, ImageEnhance

try:
    from modules.database import init_db
    init_db()
except Exception:
    pass

st.set_page_config(page_title="Πρόσκληση Εργασιών", page_icon="🖼️", layout="wide")

PAGE_W, PAGE_H = 1240, 2050
NAVY      = (18, 26, 63)
GOLD_DARK = (120, 96, 52)
BLACK     = (5, 5, 5)
WHITE     = (255, 255, 255)
PARCHMENT = (255, 255, 255)

BASE   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONTS  = os.path.join(BASE, "fonts")
ASSETS = os.path.join(BASE, "assets")

def _fp(name):
    p = os.path.join(FONTS, name)
    return p if os.path.exists(p) else None

def font(size, bold=False, italic=False):
    if bold:   path = _fp("DejaVuSans-Bold.ttf")    or _fp("DejaVuSerif-Bold.ttf")
    elif italic: path = _fp("DejaVuSans-Oblique.ttf") or _fp("DejaVuSerif-Italic.ttf")
    else:      path = _fp("DejaVuSans.ttf")          or _fp("DejaVuSerif.ttf")
    return ImageFont.truetype(path, size=size) if path else ImageFont.load_default()

def tw(draw, text, fnt):
    b = draw.textbbox((0,0), str(text), font=fnt); return b[2]-b[0]

def th(draw, text, fnt):
    b = draw.textbbox((0,0), str(text), font=fnt); return b[3]-b[1]

def wrap(draw, text, fnt, max_w):
    words = str(text or "").split()
    lines, cur = [], ""
    for word in words:
        test = word if not cur else f"{cur} {word}"
        if tw(draw, test, fnt) <= max_w: cur = test
        else:
            if cur: lines.append(cur)
            cur = word
    if cur: lines.append(cur)
    return lines

def center(draw, y, text, fnt, fill=None, max_w=None, lsp=6):
    if fill is None: fill = NAVY
    if not text: return y
    lines = [text] if not max_w else wrap(draw, text, fnt, max_w)
    for line in lines:
        w = tw(draw, line, fnt)
        draw.text(((PAGE_W - w)/2, y), line, font=fnt, fill=fill)
        y += th(draw, line, fnt) + lsp
    return y

def center_at(draw, cx, y, text, fnt, fill=None):
    if fill is None: fill = NAVY
    w = tw(draw, text, fnt)
    draw.text((cx - w/2, y), text, font=fnt, fill=fill)

def left(draw, x, y, text, fnt, fill=None, max_w=None, lsp=6):
    if fill is None: fill = NAVY
    lines = [text] if not max_w else wrap(draw, text, fnt, max_w)
    for line in lines:
        draw.text((x, y), line, font=fnt, fill=fill)
        y += th(draw, line, fnt) + lsp
    return y

def load_asset(name):
    p = os.path.join(ASSETS, name)
    if os.path.exists(p):
        with open(p, "rb") as f: return f.read()
    return None

def paste_asset(img, asset_bytes, x, y, max_w, max_h, opacity=1.0):
    if not asset_bytes: return False
    try:
        icon = Image.open(io.BytesIO(asset_bytes)).convert("RGBA")
        if opacity < 1.0:
            a = icon.getchannel("A").point(lambda p: int(p * opacity))
            icon.putalpha(a)
        icon.thumbnail((max_w, max_h), Image.LANCZOS)
        px = x + (max_w - icon.width)  // 2
        py = y + (max_h - icon.height) // 2
        img.alpha_composite(icon, (px, py))
        return True
    except Exception:
        return False

def draw_sq_compass(draw, cx, cy, size, color=WHITE, show_g=True):
    s  = size; lw = max(2, s//9)
    top = (cx, cy - int(s*0.78))
    lf  = (cx - int(s*0.65), cy + int(s*0.62))
    rf  = (cx + int(s*0.65), cy + int(s*0.62))
    draw.line([top, lf], fill=color, width=lw)
    draw.line([top, rf], fill=color, width=lw)
    arm = int(s*0.86); y0 = cy + int(s*0.38)
    draw.line([(cx-arm//2, y0),(cx, cy-int(s*0.08)),(cx+arm//2, y0)], fill=color, width=lw)
    draw.line([(cx-arm//2, y0),(cx+arm//2, y0)], fill=color, width=lw)
    if show_g:
        center_at(draw, cx, cy-int(s*0.12), "G", font(max(12,int(s*0.45)), bold=True), color)

def draw_wreath_symbol(draw, cx, cy, size, color=None):
    import math
    if color is None: color = GOLD_DARK
    s = size
    for side in [-1, 1]:
        for i in range(12):
            angle = math.radians(110 + i*11 if side==-1 else 70 - i*11)
            px = cx + int(side*(s*0.78)*math.cos(angle))
            py = cy + int((s*0.92)*math.sin(angle))
            draw.ellipse([px-5, py-3, px+5, py+3], outline=color, width=2)
    draw_sq_compass(draw, cx, cy, int(s*0.68), color)

def rule(draw, y, x1, x2, color=None):
    if color is None: color = NAVY
    draw.line([(x1,y),(x2,y)], fill=color, width=2)
    cx = (x1+x2)//2; ds = 6
    draw.polygon([(cx,y-ds),(cx+ds,y),(cx,y+ds),(cx-ds,y)], fill=color)

def ornament(draw, y, x1, x2, color=None):
    if color is None: color = NAVY
    cx = (x1+x2)//2
    draw.line([(x1,y),(cx-46,y)], fill=color, width=2)
    draw.line([(cx+46,y),(x2,y)], fill=color, width=2)
    for off in [-34,-15,15,34]:
        ox = cx+off; ds = 5
        draw.polygon([(ox,y-ds),(ox+ds*2,y),(ox,y+ds),(ox-ds*2,y)], outline=color, width=2)

def luxury_section_label(draw, y, text, fnt):
    w  = tw(draw, text, fnt) + 70
    h  = th(draw, text, fnt) + 22
    x1 = (PAGE_W - w)//2; y1 = y-8; x2 = x1+w; y2 = y1+h
    draw.rounded_rectangle([x1,y1,x2,y2], radius=4, fill=WHITE, outline=NAVY, width=1)
    draw.line([(x1-150, y1+h//2),(x1-15, y1+h//2)], fill=GOLD_DARK, width=1)
    draw.line([(x2+15,  y1+h//2),(x2+150,y1+h//2)], fill=GOLD_DARK, width=1)
    center_at(draw, PAGE_W//2, y, text, fnt, NAVY)
    return y2 + 12

def draw_diamond_border(img, corner_bytes=None):
    draw = ImageDraw.Draw(img)
    W, H = PAGE_W, PAGE_H
    corner = 92
    draw.rectangle([0,0,W-1,H-1], fill=BLACK)
    draw.rectangle([corner,corner,W-corner,H-corner], fill=PARCHMENT)
    ds = 30; step = ds*2

    def diamond(cx, cy, s):
        return [(cx,cy-s),(cx+s,cy),(cx,cy+s),(cx-s,cy)]

    x = corner+ds; idx = 0
    while x <= W-corner-ds:
        fill = WHITE if idx%2==0 else BLACK
        for cy in [ds+8, H-ds-8]:
            pts = diamond(x, cy, ds)
            draw.polygon(pts, fill=fill)
            draw.polygon(pts, outline=BLACK if fill==WHITE else WHITE, width=1)
        x += step; idx += 1

    y = corner+ds; idx = 0
    while y <= H-corner-ds:
        fill = WHITE if idx%2==0 else BLACK
        for cx in [ds+8, W-ds-8]:
            pts = diamond(cx, y, ds)
            draw.polygon(pts, fill=fill)
            draw.polygon(pts, outline=BLACK if fill==WHITE else WHITE, width=1)
        y += step; idx += 1

    for gx, gy in [(0,0),(W-corner,0),(0,H-corner),(W-corner,H-corner)]:
        draw.rectangle([gx,gy,gx+corner,gy+corner], fill=BLACK, outline=WHITE, width=2)
        if not paste_asset(img, corner_bytes, gx+11, gy+11, corner-22, corner-22):
            draw_sq_compass(draw, gx+corner//2, gy+corner//2, 32, WHITE)

    m = 112
    draw.rectangle([m,    m,    W-m,    H-m   ], outline=BLACK,           width=5)
    draw.rectangle([m+10, m+10, W-m-10, H-m-10], outline=NAVY,            width=2)
    draw.rectangle([m+18, m+18, W-m-18, H-m-18], outline=(206,190,150),   width=1)
    t = 24
    for x1,y1,sx,sy in [(m+22,m+22,1,1),(W-m-22,m+22,-1,1),(m+22,H-m-22,1,-1),(W-m-22,H-m-22,-1,-1)]:
        draw.line([(x1,y1),(x1+sx*t,y1)], fill=NAVY, width=2)
        draw.line([(x1,y1),(x1,y1+sy*t)], fill=NAVY, width=2)

def process_acropolis(photo_bytes, box_w, box_h):
    photo = Image.open(io.BytesIO(photo_bytes)).convert("L")
    pw, ph = photo.size
    photo = photo.crop((0, 0, pw, int(ph*0.81))); pw, ph = photo.size
    tr = box_w/box_h; sr = pw/ph
    if sr > tr:
        nw = int(ph*tr); lc = max(0,(pw-nw)//2)
        photo = photo.crop((lc, 0, lc+nw, ph))
    else:
        nh = int(pw/tr); top = max(0, int((ph-nh)*0.10))
        photo = photo.crop((0, top, pw, top+nh))
    photo = photo.resize((box_w, box_h), Image.LANCZOS)
    photo = ImageOps.autocontrast(photo, cutoff=1)
    photo = ImageEnhance.Contrast(photo).enhance(1.20)
    photo = ImageEnhance.Sharpness(photo).enhance(1.30)
    rgba  = photo.convert("RGBA")
    mask  = Image.new("L", (box_w, box_h), 0)
    md    = ImageDraw.Draw(mask)
    md.rounded_rectangle([0,0,box_w,box_h], radius=18, fill=255)
    mask  = mask.filter(ImageFilter.GaussianBlur(5))
    alpha = mask.copy()
    fs    = int(box_h*0.88)
    for yy in range(fs, box_h):
        t = (yy-fs)/max(1,box_h-fs); val = int(255*(1-0.28*t))
        for xx in range(box_w):
            alpha.putpixel((xx,yy), min(alpha.getpixel((xx,yy)), val))
    fside = int(box_w*0.30)
    for xx in range(fside):
        t = xx/fside; val = int(255*t)
        for yy in range(box_h):
            alpha.putpixel((xx,yy),              min(alpha.getpixel((xx,yy)), val))
            alpha.putpixel((box_w-1-xx,yy),      min(alpha.getpixel((box_w-1-xx,yy)), val))
    rgba.putalpha(alpha)
    return rgba


def to_upper_gr(text: str) -> str:
    """Κεφαλαία με διατήρηση τόνων για Ελληνικά."""
    tbl = str.maketrans(
        "άέήίόύώΆΈΉΊΌΎΏ",
        "ΆΈΉΊΌΎΏΆΈΉΊΌΎΏ"
    )
    return text.translate(tbl).upper()

def create_invitation(meeting_date, meeting_time, degree, venue,
                      agenda_items, speaker, topic, next_sessions,
                      master, secretary,
                      photo_bytes=None, symbol_top_bytes=None,
                      symbol_center_bytes=None, symbol_corner_bytes=None):

    img = Image.new("RGBA", (PAGE_W, PAGE_H), (255,255,255,255))
    draw_diamond_border(img, corner_bytes=symbol_corner_bytes)
    draw = ImageDraw.Draw(img)

    INNER_X = 150
    TEXT_W  = PAGE_W - INNER_X*2

    f_top     = font(40, bold=True)
    f_header  = font(24)
    f_lodge   = font(28, bold=True)
    f_title   = font(48, bold=True)
    f_body    = font(23)
    f_body_b  = font(23, bold=True)
    f_section = font(23, bold=True)
    f_agenda  = font(20, bold=True)
    f_small   = font(18)
    f_sig     = font(17, bold=True)
    f_next    = font(18)

    # Header
    y = 140
    y = center(draw, y, "Ε∴ Δ∴ Τ∴ Μ∴ Α∴ Τ∴ Σ∴", f_top, NAVY, lsp=14)
    y = center(draw, y, "Εν Ονόματι και Υπό την Αιγίδα", f_header, NAVY, lsp=6)
    y = center(draw, y, "της Μεγάλης Στοάς της Ελλάδος", f_header, NAVY, lsp=6)
    y = center(draw, y, "των Αρχαίων Ελευθέρων και Αποδεδεγμένων Τεκτόνων", f_header, NAVY, max_w=TEXT_W, lsp=16)
    ornament(draw, y+8, x1=475, x2=765); y += 34
    y = center(draw, y, "Σ∴ Στ∴ «ΑΚΡΟΠΟΛΙΣ» υπ' αριθμόν 84", f_lodge, NAVY, lsp=10)
    y = center(draw, y, "εν Αν∴ Αθηνών", f_lodge, NAVY, lsp=26)

    if symbol_top_bytes:
        paste_asset(img, symbol_top_bytes, PAGE_W-INNER_X-78, 150, 92, 92)

    # Φωτογραφία
    photo_x = 112; photo_y = y+18; photo_w = PAGE_W-224; photo_h = 440
    raw = photo_bytes or load_asset("acropolis.jpg")
    if raw:
        try:
            ph_img = process_acropolis(raw, photo_w, photo_h)
            img.alpha_composite(ph_img, (photo_x, photo_y))
        except Exception:
            draw.rectangle([photo_x, photo_y, photo_x+photo_w, photo_y+photo_h], fill=(220,220,220,255))
    else:
        draw.rectangle([photo_x, photo_y, photo_x+photo_w, photo_y+photo_h], fill=(220,220,220,255))

    draw = ImageDraw.Draw(img)
    y    = photo_y + photo_h + 46

    # Τίτλος
    y = center(draw, y, "ΠΡΟΣΚΛΗΣΗ ΣΕ ΕΡΓΑΣΙΕΣ", f_title, NAVY, lsp=6)
    y += 16; ornament(draw, y+6, x1=420, x2=820); y += 38

    # Στοιχεία
    y = center(draw, y, f"Την {meeting_date} και ώρα {meeting_time},", f_body_b, NAVY, max_w=TEXT_W, lsp=10)
    y = center(draw, y, "θα πραγματοποιηθούν οι Εργασίες της Σεπτής Στοάς μας", f_body, NAVY, max_w=TEXT_W, lsp=10)
    y = center(draw, y, f"εις Βαθμόν {degree},", f_body, NAVY, max_w=TEXT_W, lsp=12)
    y = center(draw, y, venue, f_body, NAVY, max_w=TEXT_W, lsp=10)

    y += 14
    y  = luxury_section_label(draw, y, "ΗΜΕΡΗΣΙΑ ΔΙΑΤΑΞΙΣ", f_section)
    y += 6

    bullet_x = INNER_X+70; text_x = bullet_x+48
    for item in agenda_items:
        if symbol_center_bytes:
            paste_asset(img, symbol_center_bytes, bullet_x-12, y-2, 28, 28, opacity=0.92)
        else:
            draw_wreath_symbol(draw, bullet_x, y+10, 16)
        draw = ImageDraw.Draw(img)
        y = left(draw, text_x, y, to_upper_gr(item), f_agenda, NAVY, max_w=TEXT_W-80, lsp=4)
        y += 10

    y += 14

    if speaker.strip():
        y = center(draw, y, f"Ομιλητής: {speaker.strip()}", f_small, NAVY, max_w=TEXT_W, lsp=8)
    else:
        y = center(draw, y, "Ομιλητής: ________________________________", f_small, NAVY, lsp=8)

    if topic.strip():
        y = center(draw, y, f"Θέμα: «{topic.strip()}»", f_small, NAVY, max_w=TEXT_W, lsp=10)
    else:
        y = center(draw, y, "Θέμα: «__________________________________»", f_small, NAVY, lsp=10)

    ornament(draw, y+6, x1=480, x2=760); y += 32

    para = ("Η παρουσία σας θα λαμπρύνει τις Εργασίες της Στοάς μας και θα αποτελέσει "
            "ιδιαίτερη χαρά και τιμή για το Πλήρωμα του Εργαστηρίου μας και τον "
            "Αδελφό Σεβάσμιο ιδιαιτέρως.")
    y = center(draw, y, para, f_small, NAVY, max_w=TEXT_W, lsp=8)
    y += 6
    y = center(draw, y, "Μετά το πέρας των Εργασιών θα ακολουθήσει Ποτήριον Αγάπης.", f_small, NAVY, max_w=TEXT_W, lsp=10)
    y = center(draw, y, "Με τον τριπλό αδελφικό ασπασμό,", f_small, NAVY, lsp=28)

    # Ονόματα — χωρίς γραμμές, χωρίς σφραγίδα
    sig_lx = INNER_X+170; sig_rx = PAGE_W-INNER_X-170
    if master.strip():
        center_at(draw, sig_lx, y, to_upper_gr(master.strip()), f_sig, NAVY)
    if secretary.strip():
        center_at(draw, sig_rx, y, to_upper_gr(secretary.strip()), f_sig, NAVY)
    y += 48

    # Επόμενες Συνεδρίες
    box_x1 = INNER_X-18; box_x2 = PAGE_W-INNER_X+18
    box_y1 = min(max(y+20, 1760), PAGE_H-290)
    box_h  = 60 + len(next_sessions[:4])*36 + 24
    box_y2 = min(box_y1+box_h, PAGE_H-160)

    draw.rounded_rectangle([box_x1,box_y1,box_x2,box_y2], radius=12, outline=BLACK, width=2, fill=WHITE)
    draw.rounded_rectangle([box_x1+5, box_y1+5, box_x2-5, box_y2-5 ], radius=10, outline=NAVY,          width=1)
    draw.rounded_rectangle([box_x1+9, box_y1+9, box_x2-9, box_y2-9 ], radius=8,  outline=(206,190,150), width=1)

    hy = box_y1+18
    center_at(draw, PAGE_W//2, hy, "ΕΠΟΜΕΝΕΣ ΣΥΝΕΔΡΙΕΣ", font(22, bold=True), NAVY)
    rule(draw, hy+36, x1=box_x1+110, x2=box_x2-110)

    row_y = hy+50
    for dt, deg in next_sessions[:4]:
        cal_x = box_x1+105
        draw.rectangle([cal_x, row_y+2, cal_x+18, row_y+22], outline=NAVY, width=2)
        draw.line([(cal_x, row_y+8),(cal_x+18, row_y+8)], fill=NAVY, width=2)
        draw.text((box_x1+138, row_y), dt,               font=f_next, fill=NAVY)
        draw.text((box_x1+515, row_y), f"Βαθμός: {deg}", font=f_next, fill=NAVY)
        row_y += 36

    if box_y2+22 < PAGE_H-118:
        ornament(draw, box_y2+20, x1=480, x2=760)

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
st.caption("Luxury mode · Συμπληρώνετε τα στοιχεία και δημιουργείται πρόσκληση PNG.")

with st.sidebar:
    st.markdown("## 📎 Assets")
    photo_up         = st.file_uploader("Φωτογραφία Ακρόπολης",     type=["jpg","jpeg","png"])
    symbol_top_up    = st.file_uploader("Σύμβολο επάνω δεξιά",      type=["jpg","jpeg","png"], key="top")
    symbol_center_up = st.file_uploader("Σύμβολο bullet ημερήσιας", type=["jpg","jpeg","png"], key="center")
    symbol_corner_up = st.file_uploader("Σύμβολο γωνιών",           type=["jpg","jpeg","png"], key="corner")
    st.caption("Αν δεν ανεβάσετε, χρησιμοποιούνται τα αρχεία του φακέλου assets/.")

c1, c2 = st.columns(2)
with c1:
    meeting_date = st.text_input("Ημερομηνία", "Πέμπτη, 14 Μαΐου 2026")
    meeting_time = st.text_input("Ώρα", "20:00")
    degree       = st.selectbox("Βαθμός", ["Μαθητού","Εταίρου","Διδασκάλου"])
    venue        = st.text_area("Τόπος",
        "στο Τεκτονικό Μέγαρο Αθηνών\n(Αχαρνών 19-21 & Σουρμελή, Τ.Κ. 104 39, Αθήνα).",
        height=80).replace("\n"," ")
with c2:
    master    = st.text_input("Σεβάσμιος", "")
    secretary = st.text_input("Γραμματεύς", "")
    speaker   = st.text_input("Ομιλητής", "")
    topic     = st.text_input("Θέμα Ομιλίας", "")

st.markdown("---")
agenda_raw   = st.text_area("Ημερήσια Διάταξη — ένα θέμα ανά γραμμή", "Ομιλία", height=90)
agenda_items = [x.strip() for x in agenda_raw.splitlines() if x.strip()]

st.markdown("### Επόμενες Συνεδρίες")
n1, n2 = st.columns(2)
with n1:
    nd1 = st.text_input("1η ημερομηνία", "Πέμπτη 4 Ιουνίου 2026")
    nb1 = st.selectbox("1ος βαθμός", ["Μαθητού","Εταίρου","Διδασκάλου"], key="nb1")
with n2:
    nd2 = st.text_input("2η ημερομηνία", "")
    nb2 = st.selectbox("2ος βαθμός", ["Μαθητού","Εταίρου","Διδασκάλου"], key="nb2")

next_s = []
if nd1.strip(): next_s.append((nd1.strip(), nb1))
if nd2.strip(): next_s.append((nd2.strip(), nb2))

photo_bytes         = photo_up.getvalue()         if photo_up         else load_asset("acropolis.jpg")
symbol_top_bytes    = symbol_top_up.getvalue()    if symbol_top_up    else load_asset("symbol_top.png")
symbol_center_bytes = symbol_center_up.getvalue() if symbol_center_up else load_asset("symbol_center.png")
symbol_corner_bytes = symbol_corner_up.getvalue() if symbol_corner_up else load_asset("symbol_corner.png")

st.markdown("---")
if st.button("🎨 Δημιουργία Πρόσκλησης PNG", type="primary", use_container_width=True):
    with st.spinner("Δημιουργία luxury πρόσκλησης…"):
        png = create_invitation(
            meeting_date=meeting_date, meeting_time=meeting_time,
            degree=degree, venue=venue, agenda_items=agenda_items,
            speaker=speaker, topic=topic, next_sessions=next_s,
            master=master, secretary=secretary,
            photo_bytes=photo_bytes, symbol_top_bytes=symbol_top_bytes,
            symbol_center_bytes=symbol_center_bytes,
            symbol_corner_bytes=symbol_corner_bytes,
        )
    st.session_state["inv_png"] = png
    st.success("✅ Έτοιμο!")

if "inv_png" in st.session_state:
    st.image(st.session_state["inv_png"], use_container_width=True)
    st.download_button("⬇️ Λήψη PNG",
        data=st.session_state["inv_png"],
        file_name="prosklisi_akropolis_84.png",
        mime="image/png", use_container_width=True)

with st.expander("ℹ️ Οδηγίες assets"):
    st.markdown("""
    Βάλτε στον φάκελο `assets/`:
    ```
    assets/acropolis.jpg
    assets/symbol_top.png
    assets/symbol_center.png   ← PNG transparent, bullet ημερήσιας
    assets/symbol_corner.png
    ```
    """)

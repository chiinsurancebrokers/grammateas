# -*- coding: utf-8 -*-
"""
Σελίδα 17 — Μεταγραφή Ηχογράφησης → Πρακτικά ΜΣΤΕ
         & Έγγραφο Word → Πρακτικά ΜΣΤΕ
"""

import sys
sys.path.append("..")

import io
import json
import os
import re
import urllib.request
from datetime import date
from typing import Callable, Optional, Tuple, List, Dict, Any

import streamlit as st

from modules.database import init_db

init_db()

st.set_page_config(
    page_title="Μεταγραφή → Πρακτικά",
    page_icon="🎧",
    layout="wide",
)

st.markdown("# 🎧📄 Ηχογράφηση / Word → Πρακτικά ΜΣΤΕ")
st.caption("Ηχογράφηση ή έγγραφο Word → Claude σύνταξη πρακτικών → επεξεργασία → PDF")

try:
    from pydub import AudioSegment  # noqa: F401
    PYDUB_OK = True
except Exception:
    PYDUB_OK = False

MAX_MB_RAW   = 300
SUPPORTED    = ["wav", "mp3", "m4a", "ogg", "webm", "aac"]

ΒΑΘΜΟΙ_GEN = {
    "Α' - Μαθητής":    "Μαθητού",
    "Β' - Εταίρος":    "Εταίρου",
    "Γ' - Διδάσκαλος": "Διδασκάλου",
}

NAVY = "#1a2a4a"
GOLD = "#b8960c"

CHUNK_SEC             = 300
OVERLAP_SEC           = 3
AUDIO_RATE            = 16000
AUDIO_BITRATE         = "32k"
MAX_OPENAI_CHUNK_MB   = 24

TRANSCRIPTION_MODEL_PRIMARY  = "gpt-4o-transcribe"
TRANSCRIPTION_MODEL_FALLBACK = "whisper-1"

CLAUDE_MODEL = "claude-sonnet-4-6"

TRANSCRIPTION_PROMPT = """
Η ηχογράφηση είναι ελληνική τεκτονική συνεδρίαση της Στοάς Ακρόπολις υπ' αριθμόν 84.
Μετέγραψε όσο πιο πιστά γίνεται στα Ελληνικά.

Συχνές λέξεις και φράσεις:
Σεβάσμιος, Σεβασμιώτατε, Αδελφός, Αδελφοί, Στοά, Στοά Ακρόπολις,
Ακρόπολις 84, Ρήτωρ, Γραμματεύς, Επόπτης, Τελετάρχης, Θησαυροφύλαξ,
Αγαθοεργία, Κορμός Αγαθοεργίας, Μέγας Αρχιτέκτων του Σύμπαντος,
Εργασίες, Πρακτικά, Ημερησία Διάταξις, Ανατολή, Μεσημβρία, Βορράς,
Ναός, Βαθμός Μαθητού, Βαθμός Εταίρου, Βαθμός Διδασκάλου.

Μην προσθέτεις δικά σου λόγια.
Μην επινοείς κείμενο όταν δεν ακούγεται καθαρά.
Μην γράφεις "Υπότιτλοι AUTHORWAVE".
Μην γράφεις "Ευχαριστούμε που παρακολουθήσατε".
Αν ένα σημείο δεν ακούγεται, γράψε [ακατάληπτο].
""".strip()

# ══════════════════════════════════════════════════════════════
# ΠΡΩΤΟΚΟΛΛΟ ΤΑΞΗΣ ΠΡΟΣΦΩΝΗΣΕΩΝ
# Εγκύκλιος υπ' αριθ. 27/(Κ) της 19.04.2019 — Πίνακας Α
# ══════════════════════════════════════════════════════════════
TAXH_PROSFWNHSEWN: List[Dict[str, Any]] = [
    {
        "order": 1,
        "title": "Μέγας Διδάσκαλος της Μ∴Σ∴Τ∴Ε∴",
        "prosfwnisi": "Ενδοξότατε Μέγ∴ Διδ∴",
        "keywords": [r"μεγ.{0,4}διδάσκαλ", r"μέγα.{0,4}διδ", r"grand.?master",
                     r"μεγ.{0,4}διδ.{0,10}μστε"],
    },
    {
        "order": 2,
        "title": "Επίτιμοι Μεγ∴ Διδάσκαλοι της Μ∴Σ∴Τ∴Ε∴",
        "prosfwnisi": "Ενδοξότατε Επίτ∴ Μέγ∴ Διδ∴",
        "keywords": [r"επίτιμ.{0,6}μεγ.{0,4}διδ", r"επιτ.{0,4}μεγ.{0,4}διδ"],
    },
    {
        "order": 3,
        "title": "Πρώην Μεγ∴ Διδάσκαλοι της Μ∴Σ∴Τ∴Ε∴",
        "prosfwnisi": "Ενδοξότατε πρ∴ Μέγ∴ Διδ∴",
        "keywords": [r"πρώην.{0,6}μεγ.{0,4}διδ", r"πρ.{0,4}μεγ.{0,4}διδ"],
    },
    {
        "order": 4,
        "title": "Πρόσθετος Μέγας Διδάσκαλος της Μ∴Σ∴Τ∴Ε∴",
        "prosfwnisi": "Ενδοξότατε Πρόσθ∴ Μέγ∴ Διδ∴",
        "keywords": [r"πρόσθετ.{0,4}μεγ", r"πρόσθ.{0,4}μεγ.{0,4}διδ"],
    },
    {
        "order": 5,
        "title": "Ένδοξοι Μεγ∴ Αξιωματικοί Συμβουλίου Μ∴Σ∴Τ∴Ε∴",
        "prosfwnisi": "Ένδοξε Μέγ∴ Αξ∴",
        "keywords": [r"μεγ.{0,4}αξιωμ.{0,6}συμβ", r"ένδοξ.{0,4}μεγ.{0,4}αξ",
                     r"μεγ.{0,4}αξ.{0,6}μστε"],
    },
    {
        "order": 6,
        "title": "Πρώην Μεγ∴ Αξιωματικοί Συμβουλίου Μ∴Σ∴Τ∴Ε∴",
        "prosfwnisi": "Ένδ∴ Αδ∴ πρ∴ Μέγ∴ Αξ∴",
        "keywords": [r"πρώην.{0,4}μεγ.{0,4}αξιωμ", r"πρ.{0,4}μεγ.{0,4}αξ"],
    },
    {
        "order": 7,
        "title": "Επίτιμα Μέλη Μ∴Σ∴Τ∴Ε∴",
        "prosfwnisi": "Επίτιμε",
        "keywords": [r"επίτιμ.{0,4}μέλ.{0,10}μστε", r"επίτιμ.{0,4}μέλ.{0,10}μεγάλ"],
    },
    {
        "order": 8,
        "title": "Ενεργοί Κοσμήτορες Μ∴Σ∴Τ∴Ε∴",
        "prosfwnisi": "Αιδεσιμ∴ Κοσμ∴",
        "keywords": [r"ενεργ.{0,4}κοσμήτορ", r"κοσμήτορ.{0,10}μστε",
                     r"κοσμήτορ.{0,10}μεγάλ"],
    },
    {
        "order": 9,
        "title": "Ομότιμοι Κοσμήτορες Μ∴Σ∴Τ∴Ε∴",
        "prosfwnisi": "Αιδεσιμ∴ ομότ∴ Κοσμ∴",
        "keywords": [r"ομότιμ.{0,4}κοσμ"],
    },
    {
        "order": 10,
        "title": "Μέγας Επιθεωρητής Στοάς",
        "prosfwnisi": "Σεβ∴ Μέγ∴ Επιθ∴",
        "keywords": [r"μεγ.{0,4}επιθεωρητ", r"μέγ.{0,4}επιθ"],
    },
    {
        "order": 11,
        "title": "Σεβάσμιος (εν ενεργεία)",
        "prosfwnisi": "Σεβ∴ Διδ∴",
        "keywords": [r"σεβάσμι", r"σεβ.{0,4}διδ", r"worshipful"],
    },
    {
        "order": 12,
        "title": "Πρώην Σεβάσμιοι Στοάς",
        "prosfwnisi": "Πρώην Σεβάσμιος",
        "keywords": [r"πρώην.{0,4}σεβ", r"πρ.{0,4}σεβ.{0,10}στοά"],
    },
    {
        "order": 13,
        "title": "Αξιωματικοί Στοάς",
        "prosfwnisi": "Αδ∴ [αξίωμα]",
        "keywords": [r"επόπτ", r"γραμματεύ", r"ταμία", r"τελετάρχ", r"ρήτορ",
                     r"θησαυροφύλ", r"ελεγκτ", r"αξιωματ.{0,6}στοά"],
    },
    {
        "order": 14,
        "title": "Διδάσκαλοι Στοάς",
        "prosfwnisi": "Αδ∴",
        "keywords": [r"διδάσκαλ.{0,6}στοά", r"βαθμ.{0,4}διδ"],
    },
    {
        "order": 15,
        "title": "Εταίροι Στοάς",
        "prosfwnisi": "Αδ∴",
        "keywords": [r"εταίρ.{0,6}στοά", r"βαθμ.{0,4}εταίρ"],
    },
    {
        "order": 16,
        "title": "Μαθηταί Στοάς",
        "prosfwnisi": "Αδ∴",
        "keywords": [r"μαθητ.{0,6}στοά", r"βαθμ.{0,4}μαθ"],
    },
]

PROTOCOL_TEXT = "\n".join(
    f"{e['order']}. {e['title']} → «{e['prosfwnisi']}»"
    for e in TAXH_PROSFWNHSEWN
)

# ══════════════════════════════════════════════════════════════
# ΣΕΙΡΑ ΛΗΨΗΣ ΛΟΓΟΥ — ΕΠΙ ΟΜΙΛΙΩΝ / ΕΥΗΜΕΡΙΑΣ
# Από κατώτερο → ανώτερο (ο Μέγ∴ Διδ∴ λαμβάνει τελευταίος)
# ══════════════════════════════════════════════════════════════
TAXH_OMILION: List[Dict[str, Any]] = [
    {"order": 1,  "title": "Μαθηταί, μέλη άλλων Στοών (Βορράς)",
     "keywords": [r"\bμαθητ"]},
    {"order": 2,  "title": "Εταίροι, μέλη άλλων Στοών (Βορράς)",
     "keywords": [r"\bεταίρ"]},
    {"order": 3,  "title": "Διδάσκαλοι, μέλη άλλων Στοών (Μεσημβρία)",
     "keywords": [r"βαθμ.{0,4}γ", r"διδάσκαλ.{0,6}στοά"]},
    {"order": 4,  "title": "Αξιωματικοί Στοάς (Μεσημβρία)",
     "keywords": [r"επόπτ", r"γραμματεύ", r"ταμί", r"τελετάρχ",
                  r"ρήτορ", r"θησαυροφύλ", r"ελεγκτ"]},
    {"order": 5,  "title": "Επί Τιμή Σεβάσμιοι (Αριστερά Σεβ.)",
     "keywords": [r"επίτιμ.{0,4}σεβ", r"ε\.τ\.\s*σεβ"]},
    {"order": 6,  "title": "Πρώην Σεβάσμιοι / Επιθεωρηταί (Αριστερά Σεβ.)",
     "keywords": [r"πρώην.{0,4}σεβ", r"πρ.{0,4}σεβ", r"επιθεωρητ"]},
    {"order": 7,  "title": "Σεβάσμιοι (Δεξιά Σεβ.)",
     "keywords": [r"σεβάσμι", r"σεβ.{0,4}διδ"]},
    {"order": 8,  "title": "Ομότιμοι Κοσμήτορες (Αριστερά Σεβ.)",
     "keywords": [r"ομότιμ.{0,4}κοσμ"]},
    {"order": 9,  "title": "Κοσμήτορες (Δεξιά Σεβ.)",
     "keywords": [r"κοσμήτορ"]},  # Ομότιμοι ήδη πιάστηκαν από entry 8
    {"order": 10, "title": "Μέγας Επιθεωρητής (Δεξιά Σεβ.)",
     "keywords": [r"μεγ.{0,4}επιθεωρητ", r"μέγ.{0,4}επιθ"]},
    {"order": 11, "title": "Πρόσθετοι Μεγ. Αξιωματικοί (Δεξιά Σεβ.)",
     "keywords": [r"πρόσθετ.{0,4}μεγ.{0,4}αξ", r"έξοχ.{0,4}αδ"]},
    {"order": 12, "title": "Επίτιμα Μέλη Μ∴Σ∴Τ∴Ε∴ (Δεξιά Σεβ.)",
     "keywords": [r"επίτιμ.{0,4}μέλ", r"έκλαμπρ.{0,4}αδ"]},
    {"order": 13, "title": "Πρώην Μεγ. Αξιωματικοί (Αριστερά Σεβ.)",
     "keywords": [r"πρώην.{0,4}μεγ.{0,4}αξ", r"πρ.{0,4}μεγ.{0,4}αξ",
                  r"ένδοξ.{0,4}αδ.{0,8}πρ.{0,4}μεγ"]},
    {"order": 14, "title": "Μεγάλοι Αξιωματικοί (Δεξιά Σεβ.)",
     "keywords": [r"μεγ.{0,4}αξιωμ", r"ένδοξ.{0,4}αδ.{0,4}μεγ.{0,4}αξ"]},
    {"order": 15, "title": "Πρόσθετος Μέγ. Διδάσκαλος (Δεξιά Σεβ.)",
     "keywords": [r"πρόσθετ.{0,4}μεγ.{0,4}διδ"]},
    {"order": 16, "title": "Πρώην Μεγ. Διδάσκαλοι (Αριστερά Σεβ.)",
     "keywords": [r"πρώην.{0,4}μεγ.{0,4}διδ", r"πρ.{0,4}μεγ.{0,4}διδ",
                  r"ενδοξότατ.{0,4}αδ.{0,8}πρ.{0,4}μεγ.{0,4}διδ"]},
    {"order": 17, "title": "Επίτιμοι Μεγ. Διδάσκαλοι (Αριστερά Σεβ.)",
     "keywords": [r"επίτιμ.{0,4}μεγ.{0,4}διδ",
                  r"ενδοξότατ.{0,4}αδ.{0,8}επίτιμ.{0,4}μεγ"]},
    {"order": 18, "title": "Μέγας Διδάσκαλος",
     "keywords": [r"μεγ.{0,4}διδάσκαλ", r"grand.?master",
                  r"ενδοξότατ.{0,4}μέγ.{0,4}διδ"]},
]

OMILION_TEXT = "\n".join(
    f"{e['order']}. {e['title']}"
    for e in TAXH_OMILION
)


# ══════════════════════════════════════════════════════════════
# DEJAVU FONTS — AUTO DOWNLOAD
# ══════════════════════════════════════════════════════════════
_FONT_URLS = {
    "DejaVuSans.ttf":         "https://github.com/dejavu-fonts/dejavu-fonts/raw/master/ttf/DejaVuSans.ttf",
    "DejaVuSans-Bold.ttf":    "https://github.com/dejavu-fonts/dejavu-fonts/raw/master/ttf/DejaVuSans-Bold.ttf",
    "DejaVuSerif.ttf":        "https://github.com/dejavu-fonts/dejavu-fonts/raw/master/ttf/DejaVuSerif.ttf",
    "DejaVuSerif-Bold.ttf":   "https://github.com/dejavu-fonts/dejavu-fonts/raw/master/ttf/DejaVuSerif-Bold.ttf",
    "DejaVuSerif-Italic.ttf": "https://github.com/dejavu-fonts/dejavu-fonts/raw/master/ttf/DejaVuSerif-Italic.ttf",
}
_FONT_CACHE_DIR = "/tmp/grammateas_fonts"


def ensure_fonts() -> str:
    sentinel  = "DejaVuSans.ttf"
    system_candidates = [
        "/usr/share/fonts/truetype/dejavu",
        "/usr/share/fonts/dejavu",
        "/usr/share/fonts/TTF",
        "/usr/local/share/fonts/dejavu",
    ]
    project_candidates = []
    try:
        this_file = os.path.abspath(__file__)
        project_candidates += [
            os.path.join(os.path.dirname(os.path.dirname(this_file)), "fonts"),
            os.path.join(os.path.dirname(this_file), "fonts"),
        ]
    except Exception:
        pass
    project_candidates += [
        os.path.join(os.getcwd(), "fonts"),
        os.path.join(os.getcwd(), "..", "fonts"),
        "/mount/src/grammateas/fonts",
        _FONT_CACHE_DIR,
    ]

    all_candidates = system_candidates + project_candidates
    for candidate in all_candidates:
        candidate = os.path.normpath(candidate)
        if os.path.isdir(candidate) and os.path.exists(os.path.join(candidate, sentinel)):
            return candidate

    os.makedirs(_FONT_CACHE_DIR, exist_ok=True)
    for filename, url in _FONT_URLS.items():
        dest = os.path.join(_FONT_CACHE_DIR, filename)
        if not os.path.exists(dest):
            try:
                urllib.request.urlretrieve(url, dest)
            except Exception:
                pass
    return _FONT_CACHE_DIR


def register_dejavu_fonts() -> Tuple[str, str, str, str]:
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    font_dir = ensure_fonts()
    font_map = {
        "DJVS":  "DejaVuSans.ttf",
        "DJVSB": "DejaVuSans-Bold.ttf",
        "DJVR":  "DejaVuSerif.ttf",
        "DJVRB": "DejaVuSerif-Bold.ttf",
        "DJVRI": "DejaVuSerif-Italic.ttf",
    }

    registered = set(pdfmetrics.getRegisteredFontNames())
    for alias, filename in font_map.items():
        if alias not in registered:
            path = os.path.join(font_dir, filename)
            if os.path.exists(path):
                try:
                    pdfmetrics.registerFont(TTFont(alias, path))
                except Exception:
                    pass

    registered = set(pdfmetrics.getRegisteredFontNames())
    fs  = "DJVS"  if "DJVS"  in registered else "Helvetica"
    fsb = "DJVSB" if "DJVSB" in registered else "Helvetica-Bold"
    fr  = "DJVR"  if "DJVR"  in registered else "Helvetica"
    frb = "DJVRB" if "DJVRB" in registered else "Helvetica-Bold"

    if fs == "Helvetica":
        import sys as _sys
        print(
            f"[PDF] ⚠️  DejaVu not found in {font_dir} — "
            "Greek characters may not render.",
            file=_sys.stderr,
        )
    return fs, fsb, fr, frb


# ══════════════════════════════════════════════════════════════
# API KEYS
# ══════════════════════════════════════════════════════════════
def get_openai_key() -> str:
    try:
        return (
            st.secrets.get("AI", {}).get("OPENAI_API_KEY")
            or st.secrets.get("OPENAI_API_KEY", "")
        )
    except Exception:
        return ""


def get_anthropic_key() -> str:
    try:
        return (
            st.secrets.get("AI", {}).get("ANTHROPIC_API_KEY")
            or st.secrets.get("ANTHROPIC_API_KEY", "")
        )
    except Exception:
        return ""


# ══════════════════════════════════════════════════════════════
# AUDIO HELPERS
# ══════════════════════════════════════════════════════════════
def mb_size(data: bytes) -> float:
    return len(data) / (1024 * 1024)


def normalize_to_mp3(audio_bytes: bytes, ext: str) -> Tuple[Optional[bytes], Optional[str]]:
    try:
        from pydub import AudioSegment
        audio = AudioSegment.from_file(io.BytesIO(audio_bytes), format=ext)
        audio = audio.set_channels(1).set_frame_rate(AUDIO_RATE)
        out_buf = io.BytesIO()
        audio.export(out_buf, format="mp3", bitrate=AUDIO_BITRATE,
                     parameters=["-ac", "1", "-ar", str(AUDIO_RATE)])
        out_buf.seek(0)
        return out_buf.read(), None
    except ImportError as e:
        return None, f"❌ Δεν φορτώθηκε το `pydub`. Λεπτομέρεια: {e}"
    except Exception as e:
        return None, f"❌ Σφάλμα μετατροπής ήχου (ελέγξτε ffmpeg). Λεπτομέρεια: {e}"


def split_audio_to_chunks(audio_bytes: bytes) -> Tuple[List[bytes], Optional[str]]:
    try:
        from pydub import AudioSegment
        audio     = AudioSegment.from_file(io.BytesIO(audio_bytes), format="mp3")
        chunk_ms  = CHUNK_SEC * 1000
        overlap_ms = OVERLAP_SEC * 1000
        step_ms   = max(chunk_ms - overlap_ms, 1)
        chunks: List[bytes] = []
        for start_ms in range(0, len(audio), step_ms):
            end_ms = min(start_ms + chunk_ms, len(audio))
            part   = audio[start_ms:end_ms]
            out_buf = io.BytesIO()
            part.export(out_buf, format="mp3", bitrate=AUDIO_BITRATE,
                        parameters=["-ac", "1", "-ar", str(AUDIO_RATE)])
            data = out_buf.getvalue()
            if len(data) > 5000:
                chunks.append(data)
        return chunks if chunks else [audio_bytes], None
    except ImportError as e:
        return [audio_bytes], f"⚠️ Δεν φορτώθηκε το `pydub`. Λεπτομέρεια: {e}"
    except Exception as e:
        return [audio_bytes], f"⚠️ Δεν έγινε σωστό split. Λεπτομέρεια: {e}"


# ══════════════════════════════════════════════════════════════
# WORD DOCUMENT HELPER
# ══════════════════════════════════════════════════════════════
def extract_text_from_docx(docx_bytes: bytes) -> Tuple[str, Optional[str]]:
    try:
        from docx import Document as DocxDocument
        from docx.oxml.ns import qn
        doc   = DocxDocument(io.BytesIO(docx_bytes))
        lines: List[str] = []

        def process_element(elem):
            tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
            if tag == "p":
                style_name = ""
                pPr = elem.find(qn("w:pPr"))
                if pPr is not None:
                    pStyle = pPr.find(qn("w:pStyle"))
                    if pStyle is not None:
                        style_name = pStyle.get(qn("w:val"), "")
                text_parts = [c.text for c in elem.iter(qn("w:t")) if c.text]
                text = "".join(text_parts).strip()
                if text:
                    if "Heading" in style_name or "heading" in style_name:
                        lines.append(f"\n### {text}")
                    else:
                        lines.append(text)
            elif tag == "tbl":
                for row in elem.findall(f".//{qn('w:tr')}"):
                    cell_texts = []
                    for cell in row.findall(f".//{qn('w:tc')}"):
                        cell_texts.append("".join(
                            t.text for t in cell.iter(qn("w:t")) if t.text
                        ).strip())
                    row_line = " | ".join(c for c in cell_texts if c)
                    if row_line:
                        lines.append(row_line)

        for child in doc.element.body:
            process_element(child)

        full_text = "\n".join(lines).strip()
        if not full_text:
            return "", "⚠️ Το αρχείο Word δεν περιέχει αναγνώσιμο κείμενο."
        return full_text, None
    except ImportError:
        return "", "❌ Δεν βρέθηκε το `python-docx`. Προσθέστε `python-docx>=1.0.0`."
    except Exception as e:
        return "", f"❌ Σφάλμα ανάγνωσης αρχείου Word: {e}"


# ══════════════════════════════════════════════════════════════
# TRANSCRIPTION CLEANING
# ══════════════════════════════════════════════════════════════
def clean_transcript(text: str) -> str:
    if not text:
        return ""
    for pat in [
        r"Υπότιτλοι\s+AUTHORWAVE", r"Υποτιτλοι\s+AUTHORWAVE", r"AUTHORWAVE",
        r"Ευχαριστούμε πολύ που παρακολουθήσατε το βίντεο!?",
        r"Παρακολουθείτε και εγγραφείτε στο κανάλι μας.*?(?=\n|$)",
        r"www\.argirobarbarigou\.com",
        r"\bUSING\b", r"\bresolving\b", r"\bprogresses\b", r"\battendant\b",
    ]:
        text = re.sub(pat, " ", text, flags=re.IGNORECASE | re.MULTILINE)
    text = re.sub(r"(.{8,80}?)(\s+\1){2,}", r"\1", text, flags=re.IGNORECASE)
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"\n[ \t]+", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def remove_overlap_repetition(full_text: str) -> str:
    lines   = [l.strip() for l in full_text.splitlines() if l.strip()]
    cleaned: List[str] = []
    for line in lines:
        if cleaned and line == cleaned[-1]:
            continue
        cleaned.append(line)
    return "\n".join(cleaned).strip()


# ══════════════════════════════════════════════════════════════
# OPENAI TRANSCRIPTION
# ══════════════════════════════════════════════════════════════
def transcribe_chunk(chunk: bytes, chunk_idx: int, total: int) -> str:
    openai_key = get_openai_key()
    if not openai_key:
        return f"[❌ Chunk {chunk_idx+1}: Δεν βρέθηκε OPENAI_API_KEY]"
    if mb_size(chunk) > MAX_OPENAI_CHUNK_MB:
        return f"[❌ Chunk {chunk_idx+1}: {mb_size(chunk):.1f}MB > {MAX_OPENAI_CHUNK_MB}MB]"
    try:
        from openai import OpenAI
        client     = OpenAI(api_key=openai_key)
        audio_file = io.BytesIO(chunk)
        audio_file.name = f"chunk_{chunk_idx+1}.mp3"
        try:
            result = client.audio.transcriptions.create(
                model=TRANSCRIPTION_MODEL_PRIMARY, file=audio_file,
                language="el", prompt=TRANSCRIPTION_PROMPT,
                response_format="text", temperature=0,
            )
        except Exception as primary_error:
            audio_file.seek(0)
            try:
                result = client.audio.transcriptions.create(
                    model=TRANSCRIPTION_MODEL_FALLBACK, file=audio_file,
                    language="el", prompt=TRANSCRIPTION_PROMPT,
                    response_format="text", temperature=0,
                )
            except Exception as fallback_error:
                return (f"[❌ Chunk {chunk_idx+1}: Primary: {primary_error}. "
                        f"Fallback: {fallback_error}]")
        return clean_transcript(str(result))
    except ImportError:
        return f"[❌ Chunk {chunk_idx+1}: Προσθέστε `openai` στο requirements.txt]"
    except Exception as e:
        return f"[❌ Chunk {chunk_idx+1}: {e}]"


def transcribe_audio(
    audio_bytes: bytes, ext: str,
    progress_cb: Optional[Callable] = None,
) -> Tuple[str, Optional[str]]:
    if progress_cb:
        progress_cb(5, "🎚️ Κανονικοποίηση ήχου σε MP3 mono 16kHz…")
    mp3_bytes, err = normalize_to_mp3(audio_bytes, ext)
    if err:
        return "", err
    if progress_cb:
        progress_cb(12, f"✂️ Διαχωρισμός… MP3: {mb_size(mp3_bytes):.1f}MB")
    chunks, split_warning = split_audio_to_chunks(mp3_bytes)
    n           = len(chunks)
    transcripts: List[str] = []
    errors:      List[str] = []
    for i, chunk in enumerate(chunks):
        if progress_cb:
            progress_cb(15 + int(65 * (i / max(n, 1))),
                        f"🎧 Μεταγραφή τμήματος {i+1}/{n} — {mb_size(chunk):.1f}MB…")
        text = transcribe_chunk(chunk, i, n)
        if text:
            if text.startswith("[❌"):
                errors.append(text)
            transcripts.append(f"=== Τμήμα {i+1}/{n} ===\n{text}")
    full     = remove_overlap_repetition(clean_transcript("\n\n".join(transcripts)))
    warnings: List[str] = []
    if split_warning:
        warnings.append(split_warning)
    if errors:
        warnings.append("⚠️ Κάποια chunks δεν μεταγράφηκαν σωστά.")
    return full, "\n".join(warnings) if warnings else None


# ══════════════════════════════════════════════════════════════
# JSON EXTRACTION HELPER
# ══════════════════════════════════════════════════════════════
def _extract_json(raw: str) -> Optional[dict]:
    if not raw:
        return None

    clean = raw.strip()
    clean = re.sub(r"^```(?:json)?\s*", "", clean, flags=re.MULTILINE)
    clean = re.sub(r"\s*```\s*$",       "", clean, flags=re.MULTILINE).strip()
    try:
        return json.loads(clean)
    except (json.JSONDecodeError, ValueError):
        pass

    start = raw.find("{")
    if start != -1:
        depth, in_str, esc, end = 0, False, False, -1
        for idx in range(start, len(raw)):
            ch = raw[idx]
            if esc:
                esc = False
                continue
            if ch == "\\" and in_str:
                esc = True
                continue
            if ch == '"':
                in_str = not in_str
            if not in_str:
                if ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0:
                        end = idx
                        break
        if end != -1:
            try:
                return json.loads(raw[start:end + 1])
            except (json.JSONDecodeError, ValueError):
                pass

    candidates = re.findall(r"\{[\s\S]+\}", raw)
    for candidate in sorted(candidates, key=len, reverse=True):
        try:
            return json.loads(candidate)
        except (json.JSONDecodeError, ValueError):
            continue

    return None


def _empty_result(transcript: str = "", raw_text: str = "") -> dict:
    return {
        "ημερομηνία": "", "ημέρα": "", "βαθμός_γενική": "Μαθητού",
        "τόπος": "", "σεβάσμιος": "", "παρόντες_αριθμός": 0,
        "παρόντες_ολογράφως": "", "ημερησία_διάταξη": [],
        "χαιρετισμοί_κατά_σειράν": [], "ομιλητές_κατά_σειράν": [],
        "κείμενο_πρακτικών": raw_text,
        "αποφάσεις": [], "κορμός_αγαθοεργίας": 0.0,
        "κορμός_ολογράφως": "", "γραμματεύς": "", "ρήτωρ": "",
        "μεταγραφή_λέξη_προς_λέξη": transcript,
    }


# ══════════════════════════════════════════════════════════════
# ΤΑΞΙΝΟΜΗΣΗ ΑΞΙΩΜΑΤΙΚΩΝ ΚΑΤΑ ΠΡΩΤΟΚΟΛΛΟ ΠΡΟΣΦΩΝΗΣΕΩΝ
# ══════════════════════════════════════════════════════════════
def _protocol_rank(title_or_name: str) -> int:
    text = title_or_name.lower()
    for entry in TAXH_PROSFWNHSEWN:
        for kw in entry["keywords"]:
            if re.search(kw, text, flags=re.IGNORECASE):
                return entry["order"]
    return 99


def sort_officials_by_protocol(officials: List[str]) -> List[str]:
    return sorted(officials, key=_protocol_rank)


# ══════════════════════════════════════════════════════════════
# ΤΑΞΙΝΟΜΗΣΗ ΣΕΙΡΑΣ ΛΗΨΗΣ ΛΟΓΟΥ (ΕΠΙ ΟΜΙΛΙΩΝ / ΕΥΗΜΕΡΙΑΣ)
# Από κατώτερο → ανώτερο βαθμό
# ══════════════════════════════════════════════════════════════
def _omilion_rank(speaker_line: str) -> int:
    text = speaker_line.lower()
    for entry in TAXH_OMILION:
        for kw in entry["keywords"]:
            if re.search(kw, text, flags=re.IGNORECASE):
                return entry["order"]
    return 50  # άγνωστος → μέση θέση


def sort_speakers_by_omilion(speakers: List[str]) -> List[str]:
    """Ταξινομεί τους ομιλητές από κατώτερο → ανώτερο (σειρά λήψης λόγου)."""
    return sorted(speakers, key=_omilion_rank)


# ══════════════════════════════════════════════════════════════
# CLAUDE → ΠΡΑΚΤΙΚΑ
# ══════════════════════════════════════════════════════════════
_SYSTEM_PROMPT = f"""
Είσαι έμπειρος Γραμματεύς-Σφραγιδοφύλαξ της Σ∴ Στ∴ ΑΚΡΟΠΟΛΙΣ υπ' αρ. 84.
Σου δίνεται κείμενο ελληνικής τεκτονικής συνεδρίασης και πρέπει να συντάξεις
επίσημα Πρακτικά ΜΣΤΕ.

════════════════════════════════════════════════════════════════
ΓΛΩΣΣΑ — ΚΡΙΣΙΜΗ ΟΔΗΓΙΑ
════════════════════════════════════════════════════════════════

Γράφεις σε ΤΕΚΤΟΝΙΚΗ αλλά ΣΥΓΧΡΟΝΗ ελληνική. Ο στόχος είναι να
διαβάζεται άνετα από σύγχρονο αναγνώστη χωρίς να χάνει το τεκτονικό ύφος.

ΚΑΝΟΝΕΣ ΓΛΩΣΣΑΣ:
• Χρησιμοποίησε νέα ελληνική σύνταξη και λεξιλόγιο παντού.
• Ρήματα σε απλό αόριστο ή ενεστώτα: «άνοιξε», «καλωσόρισε»,
  «παρουσίασε», «τόνισε», «ευχαρίστησε», «ανέπτυξε», «επισήμανε».
• ΟΧΙ αρχαίες καταλήξεις σε καθημερινά ρήματα:
  ΛΑΘΟΣ: «εκήρυξε», «ανεγνώσθησαν», «ενεκρίθησαν», «άπαντες»,
          «εκόσμουν», «υπογράψαντες», «ανέλαβον», «παρευρέθησαν».
  ΣΩΣΤΟ: «άνοιξε τις εργασίες», «αναγνώστηκαν», «εγκρίθηκαν»,
         «όλοι», «κοσμούσαν», «που υπέγραψαν», «ανέλαβαν», «παρευρέθηκαν».
• Χρησιμοποίησε «οι Αδδ∴» αντί «άπαντες».
• Χρησιμοποίησε «ο Σεβ∴» (όχι «ο Φιλτ∴ Αδ∴ Σεβ∴» σε κάθε πρόταση —
  μόνο στην πρώτη αναφορά κάθε ενότητας).

ΤΕΚΤΟΝΙΚΕΣ ΦΡΑΣΕΙΣ ΠΟΥ ΔΙΑΤΗΡΟΥΝΤΑΙ ΑΝΑΛΛΟΙΩΤΕΣ (ΟΧΙ αρχαϊσμοί,
αλλά καθιερωμένες εκφράσεις — μην τις αλλάζεις):
• «ως εχαράχθησαν» (μόνο για επικύρωση πρακτικών)
• «εις Αιωνίαν Ανατολήν» (για μεταστάντα μέλη)
• «τιμής ένεκεν» (για χειροκρουσία εις μνήμην)
• «φέρωμεν την πενθίμον χειροκρουσίαν»
• «μετά του οβολού του»
• «Βήμα της Ευγλωττίας», «Βιβλίον των Παρουσιών»,
  «Βωμός των Επισήμων Διαβεβαιώσεων»
• «Εργαστήριο», «πλήρωμα», «Κορμός Αγαθοεργίας»
• «Φιλτ∴ Αδ∴ Σεβ∴ Διδ∴», «Αδ∴», «Αδδ∴», «Σ∴ Στ∴»
• «Αιωνία Ανατολή», «Τεκτ∴ Ναός»

ΠΑΡΑΔΕΙΓΜΑ ΣΩΣΤΟΥ ΥΦΟΥΣ:
---
Ο Φιλτ∴ Αδ∴ Σεβ∴ Γεώργιος Παρίσης άνοιξε τις εργασίες της Σ∴ Στ∴
ΑΚΡΟΠΟΛΙΣ υπ' αρ. 84 σε Βαθμ∴ Μαθητού, καλωσορίζοντας εγκάρδια
όλους τους Αδδ∴ και ιδιαίτερα τον Ένδοξο Αδ∴ Μέγα Στεγαστή.
Τόνισε τη χαρά της σημερινής συνεδρίασης, ενόψει της εγκατάστασης
των νέων Αξιωματικών.
---

════════════════════════════════════════════════════════════════
ΠΡΩΤΟΚΟΛΛΟ ΤΑΞΗΣ ΠΡΟΣΦΩΝΗΣΕΩΝ (Εγκ. 27/2019 — Πίνακας Α)
════════════════════════════════════════════════════════════════

{PROTOCOL_TEXT}

ΚΑΝΟΝΕΣ ΧΑΙΡΕΤΙΣΜΩΝ:
• Κατέγραψε ΟΛΟΥΣ όσους χαιρέτισε ο Σεβ∴ κατά την έναρξη.
• ΜΗΝ βάζεις τον Σεβ∴ στους χαιρετισμούς — αυτός χαιρετά.
• Ο Μέγας Στεγαστής = «Ένδοξε Μέγ∴ Αξ∴» → ΤΑΞΗ 5.
• Πρώην Σεβάσμιοι = «Πρώην Σεβάσμιος» → ΤΑΞΗ 12.
• Μορφή: "Ένδοξε Μέγ∴ Αξ∴ Δημήτριος Δενεδιός — Μέγας Στεγαστής Μ∴Σ∴Τ∴Ε∴"

ΑΝΑΦΟΡΑ ΜΕΓΑ ΣΤΕΓΑΣΤΗ ΣΤΗΝ ΑΦΗΓΗΣΗ:
• Πάντα: «τον Ένδοξο Αδ∴ [ΟΝΟΜΑ ΕΠΩΝΥΜΟ], Μέγα Στεγαστή της Μεγάλης Στοάς της Ελλάδος»
• ΟΧΙ «τον Ένδοξε Μέγ∴ Αξ∴» μέσα στο αφηγηματικό κείμενο.

════════════════════════════════════════════════════════════════
ΣΕΙΡΑ ΛΗΨΗΣ ΛΟΓΟΥ — ΕΠΙ ΟΜΙΛΙΩΝ & ΕΠΙ ΕΥΗΜΕΡΙΑΣ
(από κατώτερο → ανώτερο — ο Μέγ∴ Διδ∴ λαμβάνει τελευταίος)
════════════════════════════════════════════════════════════════

{OMILION_TEXT}

ΚΡΙΣΙΜΟ για τις ενότητες «ΕΠΙ ΤΗΣ ΟΜΙΛΙΑΣ» και «ΕΠΙ ΤΗΣ ΕΥΗΜΕΡΙΑΣ»:
• Η σειρά λήψης λόγου ακολουθεί ΠΑΝΤΑ τον παραπάνω πίνακα (1→18).
• Οι Μαθηταί μιλούν πρώτοι, ο Μέγ∴ Διδ∴ (αν παρευρίσκεται) τελευταίος.
• Στο πεδίο "ομιλητές_κατά_σειράν" του JSON, λίσταρε τους ομιλητές
  στη σωστή σειρά (κατώτερος → ανώτερος).
• Αν δεν γνωρίζεις τον βαθμό/αξίωμα κάποιου ομιλητή, βάλτον στη μέση.

════════════════════════════════════════════════════════════════
ΔΟΜΗ ΚΑΙ ΠΕΡΙΕΧΟΜΕΝΟ ΤΟΥ "κείμενο_πρακτικών"
════════════════════════════════════════════════════════════════

Γράψε ΟΛΕΣ τις παρακάτω ενότητες που προκύπτουν από το κείμενο.
Κάθε ενότητα ξεκινά με τίτλο σε κεφαλαία.
Κάθε παράγραφος: 3–6 προτάσεις σε σύγχρονη ελληνική.

ΥΠΟΧΡΕΩΤΙΚΕΣ ΕΝΟΤΗΤΕΣ (αν υπάρχουν στο κείμενο):

1. ΕΝΑΡΞΗ — ΚΑΛΩΣΟΡΙΣΜΑ
   Ο Φιλτ∴ Αδ∴ Σεβ∴ [ΟΝΟΜΑ] άνοιξε τις εργασίες της Σ∴ Στ∴ [ΟΝΟΜΑ] σε
   Βαθμ∴ [ΒΑΘΜΟΣ], καλωσορίζοντας θερμά όλους τους Αδδ∴ και ιδιαίτερα
   [ΕΠΙΣΚΕΠΤΕΣ].

2. ΕΠΙΚΥΡΩΣΗ ΠΡΟΗΓΟΥΜΕΝΩΝ ΠΡΑΚΤΙΚΩΝ
   Αναγνώστηκαν τα Πρακτικά της συνεδρίασης της [ΗΜΕΡΟΜΗΝΙΑ] και
   εγκρίθηκαν ομόφωνα ως εχαράχθησαν.

3. ΑΛΛΗΛΟΓΡΑΦΙΑ / ΕΓΚΡΙΤΙΚΟΙ ΠΙΝΑΚΕΣ (αν υπάρχουν)

4. ΠΕΝΘΙΜΗ ΧΕΙΡΟΚΡΟΥΣΙΑ (αν υπάρχει)
   Ο Σεβ∴ κάλεσε το πλήρωμα να φέρει την πενθίμον χειροκρουσίαν
   εις μνήμην του [ΟΝΟΜΑ]. Το Εργαστήριο απέτισε φόρο τιμής.

5. ΕΓΚΑΤΑΣΤΑΣΗ ΑΞΙΩΜΑΤΙΚΩΝ (αν υπάρχει)
   Ο Σεβ∴ κάλεσε τους νέους Αξιωματικούς ενώπιον του Βωμού των
   Επισήμων Διαβεβαιώσεων, όπου έδωσαν τον καθορισμένο όρκο.

6. ΟΜΙΛΙΑ ΕΣΠΕΡΑΣ (τίτλος + περίληψη 5-8 προτάσεων σε σύγχρονη γλώσσα)

7. ΕΠΙ ΤΗΣ ΟΜΙΛΙΑΣ
   Λόγο πήραν κατά σειρά (κατώτερος → ανώτερος):
   [Κάθε παρέμβαση σε ξεχωριστή παράγραφο, 3-4 προτάσεων]

8. ΑΠΟΧΩΡΗΣΗ ΕΠΙΣΚΕΠΤΗ (αν υπάρχει)

9. ΕΠΙ ΤΗΣ ΕΥΗΜΕΡΙΑΣ (αν υπάρχει)
   Σύντομη περίληψη σε σύγχρονη γλώσσα.

10. ΣΑΚΟΣ ΠΡΟΤΑΣΕΩΝ (αν υπάρχει)

ΤΙ ΝΑ ΜΗΝ ΣΥΜΠΕΡΙΛΑΒΕΙΣ στο "κείμενο_πρακτικών":
• ΜΗΝ γράφεις ΚΛΕΙΣΙΜΟ — γίνεται αυτόματα
• ΜΗΝ γράφεις υπογραφές
• ΜΗΝ γράφεις "Μη υπάρχοντος ετέρου θέματος..." — γίνεται αυτόματα
• ΜΗΝ γράφεις "Είπον Σεβ∴ Διδ∴" — γίνεται αυτόματα
• ΜΗΝ γράφεις "Ο Κορμός εβλάστησεν..." — γίνεται αυτόματα

════════════════════════════════════════════════════════════════
ΑΦΗΓΗΜΑΤΙΚΗ ΡΟΗ
════════════════════════════════════════════════════════════════

ΑΡΧΗ ΚΕΙΜΕΝΟΥ — ξεκίνα με εισαγωγικό εδάφιο:
  α) Παρόντες: «Παρευρέθηκαν [ΑΡΙΘΜΟΣ ΟΛΟΓΡΑΦΩΣ] ([ΑΡΙΘΜΟΣ]) Αδδ∴,
     που υπέγραψαν το Βιβλίον των Παρουσιών.»
  β) Θέσεις απόντων: «Τις θέσεις των απόντων Αξιωματικών ανέλαβαν:
     [ΑΞΙΩΜΑ] ο [ΟΝΟΜΑ]...»
  γ) Ανατολή: «Την Ανατολή κοσμούσαν ο [ΟΝΟΜΑ] και ο [ΟΝΟΜΑ].»

Παράδειγμα:
---
ΠΑΡΟΝΤΕΣ — ΘΕΣΕΙΣ ΑΞΙΩΜΑΤΙΚΩΝ
Παρευρέθηκαν δώδεκα (12) Αδδ∴, που υπέγραψαν το Βιβλίον των Παρουσιών.
Τις θέσεις των απόντων Αξιωματικών ανέλαβαν: Ρήτωρ ο πρ∴ Σεβ∴ Θεόδωρος
Κεσσανής, Α΄ Επόπτης ο πρ∴ Σεβ∴ Δημήτριος Γεωργακόπουλος.
Την Ανατολή κοσμούσαν ο πρ∴ Σεβ∴ Θεόδωρος Κεσσανής και ο Ένδοξος Αδ∴
Μέγας Στεγαστής Δημήτριος Δενεδιός.
---

ΜΕΙΩΣΗ ΕΠΑΝΑΛΗΨΕΩΝ «Ο Φιλτ∴ Αδ∴ Σεβ∴»:
• Χρησιμοποίησε «Ο Φιλτ∴ Αδ∴ Σεβ∴» ΜΟΝΟ στην πρώτη αναφορά κάθε ενότητας.
• Στη συνέχεια: «Ο Σεβ∴», «Στη συνέχεια», «Κατόπιν», «Ακολούθως».

════════════════════════════════════════════════════════════════
ΚΡΙΣΙΜΟ — ΜΟΡΦΗ ΑΠΑΝΤΗΣΗΣ
════════════════════════════════════════════════════════════════
Επέστρεψε ΑΠΟΚΛΕΙΣΤΙΚΑ ένα valid JSON object.
• Μην γράψεις ΤΙΠΟΤΑ πριν το {{
• Μην γράψεις ΤΙΠΟΤΑ μετά το }}
• Χωρίς markdown, χωρίς backticks
• Στο "κείμενο_πρακτικών" χρησιμοποίησε \\n\\n για αλλαγή παραγράφου
• Στο "κορμός_ολογράφως" γράψε π.χ. "τριάκοντα και πέντε δεκάτων"

Δομή JSON:
{{
  "ημερομηνία": "DD/MM/YYYY",
  "ημέρα": "π.χ. Τετάρτη",
  "βαθμός_γενική": "Μαθητού",
  "τόπος": "τον Τεκτ∴ Ναόν",
  "σεβάσμιος": "Ονοματεπώνυμο",
  "παρόντες_αριθμός": 0,
  "παρόντες_ολογράφως": "π.χ. δώδεκα",
  "ημερησία_διάταξη": ["θέμα 1", "θέμα 2"],
  "χαιρετισμοί_κατά_σειράν": [
    "Ένδοξε Μέγ∴ Αξ∴ Δημήτριος Δενεδιός — Μέγας Στεγαστής Μ∴Σ∴Τ∴Ε∴",
    "Πρώην Σεβάσμιος Ελευθέριος Κεσσανής — πρώην Σεβ∴ Σ∴ Στ∴"
  ],
  "ομιλητές_κατά_σειράν": [
    "Αδ∴ Μαθητής Χρήστος Ιωάννου — σχόλια επί ομιλίας",
    "Αδ∴ Εταίρος Νίκος Παππάς — παρέμβαση",
    "Σεβ∴ Διδ∴ Γεώργιος Παρίσης — καλωσόρισμα και έναρξη"
  ],
  "κείμενο_πρακτικών": "ΠΛΗΡΕΙΣ ΠΑΡΑΓΡΑΦΟΙ ΜΕ \\n\\n ΜΕΤΑΞΥ ΤΟΥΣ",
  "αποφάσεις": ["απόφαση 1 αν υπάρχει"],
  "κορμός_αγαθοεργίας": 0.0,
  "κορμός_ολογράφως": "ολογράφως π.χ. τριάκοντα",
  "γραμματεύς": "Ονοματεπώνυμο νέου Γραμματέα",
  "ρήτωρ": "Ονοματεπώνυμο Ρήτορα"
}}
""".strip()


# ══════════════════════════════════════════════════════════════
# ΚΑΝΟΝΙΚΟΠΟΙΗΣΗ ΤΕΚΤΟΝΙΚΟΥ ΚΕΙΜΕΝΟΥ
# ══════════════════════════════════════════════════════════════
_TRIA_REPLACEMENTS = [
    (r"Φιλτ\.?\s*Αδ\.?\s*Σεβ\.?", "Φιλτ∴ Αδ∴ Σεβ∴"),
    (r"Φιλτάτ\w*\s+Αδ\w*\s+Σεβ\w*", "Φιλτ∴ Αδ∴ Σεβ∴ Διδ∴"),
    (r"\bΑδδ\b(?!∴)", "Αδδ∴"),
    (r"\bΑδ\b(?!∴|ε|α|ο|ι|η|ω|υ|ά|έ|ό|ί|ή|ώ|ύ|λ|φ)", "Αδ∴"),
    (r"\bΣεβ\b(?!∴|ά|α|ε|ο)", "Σεβ∴"),
    (r"\bΔιδ\b(?!∴|ά|α|ε|ο|ι|ή)", "Διδ∴"),
    (r"\bΣ\b\.?\s*Στ\b\.?", "Σ∴ Στ∴"),
    (r"\bΦιλτ\b(?!∴)", "Φιλτ∴"),
    (r"\bΤεκτ\b(?!∴)", "Τεκτ∴"),
    (r"\bΒαθμ\b(?!∴)", "Βαθμ∴"),
    (r"\bΓραμμ\b(?!∴)", "Γραμμ∴"),
    (r"\bΡήτ\b(?!∴)", "Ρήτ∴"),
    (r"\bΜέγ\b(?!∴|α|ε|ο|ι)", "Μέγ∴"),
    (r"\bΑξ\b(?!∴|ι|η|ω)", "Αξ∴"),
    (r"\bΑν\b\.?\s*Αθ\b\.?", "Αν∴ Αθ∴"),
]

_HONORIFIC_REPLACEMENTS = [
    (r"Αιδεσιμ[∴\.ώτα]*\.?\s*πρ[∴\.ώην]*\.?\s*Σεβ[∴\.]*",
     "Πρώην Σεβάσμιος"),
    (r"Ένδοξος\s+Μέγ[∴\.]*\s*Αξ[∴\.]*",
     "Ένδοξε Μέγ∴ Αξ∴"),
    (r"Ενδοξότατος\b",  "Ενδοξότατε"),
    (r"Ενδοξότατoς\b",  "Ενδοξότατε"),
]


def _normalize_tektonic_text(text: str) -> str:
    if not text:
        return text
    import re as _re
    for pat, repl in _HONORIFIC_REPLACEMENTS:
        text = _re.sub(pat, repl, text, flags=_re.IGNORECASE)
    for pat, repl in _TRIA_REPLACEMENTS:
        text = _re.sub(pat, repl, text)
    return text


def _normalize_result_fields(result: dict) -> dict:
    text_fields = [
        "κείμενο_πρακτικών", "σεβάσμιος", "γραμματεύς", "ρήτωρ",
        "τόπος", "παρόντες_ολογράφως", "κορμός_ολογράφως",
    ]
    for field in text_fields:
        if isinstance(result.get(field), str):
            result[field] = _normalize_tektonic_text(result[field])
    for list_field in ["χαιρετισμοί_κατά_σειράν", "ομιλητές_κατά_σειράν",
                        "ημερησία_διάταξη", "αποφάσεις"]:
        if isinstance(result.get(list_field), list):
            result[list_field] = [
                _normalize_tektonic_text(item) if isinstance(item, str) else item
                for item in result[list_field]
            ]
    return result


def format_into_praktiko(
    transcript: str,
    context: str,
    source_label: str = "Ακατέργαστη μεταγραφή",
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:

    anthropic_key = get_anthropic_key()
    if not anthropic_key:
        return None, "❌ Δεν βρέθηκε ANTHROPIC_API_KEY στα Streamlit Secrets."

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=anthropic_key)
    except ImportError:
        return None, "❌ Προσθέστε `anthropic` στο requirements.txt."

    raw = ""
    try:
        _stream_placeholder = None
        try:
            import streamlit as _st
            _stream_placeholder = _st.empty()
        except Exception:
            pass

        raw_parts: List[str] = []
        with client.messages.stream(
            model=CLAUDE_MODEL,
            max_tokens=13000,  # ← μειώθηκε από 16000
            system=_SYSTEM_PROMPT,
            messages=[{
                "role": "user",
                "content": (
                    f"Πλαίσιο συνεδρίασης:\n{context or '-'}\n\n"
                    f"{source_label}:\n{transcript}"
                ),
            }],
        ) as stream:
            for text_chunk in stream.text_stream:
                raw_parts.append(text_chunk)
                if _stream_placeholder is not None:
                    _stream_placeholder.caption(
                        f"✍️ Σύνταξη πρακτικού… {sum(len(p) for p in raw_parts):,} χαρακτήρες"
                    )
        if _stream_placeholder is not None:
            _stream_placeholder.empty()
        raw = "".join(raw_parts).strip()

        if not raw:
            return None, (
                "❌ Ο Claude επέστρεψε κενή απάντηση. "
                "Δοκίμασε ξανά ή έλεγξε το API key."
            )

        result = _extract_json(raw)

        if result is None:
            st.warning(
                "⚠️ Το Claude δεν επέστρεψε καθαρό JSON. "
                "Το κείμενο μεταφέρθηκε στον editor. "
                f"Αρχή απάντησης: `{raw[:300]}`"
            )
            return _empty_result(transcript=transcript, raw_text=raw), (
                "⚠️ Ο Claude δεν επέστρεψε καθαρό JSON. "
                "Το κείμενο μπήκε στον editor για χειροκίνητη επεξεργασία."
            )

        # Post-process: κανονικοποίηση
        result = _normalize_result_fields(result)

        # Post-process: ταξινόμηση χαιρετισμών (κατά πρωτόκολλο προσφωνήσεων)
        if isinstance(result.get("χαιρετισμοί_κατά_σειράν"), list):
            result["χαιρετισμοί_κατά_σειράν"] = sort_officials_by_protocol(
                result["χαιρετισμοί_κατά_σειράν"]
            )

        # Post-process: ταξινόμηση ομιλητών (σειρά λήψης λόγου: κατώτερος → ανώτερος)
        if isinstance(result.get("ομιλητές_κατά_σειράν"), list):
            result["ομιλητές_κατά_σειράν"] = sort_speakers_by_omilion(
                result["ομιλητές_κατά_σειράν"]
            )

        result["μεταγραφή_λέξη_προς_λέξη"] = transcript
        return result, None

    except Exception as e:
        import anthropic as _anthropic

        if isinstance(e, _anthropic.RateLimitError):
            return None, (
                "❌ Rate limit Claude API. "
                "Περίμενε 1-2 λεπτά και δοκίμασε ξανά."
            )
        if isinstance(e, _anthropic.AuthenticationError):
            return None, (
                "❌ Λάθος ANTHROPIC_API_KEY. "
                "Έλεγξε τα Streamlit Secrets."
            )
        if isinstance(e, _anthropic.APIStatusError):
            return None, (
                f"❌ Claude API σφάλμα {e.status_code}: {e.message}\n\n"
                f"Βεβαιώσου ότι το model '{CLAUDE_MODEL}' είναι διαθέσιμο "
                "στο API key σου."
            )

        detail = f"\n\nΑπάντηση Claude (αρχή): `{raw[:300]}`" if raw else ""
        return None, f"❌ Σφάλμα σύνταξης πρακτικών: {type(e).__name__}: {e}{detail}"


# ══════════════════════════════════════════════════════════════
# PIPELINE FUNCTIONS
# ══════════════════════════════════════════════════════════════
def process_audio_to_praktiko(
    audio_bytes: bytes, ext: str, context: str,
    progress_cb: Optional[Callable] = None,
):
    if progress_cb:
        progress_cb(2, "🚀 Έναρξη επεξεργασίας…")
    transcript, warn = transcribe_audio(audio_bytes, ext, progress_cb)
    if not transcript:
        return None, warn or "❌ Δεν δημιουργήθηκε μεταγραφή."
    if progress_cb:
        progress_cb(82, "🧹 Καθαρισμός μεταγραφής…")
    transcript = clean_transcript(transcript)
    if progress_cb:
        progress_cb(88, "📝 Σύνταξη Πρακτικών με Claude…")
    result, err = format_into_praktiko(transcript, context)
    if progress_cb:
        progress_cb(100, "✅ Ολοκληρώθηκε.")
    if result and warn and warn.startswith("⚠️"):
        result["προειδοποίηση"] = warn
    return result, err


def process_docx_to_praktiko(
    docx_bytes: bytes, context: str,
    progress_cb: Optional[Callable] = None,
):
    if progress_cb:
        progress_cb(10, "📄 Ανάγνωση αρχείου Word…")
    text, err = extract_text_from_docx(docx_bytes)
    if err and not text:
        return None, err
    if progress_cb:
        progress_cb(40, f"✅ Εξήχθησαν {len(text):,} χαρακτήρες. Σύνταξη με Claude…")
    result, praktiko_err = format_into_praktiko(
        text, context, source_label="Κείμενο από αρχείο Word",
    )
    if progress_cb:
        progress_cb(100, "✅ Ολοκληρώθηκε.")
    if result and err:
        result["προειδοποίηση"] = err
    return result, praktiko_err


# ══════════════════════════════════════════════════════════════
# ΕΙΚΟΝΕΣ PDF
# ══════════════════════════════════════════════════════════════
_PDF_IMG_MASONIC  = "/tmp/masonic.jpg"
_PDF_IMG_ACROPOLIS = "/tmp/acropolis.jpg"


def _find_pdf_image(tmp_path: str, filename: str) -> Optional[str]:
    import os as _os
    if _os.path.exists(tmp_path):
        return tmp_path
    candidates = [
        _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), filename),
        _os.path.join(_os.getcwd(), filename),
        _os.path.join("/mount/src/grammateas/assets", filename),
    ]
    for c in candidates:
        if _os.path.exists(c):
            return c
    return None


def _ensure_pdf_images():
    import shutil as _sh
    _lookup = {
        _PDF_IMG_MASONIC: [
            "/mount/src/grammateas/assets/masonic.jpg",
            "/mount/src/grammateas/static/masonic.jpg",
            os.path.join(os.getcwd(), "assets", "masonic.jpg"),
            os.path.join(os.getcwd(), "masonic.jpg"),
        ],
        _PDF_IMG_ACROPOLIS: [
            "/mount/src/grammateas/assets/acropolis.jpg",
            "/mount/src/grammateas/static/acropolis.jpg",
            os.path.join(os.getcwd(), "assets", "acropolis.jpg"),
            os.path.join(os.getcwd(), "acropolis.jpg"),
        ],
    }
    for dest, sources in _lookup.items():
        if not os.path.exists(dest):
            for src_path in sources:
                if os.path.exists(src_path):
                    try:
                        _sh.copy2(src_path, dest)
                        break
                    except Exception:
                        pass

_ensure_pdf_images()


# ══════════════════════════════════════════════════════════════
# PDF GENERATOR
# ══════════════════════════════════════════════════════════════
def generate_praktiko_pdf(d: dict) -> io.BytesIO:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Table,
        Image as RLImage, KeepTogether,
    )

    fs, fsb, fr, frb = register_dejavu_fonts()
    cnvy  = colors.HexColor(NAVY)
    cgold = colors.HexColor(GOLD)
    cgrey = colors.HexColor("#888888")

    def S(name, **kw):
        return ParagraphStyle(name, **kw)

    H1   = S("H1",   fontName=fsb, fontSize=11, alignment=TA_CENTER, spaceAfter=1,  leading=14, textColor=cnvy)
    H2   = S("H2",   fontName=fs,  fontSize=9,  alignment=TA_CENTER, spaceAfter=1,  leading=12, textColor=cnvy)
    LDG  = S("LDG",  fontName=fsb, fontSize=10, alignment=TA_CENTER, spaceAfter=4,  leading=13)
    TTL  = S("TTL",  fontName=fsb, fontSize=13, alignment=TA_CENTER, spaceAfter=4,  spaceBefore=4,
             leading=17, textColor=cnvy)
    SEC  = S("SEC",  fontName=fsb, fontSize=10, alignment=TA_LEFT, spaceAfter=4, spaceBefore=10,
             leading=13, textColor=cnvy)
    BOD  = S("BOD",  fontName=fs,  fontSize=10.5, alignment=TA_JUSTIFY, spaceAfter=7, leading=16)
    BUL  = S("BUL",  fontName=fs,  fontSize=9.5, alignment=TA_LEFT, leftIndent=14, spaceAfter=3, leading=14)
    SML  = S("SML",  fontName=fs,  fontSize=7.5, alignment=TA_CENTER, textColor=cgrey, spaceAfter=2)
    SGN  = S("SGN",  fontName=fs,  fontSize=10, alignment=TA_CENTER, spaceAfter=0, leading=14)
    SGNB = S("SGNB", fontName=fsb, fontSize=10, alignment=TA_CENTER, spaceAfter=0, leading=14)
    IPO  = S("IPO",  fontName=fs,  fontSize=10, alignment=TA_RIGHT, spaceAfter=4, textColor=cnvy)

    def xe(t):
        return str(t or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    βαθμ = d.get("βαθμός_γενική", "Μαθητού") or "Μαθητού"
    ημερ = d.get("ημερομηνία", "") or ""
    σεβ  = d.get("σεβάσμιος", "") or ""
    γραμ = d.get("γραμματεύς", "") or ""
    ρητ  = d.get("ρήτωρ", "") or ""

    story: list = []

    masonic_path = _find_pdf_image(_PDF_IMG_MASONIC, "masonic.jpg")
    if masonic_path:
        try:
            logo = RLImage(masonic_path, width=2.2*cm, height=2.2*cm)
            logo.hAlign = "CENTER"
            story.append(logo)
            story.append(Spacer(1, 0.2*cm))
        except Exception:
            pass

    story += [
        Paragraph("Ε∴Δ∴Τ∴Μ∴Α∴Τ∴Σ∴", H1),
        Paragraph("Εν Ονόματι και Υπό την Αιγίδα", H2),
        Paragraph("της Μεγάλης Στοάς της Ελλάδος", H2),
        Paragraph("των Αρχαίων Ελευθέρων και Αποδεδεγμένων Τεκτόνων", H2),
        Spacer(1, 0.1*cm),
        Paragraph("Σ∴ Στ∴ ΑΚΡΟΠΟΛΙΣ υπ' αρ. 84 · εν Αν∴ Αθ∴", LDG),
        HRFlowable(width="100%", thickness=1.5, color=cnvy, spaceAfter=6),
        Paragraph(
            f"Πρακτικόν Συνεδρίας της <b>{xe(ημερ)}</b> εις Βαθμ∴ {xe(βαθμ[:3])}∴",
            TTL
        ),
        HRFlowable(width="100%", thickness=0.5, color=cgold, spaceAfter=8),
    ]

    acropolis_path = _find_pdf_image(_PDF_IMG_ACROPOLIS, "acropolis.jpg")
    if acropolis_path:
        try:
            acro = RLImage(acropolis_path, width=16*cm, height=5*cm)
            acro.hAlign = "CENTER"
            story.append(acro)
            story.append(Paragraph(
                "Σ∴ Στ∴ ΑΚΡΟΠΟΛΙΣ υπ' αρ. 84 · Αθήναι",
                S("CAP", fontName=fs, fontSize=7.5, alignment=TA_CENTER,
                  textColor=cgrey, spaceAfter=8, leading=10)
            ))
        except Exception:
            pass

    story.append(Spacer(1, 0.3*cm))

    body = d.get("κείμενο_πρακτικών", "") or ""

    παρ_αρ  = d.get("παρόντες_αριθμός", 0) or 0
    παρ_ολ  = d.get("παρόντες_ολογράφως", "") or ""
    if παρ_ολ and "ΠΑΡΟΝΤΕΣ" not in body[:200].upper():
        intro_lines = [
            f"Παρευρέθηκαν <b>{xe(παρ_ολ)} ({παρ_αρ})</b> Αδδ∴, "
            "που υπέγραψαν το Βιβλίον των Παρουσιών."
        ]
        story += [
            Paragraph("<b>ΠΑΡΟΝΤΕΣ — ΘΕΣΕΙΣ ΑΞΙΩΜΑΤΙΚΩΝ</b>", SEC),
            Paragraph(" ".join(intro_lines), BOD),
            Spacer(1, 0.1*cm),
        ]

    masonic_inserted = False

    paragraphs = [p.strip() for p in body.split("\n\n") if p.strip()]
    for idx, para in enumerate(paragraphs):
        lines = [l.strip() for l in para.split("\n") if l.strip()]
        if not lines:
            continue

        first_line = lines[0]
        is_header = (
            first_line == first_line.upper()
            and len(first_line) < 90
            and not first_line.endswith(".")
            and any(c.isalpha() for c in first_line)
        )

        if is_header:
            header_text = xe(first_line)
            rest_lines  = lines[1:]

            if (not masonic_inserted
                    and masonic_path
                    and "ΟΜΙΛΙΑ" in first_line):
                masonic_inserted = True
                try:
                    sym = RLImage(masonic_path, width=1.4*cm, height=1.4*cm)
                    sym_cell = [sym]
                    hdr_cell = [Paragraph(f"<b>{header_text}</b>", SEC)]
                    tbl = Table(
                        [[hdr_cell, sym_cell]],
                        colWidths=[13.5*cm, 1.5*cm],
                        hAlign="LEFT",
                    )
                    story.append(tbl)
                except Exception:
                    story.append(Paragraph(f"<b>{header_text}</b>", SEC))
            else:
                story.append(Paragraph(f"<b>{header_text}</b>", SEC))

            if rest_lines:
                story.append(Paragraph(xe(" ".join(rest_lines)), BOD))
        else:
            if all(l[:1] in ("-", "–", "•", "*") for l in lines):
                for ln in lines:
                    story.append(Paragraph(xe(ln), BUL))
            else:
                story.append(Paragraph(xe(para.replace("\n", " ")), BOD))

    κορμ = float(d.get("κορμός_αγαθοεργίας", 0) or 0)
    κολ  = d.get("κορμός_ολογράφως", "") or ""
    if κορμ:
        story.append(Paragraph(
            f"Ο Κορμός της Αγαθοεργίας εβλάστησεν "
            f"<b>{xe(κολ)} ({κορμ:.2f})</b> όστρακα.",
            BOD
        ))

    if σεβ:
        closing_1 = (
            f"Μη υπάρχοντος ετέρου θέματος, οι εργασίες έκλεισαν κανονικά υπό την "
            f"Σφύρα του Σεβ∴ Διδ∴ <b>{xe(σεβ)}</b>, με τους Αδδ∴ της Σ∴ Στ∴ ημών "
            f"ευχαριστημένους και ικανοποιημένους."
        )
    else:
        closing_1 = (
            "Μη υπάρχοντος ετέρου θέματος, οι εργασίες έκλεισαν κανονικά, "
            "με τους Αδδ∴ της Σ∴ Στ∴ ημών ευχαριστημένους και ικανοποιημένους."
        )
    closing_2 = (
        "Οι Αδδ∴, αφού διαβεβαίωσαν ότι θα τηρήσουν σιγή για τις Εργασίες, "
        "αποχώρησαν εν ειρήνη για το Ποτήριον της Αγάπης."
    )
    story += [
        Spacer(1, 0.35*cm),
        Paragraph(closing_1, BOD),
        Spacer(1, 0.1*cm),
        Paragraph(closing_2, BOD),
        Spacer(1, 0.25*cm),
        Paragraph("Είπον Σεβ∴ Διδ∴.", IPO),
        Spacer(1, 0.4*cm),
        HRFlowable(width="100%", thickness=0.5, color=cnvy, spaceAfter=14),
    ]

    def sig_col(title, name):
        return [
            Paragraph(title, SGN),
            Spacer(1, 1.0*cm),
            Paragraph(xe(name), SGNB),
        ]

    story.append(
        Table([[sig_col("Ο Σεβ∴ Διδ∴", σεβ)]],
              colWidths=[14*cm], hAlign="CENTER")
    )
    story.append(Spacer(1, 0.7*cm))
    story.append(
        Table(
            [[sig_col("Ο Γραμματεύς", γραμ), sig_col("Ο Ρήτωρ", ρητ)]],
            colWidths=[7*cm, 7*cm], hAlign="CENTER",
        )
    )

    story += [
        Spacer(1, 0.6*cm),
        HRFlowable(width="100%", thickness=0.3, color=colors.lightgrey),
        Paragraph(
            f"Αρ. Πρωτ.: {xe(d.get('αρ_πρωτ', ''))} · "
            f"Ημερομηνία: {xe(ημερ)} · Βαθμ∴: {xe(βαθμ)}",
            SML
        ),
    ]

    buf = io.BytesIO()
    SimpleDocTemplate(
        buf, pagesize=A4,
        rightMargin=2.5*cm, leftMargin=2.5*cm,
        topMargin=1.8*cm, bottomMargin=1.8*cm,
        title=f"Πρακτικό Σ∴ Στ∴ ΑΚΡΟΠΟΛΙΣ 84 — {ημερ}",
    ).build(story)
    buf.seek(0)
    return buf


# ══════════════════════════════════════════════════════════════
# EDITOR
# ══════════════════════════════════════════════════════════════
def show_editor(r: dict, key_prefix: str = "") -> dict:
    st.markdown("---")
    st.markdown("## ✏️ Επεξεργασία Πρακτικού")
    st.caption("Ελέγξτε και διορθώστε τα πεδία. Το AI βοηθά, αλλά ο Γραμματεύς κάνει τον τελικό έλεγχο.")

    c1, c2, c3 = st.columns(3)
    with c1:
        r["ημερομηνία"]    = st.text_input("Ημερομηνία (DD/MM/YYYY)", r.get("ημερομηνία", ""),           key=f"{key_prefix}dat")
        r["ημέρα"]         = st.text_input("Ημέρα",                    r.get("ημέρα", ""),               key=f"{key_prefix}day")
        r["βαθμός_γενική"] = st.text_input("Βαθμός γενική",            r.get("βαθμός_γενική", "Μαθητού"),key=f"{key_prefix}deg")
        r["τόπος"]         = st.text_input("Τόπος",                    r.get("τόπος", "τον Τεκτ∴ Ναόν"), key=f"{key_prefix}plc")
    with c2:
        r["σεβάσμιος"]  = st.text_input("Σεβ∴ Διδ∴",       r.get("σεβάσμιος", ""),  key=f"{key_prefix}sev")
        r["γραμματεύς"] = st.text_input("Γραμματεύς",       r.get("γραμματεύς", ""), key=f"{key_prefix}grm")
        r["ρήτωρ"]      = st.text_input("Ρήτωρ",            r.get("ρήτωρ", ""),      key=f"{key_prefix}rht")
        r["αρ_πρωτ"]    = st.text_input("Αρ. Πρωτοκόλλου", r.get("αρ_πρωτ", ""),   key=f"{key_prefix}prt")
    with c3:
        r["παρόντες_αριθμός"]   = st.number_input("Παρόντες (αριθμός)", 0, 300,
            int(r.get("παρόντες_αριθμός", 0) or 0), key=f"{key_prefix}parn")
        r["παρόντες_ολογράφως"] = st.text_input("Παρόντες (ολογράφως)", r.get("παρόντες_ολογράφως", ""), key=f"{key_prefix}paro")
        r["κορμός_αγαθοεργίας"] = st.number_input("Κορμός (€)", 0.0, 99999.0,
            float(r.get("κορμός_αγαθοεργίας", 0) or 0), step=1.0, format="%.2f", key=f"{key_prefix}kor")
        r["κορμός_ολογράφως"]   = st.text_input("Κορμός ολογράφως", r.get("κορμός_ολογράφως", ""), key=f"{key_prefix}koro")

    st.markdown("#### 📋 Ημερησία Διάταξη")
    agenda_raw = st.text_area("Ένα θέμα ανά γραμμή:",
        "\n".join(r.get("ημερησία_διάταξη", []) or []),
        height=90, label_visibility="collapsed", key=f"{key_prefix}agd")
    r["ημερησία_διάταξη"] = [l.strip() for l in agenda_raw.splitlines() if l.strip()]

    st.markdown("#### 🎩 Χαιρετισμοί κατά πρωτόκολλον (Εγκ. 27/2019)")
    st.caption(
        "Ένας ανά γραμμή. Μορφή: «Προσφώνηση Ονοματεπώνυμο — Αξίωμα»"
    )
    xairet_raw = st.text_area(
        "Χαιρετισμοί",
        "\n".join(r.get("χαιρετισμοί_κατά_σειράν", []) or []),
        height=130, label_visibility="collapsed", key=f"{key_prefix}xrt",
    )
    r["χαιρετισμοί_κατά_σειράν"] = [l.strip() for l in xairet_raw.splitlines() if l.strip()]

    col_sort, _ = st.columns([1, 3])
    with col_sort:
        if st.button("🔀 Αυτόματη ταξινόμηση χαιρετισμών",
                     key=f"{key_prefix}sort_xrt", use_container_width=True):
            r["χαιρετισμοί_κατά_σειράν"] = sort_officials_by_protocol(
                r["χαιρετισμοί_κατά_σειράν"]
            )
            st.success("✅ Η λίστα ταξινομήθηκε.")
            st.rerun()

    st.markdown("#### 🎤 Ομιλητές (σειρά λήψης λόγου: κατώτερος → ανώτερος)")
    st.caption(
        "Ένας ανά γραμμή. Μορφή: «Αξίωμα Ονοματεπώνυμο — θέμα». "
        "Σειρά: Μαθηταί → Εταίροι → Διδάσκαλοι → Αξιωματικοί → Σεβάσμιοι → Μέγ∴ Διδ∴"
    )
    omil_raw = st.text_area(
        "Ομιλητές",
        "\n".join(r.get("ομιλητές_κατά_σειράν", []) or []),
        height=110, label_visibility="collapsed", key=f"{key_prefix}oml",
    )
    r["ομιλητές_κατά_σειράν"] = [l.strip() for l in omil_raw.splitlines() if l.strip()]

    col_sort2, _ = st.columns([1, 3])
    with col_sort2:
        if st.button("🔀 Αυτόματη ταξινόμηση ομιλητών",
                     key=f"{key_prefix}sort_oml", use_container_width=True):
            r["ομιλητές_κατά_σειράν"] = sort_speakers_by_omilion(
                r["ομιλητές_κατά_σειράν"]
            )
            st.success("✅ Η λίστα ταξινομήθηκε.")
            st.rerun()

    st.markdown("#### 📄 Κείμενο Πρακτικών")
    r["κείμενο_πρακτικών"] = st.text_area("Κείμενο Πρακτικών",
        r.get("κείμενο_πρακτικών", ""),
        height=550, label_visibility="collapsed", key=f"{key_prefix}bdy")
    return r


# ══════════════════════════════════════════════════════════════
# UI HELPERS
# ══════════════════════════════════════════════════════════════
def render_meeting_fields(prefix: str):
    ca, cb, cc = st.columns(3)
    with ca:
        sel_βαθμ = st.selectbox("Βαθμός", list(ΒΑΘΜΟΙ_GEN.keys()), key=f"{prefix}_βαθμ")
        sel_ημερ = st.date_input("Ημερομηνία", value=date.today(), key=f"{prefix}_ημερ")
    with cb:
        sel_σεβ  = st.text_input("Σεβ∴ Διδ∴",  placeholder="Όνομα Επώνυμο", key=f"{prefix}_σεβ")
        sel_γραμ = st.text_input("Γραμματεύς", placeholder="Όνομα Επώνυμο", key=f"{prefix}_γραμ")
    with cc:
        sel_ρητ   = st.text_input("Ρήτωρ",   placeholder="Όνομα Επώνυμο", key=f"{prefix}_ρητ")
        sel_extra = st.text_area("Επιπλέον πλαίσιο για AI",
            placeholder="π.χ. παρόντες, θέματα, ονόματα ομιλητών, ποσό κορμού κλπ.",
            height=68, key=f"{prefix}_extra")
    return sel_βαθμ, sel_ημερ, sel_σεβ, sel_γραμ, sel_ρητ, sel_extra


def build_ctx(sel_βαθμ, sel_ημερ, sel_σεβ, sel_γραμ, sel_ρητ, sel_extra) -> str:
    return (
        f"Βαθμός: {sel_βαθμ}\n"
        f"Βαθμός σε γενική: {ΒΑΘΜΟΙ_GEN[sel_βαθμ]}\n"
        f"Ημερομηνία: {sel_ημερ.strftime('%d/%m/%Y')}\n"
        f"Σεβ∴ Διδ∴: {sel_σεβ}\n"
        f"Γραμματεύς: {sel_γραμ}\n"
        f"Ρήτωρ: {sel_ρητ}\n"
        f"Επιπλέον πληροφορίες: {sel_extra or '-'}"
    )


def finalize_result(result, sel_σεβ, sel_γραμ, sel_ρητ, sel_βαθμ, sel_ημερ):
    for k, v in [("σεβάσμιος", sel_σεβ), ("γραμματεύς", sel_γραμ), ("ρήτωρ", sel_ρητ)]:
        if not result.get(k) and v:
            result[k] = v
    if not result.get("βαθμός_γενική"):
        result["βαθμός_γενική"] = ΒΑΘΜΟΙ_GEN[sel_βαθμ]
    if not result.get("ημερομηνία"):
        result["ημερομηνία"] = sel_ημερ.strftime("%d/%m/%Y")
    result.setdefault("χαιρετισμοί_κατά_σειράν", [])
    result.setdefault("ομιλητές_κατά_σειράν", [])
    return result


def render_pdf_section(edited: dict, key_prefix: str):
    st.markdown("---")
    st.markdown("### Βήμα · Δημιουργία PDF")
    col_gen, col_dl = st.columns(2)
    with col_gen:
        if st.button("📄 Δημιουργία PDF Πρακτικού", type="primary",
                     use_container_width=True, key=f"{key_prefix}_genpdf"):
            with st.spinner("Δημιουργία PDF…"):
                try:
                    pdf = generate_praktiko_pdf(edited)
                    st.session_state[f"{key_prefix}_pdf_bytes"] = pdf.getvalue()
                    st.session_state[f"{key_prefix}_pdf_label"] = (
                        edited.get("ημερομηνία", "") or str(date.today())
                    ).replace("/", "_")
                    st.success("✅ PDF έτοιμο.")
                except Exception as e:
                    st.error(f"❌ Σφάλμα δημιουργίας PDF: {e}")
    with col_dl:
        pdf_key = f"{key_prefix}_pdf_bytes"
        if pdf_key in st.session_state:
            lbl = st.session_state.get(f"{key_prefix}_pdf_label", date.today())
            st.download_button(
                "⬇️ Λήψη PDF — Πρακτικό Συνεδρίασης",
                data=st.session_state[pdf_key],
                file_name=f"πρακτικό_{lbl}.pdf",
                mime="application/pdf",
                use_container_width=True,
                key=f"{key_prefix}_dlpdf",
            )


# ══════════════════════════════════════════════════════════════
# UI — ΚΑΡΤΕΛΕΣ
# ══════════════════════════════════════════════════════════════
tab_audio, tab_word, tab_help = st.tabs([
    "🎵 Ηχογράφηση → Πρακτικά",
    "📄 Word → Πρακτικά",
    "ℹ️ Οδηγίες & Ρυθμίσεις",
])

# ──────────────────────────────────────────────────────────────
# TAB 1: ΗΧΟΓΡΑΦΗΣΗ
# ──────────────────────────────────────────────────────────────
with tab_audio:
    st.markdown("### Βήμα 1 · Στοιχεία Συνεδρίασης")
    a_βαθμ, a_ημερ, a_σεβ, a_γραμ, a_ρητ, a_extra = render_meeting_fields("aud")

    st.markdown("---")
    st.markdown("### Βήμα 2 · Αρχείο Ηχογράφησης")
    audio_file = st.file_uploader(
        f"Ανεβάστε αρχείο ήχου ({', '.join(SUPPORTED)}) — max {MAX_MB_RAW}MB",
        type=SUPPORTED, key="aud_uploader",
    )
    if audio_file:
        raw_bytes = audio_file.getvalue()
        size_mb   = mb_size(raw_bytes)
        ext       = audio_file.name.rsplit(".", 1)[-1].lower()
        show_audio_preview = st.checkbox("🎧 Εμφάνιση audio player", value=False)
        if show_audio_preview:
            with st.expander("🎧 Προεπισκόπηση", expanded=True):
                st.audio(raw_bytes, format=f"audio/{ext}")
        if size_mb > MAX_MB_RAW:
            st.error(f"⛔ {size_mb:.1f}MB > {MAX_MB_RAW}MB")
        else:
            st.success(f"✅ {audio_file.name} — {size_mb:.1f}MB")
            st.session_state["aud_ready_audio"] = raw_bytes
            st.session_state["aud_ready_ext"]   = ext

    st.markdown("---")
    st.markdown("### Βήμα 3 · Μεταγραφή & Σύνταξη Πρακτικών")
    aud_ready = "aud_ready_audio" in st.session_state
    if not aud_ready:
        st.info("📌 Ανεβάστε πρώτα αρχείο ηχογράφησης.")

    if st.button("🎧 Μεταγραφή & Σύνταξη Πρακτικών", type="primary",
                 use_container_width=True, disabled=not aud_ready, key="aud_run"):
        ctx = build_ctx(a_βαθμ, a_ημερ, a_σεβ, a_γραμ, a_ρητ, a_extra)
        st.session_state["aud_last_βαθμ"] = a_βαθμ
        st.session_state["aud_last_ημερ"] = a_ημερ.strftime("%d/%m/%Y")
        progress_bar = st.progress(0)
        status_text  = st.empty()

        def aud_cb(pct, msg):
            progress_bar.progress(min(max(int(pct), 0), 100))
            status_text.info(msg)

        aud_cb(1, f"🚀 Επεξεργασία {mb_size(st.session_state['aud_ready_audio']):.1f}MB…")
        try:
            result, err = process_audio_to_praktiko(
                st.session_state["aud_ready_audio"],
                st.session_state["aud_ready_ext"],
                ctx, progress_cb=aud_cb,
            )
        except Exception as e:
            result, err = None, f"❌ Σφάλμα: {e}"

        status_text.empty()
        progress_bar.progress(100)
        if err and not result:
            st.error(err)
        elif result:
            if err:
                st.warning(err)
            st.session_state["aud_praktiko"] = finalize_result(
                result, a_σεβ, a_γραμ, a_ρητ, a_βαθμ, a_ημερ)
            st.session_state.pop("aud_editable_raw", None)
            st.success("✅ Έτοιμο.")

    if "aud_praktiko" in st.session_state:
        raw_tr = st.session_state["aud_praktiko"].get("μεταγραφή_λέξη_προς_λέξη", "")
        if raw_tr:
            with st.expander("📄 Ακατέργαστη μεταγραφή", expanded=False):
                edit_limit = 50000
                if "aud_editable_raw" not in st.session_state:
                    st.session_state["aud_editable_raw"] = raw_tr[:edit_limit]
                edited_raw = st.text_area(
                    "Μεταγραφή", st.session_state["aud_editable_raw"],
                    height=400, label_visibility="collapsed", key="aud_raw_ta",
                )
                st.session_state["aud_editable_raw"] = edited_raw
                st.session_state["aud_praktiko"]["μεταγραφή_λέξη_προς_λέξη"] = edited_raw
                if len(raw_tr) > edit_limit:
                    st.warning("Εμφανίζονται οι πρώτοι 50.000 χαρακτήρες.")
                if st.button("🔄 Ενημέρωση Πρακτικού από διορθωμένη μεταγραφή",
                             use_container_width=True, key="aud_reformat"):
                    ctx2 = (
                        f"Βαθμός: {st.session_state.get('aud_last_βαθμ', '')}\n"
                        f"Ημερομηνία: {st.session_state.get('aud_last_ημερ', '')}\n"
                        "Επιπλέον: διορθωμένη μεταγραφή από τον χρήστη"
                    )
                    with st.spinner("Σύνταξη νέου πρακτικού…"):
                        upd, ue = format_into_praktiko(edited_raw, ctx2)
                    if ue and not upd:
                        st.error(ue)
                    elif upd:
                        st.session_state["aud_praktiko"].update(upd)
                        st.success("✅ Ενημερώθηκε.")
                st.download_button("⬇️ Λήψη μεταγραφής .txt",
                    raw_tr.encode("utf-8"),
                    f"μεταγραφή_{date.today()}.txt", "text/plain", key="aud_dl_txt")

        edited_a = show_editor(st.session_state["aud_praktiko"].copy(), key_prefix="ae_")
        render_pdf_section(edited_a, "aud")


# ──────────────────────────────────────────────────────────────
# TAB 2: WORD → ΠΡΑΚΤΙΚΑ
# ──────────────────────────────────────────────────────────────
with tab_word:
    st.markdown("### Βήμα 1 · Στοιχεία Συνεδρίασης")
    w_βαθμ, w_ημερ, w_σεβ, w_γραμ, w_ρητ, w_extra = render_meeting_fields("wrd")

    st.markdown("---")
    st.markdown("### Βήμα 2 · Αρχείο Word (.docx)")
    st.caption("Ανεβάστε **.docx** — σημειώσεις, προσχέδιο ή ακατέργαστο κείμενο.")
    word_file = st.file_uploader("Ανεβάστε αρχείο .docx — max 50MB",
                                  type=["docx"], key="wrd_uploader")
    if word_file:
        wrd_bytes = word_file.getvalue()
        wrd_mb    = mb_size(wrd_bytes)
        if wrd_mb > 50:
            st.error(f"⛔ {wrd_mb:.1f}MB > 50MB")
        else:
            st.success(f"✅ {word_file.name} — {wrd_mb:.1f}MB")
            st.session_state["wrd_ready_bytes"] = wrd_bytes
            st.session_state["wrd_ready_name"]  = word_file.name

    st.markdown("---")
    st.markdown("### Βήμα 3 · Σύνταξη Πρακτικών")
    wrd_ready = "wrd_ready_bytes" in st.session_state
    if not wrd_ready:
        st.info("📌 Ανεβάστε πρώτα αρχείο .docx.")

    if st.button("📄 Ανάγνωση Word & Σύνταξη Πρακτικών", type="primary",
                 use_container_width=True, disabled=not wrd_ready, key="wrd_run"):
        ctx = build_ctx(w_βαθμ, w_ημερ, w_σεβ, w_γραμ, w_ρητ, w_extra)
        st.session_state["wrd_last_βαθμ"] = w_βαθμ
        st.session_state["wrd_last_ημερ"] = w_ημερ.strftime("%d/%m/%Y")
        progress_bar = st.progress(0)
        status_text  = st.empty()

        def wrd_cb(pct, msg):
            progress_bar.progress(min(max(int(pct), 0), 100))
            status_text.info(msg)

        try:
            result, err = process_docx_to_praktiko(
                st.session_state["wrd_ready_bytes"], ctx, progress_cb=wrd_cb)
        except Exception as e:
            result, err = None, f"❌ Σφάλμα: {e}"

        status_text.empty()
        progress_bar.progress(100)
        if err and not result:
            st.error(err)
        elif result:
            if err:
                st.warning(err)
            st.session_state["wrd_praktiko"] = finalize_result(
                result, w_σεβ, w_γραμ, w_ρητ, w_βαθμ, w_ημερ)
            st.success("✅ Έτοιμο.")

    if "wrd_praktiko" in st.session_state:
        raw_wrd = st.session_state["wrd_praktiko"].get("μεταγραφή_λέξη_προς_λέξη", "")
        if raw_wrd:
            with st.expander("📄 Κείμενο που εξήχθη από το Word", expanded=False):
                st.text_area("Εξαχθέν κείμενο", raw_wrd, height=300,
                             label_visibility="collapsed", key="wrd_raw_view")
                if st.button("🔄 Επανασύνταξη Πρακτικού",
                             use_container_width=True, key="wrd_reformat"):
                    ctx2 = (
                        f"Βαθμός: {st.session_state.get('wrd_last_βαθμ', '')}\n"
                        f"Ημερομηνία: {st.session_state.get('wrd_last_ημερ', '')}\n"
                        "Επιπλέον: επανασύνταξη από το ίδιο κείμενο Word"
                    )
                    with st.spinner("Επανασύνταξη…"):
                        upd, ue = format_into_praktiko(
                            raw_wrd, ctx2, source_label="Κείμενο από αρχείο Word")
                    if ue and not upd:
                        st.error(ue)
                    elif upd:
                        st.session_state["wrd_praktiko"].update(upd)
                        st.success("✅ Επανασυντάχθηκε.")
                st.download_button("⬇️ Λήψη εξαχθέντος κειμένου .txt",
                    raw_wrd.encode("utf-8"),
                    f"εξαχθέν_{date.today()}.txt", "text/plain", key="wrd_dl_txt")

        edited_w = show_editor(st.session_state["wrd_praktiko"].copy(), key_prefix="we_")
        render_pdf_section(edited_w, "wrd")


# ──────────────────────────────────────────────────────────────
# TAB 3: ΟΔΗΓΙΕΣ
# ──────────────────────────────────────────────────────────────
with tab_help:
    st.markdown(f"""
    ## Ροή εργασίας — Ηχογράφηση
    1. Συμπληρώνετε βαθμό, ημερομηνία και αξιωματικούς.
    2. Ανεβάζετε αρχείο ήχου (wav/mp3/m4a/ogg/webm/aac).
    3. Πατάτε **Μεταγραφή & Σύνταξη Πρακτικών**.
    4. Ελέγχετε/διορθώνετε την ακατέργαστη μεταγραφή.
    5. Διορθώνετε το πρακτικό στον editor.
    6. Δημιουργείτε PDF.

    ## Ροή εργασίας — Word
    1. Συμπληρώνετε βαθμό, ημερομηνία και αξιωματικούς.
    2. Ανεβάζετε αρχείο **.docx**.
    3. Πατάτε **Ανάγνωση Word & Σύνταξη Πρακτικών**.
    4. Ελέγχετε το εξαχθέν κείμενο.
    5. Διορθώνετε στον editor.
    6. Δημιουργείτε PDF.

    ## Μοντέλο Claude
    `{CLAUDE_MODEL}` · max_tokens: 13 000

    ## Πρωτόκολλο Τάξης Προσφωνήσεων (Εγκ. 27/2019 — Πίνακας Α)

    | # | Αξίωμα | Προσφώνηση |
    |---|--------|------------|
    | 1 | Μέγας Διδάσκαλος Μ∴Σ∴Τ∴Ε∴ | Ενδοξότατε Μέγ∴ Διδ∴ |
    | 2 | Επίτιμοι Μέγ∴ Διδάσκαλοι | Ενδοξότατε Επίτ∴ Μέγ∴ Διδ∴ |
    | 3 | Πρώην Μέγ∴ Διδάσκαλοι | Ενδοξότατε πρ∴ Μέγ∴ Διδ∴ |
    | 4 | Πρόσθετος Μέγ∴ Διδάσκαλος | Ενδοξότατε Πρόσθ∴ Μέγ∴ Διδ∴ |
    | 5 | Ένδοξοι Μέγ∴ Αξιωματικοί Συμβ∴ | Ένδοξε Μέγ∴ Αξ∴ |
    | 6 | Πρώην Μέγ∴ Αξιωματικοί Συμβ∴ | Ένδ∴ Αδ∴ πρ∴ Μέγ∴ Αξ∴ |
    | 7 | Επίτιμα Μέλη Μ∴Σ∴Τ∴Ε∴ | Επίτιμε |
    | 8 | Ενεργοί Κοσμήτορες | Αιδεσιμ∴ Κοσμ∴ |
    | 9 | Ομότιμοι Κοσμήτορες | Αιδεσιμ∴ ομότ∴ Κοσμ∴ |
    | 10 | Μέγ∴ Επιθεωρητής Στοάς | Σεβ∴ Μέγ∴ Επιθ∴ |
    | 11 | Σεβάσμιος εν ενεργεία | Σεβ∴ Διδ∴ |
    | 12 | Πρώην Σεβάσμιοι | Αιδεσιμ∴ πρ∴ Σεβ∴ |
    | 13+ | Αξιωματικοί & μέλη Στοάς | Αδ∴ |

    ## Σειρά Λήψης Λόγου (Επί Ομιλιών / Ευημερίας)

    | # | Κατηγορία | Θέση |
    |---|-----------|------|
    | 1 | Μαθηταί, μέλη άλλων Στοών | Βορράς |
    | 2 | Εταίροι, μέλη άλλων Στοών | Βορράς |
    | 3 | Διδάσκαλοι, μέλη άλλων Στοών | Μεσημβρία |
    | 4 | Αξιωματικοί Στοάς | Μεσημβρία |
    | 5 | Επί Τιμή Σεβάσμιοι | Αριστερά Σεβ. |
    | 6 | Πρώην Σεβάσμιοι / Επιθεωρηταί | Αριστερά Σεβ. |
    | 7 | Σεβάσμιοι | Δεξιά Σεβ. |
    | 8 | Ομότιμοι Κοσμήτορες | Αριστερά Σεβ. |
    | 9 | Κοσμήτορες | Δεξιά Σεβ. |
    | 10 | Μέγας Επιθεωρητής | Δεξιά Σεβ. |
    | 11 | Πρόσθετοι Μέγ. Αξιωματικοί | Δεξιά Σεβ. |
    | 12 | Επίτιμα Μέλη Μ.Σ.Τ.Ε. | Δεξιά Σεβ. |
    | 13 | Πρώην Μέγ. Αξιωματικοί | Αριστερά Σεβ. |
    | 14 | Μεγάλοι Αξιωματικοί | Δεξιά Σεβ. |
    | 15 | Πρόσθετος Μέγ. Διδάσκαλος | Δεξιά Σεβ. |
    | 16 | Πρώην Μέγ. Διδάσκαλοι | Αριστερά Σεβ. |
    | 17 | Επίτιμοι Μέγ. Διδάσκαλοι | Αριστερά Σεβ. |
    | 18 | Μέγας Διδάσκαλος | — |

    Ο Claude ταξινομεί αυτόματα. Στον editor υπάρχει κουμπί **🔀 Αυτόματη ταξινόμηση ομιλητών**.

    ## Streamlit Secrets
    ```toml
    [AI]
    OPENAI_API_KEY    = "sk-..."
    ANTHROPIC_API_KEY = "sk-ant-..."
    ```

    ## requirements.txt
    ```
    streamlit>=1.30
    reportlab>=4.0
    anthropic>=0.25
    openai>=1.50.0
    pydub>=0.25.1
    python-docx>=1.0.0
    ```

    ## packages.txt
    ```
    ffmpeg
    ```
    """)

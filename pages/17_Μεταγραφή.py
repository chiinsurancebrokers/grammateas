# -*- coding: utf-8 -*-
"""
Σελίδα 17 — Μεταγραφή Ηχογράφησης → Πρακτικά ΜΣΤΕ
         & Έγγραφο Word → Πρακτικά ΜΣΤΕ

Ροή Ηχογράφησης:
1. Upload αρχείου ήχου: wav/mp3/m4a/ogg/webm/aac
2. Μετατροπή/κανονικοποίηση σε MP3 mono 16kHz με pydub/ffmpeg
3. Αυτόματο split σε ασφαλή chunks με μικρό overlap
4. OpenAI transcription στα Ελληνικά με domain prompt
5. Καθαρισμός hallucinations / υποτίτλων / άχρηστων επαναλήψεων
6. Claude → σύνταξη επίσημων Πρακτικών σε JSON
7. Editor → PDF

Ροή Word:
1. Upload αρχείου .docx
2. Εξαγωγή κειμένου με python-docx
3. Claude → σύνταξη επίσημων Πρακτικών σε JSON
4. Editor → PDF
"""

import sys
sys.path.append("..")

import io
import json
import os
import re
from datetime import date
from typing import Callable, Optional, Tuple, List, Dict, Any

import streamlit as st

from modules.database import init_db

# ══════════════════════════════════════════════════════════════
# APP SETUP
# ══════════════════════════════════════════════════════════════
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

# ══════════════════════════════════════════════════════════════
# ΣΤΑΘΕΡΕΣ
# ══════════════════════════════════════════════════════════════
MAX_MB_RAW = 300
SUPPORTED = ["wav", "mp3", "m4a", "ogg", "webm", "aac"]

ΒΑΘΜΟΙ_GEN = {
    "Α' - Μαθητής": "Μαθητού",
    "Β' - Εταίρος": "Εταίρου",
    "Γ' - Διδάσκαλος": "Διδασκάλου",
}

NAVY = "#1a2a4a"
GOLD = "#b8960c"

CHUNK_SEC = 300
OVERLAP_SEC = 3
AUDIO_RATE = 16000
AUDIO_BITRATE = "32k"
MAX_OPENAI_CHUNK_MB = 24

TRANSCRIPTION_MODEL_PRIMARY = "gpt-4o-transcribe"
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
        audio = audio.set_channels(1)
        audio = audio.set_frame_rate(AUDIO_RATE)
        out_buf = io.BytesIO()
        audio.export(out_buf, format="mp3", bitrate=AUDIO_BITRATE,
                     parameters=["-ac", "1", "-ar", str(AUDIO_RATE)])
        out_buf.seek(0)
        return out_buf.read(), None
    except ImportError as e:
        return None, (
            "❌ Δεν φορτώθηκε το package `pydub`. "
            "Ελέγξτε ότι στο requirements.txt υπάρχει `pydub>=0.25.1`. "
            f"Λεπτομέρεια: {e}"
        )
    except Exception as e:
        return None, (
            "❌ Σφάλμα στη μετατροπή ήχου. "
            "Αν το αρχείο είναι από iPhone/M4A/AAC, ελέγξτε ότι στο packages.txt υπάρχει `ffmpeg`. "
            f"Λεπτομέρεια: {e}"
        )


def split_audio_to_chunks(audio_bytes: bytes) -> Tuple[List[bytes], Optional[str]]:
    try:
        from pydub import AudioSegment
        audio = AudioSegment.from_file(io.BytesIO(audio_bytes), format="mp3")
        chunk_ms = CHUNK_SEC * 1000
        overlap_ms = OVERLAP_SEC * 1000
        step_ms = max(chunk_ms - overlap_ms, 1)
        chunks: List[bytes] = []
        for start_ms in range(0, len(audio), step_ms):
            end_ms = min(start_ms + chunk_ms, len(audio))
            part = audio[start_ms:end_ms]
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
    """
    Εξάγει το πλήρες κείμενο από .docx αρχείο με python-docx.
    Διατηρεί παραγράφους, πίνακες και επικεφαλίδες με τη σωστή σειρά.
    """
    try:
        from docx import Document as DocxDocument
        from docx.oxml.ns import qn

        doc = DocxDocument(io.BytesIO(docx_bytes))
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

                text_parts = []
                for child in elem.iter(qn("w:t")):
                    if child.text:
                        text_parts.append(child.text)
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
                        parts = []
                        for t in cell.iter(qn("w:t")):
                            if t.text:
                                parts.append(t.text)
                        cell_texts.append("".join(parts).strip())
                    row_line = " | ".join(c for c in cell_texts if c)
                    if row_line:
                        lines.append(row_line)

        body = doc.element.body
        for child in body:
            process_element(child)

        full_text = "\n".join(lines).strip()

        if not full_text:
            return "", "⚠️ Το αρχείο Word δεν περιέχει αναγνώσιμο κείμενο."

        return full_text, None

    except ImportError:
        return "", (
            "❌ Δεν βρέθηκε το package `python-docx`. "
            "Προσθέστε `python-docx>=1.0.0` στο requirements.txt."
        )
    except Exception as e:
        return "", f"❌ Σφάλμα ανάγνωσης αρχείου Word: {e}"

# ══════════════════════════════════════════════════════════════
# TRANSCRIPTION CLEANING
# ══════════════════════════════════════════════════════════════
def clean_transcript(text: str) -> str:
    if not text:
        return ""
    junk_patterns = [
        r"Υπότιτλοι\s+AUTHORWAVE", r"Υποτιτλοι\s+AUTHORWAVE", r"AUTHORWAVE",
        r"Ευχαριστούμε πολύ που παρακολουθήσατε το βίντεο!?",
        r"Παρακολουθείτε και εγγραφείτε στο κανάλι μας.*?(?=\n|$)",
        r"www\.argirobarbarigou\.com",
        r"\bUSING\b", r"\bresolving\b", r"\bprogresses\b", r"\battendant\b",
    ]
    for pat in junk_patterns:
        text = re.sub(pat, " ", text, flags=re.IGNORECASE | re.MULTILINE)
    text = re.sub(r"(.{8,80}?)(\s+\1){2,}", r"\1", text, flags=re.IGNORECASE)
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"\n[ \t]+", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def remove_overlap_repetition(full_text: str) -> str:
    lines = [l.strip() for l in full_text.splitlines() if l.strip()]
    cleaned = []
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
        return f"[❌ Chunk {chunk_idx + 1}: Δεν βρέθηκε OPENAI_API_KEY στα Streamlit Secrets]"
    chunk_mb = mb_size(chunk)
    if chunk_mb > MAX_OPENAI_CHUNK_MB:
        return f"[❌ Chunk {chunk_idx + 1}: {chunk_mb:.1f}MB > {MAX_OPENAI_CHUNK_MB}MB]"
    try:
        from openai import OpenAI
        client = OpenAI(api_key=openai_key)
        audio_file = io.BytesIO(chunk)
        audio_file.name = f"chunk_{chunk_idx + 1}.mp3"
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
                return (f"[❌ Chunk {chunk_idx + 1}: Primary: {primary_error}. "
                        f"Fallback: {fallback_error}]")
        return clean_transcript(str(result))
    except ImportError:
        return f"[❌ Chunk {chunk_idx + 1}: Προσθέστε `openai` στο requirements.txt]"
    except Exception as e:
        return f"[❌ Chunk {chunk_idx + 1}: {e}]"


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
    n = len(chunks)
    transcripts, errors = [], []
    for i, chunk in enumerate(chunks):
        if progress_cb:
            progress_cb(15 + int(65 * (i / max(n, 1))),
                        f"🎧 Μεταγραφή τμήματος {i+1}/{n} — {mb_size(chunk):.1f}MB…")
        text = transcribe_chunk(chunk, i, n)
        if text:
            if text.startswith("[❌"):
                errors.append(text)
            transcripts.append(f"=== Τμήμα {i+1}/{n} ===\n{text}")
    full = remove_overlap_repetition(clean_transcript("\n\n".join(transcripts)))
    warnings = []
    if split_warning:
        warnings.append(split_warning)
    if errors:
        warnings.append("⚠️ Κάποια chunks δεν μεταγράφηκαν σωστά.")
    return full, "\n".join(warnings) if warnings else None

# ══════════════════════════════════════════════════════════════
# CLAUDE → ΠΡΑΚΤΙΚΑ
# ══════════════════════════════════════════════════════════════
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

    system = """
Είσαι Γραμματεύς-Σφραγιδοφύλαξ της Σ∴ Στ∴ ΑΚΡΟΠΟΛΙΣ υπ' αρ. 84.
Σου δίνεται κείμενο ελληνικής τεκτονικής συνεδρίασης (από ηχογράφηση ή από έγγραφο Word).
Στόχος σου είναι να συντάξεις επίσημα Πρακτικά ΜΣΤΕ.

Πολύ σημαντικό:
- Μην εφευρίσκεις ονόματα, ποσά, αποφάσεις ή αριθμούς παρόντων αν δεν υπάρχουν καθαρά.
- Αν κάτι δεν προκύπτει, άφησέ το κενό ή γράψε "Δεν προέκυψε σαφώς".
- Κράτα επίσημο, αρχαιοπρεπές, γραμματειακό ύφος.
- Για κείμενα από Word: κάνε περίληψη ομιλιών διατηρώντας το νόημα και τη δομή.
- Διόρθωσε εμφανή λάθη μόνο όταν το νόημα είναι σαφές.

Υποχρεωτική δομή κειμένου:
• Έναρξη
• Παρόντες
• Θέσεις αξιωματικών, εφόσον προκύπτουν
• Αλληλογραφία, εφόσον προκύπτει
• Επικύρωση προηγουμένων πρακτικών, εφόσον προκύπτει
• Εργασίες / Ομιλίες / Αποφάσεις
• Κεφάλαιον Αγαθοεργίας, εφόσον προκύπτει
• Κλείσιμο

Χρησιμοποίησε όπου ταιριάζει:
Σεβ∴ Διδ∴, Αδ∴, Αδδ∴, Σ∴ Στ∴, Βαθμ∴ Μαθ∴/Ετ∴/Διδ∴, Γραμμ∴, Ρήτ∴.

Επέστρεψε ΜΟΝΟ valid JSON, χωρίς markdown, χωρίς backticks, με ακριβώς αυτά τα keys:
{
  "ημερομηνία": "DD/MM/YYYY",
  "ημέρα": "",
  "βαθμός_γενική": "Μαθητού",
  "τόπος": "",
  "σεβάσμιος": "",
  "παρόντες_αριθμός": 0,
  "παρόντες_ολογράφως": "",
  "ημερησία_διάταξη": [],
  "κείμενο_πρακτικών": "",
  "αποφάσεις": [],
  "κορμός_αγαθοεργίας": 0.0,
  "κορμός_ολογράφως": "",
  "γραμματεύς": "",
  "ρήτωρ": ""
}
""".strip()

    try:
        msg = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=8000,
            system=system,
            messages=[{
                "role": "user",
                "content": (
                    f"Πλαίσιο συνεδρίασης από τη φόρμα:\n{context or '-'}\n\n"
                    f"{source_label}:\n{transcript}"
                ),
            }],
        )
        raw = msg.content[0].text if msg.content else ""
        clean = re.sub(r"^```(?:json)?\s*", "", raw.strip())
        clean = re.sub(r"\s*```$", "", clean)
        result = json.loads(clean)
        result["μεταγραφή_λέξη_προς_λέξη"] = transcript
        return result, None

    except json.JSONDecodeError:
        return {
            "ημερομηνία": "", "ημέρα": "", "βαθμός_γενική": "Μαθητού",
            "τόπος": "", "σεβάσμιος": "", "παρόντες_αριθμός": 0,
            "παρόντες_ολογράφως": "", "ημερησία_διάταξη": [],
            "κείμενο_πρακτικών": raw if "raw" in locals() else "",
            "αποφάσεις": [], "κορμός_αγαθοεργίας": 0.0,
            "κορμός_ολογράφως": "", "γραμματεύς": "", "ρήτωρ": "",
            "μεταγραφή_λέξη_προς_λέξη": transcript,
        }, "⚠️ Ο Claude δεν επέστρεψε καθαρό JSON. Το κείμενο μπήκε στον editor για χειροκίνητο έλεγχο."
    except Exception as e:
        return None, f"❌ Σφάλμα σύνταξης πρακτικών: {e}"


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
        progress_cb(88, "📝 Σύνταξη επίσημων Πρακτικών με Claude…")
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
    """Εξάγει κείμενο από .docx και συντάσσει πρακτικά με Claude."""
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
# PDF GENERATOR
# ══════════════════════════════════════════════════════════════
def generate_praktiko_pdf(d: dict) -> io.BytesIO:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Table
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    font_dir = os.path.join(base_dir, "fonts")
    fonts = {
        "DSS": "DejaVuSans.ttf", "DSSB": "DejaVuSans-Bold.ttf",
        "DSR": "DejaVuSerif.ttf", "DSB": "DejaVuSerif-Bold.ttf",
        "DSI": "DejaVuSerif-Italic.ttf",
    }
    for alias, filename in fonts.items():
        path = os.path.join(font_dir, filename)
        if alias not in pdfmetrics.getRegisteredFontNames() and os.path.exists(path):
            pdfmetrics.registerFont(TTFont(alias, path))

    fs  = "DSS"  if "DSS"  in pdfmetrics.getRegisteredFontNames() else "Helvetica"
    fsb = "DSSB" if "DSSB" in pdfmetrics.getRegisteredFontNames() else "Helvetica-Bold"
    fr  = "DSR"  if "DSR"  in pdfmetrics.getRegisteredFontNames() else "Helvetica"
    frb = "DSB"  if "DSB"  in pdfmetrics.getRegisteredFontNames() else "Helvetica-Bold"

    cnvy = colors.HexColor(NAVY)
    cgold = colors.HexColor(GOLD)

    def S(name, **kw):
        return ParagraphStyle(name, **kw)

    H1   = S("H1",   fontName=fsb, fontSize=12, alignment=TA_CENTER, spaceAfter=2,  leading=15)
    H2   = S("H2",   fontName=fs,  fontSize=10, alignment=TA_CENTER, spaceAfter=2,  leading=13)
    LDG  = S("LDG",  fontName=fsb, fontSize=10, alignment=TA_CENTER, spaceAfter=6,  leading=13)
    TTL  = S("TTL",  fontName=fsb, fontSize=11, alignment=TA_CENTER, spaceAfter=2,  spaceBefore=6, leading=15, textColor=cnvy)
    HDA  = S("HDA",  fontName=fsb, fontSize=10, alignment=TA_LEFT,   spaceAfter=4,  leading=13)
    BUL  = S("BUL",  fontName=fr,  fontSize=10, alignment=TA_LEFT,   leftIndent=20, spaceAfter=3,  leading=14)
    BOD  = S("BOD",  fontName=fr,  fontSize=10, alignment=TA_JUSTIFY, spaceAfter=6, leading=15)
    SML  = S("SML",  fontName=fr,  fontSize=8,  alignment=TA_CENTER, textColor=colors.grey, spaceAfter=2)
    SGN  = S("SGN",  fontName=fr,  fontSize=10, alignment=TA_CENTER, spaceAfter=0,  leading=14)
    SGNB = S("SGNB", fontName=frb, fontSize=10, alignment=TA_CENTER, spaceAfter=0,  leading=14)
    IPO  = S("IPO",  fontName=fr,  fontSize=10, alignment=TA_RIGHT,  spaceAfter=4)

    def xe(t):
        return str(t or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    story = [
        Paragraph("Ε∴Δ∴Τ∴Μ∴Α∴Τ∴Σ∴", H1),
        Spacer(1, 0.15 * cm),
        Paragraph("Εν Ονόματι και Υπό την Αιγίδα", H2),
        Paragraph("της Μεγάλης Στοάς της Ελλάδος", H2),
        Paragraph("των Αρχαίων Ελευθέρων και Αποδεδεγμένων Τεκτόνων", H2),
        Spacer(1, 0.1 * cm),
        Paragraph("Σ∴ Στ∴ ΑΚΡΟΠΟΛΙΣ υπ' αρ. 84       εν Αν∴Αθ∴", LDG),
        HRFlowable(width="100%", thickness=1.5, color=cnvy, spaceAfter=8),
    ]

    βαθμ = d.get("βαθμός_γενική", "Μαθητού") or "Μαθητού"
    ημερ = d.get("ημερομηνία", "") or ""
    story.append(Paragraph(f"Πρακτικόν Συνεδρίας της {xe(ημερ)} εις Βαθμ∴ {xe(βαθμ[:3])}∴", TTL))

    agenda = d.get("ημερησία_διάταξη", []) or []
    if agenda:
        story += [Spacer(1, 0.2 * cm), Paragraph("<b>Ημερησία Διάταξις:</b>", HDA)]
        for item in agenda:
            story.append(Paragraph(f"– {xe(item)}", BUL))
        story.append(Spacer(1, 0.2 * cm))

    story.append(HRFlowable(width="100%", thickness=0.5, color=cgold, spaceAfter=10))

    body = d.get("κείμενο_πρακτικών", "") or ""
    for para in body.split("\n\n"):
        para = para.strip()
        if not para:
            continue
        lines = [l.strip() for l in para.split("\n") if l.strip()]
        if lines and all(l[:1] in ("-", "–", "•", "*") for l in lines):
            for ln in lines:
                story.append(Paragraph(xe(ln), BUL))
        else:
            story.append(Paragraph(xe(para.replace("\n", " ")), BOD))

    κορμ = float(d.get("κορμός_αγαθοεργίας", 0) or 0)
    κολ  = d.get("κορμός_ολογράφως", "") or ""
    if κορμ:
        story.append(Paragraph(
            f"Εκ του Κορμού της Αγαθοεργίας εβλάστησαν <b>{xe(κολ)} ({κορμ:.2f})</b> όστρακα.", BOD))

    σεβ = d.get("σεβάσμιος", "") or ""
    closing = (
        f"Τέλος, οι Εργασίες έκλεισαν κανονικώς υπό την Σφύραν του Σεβ∴ Διδ∴ "
        f"<b>{xe(σεβ)}</b>, των Αδδ∴ της Σ∴ Στ∴ μας ευχαριστημένων και ικανοποιημένων."
        if σεβ else "Τέλος, οι Εργασίες έκλεισαν κανονικώς."
    )
    story += [
        Spacer(1, 0.3 * cm), Paragraph(closing, BOD),
        Spacer(1, 0.2 * cm), Paragraph("Είπον Σεβ∴ Διδ∴.", IPO),
        Spacer(1, 1.5 * cm),
    ]

    γραμ = d.get("γραμματεύς", "") or ""
    ρητ  = d.get("ρήτωρ", "") or ""

    def sig_col(title, name):
        return [Paragraph(title, SGN), Spacer(1, 1.2 * cm), Paragraph(xe(name), SGNB)]

    story.append(Table([[sig_col("Ο Σεβ∴ Διδ∴", σεβ)]], colWidths=[14 * cm], hAlign="CENTER"))
    story.append(Spacer(1, 0.8 * cm))
    story.append(Table(
        [[sig_col("Ο Γραμματεύς", γραμ), sig_col("Ο Ρήτωρ", ρητ)]],
        colWidths=[7 * cm, 7 * cm], hAlign="CENTER",
    ))
    story += [
        Spacer(1, 0.6 * cm),
        HRFlowable(width="100%", thickness=0.3, color=colors.lightgrey),
        Paragraph(
            f"Αρ. Πρωτ.: {xe(d.get('αρ_πρωτ', ''))} | Ημερομηνία: {xe(ημερ)} | Βαθμ∴: {xe(βαθμ)}",
            SML),
    ]

    buf = io.BytesIO()
    SimpleDocTemplate(buf, pagesize=A4,
                      rightMargin=2.5*cm, leftMargin=2.5*cm,
                      topMargin=2*cm, bottomMargin=2*cm,
                      title="Πρακτικό Συνεδρίασης ΑΚΡΟΠΟΛΙΣ 84").build(story)
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
        r["ημερομηνία"]    = st.text_input("Ημερομηνία (DD/MM/YYYY)", r.get("ημερομηνία", ""),  key=f"{key_prefix}dat")
        r["ημέρα"]         = st.text_input("Ημέρα",                    r.get("ημέρα", ""),        key=f"{key_prefix}day")
        r["βαθμός_γενική"] = st.text_input("Βαθμός γενική",            r.get("βαθμός_γενική", "Μαθητού"), key=f"{key_prefix}deg")
        r["τόπος"]         = st.text_input("Τόπος",                    r.get("τόπος", "τον Τεκτ∴ Ναόν"), key=f"{key_prefix}plc")
    with c2:
        r["σεβάσμιος"]  = st.text_input("Σεβ∴ Διδ∴",       r.get("σεβάσμιος", ""),  key=f"{key_prefix}sev")
        r["γραμματεύς"] = st.text_input("Γραμματεύς",       r.get("γραμματεύς", ""), key=f"{key_prefix}grm")
        r["ρήτωρ"]      = st.text_input("Ρήτωρ",            r.get("ρήτωρ", ""),      key=f"{key_prefix}rht")
        r["αρ_πρωτ"]    = st.text_input("Αρ. Πρωτοκόλλου", r.get("αρ_πρωτ", ""),   key=f"{key_prefix}prt")
    with c3:
        r["παρόντες_αριθμός"]  = st.number_input("Παρόντες (αριθμός)", 0, 300,
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

    st.markdown("#### 📄 Κείμενο Πρακτικών")
    r["κείμενο_πρακτικών"] = st.text_area("Κείμενο Πρακτικών",
        r.get("κείμενο_πρακτικών", ""),
        height=550, label_visibility="collapsed", key=f"{key_prefix}bdy")
    return r

# ══════════════════════════════════════════════════════════════
# HELPERS UI
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
        sel_ρητ   = st.text_input("Ρήτωρ",     placeholder="Όνομα Επώνυμο", key=f"{prefix}_ρητ")
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
        size_mb = mb_size(raw_bytes)
        ext = audio_file.name.rsplit(".", 1)[-1].lower()

        show_audio_preview = st.checkbox(
            "🎧 Εμφάνιση audio player", value=False,
            help="Για μεγάλα αρχεία, αφήστε το κλειστό όσο διορθώνετε τη μεταγραφή.",
        )
        if show_audio_preview:
            with st.expander("🎧 Προεπισκόπηση ηχογράφησης", expanded=True):
                st.warning("Για μεγάλα αρχεία, μην έχετε ανοιχτό ταυτόχρονα το audio player και την ακατέργαστη μεταγραφή.")
                st.audio(raw_bytes, format=f"audio/{ext}")

        if size_mb > MAX_MB_RAW:
            st.error(f"⛔ Το αρχείο είναι {size_mb:.1f}MB και ξεπερνά το όριο {MAX_MB_RAW}MB.")
        else:
            st.success(f"✅ {audio_file.name} — {size_mb:.1f}MB — έτοιμο για μεταγραφή.")
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

        aud_cb(1, f"🚀 Επεξεργασία αρχείου {mb_size(st.session_state['aud_ready_audio']):.1f}MB…")
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
            st.success("✅ Έτοιμο. Ελέγξτε/διορθώστε πρώτα την ακατέργαστη μεταγραφή.")

    if "aud_praktiko" in st.session_state:
        raw_tr = st.session_state["aud_praktiko"].get("μεταγραφή_λέξη_προς_λέξη", "")
        if raw_tr:
            with st.expander("📄 Ακατέργαστη μεταγραφή", expanded=False):
                edit_limit = 50000
                if "aud_editable_raw" not in st.session_state:
                    st.session_state["aud_editable_raw"] = raw_tr[:edit_limit]
                edited_raw = st.text_area(
                    "Ακατέργαστη μεταγραφή", st.session_state["aud_editable_raw"],
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
                        f"Επιπλέον: διορθωμένη μεταγραφή από τον χρήστη"
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
    st.caption(
        "Ανεβάστε αρχείο **.docx** — σημειώσεις, προσχέδιο ή ακατέργαστο κείμενο συνεδρίασης. "
        "Το κείμενο εξάγεται αυτόματα και ο Claude συντάσσει τα επίσημα Πρακτικά."
    )

    word_file = st.file_uploader("Ανεβάστε αρχείο .docx — max 50MB",
                                  type=["docx"], key="wrd_uploader")
    if word_file:
        wrd_bytes = word_file.getvalue()
        wrd_mb = mb_size(wrd_bytes)
        if wrd_mb > 50:
            st.error(f"⛔ Το αρχείο είναι {wrd_mb:.1f}MB και ξεπερνά το όριο 50MB.")
        else:
            st.success(f"✅ {word_file.name} — {wrd_mb:.1f}MB — έτοιμο για επεξεργασία.")
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
            st.success("✅ Έτοιμο. Ελέγξτε και διορθώστε τα πρακτικά στον editor.")

    if "wrd_praktiko" in st.session_state:
        raw_wrd = st.session_state["wrd_praktiko"].get("μεταγραφή_λέξη_προς_λέξη", "")
        if raw_wrd:
            with st.expander("📄 Κείμενο που εξήχθη από το Word", expanded=False):
                st.text_area("Εξαχθέν κείμενο", raw_wrd, height=300,
                             label_visibility="collapsed", key="wrd_raw_view",
                             help="Αυτό είναι το κείμενο που διάβασε ο Claude από το αρχείο σας.")
                if st.button("🔄 Επανασύνταξη Πρακτικού",
                             use_container_width=True, key="wrd_reformat"):
                    ctx2 = (
                        f"Βαθμός: {st.session_state.get('wrd_last_βαθμ', '')}\n"
                        f"Ημερομηνία: {st.session_state.get('wrd_last_ημερ', '')}\n"
                        f"Επιπλέον: επανασύνταξη από το ίδιο κείμενο Word"
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
    st.markdown("""
    ## Ροή εργασίας — Ηχογράφηση

    1. Συμπληρώνετε βαθμό, ημερομηνία και αξιωματικούς.
    2. Ανεβάζετε αρχείο ήχου (wav/mp3/m4a/ogg/webm/aac).
    3. Πατάτε **Μεταγραφή & Σύνταξη Πρακτικών**.
    4. Ελέγχετε/διορθώνετε την ακατέργαστη μεταγραφή.
    5. Διορθώνετε το πρακτικό στον editor.
    6. Δημιουργείτε PDF.

    ## Ροή εργασίας — Word

    1. Συμπληρώνετε βαθμό, ημερομηνία και αξιωματικούς.
    2. Ανεβάζετε αρχείο **.docx** (σημειώσεις, προσχέδιο, ακατέργαστο κείμενο).
    3. Πατάτε **Ανάγνωση Word & Σύνταξη Πρακτικών**.
    4. Ελέγχετε το εξαχθέν κείμενο.
    5. Διορθώνετε το πρακτικό στον editor.
    6. Δημιουργείτε PDF.

    ## Streamlit Secrets

    ```toml
    [AI]
    OPENAI_API_KEY = "sk-..."
    ANTHROPIC_API_KEY = "sk-ant-..."
    ```

    ## requirements.txt

    ```txt
    streamlit>=1.30
    pandas>=2.0
    plotly>=5.0
    reportlab>=4.0
    anthropic>=0.25
    openai>=1.50.0
    pydub>=0.25.1
    python-docx>=1.0.0
    ```

    ## packages.txt

    ```txt
    ffmpeg
    ```

    ## Συμβουλές για το αρχείο Word

    - Το .docx μπορεί να είναι απλές σημειώσεις, ακατέργαστο πρακτικό ή transcript.
    - Πίνακες, επικεφαλίδες και παράγραφοι αναγνωρίζονται αυτόματα.
    - Στο "Επιπλέον πλαίσιο" αναφέρετε αν το κείμενο χρειάζεται περίληψη ομιλιών.
    - Μετά τη σύνταξη μπορείτε να πατήσετε **Επανασύνταξη** χωρίς να ξανανεβάσετε αρχείο.

    ## Σημαντικές πρακτικές για καλύτερη μεταγραφή

    - Το κινητό να είναι κοντά στους ομιλητές.
    - Προτιμήστε WAV, M4A ή MP3 με καθαρό ήχο.
    - Μειώστε θόρυβο, μουσική και παράλληλες συζητήσεις.
    - Στο πεδίο "Επιπλέον πλαίσιο" γράψτε ονόματα, θέματα και γνωστούς όρους.
    """)

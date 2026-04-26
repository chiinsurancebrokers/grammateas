# -*- coding: utf-8 -*-
"""
Σελίδα 17 — Μεταγραφή Ηχογράφησης → Πρακτικά ΜΣΤΕ

Ροή:
1. Upload αρχείου ήχου: wav/mp3/m4a/ogg/webm/aac
2. Μετατροπή/κανονικοποίηση σε MP3 mono 16kHz με pydub/ffmpeg
3. Αυτόματο split σε ασφαλή chunks με μικρό overlap
4. OpenAI transcription στα Ελληνικά με domain prompt
5. Καθαρισμός hallucinations / υποτίτλων / άχρηστων επαναλήψεων
6. Claude → σύνταξη επίσημων Πρακτικών σε JSON
7. Editor → PDF
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

st.markdown("# 🎧 Ηχογράφηση → Πρακτικά ΜΣΤΕ")
st.caption("Ηχογράφηση → OpenAI transcription → Claude σύνταξη πρακτικών → επεξεργασία → PDF")

# Μικρός έλεγχος περιβάλλοντος για να μη βγάζει παραπλανητικά errors στο audio
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

# Ασφαλέστερες ρυθμίσεις για Streamlit Cloud / OpenAI audio upload
CHUNK_SEC = 300              # 5 λεπτά ανά chunk
OVERLAP_SEC = 3              # μικρό overlap για να μην κόβονται λέξεις
AUDIO_RATE = 16000           # speech-friendly sample rate
AUDIO_BITRATE = "32k"        # μικρότερο μέγεθος, αρκετό για speech
MAX_OPENAI_CHUNK_MB = 24      # κάτω από το όριο των 25MB

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
    """
    Μετατρέπει οποιοδήποτε supported audio σε MP3 mono 16kHz.
    Χρησιμοποιεί pydub/ffmpeg, πιο σταθερό από PyAV για Streamlit Cloud.
    """
    try:
        from pydub import AudioSegment

        audio = AudioSegment.from_file(io.BytesIO(audio_bytes), format=ext)

        # Κανονικοποίηση για ομιλία
        audio = audio.set_channels(1)
        audio = audio.set_frame_rate(AUDIO_RATE)

        out_buf = io.BytesIO()
        audio.export(
            out_buf,
            format="mp3",
            bitrate=AUDIO_BITRATE,
            parameters=["-ac", "1", "-ar", str(AUDIO_RATE)],
        )

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
            "Αν το αρχείο είναι από iPhone/M4A/AAC, ελέγξτε ότι στο packages.txt υπάρχει `ffmpeg` "
            "και κάντε Reboot το Streamlit app. "
            f"Λεπτομέρεια: {e}"
        )


def split_audio_to_chunks(audio_bytes: bytes) -> Tuple[List[bytes], Optional[str]]:
    """
    Σπάει το normalized MP3 σε chunks περίπου 5 λεπτών με μικρό overlap.
    Επιστρέφει chunks σε MP3 bytes.
    """
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
            part.export(
                out_buf,
                format="mp3",
                bitrate=AUDIO_BITRATE,
                parameters=["-ac", "1", "-ar", str(AUDIO_RATE)],
            )

            data = out_buf.getvalue()
            if len(data) > 5000:
                chunks.append(data)

        return chunks if chunks else [audio_bytes], None

    except ImportError as e:
        return [audio_bytes], (
            "⚠️ Δεν φορτώθηκε το `pydub`, οπότε δεν έγινε split. "
            f"Λεπτομέρεια: {e}"
        )
    except Exception as e:
        return [audio_bytes], (
            "⚠️ Δεν έγινε σωστό split. Θα γίνει προσπάθεια αποστολής ως ένα αρχείο. "
            "Αν πρόκειται για iPhone/M4A/AAC, ελέγξτε το `ffmpeg` στο packages.txt. "
            f"Λεπτομέρεια: {e}"
        )

# ══════════════════════════════════════════════════════════════
# TRANSCRIPTION CLEANING
# ══════════════════════════════════════════════════════════════
def clean_transcript(text: str) -> str:
    """Καθαρίζει συχνά hallucinations από ελληνικά transcriptions."""
    if not text:
        return ""

    junk_patterns = [
        r"Υπότιτλοι\s+AUTHORWAVE",
        r"Υποτιτλοι\s+AUTHORWAVE",
        r"AUTHORWAVE",
        r"Ευχαριστούμε πολύ που παρακολουθήσατε το βίντεο!?",
        r"Παρακολουθείτε και εγγραφείτε στο κανάλι μας.*?(?=\n|$)",
        r"www\.argirobarbarigou\.com",
        r"\bUSING\b",
        r"\bresolving\b",
        r"\bprogresses\b",
        r"\battendant\b",
    ]

    for pat in junk_patterns:
        text = re.sub(pat, " ", text, flags=re.IGNORECASE | re.MULTILINE)

    # Αφαίρεση ακραίων επαναλήψεων ίδιας φράσης στην ίδια γραμμή
    text = re.sub(r"(.{8,80}?)(\s+\1){2,}", r"\1", text, flags=re.IGNORECASE)

    # Καθαρισμός κενών
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"\n[ \t]+", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def remove_overlap_repetition(full_text: str) -> str:
    """
    Ελαφρύ καθάρισμα από επαναλήψεις λόγω overlap.
    Δεν είναι επιθετικό, ώστε να μη σβήσει χρήσιμο κείμενο.
    """
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
        return f"[❌ Chunk {chunk_idx + 1}: Το αρχείο είναι {chunk_mb:.1f}MB και ξεπερνά το ασφαλές όριο των {MAX_OPENAI_CHUNK_MB}MB]"

    try:
        from openai import OpenAI

        client = OpenAI(api_key=openai_key)
        audio_file = io.BytesIO(chunk)
        audio_file.name = f"chunk_{chunk_idx + 1}.mp3"

        try:
            result = client.audio.transcriptions.create(
                model=TRANSCRIPTION_MODEL_PRIMARY,
                file=audio_file,
                language="el",
                prompt=TRANSCRIPTION_PROMPT,
                response_format="text",
                temperature=0,
            )
        except Exception as primary_error:
            audio_file.seek(0)
            try:
                result = client.audio.transcriptions.create(
                    model=TRANSCRIPTION_MODEL_FALLBACK,
                    file=audio_file,
                    language="el",
                    prompt=TRANSCRIPTION_PROMPT,
                    response_format="text",
                    temperature=0,
                )
            except Exception as fallback_error:
                return (
                    f"[❌ Chunk {chunk_idx + 1}: Απέτυχε η μεταγραφή. "
                    f"Primary error: {primary_error}. Fallback error: {fallback_error}]"
                )

        return clean_transcript(str(result))

    except ImportError:
        return f"[❌ Chunk {chunk_idx + 1}: Προσθέστε `openai` στο requirements.txt]"
    except Exception as e:
        return f"[❌ Chunk {chunk_idx + 1}: {e}]"


def transcribe_audio(
    audio_bytes: bytes,
    ext: str,
    progress_cb: Optional[Callable] = None,
) -> Tuple[str, Optional[str]]:
    """
    Πλήρης μεταγραφή:
    1. normalize σε MP3
    2. split σε chunks
    3. transcribe chunks
    4. clean/merge
    """
    if progress_cb:
        progress_cb(5, "🎚️ Κανονικοποίηση ήχου σε MP3 mono 16kHz…")

    mp3_bytes, err = normalize_to_mp3(audio_bytes, ext)
    if err:
        return "", err

    if progress_cb:
        progress_cb(12, f"✂️ Διαχωρισμός ηχογράφησης σε ασφαλή τμήματα… MP3: {mb_size(mp3_bytes):.1f}MB")

    chunks, split_warning = split_audio_to_chunks(mp3_bytes)
    n = len(chunks)

    transcripts = []
    errors = []

    for i, chunk in enumerate(chunks):
        chunk_mb = mb_size(chunk)

        if progress_cb:
            pct = 15 + int(65 * (i / max(n, 1)))
            progress_cb(pct, f"🎧 Μεταγραφή τμήματος {i + 1}/{n} — {chunk_mb:.1f}MB…")

        text = transcribe_chunk(chunk, i, n)
        if text:
            if text.startswith("[❌"):
                errors.append(text)
            transcripts.append(f"=== Τμήμα {i + 1}/{n} ===\n{text}")

    full_transcript = "\n\n".join(transcripts)
    full_transcript = clean_transcript(full_transcript)
    full_transcript = remove_overlap_repetition(full_transcript)

    warnings = []
    if split_warning:
        warnings.append(split_warning)
    if errors:
        warnings.append("⚠️ Κάποια chunks δεν μεταγράφηκαν σωστά. Δείτε την ακατέργαστη μεταγραφή.")

    return full_transcript, "\n".join(warnings) if warnings else None

# ══════════════════════════════════════════════════════════════
# CLAUDE → ΠΡΑΚΤΙΚΑ
# ══════════════════════════════════════════════════════════════
def format_into_praktiko(transcript: str, context: str) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
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
Σου δίνεται ακατέργαστη μεταγραφή ελληνικής τεκτονικής συνεδρίασης.
Στόχος σου είναι να συντάξεις επίσημα Πρακτικά ΜΣΤΕ.

Πολύ σημαντικό:
- Μην εφευρίσκεις ονόματα, ποσά, αποφάσεις ή αριθμούς παρόντων αν δεν υπάρχουν καθαρά.
- Αν κάτι δεν προκύπτει, άφησέ το κενό ή γράψε "Δεν προέκυψε σαφώς από τη μεταγραφή".
- Κράτα επίσημο, αρχαιοπρεπές, γραμματειακό ύφος.
- Διόρθωσε εμφανή λάθη μεταγραφής μόνο όταν το νόημα είναι σαφές.
- Απόφυγε άσχετα κείμενα τύπου υπότιτλοι, διαφημίσεις, κλπ.

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
            messages=[
                {
                    "role": "user",
                    "content": f"Πλαίσιο συνεδρίασης από τη φόρμα:\n{context or '-'}\n\nΑκατέργαστη μεταγραφή:\n{transcript}",
                }
            ],
        )

        raw = msg.content[0].text if msg.content else ""
        clean = raw.strip()
        clean = re.sub(r"^```(?:json)?\s*", "", clean)
        clean = re.sub(r"\s*```$", "", clean)

        result = json.loads(clean)
        result["μεταγραφή_λέξη_προς_λέξη"] = transcript
        return result, None

    except json.JSONDecodeError:
        return {
            "ημερομηνία": "",
            "ημέρα": "",
            "βαθμός_γενική": "Μαθητού",
            "τόπος": "",
            "σεβάσμιος": "",
            "παρόντες_αριθμός": 0,
            "παρόντες_ολογράφως": "",
            "ημερησία_διάταξη": [],
            "κείμενο_πρακτικών": raw if "raw" in locals() else "",
            "αποφάσεις": [],
            "κορμός_αγαθοεργίας": 0.0,
            "κορμός_ολογράφως": "",
            "γραμματεύς": "",
            "ρήτωρ": "",
            "μεταγραφή_λέξη_προς_λέξη": transcript,
        }, "⚠️ Ο Claude δεν επέστρεψε καθαρό JSON. Το κείμενο μπήκε στον editor για χειροκίνητο έλεγχο."
    except Exception as e:
        return None, f"❌ Σφάλμα σύνταξης πρακτικών: {e}"


def process_audio_to_praktiko(
    audio_bytes: bytes,
    ext: str,
    context: str,
    progress_cb: Optional[Callable] = None,
):
    if progress_cb:
        progress_cb(2, "🚀 Έναρξη επεξεργασίας…")

    transcript, transcribe_warning_or_error = transcribe_audio(audio_bytes, ext, progress_cb)

    if not transcript:
        return None, transcribe_warning_or_error or "❌ Δεν δημιουργήθηκε μεταγραφή."

    if progress_cb:
        progress_cb(82, "🧹 Καθαρισμός μεταγραφής…")

    transcript = clean_transcript(transcript)

    if progress_cb:
        progress_cb(88, "📝 Σύνταξη επίσημων Πρακτικών με Claude…")

    result, praktiko_err = format_into_praktiko(transcript, context)

    if progress_cb:
        progress_cb(100, "✅ Ολοκληρώθηκε.")

    if result and transcribe_warning_or_error and transcribe_warning_or_error.startswith("⚠️"):
        result["προειδοποίηση"] = transcribe_warning_or_error

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
        "DSS": "DejaVuSans.ttf",
        "DSSB": "DejaVuSans-Bold.ttf",
        "DSR": "DejaVuSerif.ttf",
        "DSB": "DejaVuSerif-Bold.ttf",
        "DSI": "DejaVuSerif-Italic.ttf",
    }

    for alias, filename in fonts.items():
        path = os.path.join(font_dir, filename)
        if alias not in pdfmetrics.getRegisteredFontNames() and os.path.exists(path):
            pdfmetrics.registerFont(TTFont(alias, path))

    font_sans = "DSS" if "DSS" in pdfmetrics.getRegisteredFontNames() else "Helvetica"
    font_sans_bold = "DSSB" if "DSSB" in pdfmetrics.getRegisteredFontNames() else "Helvetica-Bold"
    font_serif = "DSR" if "DSR" in pdfmetrics.getRegisteredFontNames() else "Helvetica"
    font_serif_bold = "DSB" if "DSB" in pdfmetrics.getRegisteredFontNames() else "Helvetica-Bold"

    cnvy = colors.HexColor(NAVY)
    cgold = colors.HexColor(GOLD)

    def S(name, **kwargs):
        return ParagraphStyle(name, **kwargs)

    H1 = S("H1", fontName=font_sans_bold, fontSize=12, alignment=TA_CENTER, spaceAfter=2, leading=15)
    H2 = S("H2", fontName=font_sans, fontSize=10, alignment=TA_CENTER, spaceAfter=2, leading=13)
    LDG = S("LDG", fontName=font_sans_bold, fontSize=10, alignment=TA_CENTER, spaceAfter=6, leading=13)
    TTL = S("TTL", fontName=font_sans_bold, fontSize=11, alignment=TA_CENTER, spaceAfter=2, spaceBefore=6, leading=15, textColor=cnvy)
    HDA = S("HDA", fontName=font_sans_bold, fontSize=10, alignment=TA_LEFT, spaceAfter=4, leading=13)
    BUL = S("BUL", fontName=font_serif, fontSize=10, alignment=TA_LEFT, leftIndent=20, spaceAfter=3, leading=14)
    BOD = S("BOD", fontName=font_serif, fontSize=10, alignment=TA_JUSTIFY, spaceAfter=6, leading=15)
    SML = S("SML", fontName=font_serif, fontSize=8, alignment=TA_CENTER, textColor=colors.grey, spaceAfter=2)
    SGN = S("SGN", fontName=font_serif, fontSize=10, alignment=TA_CENTER, spaceAfter=0, leading=14)
    SGNB = S("SGNB", fontName=font_serif_bold, fontSize=10, alignment=TA_CENTER, spaceAfter=0, leading=14)
    IPO = S("IPO", fontName=font_serif, fontSize=10, alignment=TA_RIGHT, spaceAfter=4)

    def xml_escape(text: str) -> str:
        return (
            str(text or "")
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )

    story = []

    story += [
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
    abbr = βαθμ[:3]
    ημερ = d.get("ημερομηνία", "") or ""

    story.append(Paragraph(f"Πρακτικόν Συνεδρίας της {xml_escape(ημερ)} εις Βαθμ∴ {xml_escape(abbr)}∴", TTL))

    agenda = d.get("ημερησία_διάταξη", []) or []
    if agenda:
        story.append(Spacer(1, 0.2 * cm))
        story.append(Paragraph("<b>Ημερησία Διάταξις:</b>", HDA))
        for item in agenda:
            story.append(Paragraph(f"– {xml_escape(item)}", BUL))
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
                story.append(Paragraph(f"{xml_escape(ln)}", BUL))
        else:
            story.append(Paragraph(xml_escape(para.replace("\n", " ")), BOD))

    κορμ = float(d.get("κορμός_αγαθοεργίας", 0) or 0)
    κολ = d.get("κορμός_ολογράφως", "") or ""
    if κορμ:
        story.append(Paragraph(
            f"Εκ του Κορμού της Αγαθοεργίας εβλάστησαν <b>{xml_escape(κολ)} ({κορμ:.2f})</b> όστρακα.",
            BOD,
        ))

    σεβ = d.get("σεβάσμιος", "") or ""
    if σεβ:
        closing = (
            f"Τέλος, οι Εργασίες έκλεισαν κανονικώς υπό την Σφύραν "
            f"του Σεβ∴ Διδ∴ <b>{xml_escape(σεβ)}</b>, "
            f"των Αδδ∴ της Σ∴ Στ∴ μας ευχαριστημένων και ικανοποιημένων."
        )
    else:
        closing = "Τέλος, οι Εργασίες έκλεισαν κανονικώς."

    story += [
        Spacer(1, 0.3 * cm),
        Paragraph(closing, BOD),
        Spacer(1, 0.2 * cm),
        Paragraph("Είπον Σεβ∴ Διδ∴.", IPO),
        Spacer(1, 1.5 * cm),
    ]

    γραμ = d.get("γραμματεύς", "") or ""
    ρητ = d.get("ρήτωρ", "") or ""

    def sig_col(title: str, name: str):
        return [Paragraph(title, SGN), Spacer(1, 1.2 * cm), Paragraph(xml_escape(name), SGNB)]

    story.append(Table([[sig_col("Ο Σεβ∴ Διδ∴", σεβ)]], colWidths=[14 * cm], hAlign="CENTER"))
    story.append(Spacer(1, 0.8 * cm))
    story.append(Table(
        [[sig_col("Ο Γραμματεύς", γραμ), sig_col("Ο Ρήτωρ", ρητ)]],
        colWidths=[7 * cm, 7 * cm],
        hAlign="CENTER",
    ))

    story += [
        Spacer(1, 0.6 * cm),
        HRFlowable(width="100%", thickness=0.3, color=colors.lightgrey),
        Paragraph(
            f"Αρ. Πρωτ.: {xml_escape(d.get('αρ_πρωτ', ''))} | Ημερομηνία: {xml_escape(ημερ)} | Βαθμ∴: {xml_escape(βαθμ)}",
            SML,
        ),
    ]

    buf = io.BytesIO()
    SimpleDocTemplate(
        buf,
        pagesize=A4,
        rightMargin=2.5 * cm,
        leftMargin=2.5 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        title="Πρακτικό Συνεδρίασης ΑΚΡΟΠΟΛΙΣ 84",
    ).build(story)
    buf.seek(0)
    return buf

# ══════════════════════════════════════════════════════════════
# EDITOR
# ══════════════════════════════════════════════════════════════
def show_editor(r: dict) -> dict:
    st.markdown("---")
    st.markdown("## ✏️ Επεξεργασία Πρακτικού")
    st.caption("Ελέγξτε και διορθώστε τα πεδία. Το AI βοηθά, αλλά ο Γραμματεύς κάνει τον τελικό έλεγχο.")

    c1, c2, c3 = st.columns(3)

    with c1:
        r["ημερομηνία"] = st.text_input("Ημερομηνία (DD/MM/YYYY)", r.get("ημερομηνία", ""))
        r["ημέρα"] = st.text_input("Ημέρα", r.get("ημέρα", ""))
        r["βαθμός_γενική"] = st.text_input("Βαθμός γενική", r.get("βαθμός_γενική", "Μαθητού"))
        r["τόπος"] = st.text_input("Τόπος", r.get("τόπος", "τον Τεκτ∴ Ναόν"))

    with c2:
        r["σεβάσμιος"] = st.text_input("Σεβ∴ Διδ∴", r.get("σεβάσμιος", ""))
        r["γραμματεύς"] = st.text_input("Γραμματεύς", r.get("γραμματεύς", ""))
        r["ρήτωρ"] = st.text_input("Ρήτωρ", r.get("ρήτωρ", ""))
        r["αρ_πρωτ"] = st.text_input("Αρ. Πρωτοκόλλου", r.get("αρ_πρωτ", ""))

    with c3:
        r["παρόντες_αριθμός"] = st.number_input(
            "Παρόντες (αριθμός)",
            0,
            300,
            int(r.get("παρόντες_αριθμός", 0) or 0),
        )
        r["παρόντες_ολογράφως"] = st.text_input("Παρόντες (ολογράφως)", r.get("παρόντες_ολογράφως", ""))
        r["κορμός_αγαθοεργίας"] = st.number_input(
            "Κορμός (€)",
            0.0,
            99999.0,
            float(r.get("κορμός_αγαθοεργίας", 0) or 0),
            step=1.0,
            format="%.2f",
        )
        r["κορμός_ολογράφως"] = st.text_input("Κορμός ολογράφως", r.get("κορμός_ολογράφως", ""))

    st.markdown("#### 📋 Ημερησία Διάταξη")
    agenda_raw = st.text_area(
        "Ένα θέμα ανά γραμμή:",
        "\n".join(r.get("ημερησία_διάταξη", []) or []),
        height=90,
        label_visibility="collapsed",
    )
    r["ημερησία_διάταξη"] = [line.strip() for line in agenda_raw.splitlines() if line.strip()]

    st.markdown("#### 📄 Κείμενο Πρακτικών")
    r["κείμενο_πρακτικών"] = st.text_area(
        "Κείμενο Πρακτικών",
        r.get("κείμενο_πρακτικών", ""),
        height=550,
        label_visibility="collapsed",
    )

    return r

# ══════════════════════════════════════════════════════════════
# UI
# ══════════════════════════════════════════════════════════════
tab_main, tab_help = st.tabs(["🎵 Ηχογράφηση → Πρακτικά", "ℹ️ Οδηγίες & Ρυθμίσεις"])

with tab_main:
    st.markdown("### Βήμα 1 · Στοιχεία Συνεδρίασης")

    ca, cb, cc = st.columns(3)

    with ca:
        sel_βαθμ = st.selectbox("Βαθμός", list(ΒΑΘΜΟΙ_GEN.keys()))
        sel_ημερ = st.date_input("Ημερομηνία", value=date.today())

    with cb:
        sel_σεβ = st.text_input("Σεβ∴ Διδ∴", placeholder="Όνομα Επώνυμο")
        sel_γραμ = st.text_input("Γραμματεύς", placeholder="Όνομα Επώνυμο")

    with cc:
        sel_ρητ = st.text_input("Ρήτωρ", placeholder="Όνομα Επώνυμο")
        sel_extra = st.text_area(
            "Επιπλέον πλαίσιο για AI",
            placeholder="π.χ. παρόντες, θέματα, ονόματα ομιλητών, ποσό κορμού κλπ.",
            height=68,
        )

    st.markdown("---")
    st.markdown("### Βήμα 2 · Αρχείο Ηχογράφησης")

    audio_file = st.file_uploader(
        f"Ανεβάστε αρχείο ήχου ({', '.join(SUPPORTED)}) — max {MAX_MB_RAW}MB",
        type=SUPPORTED,
    )

    if audio_file:
        raw_bytes = audio_file.getvalue()
        size_mb = mb_size(raw_bytes)
        ext = audio_file.name.rsplit(".", 1)[-1].lower()

        show_audio_preview = st.checkbox(
            "🎧 Εμφάνιση audio player",
            value=False,
            help="Για μεγάλα αρχεία, αφήστε το κλειστό όσο διορθώνετε τη μεταγραφή, για να μη βαραίνει το Streamlit."
        )

        if show_audio_preview:
            with st.expander("🎧 Προεπισκόπηση ηχογράφησης", expanded=True):
                st.warning(
                    "Για μεγάλα αρχεία, μην έχετε ανοιχτό ταυτόχρονα το audio player "
                    "και την ακατέργαστη μεταγραφή."
                )
                st.audio(raw_bytes, format=f"audio/{ext}")

        if size_mb > MAX_MB_RAW:
            st.error(f"⛔ Το αρχείο είναι {size_mb:.1f}MB και ξεπερνά το όριο {MAX_MB_RAW}MB.")
        else:
            st.success(f"✅ {audio_file.name} — {size_mb:.1f}MB — έτοιμο για μεταγραφή.")
            st.session_state["ready_audio"] = raw_bytes
            st.session_state["ready_ext"] = ext
            st.session_state["ready_name"] = audio_file.name

    st.markdown("---")
    st.markdown("### Βήμα 3 · Μεταγραφή & Σύνταξη Πρακτικών")

    ready = "ready_audio" in st.session_state

    if not ready:
        st.info("📌 Ανεβάστε πρώτα αρχείο ηχογράφησης.")

    if st.button(
        "🎧 Μεταγραφή & Σύνταξη Πρακτικών",
        type="primary",
        use_container_width=True,
        disabled=not ready,
    ):
        st.session_state["last_sel_βαθμ"] = sel_βαθμ
        st.session_state["last_sel_ημερ"] = sel_ημερ.strftime('%d/%m/%Y')
        st.session_state["last_sel_σεβ"] = sel_σεβ
        st.session_state["last_sel_γραμ"] = sel_γραμ
        st.session_state["last_sel_ρητ"] = sel_ρητ
        st.session_state["last_sel_extra"] = sel_extra

        # ✅ ΔΙΟΡΘΩΣΗ: \n αντί για literal newlines μέσα στο f-string
        ctx = (
            f"Βαθμός: {sel_βαθμ}\n"
            f"Βαθμός σε γενική: {ΒΑΘΜΟΙ_GEN[sel_βαθμ]}\n"
            f"Ημερομηνία: {sel_ημερ.strftime('%d/%m/%Y')}\n"
            f"Σεβ∴ Διδ∴: {sel_σεβ}\n"
            f"Γραμματεύς: {sel_γραμ}\n"
            f"Ρήτωρ: {sel_ρητ}\n"
            f"Επιπλέον πληροφορίες: {sel_extra or '-'}"
        )

        size_mb = mb_size(st.session_state["ready_audio"])
        progress_bar = st.progress(0)
        status_text = st.empty()

        def progress_cb(pct: int, msg: str):
            progress_bar.progress(min(max(int(pct), 0), 100))
            status_text.info(msg)

        progress_cb(1, f"🚀 Επεξεργασία αρχείου {size_mb:.1f}MB…")

        try:
            result, err = process_audio_to_praktiko(
                st.session_state["ready_audio"],
                st.session_state["ready_ext"],
                ctx,
                progress_cb=progress_cb,
            )
        except Exception as e:
            result, err = None, f"❌ Το Streamlit σταμάτησε την επεξεργασία λόγω σφάλματος: {e}"

        status_text.empty()
        progress_bar.progress(100)

        if err and not result:
            st.error(err)
        elif result:
            if err:
                st.warning(err)

            for k, v in [
                ("σεβάσμιος", sel_σεβ),
                ("γραμματεύς", sel_γραμ),
                ("ρήτωρ", sel_ρητ),
            ]:
                if not result.get(k) and v:
                    result[k] = v

            if not result.get("βαθμός_γενική"):
                result["βαθμός_γενική"] = ΒΑΘΜΟΙ_GEN[sel_βαθμ]

            if not result.get("ημερομηνία"):
                result["ημερομηνία"] = sel_ημερ.strftime("%d/%m/%Y")

            st.session_state["praktiko"] = result
            st.session_state.pop("editable_raw_transcript", None)
            st.success("✅ Έτοιμο. Ελέγξτε/διορθώστε πρώτα την ακατέργαστη μεταγραφή και μετά τα πρακτικά.")

    if "praktiko" in st.session_state:
        raw_tr = st.session_state["praktiko"].get("μεταγραφή_λέξη_προς_λέξη", "")

        if raw_tr:
            with st.expander("📄 Ακατέργαστη μεταγραφή", expanded=False):
                edit_limit = 50000

                if "editable_raw_transcript" not in st.session_state:
                    st.session_state["editable_raw_transcript"] = raw_tr[:edit_limit]

                edited_raw = st.text_area(
                    "Ακατέργαστη μεταγραφή",
                    st.session_state["editable_raw_transcript"],
                    height=400,
                    label_visibility="collapsed",
                    help="Μπορείτε να διορθώσετε εδώ τη μεταγραφή. Για πολύ μεγάλα κείμενα εμφανίζεται ασφαλές τμήμα έως 50.000 χαρακτήρες."
                )

                st.session_state["editable_raw_transcript"] = edited_raw
                st.session_state["praktiko"]["μεταγραφή_λέξη_προς_λέξη"] = edited_raw

                if len(raw_tr) > edit_limit:
                    st.warning(
                        "Η πλήρης μεταγραφή είναι μεγάλη. Για λόγους σταθερότητας, επεξεργάζεστε εδώ μόνο τους πρώτους 50.000 χαρακτήρες. "
                        "Κατεβάστε το πλήρες .txt αν θέλετε πλήρη χειροκίνητη διόρθωση εκτός Streamlit."
                    )

                if st.button("🔄 Ενημέρωση Πρακτικού από διορθωμένη μεταγραφή", use_container_width=True):
                    # ✅ ΔΙΟΡΘΩΣΗ: \n αντί για literal newlines μέσα στο f-string
                    ctx_update = (
                        f"Βαθμός: {st.session_state.get('last_sel_βαθμ', '')}\n"
                        f"Ημερομηνία: {st.session_state.get('last_sel_ημερ', '')}\n"
                        f"Επιπλέον πληροφορίες: διορθωμένη ακατέργαστη μεταγραφή από τον χρήστη"
                    )
                    with st.spinner("Σύνταξη νέου πρακτικού από τη διορθωμένη μεταγραφή…"):
                        updated_result, updated_err = format_into_praktiko(edited_raw, ctx_update)
                    if updated_err and not updated_result:
                        st.error(updated_err)
                    elif updated_result:
                        st.session_state["praktiko"].update(updated_result)
                        st.success("✅ Το πρακτικό ενημερώθηκε από τη διορθωμένη μεταγραφή.")
                st.download_button(
                    "⬇️ Λήψη μεταγραφής .txt",
                    raw_tr.encode("utf-8"),
                    f"μεταγραφή_{date.today()}.txt",
                    "text/plain",
                )

        edited = show_editor(st.session_state["praktiko"].copy())

        st.markdown("---")
        st.markdown("### Βήμα 4 · Δημιουργία PDF")

        col_gen, col_dl = st.columns(2)

        with col_gen:
            if st.button("📄 Δημιουργία PDF Πρακτικού", type="primary", use_container_width=True):
                with st.spinner("Δημιουργία PDF…"):
                    try:
                        pdf = generate_praktiko_pdf(edited)
                        st.session_state["pdf_bytes"] = pdf.getvalue()
                        st.session_state["pdf_label"] = (edited.get("ημερομηνία", "") or str(date.today())).replace("/", "_")
                        st.success("✅ PDF έτοιμο.")
                    except Exception as e:
                        st.error(f"❌ Σφάλμα δημιουργίας PDF: {e}")

        with col_dl:
            if "pdf_bytes" in st.session_state:
                st.download_button(
                    "⬇️ Λήψη PDF — Πρακτικό Συνεδρίασης",
                    data=st.session_state["pdf_bytes"],
                    file_name=f"πρακτικό_{st.session_state.get('pdf_label', date.today())}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )

with tab_help:
    st.markdown("""
    ## Ροή εργασίας

    1. Συμπληρώνετε βαθμό, ημερομηνία και αξιωματικούς.
    2. Ανεβάζετε αρχείο ήχου.
    3. Πατάτε **Μεταγραφή & Σύνταξη Πρακτικών**.
    4. Ελέγχετε πρώτα την ακατέργαστη μεταγραφή.
    5. Διορθώνετε το πρακτικό στον editor.
    6. Δημιουργείτε PDF.

    ## Streamlit Secrets

    Στο Streamlit Cloud → App Settings → Secrets:

    ```toml
    [AI]
    OPENAI_API_KEY = "sk-..."
    ANTHROPIC_API_KEY = "sk-ant-..."
    ```

    ## requirements.txt

    Βεβαιωθείτε ότι υπάρχουν:

    ```txt
    streamlit>=1.30
    pandas>=2.0
    plotly>=5.0
    reportlab>=4.0
    anthropic>=0.25
    openai>=1.50.0
    pydub>=0.25.1
    ```

    ## packages.txt

    Για να δουλεύει σωστά το pydub στο Streamlit Cloud, καλό είναι να υπάρχει:

    ```txt
    ffmpeg
    ```

    ## Σημαντικές πρακτικές για καλύτερη μεταγραφή

    - Το κινητό να είναι κοντά στους ομιλητές.
    - Προτιμήστε WAV, M4A ή MP3 με καθαρό ήχο.
    - Μειώστε θόρυβο, μουσική, ψιθύρους και παράλληλες συζητήσεις.
    - Στο πεδίο "Επιπλέον πλαίσιο" γράψτε ονόματα, θέματα και γνωστούς όρους.
    - Για μεγάλες συνεδριάσεις, προτιμήστε αρχείο κάτω από 300MB.
    """)

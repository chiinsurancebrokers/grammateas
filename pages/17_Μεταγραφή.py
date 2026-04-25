# -*- coding: utf-8 -*-
"""
Σελίδα 17 — Μεταγραφή Ηχογράφησης → Πρακτικά ΜΣΤΕ
WAV/MP3 upload → MP3 compress → Claude AI → Μεταγραφή → Επεξεργασία → PDF
"""
import sys; sys.path.append("..")
import streamlit as st
import base64, io, json, re, os
from datetime import date
from modules.database import init_db

init_db()
st.set_page_config(page_title="Μεταγραφή → Πρακτικά", page_icon="🎧", layout="wide")

st.markdown("# 🎧 Ηχογράφηση → Πρακτικά ΜΣΤΕ")
st.caption("WAV/MP3 ανεβαίνει · συμπιέζεται σε MP3 · μεταγράφεται από Claude AI · επεξεργάζεστε · εκτυπώνετε PDF")

# ══════════════════════════════════════════════════════════════
# ΣΤΑΘΕΡΕΣ
# ══════════════════════════════════════════════════════════════
MAX_MB_RAW  = 150
MAX_MB_SEND = 20
SUPPORTED   = ["wav","mp3","m4a","ogg","webm","aac"]
MIME_MAP    = {"wav":"audio/wav","mp3":"audio/mpeg","m4a":"audio/mp4",
               "ogg":"audio/ogg","webm":"audio/webm","aac":"audio/aac"}
ΒΑΘΜΟΙ_GEN = {"Α' - Μαθητής":"Μαθητού","Β' - Εταίρος":"Εταίρου","Γ' - Διδάσκαλος":"Διδασκάλου"}
NAVY = "#1a2a4a"
GOLD = "#b8960c"

# ══════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════

def get_api_key():
    try:
        return (st.secrets.get("AI",{}).get("ANTHROPIC_API_KEY") or
                st.secrets.get("ANTHROPIC_API_KEY",""))
    except Exception:
        return ""


def compress_to_mp3(audio_bytes: bytes, ext: str):
    """
    Προσπαθεί MP3 128kbps μέσω pydub+ffmpeg.
    Fallback: αν δεν υπάρχει ffmpeg, μειώνει WAV σε mono 16kHz (built-in Python).
    """
    # ── Δοκιμή 1: pydub + ffmpeg (καλύτερο αποτέλεσμα) ──────
    try:
        from pydub import AudioSegment
        buf_in = io.BytesIO(audio_bytes)
        fmt = ext if ext not in ("m4a","aac") else "mp4"
        seg = AudioSegment.from_file(buf_in, format=fmt)
        buf_out = io.BytesIO()
        seg.export(buf_out, format="mp3", bitrate="128k")
        buf_out.seek(0)
        return buf_out.read(), None, "mp3"
    except ImportError:
        pass  # pydub δεν υπάρχει → fallback
    except Exception:
        pass  # ffmpeg δεν υπάρχει → fallback

    # ── Fallback: WAV μόνο — mono 16kHz μέσω built-in Python ─
    if ext != "wav":
        return None, (
            "❌ Το ffmpeg δεν έχει εγκατασταθεί ακόμα στο Streamlit Cloud.\n"
            "👉 Κάντε **Delete app → Redeploy** από το Streamlit Cloud dashboard "
            "για να γίνει clean build με το ffmpeg.\n"
            "Εναλλακτικά, ανεβάστε το αρχείο ήδη σε MP3 μορφή."
        ), None

    # WAV fallback: wave + audioop (built-in, δεν χρειάζεται ffmpeg)
    try:
        import wave, audioop, struct
        with wave.open(io.BytesIO(audio_bytes)) as wf:
            n_ch      = wf.getnchannels()
            orig_rate = wf.getframerate()
            sampwidth = wf.getsampwidth()
            frames    = wf.readframes(wf.getnframes())

        # Mono (αν stereo)
        if n_ch == 2:
            frames = audioop.tomono(frames, sampwidth, 0.5, 0.5)

        # Resample → 16000 Hz
        target_rate = 16000
        if orig_rate != target_rate:
            frames, _ = audioop.ratecv(frames, sampwidth, 1, orig_rate, target_rate, None)

        # Γράψε νέο WAV
        buf_out = io.BytesIO()
        with wave.open(buf_out, "wb") as wo:
            wo.setnchannels(1)
            wo.setsampwidth(sampwidth)
            wo.setframerate(target_rate)
            wo.writeframes(frames)
        buf_out.seek(0)
        result = buf_out.read()

        orig_mb = len(audio_bytes) / (1024*1024)
        new_mb  = len(result) / (1024*1024)
        return result, (
            f"⚠️ ffmpeg δεν βρέθηκε — χρησιμοποιήθηκε Python fallback.\n"
            f"WAV: {orig_mb:.1f}MB → mono 16kHz WAV: {new_mb:.1f}MB\n"
            f"Για MP3 (μικρότερο), κάντε **Delete app → Redeploy** στο Streamlit Cloud."
        ), "wav"

    except Exception as e:
        return None, f"❌ Σφάλμα fallback συμπίεσης: {e}", None


def call_claude_audio(audio_bytes: bytes, ext: str, context: str):
    api_key = get_api_key()
    if not api_key:
        return None, "❌ Δεν βρέθηκε ANTHROPIC_API_KEY στα Streamlit Secrets."
    try:
        import anthropic
    except ImportError:
        return None, "❌ Προσθέστε 'anthropic' στο requirements.txt"

    system = """Είσαι Γραμματεύς-Σφραγιδοφύλαξ της Σ∴ Στ∴ ΑΚΡΟΠΟΛΙΣ υπ' αρ. 84 (ΜΣΤΕ).
Σου δίνεται ηχογράφηση Τεκτονικής Συνεδρίασης. Κάνε μεταγραφή και σύνταξε επίσημα Πρακτικά.

Υποχρεωτική δομή κειμένου:
• Έναρξη («Σήμερον [ημέρα] [ημερομηνία], εις [τόπο], και υπό την Σφύραν του Σεβ∴ Διδ∴ ... ανοίγουν οι Εργασίες εις Βαθμόν [βαθμός].»)
• Παρόντες ([αριθμός ολογράφως] ([αριθμός]) Αδδ∴)
• Θέσεις αξιωματικών
• Αλληλογραφία (ο Αδ∴ Ρήτ∴ ανέγνωσεν...)
• Επικύρωση προηγουμένων πρακτικών
• Εργασίες / Ομιλίες / Αποφάσεις (αναλυτικά)
• Κεφάλαιον Αγαθοεργίας (Κορμός, Σάκ∴ Προτάσεων)
• Κλείσιμο

Χρησιμοποίησε πάντα: Σεβ∴ Διδ∴, Αδ∴, Σ∴ Στ∴, Βαθμ∴ Μαθ∴/Ετ∴/Διδ∴, Γραμμ∴, Ρήτ∴ κλπ.
Γράψε σε αρχαιοπρεπές επίσημο τεκτονικό ύφος.
Χώριζε παραγράφους με κενή γραμμή.

Επέστρεψε ΜΟΝΟ JSON (χωρίς backticks):
{
  "μεταγραφή_λέξη_προς_λέξη": "...",
  "ημερομηνία": "DD/MM/YYYY",
  "ημέρα": "Τρίτην",
  "βαθμός_γενική": "Μαθητού",
  "τόπος": "τον Τεκτ∴ Ναόν ...",
  "σεβάσμιος": "Όνομα Επώνυμο",
  "παρόντες_αριθμός": 14,
  "παρόντες_ολογράφως": "δέκα τέσσερεις",
  "ημερησία_διάταξη": ["Θέμα 1","Θέμα 2"],
  "κείμενο_πρακτικών": "Σήμερον Τρίτην...\n\nΠαρόντες...\n\n...",
  "αποφάσεις": ["Απόφαση 1"],
  "κορμός_αγαθοεργίας": 20.0,
  "κορμός_ολογράφως": "είκοσι",
  "γραμματεύς": "Όνομα Επώνυμο",
  "ρήτωρ": "Όνομα Επώνυμο"
}"""

    media_type = MIME_MAP.get(ext, "audio/mpeg")
    b64 = base64.standard_b64encode(audio_bytes).decode()

    try:
        client = anthropic.Anthropic(api_key=api_key)
        msg = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=8000,
            system=system,
            messages=[{"role":"user","content":[
                {"type":"text","text":f"Πλαίσιο: {context or '-'}. Κάνε μεταγραφή και σύνταξε πρακτικά ΜΣΤΕ."},
                {"type":"audio","source":{"type":"base64","media_type":media_type,"data":b64}}
            ]}]
        )
        raw   = msg.content[0].text if msg.content else ""
        clean = re.sub(r"^```[a-z]*\n?","",raw.strip())
        clean = re.sub(r"\n?```$","",clean.strip())
        return json.loads(clean), None
    except json.JSONDecodeError:
        return {"μεταγραφή_λέξη_προς_λέξη":raw, "κείμενο_πρακτικών":raw}, None
    except Exception as e:
        return None, f"❌ Σφάλμα API: {e}"


# ══════════════════════════════════════════════════════════════
# PDF GENERATOR — ακριβές στυλ υποδείγματος ΜΣΤΕ
# ══════════════════════════════════════════════════════════════
def generate_praktiko_pdf(d: dict) -> io.BytesIO:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT
    from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                    HRFlowable, Table, TableStyle)
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    _base = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "fonts")
    for alias, fn in {
        "DSS":"DejaVuSans.ttf","DSSB":"DejaVuSans-Bold.ttf",
        "DSR":"DejaVuSerif.ttf","DSB":"DejaVuSerif-Bold.ttf","DSI":"DejaVuSerif-Italic.ttf",
    }.items():
        if alias not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont(alias, os.path.join(_base, fn)))

    CNVY  = colors.HexColor(NAVY)
    CGOLD = colors.HexColor(GOLD)

    def S(nm, **kw): return ParagraphStyle(nm, **kw)

    # Styles — Sans για ∴, Serif για σώμα κειμένου
    H1   = S("H1",  fontName="DSSB", fontSize=12, alignment=TA_CENTER, spaceAfter=2, leading=15)
    H2   = S("H2",  fontName="DSS",  fontSize=10, alignment=TA_CENTER, spaceAfter=2, leading=13)
    LDG  = S("LDG", fontName="DSSB", fontSize=10, alignment=TA_CENTER, spaceAfter=6, leading=13)
    TTL  = S("TTL", fontName="DSSB", fontSize=11, alignment=TA_CENTER, spaceAfter=2,
             spaceBefore=6, leading=15, textColor=CNVY)
    HDA  = S("HDA", fontName="DSSB", fontSize=10, alignment=TA_LEFT,  spaceAfter=4, leading=13)
    BUL  = S("BUL", fontName="DSR",  fontSize=10, alignment=TA_LEFT,  leftIndent=20,
             spaceAfter=3, leading=14)
    BOD  = S("BOD", fontName="DSR",  fontSize=10, alignment=TA_JUSTIFY, spaceAfter=6, leading=15)
    SML  = S("SML", fontName="DSR",  fontSize=8,  alignment=TA_CENTER, textColor=colors.grey,
             spaceAfter=2)
    SGN  = S("SGN", fontName="DSR",  fontSize=10, alignment=TA_CENTER, spaceAfter=0, leading=14)
    SGNB = S("SGNB",fontName="DSB",  fontSize=10, alignment=TA_CENTER, spaceAfter=0, leading=14)
    IPO  = S("IPO", fontName="DSR",  fontSize=10, alignment=TA_RIGHT,  spaceAfter=4)

    story = []

    # ── ΚΕΦΑΛΙΔΑ ──────────────────────────────────────────────
    story += [
        Paragraph("Ε∴Δ∴Τ∴Μ∴Α∴Τ∴Σ∴", H1),
        Spacer(1, .15*cm),
        Paragraph("Εν Ονόματι και Υπό την Αιγίδα", H2),
        Paragraph("της Μεγάλης Στοάς της Ελλάδος", H2),
        Paragraph("των Αρχαίων Ελευθέρων και Αποδεδεγμένων Τεκτόνων", H2),
        Spacer(1, .1*cm),
        Paragraph("Σ∴ Στ∴ ΑΚΡΟΠΟΛΙΣ  υπ' αρ. 84       εν Αν∴Αθ∴", LDG),
        HRFlowable(width="100%", thickness=1.5, color=CNVY, spaceAfter=8),
    ]

    # ── ΤΙΤΛΟΣ ────────────────────────────────────────────────
    βαθμ = d.get("βαθμός_γενική","Μαθητού")
    abbr = βαθμ[:3]  # Μαθ / Ετα / Διδ
    ημερ = d.get("ημερομηνία","")
    story.append(Paragraph(
        f"Πρακτικόν Συνεδρίας της {ημερ} εις Βαθμ∴ {abbr}∴", TTL))

    # ── ΗΜΕΡΗΣΙΑ ΔΙΑΤΑΞΗ ──────────────────────────────────────
    agenda = d.get("ημερησία_διάταξη", [])
    if agenda:
        story.append(Spacer(1, .2*cm))
        story.append(Paragraph("<b>Ημερησία Διάταξις:</b>", HDA))
        for item in agenda:
            story.append(Paragraph(f"– {item}", BUL))
        story.append(Spacer(1, .2*cm))

    story.append(HRFlowable(width="100%", thickness=.5, color=CGOLD, spaceAfter=10))

    # ── ΣΩΜΑ ΠΡΑΚΤΙΚΩΝ ────────────────────────────────────────
    body = d.get("κείμενο_πρακτικών","")
    for para in body.split("\n\n"):
        para = para.strip()
        if not para:
            continue
        lines = [l.strip() for l in para.split("\n") if l.strip()]
        if lines and all(l[:1] in ("-","–","•","*") for l in lines):
            for ln in lines:
                story.append(Paragraph(f"   {ln}", BUL))
        else:
            story.append(Paragraph(para.replace("\n"," "), BOD))

    # ── ΚΟΡΜΟΣ ────────────────────────────────────────────────
    κορμ = d.get("κορμός_αγαθοεργίας", 0)
    κολ  = d.get("κορμός_ολογράφως", "")
    if κορμ:
        story.append(Paragraph(
            f"Εκ του Κορμού της Αγαθοεργίας εβλάστησαν "
            f"<b>{κολ} ({κορμ:.2f})</b> όστρακα.", BOD))

    # ── ΚΛΕΙΣΙΜΟ ──────────────────────────────────────────────
    σεβ = d.get("σεβάσμιος","")
    story += [
        Spacer(1, .3*cm),
        Paragraph(
            f"Τέλος, οι Εργασίες έκλεισαν κανονικώς υπό την Σφύραν "
            f"του Σεβ∴ Διδ∴ <b>{σεβ}</b>, "
            f"των Αδδ∴ της Σ∴ Στ∴ μας ευχαριστημένων και ικανοποιημένων.", BOD),
        Spacer(1, .2*cm),
        Paragraph("Είπον Σεβ∴ Διδ∴.", IPO),
        Spacer(1, 1.5*cm),
    ]

    # ── ΥΠΟΓΡΑΦΕΣ (διάταξη υποδείγματος) ─────────────────────
    γραμ = d.get("γραμματεύς","")
    ρητ  = d.get("ρήτωρ","")

    def sig_col(title, name):
        return [Paragraph(title, SGN), Spacer(1,1.2*cm), Paragraph(name, SGNB)]

    # Σεβάσμιος κεντρικά (πλήρες πλάτος)
    story.append(Table([[sig_col("Ο Σεβ∴ Διδ∴", σεβ)]], colWidths=[14*cm],
                       hAlign="CENTER"))
    story.append(Spacer(1, .8*cm))
    # Γραμματεύς αριστερά — Ρήτωρ δεξιά
    story.append(Table(
        [[sig_col("Ο Γραμματεύς", γραμ), sig_col("Ο Ρήτωρ", ρητ)]],
        colWidths=[7*cm, 7*cm], hAlign="CENTER"
    ))

    story += [
        Spacer(1, .6*cm),
        HRFlowable(width="100%", thickness=.3, color=colors.lightgrey),
        Paragraph(
            f"Αρ. Πρωτ.: {d.get('αρ_πρωτ','')}  |  "
            f"Ημερομηνία: {ημερ}  |  Βαθμ∴: {βαθμ}", SML),
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
def show_editor(r: dict) -> dict:
    st.markdown("---")
    st.markdown("## ✏️ Επεξεργασία Πρακτικού")
    st.caption("Ελέγξτε και διορθώστε τα πεδία — το AI κάνει λάθη, εσείς τα διορθώνετε.")

    c1, c2, c3 = st.columns(3)
    with c1:
        r["ημερομηνία"]        = st.text_input("Ημερομηνία (DD/MM/YYYY)", r.get("ημερομηνία",""))
        r["ημέρα"]             = st.text_input("Ημέρα (π.χ. Τρίτην)", r.get("ημέρα",""))
        r["βαθμός_γενική"]     = st.text_input("Βαθμός γενική (π.χ. Μαθητού)", r.get("βαθμός_γενική","Μαθητού"))
        r["τόπος"]             = st.text_input("Τόπος", r.get("τόπος","τον Τεκτ∴ Ναόν Απόλλων"))
    with c2:
        r["σεβάσμιος"]         = st.text_input("Σεβ∴ Διδ∴", r.get("σεβάσμιος",""))
        r["γραμματεύς"]        = st.text_input("Γραμματεύς", r.get("γραμματεύς",""))
        r["ρήτωρ"]             = st.text_input("Ρήτωρ", r.get("ρήτωρ",""))
        r["αρ_πρωτ"]           = st.text_input("Αρ. Πρωτοκόλλου", r.get("αρ_πρωτ",""))
    with c3:
        r["παρόντες_αριθμός"]  = st.number_input("Παρόντες (αριθμός)", 0, 200,
                                                   int(r.get("παρόντες_αριθμός", 0)))
        r["παρόντες_ολογράφως"]= st.text_input("Παρόντες (ολογράφως)",
                                                r.get("παρόντες_ολογράφως",""))
        r["κορμός_αγαθοεργίας"]= st.number_input("Κορμός (€)", 0.0, 99999.0,
                                                   float(r.get("κορμός_αγαθοεργίας",0)),
                                                   step=1.0, format="%.2f")
        r["κορμός_ολογράφως"]  = st.text_input("Κορμός ολογράφως",
                                                r.get("κορμός_ολογράφως",""))

    st.markdown("#### 📋 Ημερησία Διάταξη")
    agenda_raw = st.text_area(
        "Ένα θέμα ανά γραμμή:",
        "\n".join(r.get("ημερησία_διάταξη",[])),
        height=90, label_visibility="collapsed"
    )
    r["ημερησία_διάταξη"] = [l.strip() for l in agenda_raw.splitlines() if l.strip()]

    st.markdown("#### 📄 Κείμενο Πρακτικών")
    st.caption("Χωρίζετε παραγράφους με κενή γραμμή · Bullet lines ξεκινούν με –")
    r["κείμενο_πρακτικών"] = st.text_area(
        "",
        r.get("κείμενο_πρακτικών",""),
        height=550, label_visibility="collapsed"
    )
    return r


# ══════════════════════════════════════════════════════════════
# TABS
# ══════════════════════════════════════════════════════════════
tab_main, tab_help = st.tabs(["🎵 Ηχογράφηση → Πρακτικά", "ℹ️ Οδηγίες & Ρυθμίσεις"])

# ════════════════════════════════════════
# TAB 1 — ΚΥΡΙΑ ΛΕΙΤΟΥΡΓΙΑ
# ════════════════════════════════════════
with tab_main:

    # ── ΒΗΜΑ 1: Στοιχεία ────────────────
    st.markdown("### Βήμα 1 · Στοιχεία Συνεδρίασης")
    ca, cb, cc = st.columns(3)
    with ca:
        sel_βαθμ = st.selectbox("Βαθμός", list(ΒΑΘΜΟΙ_GEN.keys()))
        sel_ημερ = st.date_input("Ημερομηνία", value=date.today())
    with cb:
        sel_σεβ  = st.text_input("Σεβ∴ Διδ∴", placeholder="Όνομα Επώνυμο")
        sel_γραμ = st.text_input("Γραμματεύς", placeholder="Όνομα Επώνυμο")
    with cc:
        sel_ρητ   = st.text_input("Ρήτωρ", placeholder="Όνομα Επώνυμο")
        sel_extra = st.text_area("Επιπλέον πλαίσιο για AI",
                                 placeholder="π.χ. 14 παρόντες, ψηφοφορία για Αδ∴ Χ...",
                                 height=68)

    # ── ΒΗΜΑ 2: Αρχείο ──────────────────
    st.markdown("---")
    st.markdown("### Βήμα 2 · Αρχείο Ηχογράφησης")

    audio_file = st.file_uploader(
        f"Ανεβάστε αρχείο (WAV, MP3, M4A, OGG — max {MAX_MB_RAW}MB)",
        type=SUPPORTED
    )

    if audio_file:
        raw_bytes = audio_file.getvalue()
        size_mb   = len(raw_bytes) / (1024*1024)
        ext       = audio_file.name.rsplit(".",1)[-1].lower()

        st.audio(audio_file)

        needs_compress = (size_mb > MAX_MB_SEND) or (ext == "wav")

        col_info, col_btn = st.columns([3,1])
        with col_info:
            if size_mb > MAX_MB_RAW:
                st.error(f"⛔ {size_mb:.1f}MB — Υπέρβαση ορίου {MAX_MB_RAW}MB. Χρησιμοποιήστε μικρότερο αρχείο.")
                needs_compress = False
            elif needs_compress:
                st.warning(
                    f"📦 **{size_mb:.1f}MB** — "
                    f"{'WAV αρχείο · ' if ext=='wav' else 'Μεγάλο αρχείο · '}"
                    f"Πατήστε **Συμπίεση** για μετατροπή σε MP3 128kbps πριν σταλεί στο AI."
                )
            else:
                st.success(f"✅ {audio_file.name} — {size_mb:.1f}MB — Έτοιμο για αποστολή.")
                st.session_state["ready_audio"] = raw_bytes
                st.session_state["ready_ext"]   = ext

        with col_btn:
            if needs_compress and size_mb <= MAX_MB_RAW:
                if st.button("🔄 Συμπίεση σε MP3", use_container_width=True, type="secondary"):
                    with st.spinner(f"Συμπίεση {size_mb:.1f}MB…"):
                        comp, msg, out_ext = compress_to_mp3(raw_bytes, ext)
                    if comp is None:
                        st.error(msg)
                    else:
                        comp_mb = len(comp)/(1024*1024)
                        if msg:  # warning (fallback mode)
                            st.warning(msg)
                        else:
                            st.success(f"✅ {size_mb:.1f}MB → {comp_mb:.1f}MB MP3")
                        st.session_state["ready_audio"] = comp
                        st.session_state["ready_ext"]   = out_ext
                        st.rerun()

        # Κουμπί λήψης MP3 αν έγινε συμπίεση
        if (st.session_state.get("ready_ext") == "mp3" and ext == "wav"
                and "ready_audio" in st.session_state):
            st.download_button(
                "⬇️ Λήψη συμπιεσμένου MP3",
                data=st.session_state["ready_audio"],
                file_name=audio_file.name.replace(".wav",".mp3"),
                mime="audio/mpeg"
            )

    # ── ΒΗΜΑ 3: Μεταγραφή ───────────────
    st.markdown("---")
    st.markdown("### Βήμα 3 · Μεταγραφή & Σύνταξη Πρακτικών")

    ready = "ready_audio" in st.session_state

    if not ready:
        st.info("📌 Ανεβάστε και (αν χρειαστεί) συμπιέστε αρχείο ηχογράφησης πρώτα.")

    if st.button("🎧 Μεταγραφή & Σύνταξη μέσω Claude AI",
                 type="primary", use_container_width=True, disabled=not ready):
        ctx = (f"Βαθμός: {sel_βαθμ} | Ημερομηνία: {sel_ημερ} | "
               f"Σεβ∴ Διδ∴: {sel_σεβ} | Γραμματεύς: {sel_γραμ} | Ρήτωρ: {sel_ρητ}\n{sel_extra}")

        with st.spinner("🔄 Claude AI μεταγράφει και συντάσσει πρακτικά… (~2-3 λεπτά)"):
            result, err = call_claude_audio(
                st.session_state["ready_audio"],
                st.session_state["ready_ext"], ctx)

        if err:
            st.error(err)
        elif result:
            # Γέμισμα από UI αν το AI δεν έβγαλε τιμές
            for k, v in [("σεβάσμιος",sel_σεβ),("γραμματεύς",sel_γραμ),
                          ("ρήτωρ",sel_ρητ)]:
                if not result.get(k) and v: result[k] = v
            if not result.get("βαθμός_γενική"):
                result["βαθμός_γενική"] = ΒΑΘΜΟΙ_GEN[sel_βαθμ]
            if not result.get("ημερομηνία"):
                result["ημερομηνία"] = sel_ημερ.strftime("%d/%m/%Y")

            st.session_state["praktiko"] = result
            st.success("✅ Έτοιμο! Ελέγξτε και επεξεργαστείτε παρακάτω.")

    # ── RAW ΜΕΤΑΓΡΑΦΗ ───────────────────
    if "praktiko" in st.session_state:
        raw_tr = st.session_state["praktiko"].get("μεταγραφή_λέξη_προς_λέξη","")
        if raw_tr:
            with st.expander("📄 Ακατέργαστη μεταγραφή (λέξη-προς-λέξη)", expanded=False):
                st.text_area("", raw_tr, height=220, label_visibility="collapsed")
                st.download_button("⬇️ .txt", raw_tr.encode("utf-8"),
                                   f"μεταγραφή_{date.today()}.txt","text/plain")

        # ── EDITOR ─────────────────────
        edited = show_editor(st.session_state["praktiko"].copy())

        # ── ΒΗΜΑ 4: PDF ────────────────
        st.markdown("---")
        st.markdown("### Βήμα 4 · Εκτύπωση PDF")
        col_gen, col_dl = st.columns(2)

        with col_gen:
            if st.button("📄 Δημιουργία PDF Πρακτικού",
                         type="primary", use_container_width=True):
                with st.spinner("Δημιουργία PDF…"):
                    pdf = generate_praktiko_pdf(edited)
                st.session_state["pdf_bytes"] = pdf.getvalue()
                st.session_state["pdf_label"] = edited.get("ημερομηνία","").replace("/","_")
                st.success("✅ PDF έτοιμο!")

        with col_dl:
            if "pdf_bytes" in st.session_state:
                st.download_button(
                    "⬇️ Λήψη PDF — Πρακτικό Συνεδρίασης",
                    data=st.session_state["pdf_bytes"],
                    file_name=f"πρακτικό_{st.session_state.get('pdf_label',date.today())}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )

# ════════════════════════════════════════
# TAB 2 — ΟΔΗΓΙΕΣ
# ════════════════════════════════════════
with tab_help:
    st.markdown(f"""
    ## Ροή Εργασίας
    1. Συμπληρώστε βαθμό, ημερομηνία, αξιωματικούς
    2. Ανεβάστε ηχογράφηση (WAV ή MP3)
    3. Αν εμφανιστεί "Συμπίεση" → πατήστε το (WAV ή > {MAX_MB_SEND}MB)
    4. Πατήστε **Μεταγραφή & Σύνταξη**
    5. Επεξεργαστείτε τα πεδία (ελέγξτε ονόματα, κορμό κλπ.)
    6. **Δημιουργία PDF** → Λήψη → Εκτύπωση

    ## Αρχεία που χρειάζονται ενημέρωση

    ### `requirements.txt` — προσθέστε:
    ```
    pydub
    ```

    ### `packages.txt` — δημιουργήστε αν δεν υπάρχει (στη ρίζα του repo):
    ```
    ffmpeg
    ```
    > Χωρίς ffmpeg η συμπίεση WAV→MP3 δεν λειτουργεί στο Streamlit Cloud.

    ## Όρια αρχείων
    | Μορφή | Ανά ώρα | Χωρίς συμπίεση |
    |-------|---------|----------------|
    | WAV 44.1kHz stereo | ~600MB | ❌ Πάντα συμπίεση |
    | MP3 128kbps | ~60MB | ✅ < 20 λεπτά |
    | MP3 256kbps | ~115MB | ⚠️ Συμπίεση αν > 20MB |
    | M4A / OGG | ~50MB | ✅ Γενικά OK |

    Για **2ωρη συνεδρίαση σε WAV**: WAV (~1.2GB) → MP3 128kbps (~120MB) → το API δέχεται έως 20MB,
    άρα θα χρειαστεί να σπάσετε σε τμήματα ~20 λεπτών. Μελλοντική βελτίωση: αυτόματος διαχωρισμός.

    ## Secrets (Streamlit Cloud → App Settings → Secrets)
    ```toml
    [AI]
    ANTHROPIC_API_KEY = "sk-ant-..."
    ```
    """)

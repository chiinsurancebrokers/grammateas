# -*- coding: utf-8 -*-
"""
Σελίδα 20 — Μεταγραφή & Σύνταξη Πρακτικών με AI

Λειτουργίες:
  • Upload m4a/mp3/wav/mp4/webm
  • Μεταγραφή στα Ελληνικά με OpenAI transcription
  • AI ανάλυση:
      - παρόντες
      - αποφάσεις
      - ημερομηνίες
      - ενέργειες / εκκρεμότητες
      - αυτόματος διαχωρισμός ανά ομιλητή όπου είναι δυνατό
  • Σύνταξη επίσημου πρακτικού
  • Export σε Word (.docx) και PDF
"""

import os
import io
import json
import tempfile
from datetime import datetime, date
from typing import Dict, Any, List

import streamlit as st
from openai import OpenAI
from docx import Document
from docx.shared import Pt
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet


# ─────────────────────────────────────────────────────────────
# PAGE SETUP
# ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Μεταγραφή & Πρακτικά",
    page_icon="🎤",
    layout="wide",
)

st.markdown("# 🎤 Μεταγραφή & Σύνταξη Πρακτικών")
st.caption(
    "Ανεβάστε ηχογράφηση συνεδρίας και δημιουργήστε μεταγραφή, ανάλυση και επίσημο πρακτικό."
)


# ─────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────
def get_openai_key() -> str:
    """Διαβάζει OpenAI API key από Streamlit secrets ή env."""
    try:
        return (
            st.secrets.get("OPENAI_API_KEY", "")
            or st.secrets.get("AI", {}).get("OPENAI_API_KEY", "")
            or os.getenv("OPENAI_API_KEY", "")
        )
    except Exception:
        return os.getenv("OPENAI_API_KEY", "")


def get_client() -> OpenAI:
    key = get_openai_key()
    if not key:
        st.error("❌ Δεν βρέθηκε OPENAI_API_KEY στα secrets ή στα environment variables.")
        st.stop()
    return OpenAI(api_key=key)


def safe_json_loads(raw: str) -> Dict[str, Any]:
    """Καθαρίζει πιθανό markdown και επιστρέφει JSON dict."""
    raw = (raw or "").strip()
    raw = raw.replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(raw)
    except Exception:
        return {
            "speakers": [],
            "present": [],
            "dates": [],
            "decisions": [],
            "actions": [],
            "summary": raw,
        }


def transcribe_audio(client: OpenAI, uploaded_file, language: str = "el") -> str:
    """Μεταγραφή audio χωρίς pydub/ffmpeg."""
    suffix = os.path.splitext(uploaded_file.name)[1] or ".m4a"

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded_file.getbuffer())
        tmp_path = tmp.name

    try:
        with open(tmp_path, "rb") as audio:
            result = client.audio.transcriptions.create(
                model="gpt-4o-mini-transcribe",
                file=audio,
                language=language,
            )
        return result.text or ""
    finally:
        try:
            os.remove(tmp_path)
        except Exception:
            pass


def analyse_transcript(client: OpenAI, transcript: str) -> Dict[str, Any]:
    """AI extraction: ομιλητές, παρόντες, αποφάσεις, ημερομηνίες."""
    system = """
Είσαι έμπειρος Γραμματεύς. Αναλύεις ελληνική μεταγραφή συνεδρίας.

Επέστρεψε ΜΟΝΟ valid JSON με ακριβώς τα παρακάτω keys:
{
  "speakers": [
    {"speaker": "Ομιλητής 1 ή όνομα αν προκύπτει", "points": ["..."]}
  ],
  "present": ["..."],
  "dates": ["..."],
  "decisions": ["..."],
  "actions": [
    {"action": "...", "owner": "...", "deadline": "..."}
  ],
  "summary": "Σύντομη σύνοψη"
}

Κανόνες:
- Μην επινοείς ονόματα.
- Αν κάτι δεν προκύπτει καθαρά, γράψε "Δεν προκύπτει σαφώς".
- Οι αποφάσεις να είναι ξεκάθαρες και πρακτικές.
- Τα actions να έχουν owner/deadline μόνο αν αναφέρονται.
""".strip()

    response = client.chat.completions.create(
        model="gpt-4o",
        temperature=0.2,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": transcript},
        ],
    )
    raw = response.choices[0].message.content
    return safe_json_loads(raw)


def draft_minutes(client: OpenAI, transcript: str, analysis: Dict[str, Any], meta: Dict[str, str]) -> str:
    """Σύνταξη επίσημου πρακτικού."""
    system = """
Είσαι Γραμματεύς Τεκτονικής Στοάς και συντάσσεις επίσημο πρακτικό.
Το ύφος πρέπει να είναι φυσικό, επίσημο, καθαρό και όχι εμφανώς AI.

Χρησιμοποίησε δομή:
ΠΡΑΚΤΙΚΟΝ ΣΥΝΕΔΡΙΑΣ
Στοιχεία Συνεδρίας
Έναρξις
Παρόντες
Θέματα Ημερήσιας Διάταξης
Συζήτηση
Αποφάσεις
Ενέργειες / Εκκρεμότητες
Λήξις

Κανόνες:
- Μην επινοείς γεγονότα.
- Όπου υπάρχει αβεβαιότητα γράψε ήπια: "εκ της μεταγραφής δεν προκύπτει σαφώς".
- Κράτησε τεκτονικό ύφος όπου αρμόζει.
""".strip()

    user_content = f"""
Στοιχεία συνεδρίας:
{json.dumps(meta, ensure_ascii=False, indent=2)}

Ανάλυση:
{json.dumps(analysis, ensure_ascii=False, indent=2)}

Μεταγραφή:
{transcript}
""".strip()

    response = client.chat.completions.create(
        model="gpt-4o",
        temperature=0.25,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user_content},
        ],
    )
    return response.choices[0].message.content or ""


def create_docx(minutes_text: str, meta: Dict[str, str]) -> bytes:
    doc = Document()

    style = doc.styles["Normal"]
    style.font.name = "Arial"
    style.font.size = Pt(11)

    title = doc.add_heading("ΠΡΑΚΤΙΚΟΝ ΣΥΝΕΔΡΙΑΣ", level=1)
    title.alignment = 1

    doc.add_paragraph(f"Στοά: {meta.get('stoaa', '')}")
    doc.add_paragraph(f"Ημερομηνία: {meta.get('meeting_date', '')}")
    doc.add_paragraph(f"Βαθμός: {meta.get('degree', '')}")
    doc.add_paragraph("")

    for line in minutes_text.splitlines():
        line = line.strip()
        if not line:
            doc.add_paragraph("")
        elif line.isupper() and len(line) < 80:
            doc.add_heading(line, level=2)
        else:
            doc.add_paragraph(line)

    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf.read()


def create_pdf(minutes_text: str, meta: Dict[str, str]) -> bytes:
    buf = io.BytesIO()
    pdf = SimpleDocTemplate(
        buf,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40,
    )

    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("ΠΡΑΚΤΙΚΟΝ ΣΥΝΕΔΡΙΑΣ", styles["Title"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"Στοά: {meta.get('stoaa', '')}", styles["Normal"]))
    story.append(Paragraph(f"Ημερομηνία: {meta.get('meeting_date', '')}", styles["Normal"]))
    story.append(Paragraph(f"Βαθμός: {meta.get('degree', '')}", styles["Normal"]))
    story.append(Spacer(1, 12))

    safe_text = (
        minutes_text
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("\n", "<br/>")
    )
    story.append(Paragraph(safe_text, styles["Normal"]))

    pdf.build(story)
    buf.seek(0)
    return buf.read()


def analysis_to_markdown(analysis: Dict[str, Any]) -> None:
    st.markdown("### 🔎 AI Ανάλυση")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 👥 Παρόντες")
        present = analysis.get("present", [])
        if present:
            for p in present:
                st.markdown(f"- {p}")
        else:
            st.caption("Δεν εντοπίστηκαν σαφώς.")

        st.markdown("#### 📅 Ημερομηνίες")
        dates = analysis.get("dates", [])
        if dates:
            for d in dates:
                st.markdown(f"- {d}")
        else:
            st.caption("Δεν εντοπίστηκαν σαφώς.")

    with col2:
        st.markdown("#### ✅ Αποφάσεις")
        decisions = analysis.get("decisions", [])
        if decisions:
            for d in decisions:
                st.markdown(f"- {d}")
        else:
            st.caption("Δεν εντοπίστηκαν σαφώς.")

        st.markdown("#### 📌 Ενέργειες")
        actions = analysis.get("actions", [])
        if actions:
            for a in actions:
                if isinstance(a, dict):
                    st.markdown(
                        f"- **{a.get('action', '')}** "
                        f"| Υπεύθυνος: {a.get('owner', '—')} "
                        f"| Προθεσμία: {a.get('deadline', '—')}"
                    )
                else:
                    st.markdown(f"- {a}")
        else:
            st.caption("Δεν εντοπίστηκαν σαφώς.")

    with st.expander("🗣️ Αυτόματος διαχωρισμός ανά ομιλητή"):
        speakers = analysis.get("speakers", [])
        if speakers:
            for s in speakers:
                st.markdown(f"**{s.get('speaker', 'Ομιλητής')}**")
                for point in s.get("points", []):
                    st.markdown(f"- {point}")
        else:
            st.caption("Δεν προέκυψε καθαρός διαχωρισμός ομιλητών.")


# ─────────────────────────────────────────────────────────────
# UI
# ─────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Ρυθμίσεις")
    stoaa = st.text_input("Στοά", value="Σ∴ Στ∴ ΑΚΡΟΠΟΛΙΣ υπ’ αρ. 84")
    meeting_date = st.date_input("Ημερομηνία συνεδρίας", value=date.today())
    degree = st.selectbox("Βαθμός", ["Μαθητού", "Εταίρου", "Διδασκάλου", "Άλλο"])
    language = st.selectbox("Γλώσσα μεταγραφής", ["el", "en"], index=0)

meta = {
    "stoaa": stoaa,
    "meeting_date": meeting_date.strftime("%d/%m/%Y"),
    "degree": degree,
}

uploaded = st.file_uploader(
    "Ανεβάστε ηχογράφηση",
    type=["m4a", "mp3", "wav", "mp4", "webm", "mpeg", "mpga"],
    help="Δεν χρησιμοποιείται pydub/ffmpeg. Το αρχείο αποστέλλεται απευθείας στο OpenAI transcription API.",
)

if uploaded:
    st.audio(uploaded)
    st.success(f"✅ Φορτώθηκε αρχείο: {uploaded.name}")

    if st.button("🎧 Βήμα 1 · Μεταγραφή", type="primary", use_container_width=True):
        client = get_client()
        with st.spinner("Γίνεται μεταγραφή με AI..."):
            transcript = transcribe_audio(client, uploaded, language=language)
        st.session_state["page20_transcript"] = transcript
        st.success("✅ Η μεταγραφή ολοκληρώθηκε.")

if "page20_transcript" in st.session_state:
    st.markdown("---")
    st.markdown("## 📝 Μεταγραφή")
    transcript_edit = st.text_area(
        "Μπορείτε να διορθώσετε τη μεταγραφή πριν την ανάλυση.",
        value=st.session_state["page20_transcript"],
        height=350,
    )
    st.session_state["page20_transcript"] = transcript_edit

    col_a, col_b = st.columns(2)

    with col_a:
        st.download_button(
            "⬇️ Λήψη μεταγραφής TXT",
            data=transcript_edit.encode("utf-8"),
            file_name=f"transcription_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
            mime="text/plain",
            use_container_width=True,
        )

    with col_b:
        if st.button("🔎 Βήμα 2 · AI Ανάλυση", use_container_width=True):
            client = get_client()
            with st.spinner("Γίνεται ανάλυση μεταγραφής..."):
                analysis = analyse_transcript(client, transcript_edit)
            st.session_state["page20_analysis"] = analysis
            st.success("✅ Η ανάλυση ολοκληρώθηκε.")

if "page20_analysis" in st.session_state:
    st.markdown("---")
    analysis = st.session_state["page20_analysis"]
    analysis_to_markdown(analysis)

    if st.button("📜 Βήμα 3 · Δημιουργία Επίσημου Πρακτικού", type="primary", use_container_width=True):
        client = get_client()
        with st.spinner("Συντάσσεται το επίσημο πρακτικό..."):
            minutes = draft_minutes(
                client=client,
                transcript=st.session_state["page20_transcript"],
                analysis=analysis,
                meta=meta,
            )
        st.session_state["page20_minutes"] = minutes
        st.success("✅ Το πρακτικό δημιουργήθηκε.")

if "page20_minutes" in st.session_state:
    st.markdown("---")
    st.markdown("## 📄 Πρακτικό")
    minutes_edit = st.text_area(
        "Μπορείτε να κάνετε τελικές διορθώσεις πριν το export.",
        value=st.session_state["page20_minutes"],
        height=500,
    )
    st.session_state["page20_minutes"] = minutes_edit

    docx_bytes = create_docx(minutes_edit, meta)
    pdf_bytes = create_pdf(minutes_edit, meta)

    col1, col2 = st.columns(2)

    with col1:
        st.download_button(
            "⬇️ Export σε Word (.docx)",
            data=docx_bytes,
            file_name=f"praktiko_{datetime.now().strftime('%Y%m%d_%H%M')}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True,
        )

    with col2:
        st.download_button(
            "⬇️ Export σε PDF",
            data=pdf_bytes,
            file_name=f"praktiko_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
            mime="application/pdf",
            use_container_width=True,
        )


# -*- coding: utf-8 -*-
"""
Σελίδα 19 — Διαδικασίες & Έντυπα ΜΣΤΕ
Clean rebuild για Streamlit.

Βασική λογική:
- Δεν βασίζεται σε Claude για τα εκλογικά έντυπα.
- Γράφει απευθείας σε Word tables με python-docx.
- Υποστηρίζει ξεχωριστά:
  1) εκλεγέντες αξιωματικούς
  2) πρόσθετους αξιωματικούς
  3) εξελεγκτική επιτροπή
  4) ψηφίσαντες Διδασκάλους για το έντυπο 5
- Κρατάει editor πριν τη δημιουργία των αρχείων.

Τοποθέτηση:
    pages/19_Διαδικασίες.py

Απαραίτητα packages:
    streamlit
    pandas
    python-docx
"""

import io
import os
import re
import zipfile
from dataclasses import dataclass
from datetime import date
from typing import Any, Dict, Iterable, List, Optional, Tuple

import pandas as pd
import streamlit as st
from docx import Document
from docx.table import _Cell, Table
from docx.text.paragraph import Paragraph

try:
    from modules.database import init_db, get_all_members
except Exception:
    init_db = None
    get_all_members = None


# ══════════════════════════════════════════════════════════════
# APP SETUP
# ══════════════════════════════════════════════════════════════
if init_db:
    init_db()

st.set_page_config(
    page_title="Διαδικασίες & Έντυπα",
    page_icon="📋",
    layout="wide",
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FORMS_ROOT = os.path.join(BASE_DIR, "forms")

STOAA_DEFAULTS = {
    "name": "ΑΚΡΟΠΟΛΙΣ",
    "number": "84",
    "anatoli": "Αθηνών",
    "address": "",
    "city": "Αθήνα",
    "street": "",
    "street_no": "",
    "zip": "",
}


# ══════════════════════════════════════════════════════════════
# DATA MODELS / CONFIG
# ══════════════════════════════════════════════════════════════
@dataclass
class FormInfo:
    name: str
    file: str
    description: str


@dataclass
class Procedure:
    code: str
    title: str
    subtitle: str
    description: str
    deadline_note: str
    forms: List[FormInfo]


PROCEDURES: Dict[str, Procedure] = {
    "ekloges": Procedure(
        code="ekloges",
        title="🗳️ Εκλογές Αξιωματικών & Εγκατάσταση",
        subtitle="Άρθρα 73–86 Γ.Κ.",
        description=(
            "Συμπλήρωση εντύπων αρχαιρεσιών: αναγγελία, απόσπασμα, "
            "αναλυτικός πίνακας, κατάσταση εκλεγέντων και ονομαστική κατάσταση ψηφισάντων."
        ),
        deadline_note="⏱️ Υποβολή εντός 10 ημερών από τις αρχαιρεσίες.",
        forms=[
            FormInfo("1. Αναγγελία Εκλογής Σεβασμίου & Συμβουλίου", "ekloges/1_-_ΑΝΑΓΓΕΛΙΑ_ΕΚΛΟΓΗΣ_ΣΕΒΑΣΜΙΟΥ___ΣΥΜΒΟΥΛΙΟΥ.docx", "Κύρια αναγγελία αποτελεσμάτων"),
            FormInfo("2Α. Απόσπασμα Εκλογής Αξιωματικών", "ekloges/2Α_-_ΑΠΟΣΠΑΣΜΑ_ΕΚΛΟΓΗΣ_ΑΞΙΩΜΑΤΙΚΩΝ.docx", "Απόσπασμα πρακτικών συνεδρίας εκλογής"),
            FormInfo("3. Αναλυτικός Πίνακας Εκλεγέντων", "ekloges/3_-_ΑΝΑΛΥΤΙΚΟΣ_ΠΙΝΑΚΑΣ__ΕΚΛΕΓΕΝΤΩΝ_ΑΞΙΩΜΑΤΙΚΩΝ.docx", "Πίνακας εκλεγέντων ανά αξίωμα"),
            FormInfo("4. Κατάσταση Εκλεγέντων Αξιωματικών", "ekloges/4_-_ΚΑΤΑΣΤΑΣΗ_ΕΚΛΕΓΕΝΤΩΝ_ΑΞΙΩΜΑΤΙΚΩΝ.docx", "Σύνοψη εκλεγέντων με στοιχεία επικοινωνίας"),
            FormInfo("5. Ονομαστική Κατάσταση Ψηφισάντων", "ekloges/5_-_ΟΝΟΜΑΣΤΙΚΗ_ΚΑΤΑΣΤΑΣΗ_ΨΗΦΙΣΑΝΤΩΝ.docx", "Κατάλογος Διδασκάλων που ψήφισαν"),
        ],
    ),
}

OFFICER_ROWS: List[Tuple[str, str, str]] = [
    ("ax_sev", "ΣΕΒΑΣΜΙΟΣ", "Τακτικός"),
    ("ax_a_ep", "Α΄ ΕΠΟΠΤΗΣ", "Τακτικός"),
    ("ax_b_ep", "Β΄ ΕΠΟΠΤΗΣ", "Τακτικός"),
    ("ax_rhtor", "ΡΗΤΩΡ", "Τακτικός"),
    ("ax_gramm", "ΓΡΑΜΜ. - ΣΦΡΑΓΙΔ.", "Τακτικός"),
    ("ax_a_dok", "Α΄ ΔΟΚΙΜΑΣΤΗΣ", "Τακτικός"),
    ("ax_tamias", "ΤΑΜΙΑΣ", "Τακτικός"),
    ("ax_eleon", "ΕΛΕΟΝΟΜΟΣ", "Τακτικός"),
    ("ax_tel", "ΤΕΛΕΤΑΡΧΗΣ", "Τακτικός"),
    ("ax_steg", "ΣΤΕΓΑΣΤΗΣ", "Τακτικός"),
    ("ax_b_dok", "Β΄ ΔΟΚΙΜΑΣΤΗΣ", "Τακτικός"),
    ("ax_arxitekt", "ΑΡΧΙΤ. - ΑΡΧΙΤΡ.", "Τακτικός"),
    ("ax_arxif", "ΑΡΧΕΙΟΦ. - ΒΙΒΛΙΟΦ.", "Τακτικός"),
    ("ax_xifok", "ΞΙΦΟΦ. - ΣΗΜΑΙΟΦ.", "Τακτικός"),
    ("pr_rhtor", "ΡΗΤΩΡ", "Πρόσθετος"),
    ("pr_gramm", "ΓΡΑΜΜ. - ΣΦΡΑΓΙΔ.", "Πρόσθετος"),
    ("pr_tamias", "ΤΑΜΙΑΣ", "Πρόσθετος"),
    ("pr_eleon", "ΕΛΕΟΝΟΜΟΣ", "Πρόσθετος"),
    ("pr_tel", "ΤΕΛΕΤΑΡΧΗΣ", "Πρόσθετος"),
]

EXELEGKTIKI_ROWS: List[Tuple[str, str, str]] = [
    ("ex_1", "ΜΕΛΟΣ 1", "Εξελεγκτική"),
    ("ex_2", "ΜΕΛΟΣ 2", "Εξελεγκτική"),
    ("ex_3", "ΜΕΛΟΣ 3", "Εξελεγκτική"),
]

# Πιθανές παραλλαγές τίτλων αξιωμάτων μέσα στα Word.
OFFICE_ALIASES: Dict[str, List[str]] = {
    "ΣΕΒΑΣΜΙΟΣ": ["ΣΕΒΑΣΜΙΟΣ"],
    "Α΄ ΕΠΟΠΤΗΣ": ["Α΄ ΕΠΟΠΤΗΣ", "Α' ΕΠΟΠΤΗΣ", "Α΄ Επόπτου", "Α' Επόπτου"],
    "Β΄ ΕΠΟΠΤΗΣ": ["Β΄ ΕΠΟΠΤΗΣ", "Β' ΕΠΟΠΤΗΣ", "Β΄ Επόπτου", "Β' Επόπτου"],
    "ΡΗΤΩΡ": ["ΡΗΤΩΡ", "Ρήτορα", "Πρόσθετου Ρήτορα"],
    "ΓΡΑΜΜ. - ΣΦΡΑΓΙΔ.": ["ΓΡΑΜΜ. - ΣΦΡΑΓΙΔ.", "ΓΡΑΜΜ. - ΣΦΡΑΓΙΔ", "Γραμματέα - Σφραγιδοφύλακα", "Πρόσθετου Γραμματέα - Σφραγιδοφύλακα"],
    "Α΄ ΔΟΚΙΜΑΣΤΗΣ": ["Α΄ ΔΟΚΙΜΑΣΤΗΣ", "Α' ΔΟΚΙΜΑΣΤΗΣ", "Α΄ Δοκιμαστή", "Α' Δοκιμαστή"],
    "ΤΑΜΙΑΣ": ["ΤΑΜΙΑΣ", "Ταμία", "Πρόσθετου Ταμία"],
    "ΕΛΕΟΝΟΜΟΣ": ["ΕΛΕΟΝΟΜΟΣ", "Ελεονόμου", "Πρόσθετου Ελεονόμου"],
    "ΤΕΛΕΤΑΡΧΗΣ": ["ΤΕΛΕΤΑΡΧΗΣ", "Τελετάρχη", "Πρόσθετου Τελετάρχη"],
    "ΣΤΕΓΑΣΤΗΣ": ["ΣΤΕΓΑΣΤΗΣ", "Στεγαστή"],
    "Β΄ ΔΟΚΙΜΑΣΤΗΣ": ["Β΄ ΔΟΚΙΜΑΣΤΗΣ", "Β' ΔΟΚΙΜΑΣΤΗΣ", "Β΄ Δοκιμαστή", "Β' Δοκιμαστή"],
    "ΑΡΧΙΤ. - ΑΡΧΙΤΡ.": ["ΑΡΧΙΤ. - ΑΡΧΙΤΡ.", "ΑΡΧΙΤ.  ΑΡΧΙΤΡ.", "Αρχιτέκτονα - Αρχιτρίκλινου"],
    "ΑΡΧΕΙΟΦ. - ΒΙΒΛΙΟΦ.": ["ΑΡΧΕΙΟΦ. - ΒΙΒΛΙΟΦ.", "Αρχειοφύλακα - Βιβλιοφύλακα"],
    "ΞΙΦΟΦ. - ΣΗΜΑΙΟΦ.": ["ΞΙΦΟΦ. - ΣΗΜΑΙΟΦ.", "Ξιφοφόρου - Σημαιοφόρου"],
}


# ══════════════════════════════════════════════════════════════
# GENERIC HELPERS
# ══════════════════════════════════════════════════════════════
def safe_str(value: Any) -> str:
    if value is None:
        return ""
    if pd.isna(value) if not isinstance(value, (dict, list, tuple)) else False:
        return ""
    return str(value).strip()


def normalize_text(text: str) -> str:
    text = safe_str(text)
    text = text.replace("\u00a0", " ")
    text = re.sub(r"\s+", " ", text)
    text = text.replace("’", "'")
    return text.strip().upper()


def member_value(member: Dict[str, Any], *keys: str) -> str:
    for key in keys:
        if key in member and safe_str(member.get(key)):
            return safe_str(member.get(key))
    return ""


def member_full_name(member: Dict[str, Any]) -> str:
    return f"{member_value(member, 'επώνυμο', 'eponimo', 'surname')} {member_value(member, 'όνομα', 'onoma', 'name')}".strip()


def member_full_with_patronymic(member: Dict[str, Any]) -> str:
    base = member_full_name(member)
    patronymic = member_value(member, "πατρώνυμο", "patronymic")
    return f"{base} του {patronymic}".strip() if patronymic else base


def member_amms(member: Dict[str, Any]) -> str:
    return member_value(member, "αρ_μητρώου_μσ", "αμμσ", "Α.Μ.Μ.Σ.", "arith_ms")


def member_ams(member: Dict[str, Any]) -> str:
    return member_value(member, "αρ_μητρώου_στοάς", "arith_stoas", "Α.Μ.Σ.")


def member_mobile(member: Dict[str, Any]) -> str:
    return member_value(member, "κινητό", "κινητο", "mobile")


def member_phone(member: Dict[str, Any]) -> str:
    return member_value(member, "τηλέφωνο", "τηλεφωνο", "phone")


def member_email(member: Dict[str, Any]) -> str:
    return member_value(member, "email", "e-mail", "mail")


def member_address(member: Dict[str, Any]) -> str:
    return member_value(member, "διεύθυνση", "διευθυνση", "address")


def member_city_zip(member: Dict[str, Any]) -> str:
    city = member_value(member, "πόλη", "πολη", "city")
    tk = member_value(member, "τ_κ", "τκ", "Τ.Κ.", "zip")
    return f"{city} {tk}".strip()


def load_members_df() -> pd.DataFrame:
    if not get_all_members:
        return pd.DataFrame()
    try:
        df = get_all_members()
        if df is None:
            return pd.DataFrame()
        return df.copy()
    except Exception as exc:
        st.warning(f"Δεν μπόρεσα να φορτώσω το μητρώο μελών: {exc}")
        return pd.DataFrame()


def df_to_member_options(df: pd.DataFrame) -> Dict[int, Dict[str, Any]]:
    result: Dict[int, Dict[str, Any]] = {}
    if df.empty:
        return result
    for i, row in df.iterrows():
        d = row.to_dict()
        mid = int(d.get("id", i + 1))
        result[mid] = d
    return result


def member_label(member: Dict[str, Any]) -> str:
    degree = member_value(member, "τεκτονικός_βαθμός", "βαθμός", "degree")
    amms = member_amms(member)
    suffix = f" — Α.Μ.Μ.Σ. {amms}" if amms else ""
    degree_part = f" ({degree})" if degree else ""
    return f"{member_full_name(member)}{degree_part}{suffix}"


def read_docx_preview(path: str, limit: int = 2500) -> str:
    try:
        doc = Document(path)
        parts: List[str] = []
        for p in doc.paragraphs:
            if p.text.strip():
                parts.append(p.text.strip())
        for table in doc.tables:
            for row in table.rows[:30]:
                row_txt = " | ".join(c.text.strip().replace("\n", " / ") for c in row.cells if c.text.strip())
                if row_txt:
                    parts.append(row_txt)
        text = "\n".join(parts)
        return text[:limit] + ("…" if len(text) > limit else "")
    except Exception as exc:
        return f"Δεν ήταν δυνατή η προεπισκόπηση: {exc}"


def write_cell(cell: _Cell, text: str, clear: bool = True) -> None:
    """Γράφει κείμενο κρατώντας κατά το δυνατόν τη μορφοποίηση του πρώτου run."""
    text = safe_str(text)
    if not text:
        return
    if not cell.paragraphs:
        cell.add_paragraph(text)
        return
    p = cell.paragraphs[0]
    if not p.runs:
        p.add_run(text)
        return
    p.runs[0].text = text
    if clear:
        for r in p.runs[1:]:
            r.text = ""
        for extra_p in cell.paragraphs[1:]:
            for r in extra_p.runs:
                r.text = ""


def replace_text_in_paragraph(paragraph: Paragraph, replacements: Dict[str, str]) -> None:
    full = "".join(run.text for run in paragraph.runs)
    new = full
    for old, val in replacements.items():
        new = new.replace(old, val)
    if new != full and paragraph.runs:
        paragraph.runs[0].text = new
        for r in paragraph.runs[1:]:
            r.text = ""


def iter_all_paragraphs(doc: Document) -> Iterable[Paragraph]:
    for p in doc.paragraphs:
        yield p
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for p in cell.paragraphs:
                    yield p


def row_text(row) -> str:
    return " | ".join(c.text.strip().replace("\n", " / ") for c in row.cells)


def find_col_with_text(row, aliases: List[str]) -> Optional[int]:
    normalized_aliases = [normalize_text(a) for a in aliases]
    for i, cell in enumerate(row.cells):
        ct = normalize_text(cell.text)
        if not ct:
            continue
        for alias in normalized_aliases:
            if ct == alias or alias in ct:
                return i
    return None


def write_after_col(row, start_col: int, values: List[str]) -> int:
    """
    Γράφει τιμές στα επόμενα cells από το start_col.
    Χρησιμοποιείται ως fallback σε Word tables με merged cells.
    """
    written = 0
    c = start_col + 1
    for value in values:
        while c < len(row.cells) and normalize_text(row.cells[c].text) in {"", " ", normalize_text(value)}:
            # κενό ή duplicate cell από merge: γράφουμε και προχωράμε
            write_cell(row.cells[c], value)
            written += 1
            c += 1
            break
        else:
            if c < len(row.cells):
                write_cell(row.cells[c], value)
                written += 1
                c += 1
    return written


def date_for_filename() -> str:
    return date.today().strftime("%Y%m%d")


def create_zip(files: List[Tuple[str, bytes]]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, data in files:
            zf.writestr(name, data)
    buf.seek(0)
    return buf.read()


def save_doc_to_bytes(doc: Document) -> bytes:
    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf.read()


# ══════════════════════════════════════════════════════════════
# INPUT / EDITOR HELPERS
# ══════════════════════════════════════════════════════════════
def blank_officers_df() -> pd.DataFrame:
    rows = []
    for field_key, office, section in OFFICER_ROWS + EXELEGKTIKI_ROWS:
        rows.append({
            "_field_key": field_key,
            "Ενότητα": section,
            "Αξίωμα": office,
            "Επώνυμο": "",
            "Όνομα": "",
            "Πατρώνυμο": "",
            "Α.Μ.Μ.Σ.": "",
            "Α.Μ.Σ.": "",
            "Διεύθυνση": "",
            "Πόλη - Τ.Κ.": "",
            "Κινητό": "",
            "Σταθερό": "",
            "Email": "",
            "Μύηση Μαθητή": "",
            "Μύηση Διδασκάλου": "",
            "Μέλος από": "",
            "Λευκές ψήφοι": "",
        })
    return pd.DataFrame(rows)


def officer_from_member(field_key: str, office: str, section: str, member: Optional[Dict[str, Any]]) -> Dict[str, str]:
    if not member:
        return {
            "_field_key": field_key, "Ενότητα": section, "Αξίωμα": office,
            "Επώνυμο": "", "Όνομα": "", "Πατρώνυμο": "", "Α.Μ.Μ.Σ.": "", "Α.Μ.Σ.": "",
            "Διεύθυνση": "", "Πόλη - Τ.Κ.": "", "Κινητό": "", "Σταθερό": "", "Email": "",
            "Μύηση Μαθητή": "", "Μύηση Διδασκάλου": "", "Μέλος από": "", "Λευκές ψήφοι": "",
        }
    return {
        "_field_key": field_key,
        "Ενότητα": section,
        "Αξίωμα": office,
        "Επώνυμο": member_value(member, "επώνυμο"),
        "Όνομα": member_value(member, "όνομα"),
        "Πατρώνυμο": member_value(member, "πατρώνυμο"),
        "Α.Μ.Μ.Σ.": member_amms(member),
        "Α.Μ.Σ.": member_ams(member),
        "Διεύθυνση": member_address(member),
        "Πόλη - Τ.Κ.": member_city_zip(member),
        "Κινητό": member_mobile(member),
        "Σταθερό": member_phone(member),
        "Email": member_email(member),
        "Μύηση Μαθητή": member_value(member, "ημ_μύησης", "ημ_μυησης"),
        "Μύηση Διδασκάλου": member_value(member, "ημ_μύησης_διδ", "ημ_αύξησης_διδ"),
        "Μέλος από": member_value(member, "μέλος_από", "melos_apo"),
        "Λευκές ψήφοι": "",
    }


def voter_from_member(idx: int, member: Dict[str, Any]) -> Dict[str, str]:
    return {
        "Α/Α": str(idx),
        "Α.Μ.Μ.Σ.": member_amms(member),
        "Ονοματεπώνυμο": member_full_name(member),
    }


def selected_member_ids_multiselect(label: str, options: Dict[int, Dict[str, Any]], key: str, max_count: Optional[int] = None) -> List[int]:
    ids = list(options.keys())
    selected = st.multiselect(
        label,
        ids,
        format_func=lambda mid: member_label(options[mid]),
        key=key,
    )
    if max_count and len(selected) > max_count:
        st.warning(f"Μέγιστος αριθμός: {max_count}. Θα χρησιμοποιηθούν οι πρώτοι {max_count}.")
        selected = selected[:max_count]
    return selected


def selected_member_selectbox(label: str, options: Dict[int, Dict[str, Any]], key: str) -> Optional[Dict[str, Any]]:
    ids = [0] + list(options.keys())
    def fmt(mid: int) -> str:
        return "— Επιλογή μέλους —" if mid == 0 else member_label(options[mid])
    selected = st.selectbox(label, ids, format_func=fmt, key=key)
    return options.get(selected) if selected else None


# ══════════════════════════════════════════════════════════════
# DOCX FILLERS — COMMON HEADER
# ══════════════════════════════════════════════════════════════
def apply_basic_replacements(doc: Document, header: Dict[str, str], stoaa: Dict[str, str]) -> None:
    replacements = {
        "ΑΚΡΟΠΟΛΙΣ": stoaa.get("name", "ΑΚΡΟΠΟΛΙΣ"),
        "2024 / 2026": header.get("Τεκτ. Διετία", "2024 / 2026").replace("-", " / "),
        "2024-2026": header.get("Τεκτ. Διετία", "2024-2026"),
    }
    for p in iter_all_paragraphs(doc):
        replace_text_in_paragraph(p, replacements)


def fill_header_cells(table: Table, header: Dict[str, str], stoaa: Dict[str, str]) -> None:
    """Γενική προσπάθεια συμπλήρωσης header πεδίων σε πίνακες."""
    diettia = header.get("Τεκτ. Διετία", "").replace("-", " / ")
    election_date = header.get("Ημ/νία Αρχαιρεσιών", "")
    voters_no = header.get("Ψηφίσαντες", "")

    for row in table.rows:
        for i, cell in enumerate(row.cells):
            ct = normalize_text(cell.text)
            if not ct:
                continue
            if "ΤΕΚΤ" in ct and "ΔΙΕΤ" in ct and diettia:
                if i + 1 < len(row.cells):
                    write_cell(row.cells[i + 1], diettia)
            elif "ΑΡΙΘΜΟΣ ΨΗΦΙΣ" in ct:
                if i + 1 < len(row.cells):
                    write_cell(row.cells[i + 1], voters_no)
            elif "Σ ΣΤΟΑ" in ct or "Σ∴ ΣΤ" in ct:
                if i + 1 < len(row.cells):
                    write_cell(row.cells[i + 1], stoaa.get("name", ""))
            elif "ΥΠ" in ct and "ΑΡΙΘ" in ct:
                if i + 1 < len(row.cells):
                    write_cell(row.cells[i + 1], stoaa.get("number", ""))
            elif "ΑΡΧΑΙΡΕΣ" in ct:
                if i + 1 < len(row.cells):
                    write_cell(row.cells[i + 1], election_date)
            elif "ΑΝΑΤΟΛ" in ct or "ΕΝ ΑΝ" in ct:
                if i + 1 < len(row.cells):
                    write_cell(row.cells[i + 1], stoaa.get("anatoli", ""))
            elif ct == "ΠΟΛΗ:" and i + 1 < len(row.cells):
                write_cell(row.cells[i + 1], stoaa.get("city", ""))
            elif ct == "ΟΔΟΣ:" and i + 1 < len(row.cells):
                write_cell(row.cells[i + 1], stoaa.get("street", ""))
            elif "ΑΡΙΘ" in ct and i + 1 < len(row.cells):
                # προσοχή να μη γράψει σε rows εκλογικών αριθμών αν δεν είναι header
                if len(row.cells) < 8:
                    write_cell(row.cells[i + 1], stoaa.get("street_no", ""))
            elif "Τ.Κ" in ct and i + 1 < len(row.cells):
                write_cell(row.cells[i + 1], stoaa.get("zip", ""))


# ══════════════════════════════════════════════════════════════
# DOCX FILLERS — FORM 4
# ══════════════════════════════════════════════════════════════
def fill_form4_katastasi(doc: Document, header: Dict[str, str], stoaa: Dict[str, str], officers: pd.DataFrame) -> None:
    if not doc.tables:
        return
    table = doc.tables[0]
    fill_header_cells(table, header, stoaa)

    current_section = "Τακτικός"
    used_keys: set[str] = set()

    for row in table.rows:
        rt = normalize_text(row_text(row))
        if "ΠΡΟΣΘΕΤΟΙ" in rt:
            current_section = "Πρόσθετος"
            continue
        if "ΤΑΚΤΙΚΟΙ" in rt:
            current_section = "Τακτικός"
            continue

        for _, data in officers.iterrows():
            section = safe_str(data.get("Ενότητα"))
            if section not in {"Τακτικός", "Πρόσθετος"}:
                continue
            if section != current_section:
                continue
            fk = safe_str(data.get("_field_key"))
            if fk in used_keys:
                continue
            office = safe_str(data.get("Αξίωμα"))
            aliases = OFFICE_ALIASES.get(office, [office])
            col = find_col_with_text(row, aliases)
            if col is None:
                continue

            values = [
                safe_str(data.get("Επώνυμο")),
                safe_str(data.get("Όνομα")),
                safe_str(data.get("Διεύθυνση")),
                safe_str(data.get("Πόλη - Τ.Κ.")),
                safe_str(data.get("Κινητό")),
                safe_str(data.get("Σταθερό")),
                safe_str(data.get("Email")),
            ]
            # Στα περισσότερα έντυπα οι στήλες είναι αμέσως μετά το αξίωμα.
            write_after_col(row, col, values)
            used_keys.add(fk)
            break


def fill_signatures(doc: Document, officers: pd.DataFrame) -> None:
    sev = officers.loc[officers["_field_key"] == "ax_sev"]
    gramm = officers.loc[officers["_field_key"] == "ax_gramm"]
    tamias = officers.loc[officers["_field_key"] == "ax_tamias"]
    sig_values = {
        "Ο ΣΕΒΑΣΜΙΟΣ": f"{safe_str(sev.iloc[0]['Επώνυμο'])} {safe_str(sev.iloc[0]['Όνομα'])}" if not sev.empty else "",
        "Ο ΓΡΑΜΜΑΤΕΑΣ": f"{safe_str(gramm.iloc[0]['Επώνυμο'])} {safe_str(gramm.iloc[0]['Όνομα'])}" if not gramm.empty else "",
        "Ο  ΤΑΜΙΑΣ": f"{safe_str(tamias.iloc[0]['Επώνυμο'])} {safe_str(tamias.iloc[0]['Όνομα'])}" if not tamias.empty else "",
        "Ο ΤΑΜΙΑΣ": f"{safe_str(tamias.iloc[0]['Επώνυμο'])} {safe_str(tamias.iloc[0]['Όνομα'])}" if not tamias.empty else "",
    }
    for table in doc.tables:
        for r_idx, row in enumerate(table.rows):
            for c_idx, cell in enumerate(row.cells):
                ct = normalize_text(cell.text)
                for label, value in sig_values.items():
                    if normalize_text(label) in ct and value:
                        # συνήθως το κενό για υπογραφή είναι 1-2 rows κάτω
                        for rr in range(r_idx + 1, min(r_idx + 4, len(table.rows))):
                            target = table.rows[rr].cells[c_idx]
                            if not target.text.strip() or "Ονοματεπώνυμο" in target.text:
                                write_cell(target, value)
                                break


# ══════════════════════════════════════════════════════════════
# DOCX FILLERS — FORM 5
# ══════════════════════════════════════════════════════════════
def extract_row_numbers(row) -> List[int]:
    nums: List[int] = []
    for cell in row.cells:
        m = re.search(r"(^|\s)(\d{1,2})\s*\.", cell.text.strip())
        if m:
            try:
                n = int(m.group(2))
                if 1 <= n <= 60 and n not in nums:
                    nums.append(n)
            except Exception:
                pass
    return nums


def fill_voter_slot(row, slot_no: int, voter: Dict[str, str]) -> bool:
    """
    Συμπληρώνει γραμμή ψηφίσαντα σε έντυπο με δύο στήλες ανά row:
    1-30 αριστερά, 31-60 δεξιά.
    Χρησιμοποιεί τη θέση του αριθμού μέσα στο row και γράφει στα επόμενα cells.
    """
    target_index = None
    for i, cell in enumerate(row.cells):
        if re.search(rf"(^|\s){slot_no}\s*\.", cell.text.strip()):
            target_index = i
            break
    if target_index is None:
        return False
    amms = safe_str(voter.get("Α.Μ.Μ.Σ."))
    name = safe_str(voter.get("Ονοματεπώνυμο"))
    if target_index + 1 < len(row.cells):
        write_cell(row.cells[target_index + 1], amms)
    if target_index + 2 < len(row.cells):
        write_cell(row.cells[target_index + 2], name)
    return True


def fill_form5_psifisantes(doc: Document, header: Dict[str, str], stoaa: Dict[str, str], voters: pd.DataFrame) -> None:
    if not doc.tables:
        return
    table = doc.tables[0]
    header = dict(header)
    header["Ψηφίσαντες"] = str(len(voters.index))
    fill_header_cells(table, header, stoaa)

    voter_records = voters.fillna("").to_dict("records")[:60]
    by_slot = {idx + 1: rec for idx, rec in enumerate(voter_records)}

    for row in table.rows:
        nums = extract_row_numbers(row)
        for n in nums:
            if n in by_slot:
                fill_voter_slot(row, n, by_slot[n])


# ══════════════════════════════════════════════════════════════
# DOCX FILLERS — FORM 3
# ══════════════════════════════════════════════════════════════
def fill_form3_analytikos(doc: Document, header: Dict[str, str], stoaa: Dict[str, str], officers: pd.DataFrame) -> None:
    if not doc.tables:
        return
    table = doc.tables[0]
    fill_header_cells(table, header, stoaa)

    current_section = "Τακτικός"
    ex_counter = 0
    used_keys: set[str] = set()

    for row in table.rows:
        rt = normalize_text(row_text(row))
        if "ΠΡΟΣΘΕΤΟΙ" in rt:
            current_section = "Πρόσθετος"
            continue
        if "ΕΞΕΛΕΓΚ" in rt:
            current_section = "Εξελεγκτική"
            ex_counter = 0
            continue
        if "ΤΑΚΤΙΚΟΙ" in rt:
            current_section = "Τακτικός"
            continue

        candidates = officers[officers["Ενότητα"] == current_section]
        for _, data in candidates.iterrows():
            fk = safe_str(data.get("_field_key"))
            if fk in used_keys:
                continue
            office = safe_str(data.get("Αξίωμα"))
            aliases = OFFICE_ALIASES.get(office, [office]) if current_section != "Εξελεγκτική" else [office]
            col = find_col_with_text(row, aliases)
            if col is None:
                # Εξελεγκτική συχνά έχει απλά κενές γραμμές ΜΕΛΟΣ 1/2/3
                if current_section == "Εξελεγκτική" and "ΜΕΛΟΣ" in rt:
                    col = find_col_with_text(row, ["ΜΕΛΟΣ"])
                else:
                    continue

            full_pat = " ".join(
                x for x in [safe_str(data.get("Επώνυμο")), safe_str(data.get("Όνομα")), f"του {safe_str(data.get('Πατρώνυμο'))}" if safe_str(data.get("Πατρώνυμο")) else ""] if x
            )
            values = [
                full_pat,
                safe_str(data.get("Α.Μ.Μ.Σ.")),
                safe_str(data.get("Μύηση Μαθητή")),
                safe_str(data.get("Μύηση Διδασκάλου")),
                safe_str(data.get("Μέλος από")),
                safe_str(data.get("Λευκές ψήφοι")),
            ]
            write_after_col(row, col, values)
            used_keys.add(fk)
            break


# ══════════════════════════════════════════════════════════════
# DOCX FILLERS — FORM 2A / FORM 1 SIMPLE
# ══════════════════════════════════════════════════════════════
def officer_name_by_key(officers: pd.DataFrame, key: str) -> str:
    row = officers.loc[officers["_field_key"] == key]
    if row.empty:
        return ""
    return f"{safe_str(row.iloc[0].get('Επώνυμο'))} {safe_str(row.iloc[0].get('Όνομα'))}".strip()


def fill_form2a_apospasma(doc: Document, header: Dict[str, str], stoaa: Dict[str, str], officers: pd.DataFrame) -> None:
    apply_basic_replacements(doc, header, stoaa)
    for table in doc.tables:
        fill_header_cells(table, header, stoaa)
        for row in table.rows:
            rt = normalize_text(row_text(row))
            for _, data in officers.iterrows():
                office = safe_str(data.get("Αξίωμα"))
                aliases = OFFICE_ALIASES.get(office, [office])
                col = find_col_with_text(row, aliases)
                if col is None:
                    continue
                name = f"{safe_str(data.get('Επώνυμο'))} {safe_str(data.get('Όνομα'))}".strip()
                # Αν το row έχει στήλη ΟΝΟΜΑΤΕΠΩΝΥΜΟ μετά το αξίωμα, γράφουμε εκεί.
                if name:
                    write_after_col(row, col, [name, safe_str(data.get("Λευκές ψήφοι"))])
                break


def fill_form1_anaggelia(doc: Document, header: Dict[str, str], stoaa: Dict[str, str], officers: pd.DataFrame) -> None:
    apply_basic_replacements(doc, header, stoaa)
    replacements = {
        "27/04/2026": header.get("Ημ/νία Αρχαιρεσιών", ""),
        "ΑΚΡΟΠΟΛΙΣ": stoaa.get("name", "ΑΚΡΟΠΟΛΙΣ"),
    }
    for p in iter_all_paragraphs(doc):
        replace_text_in_paragraph(p, {k: v for k, v in replacements.items() if v})
    for table in doc.tables:
        fill_header_cells(table, header, stoaa)
    fill_signatures(doc, officers)


def fill_unknown_generic(doc: Document, header: Dict[str, str], stoaa: Dict[str, str], officers: pd.DataFrame, voters: pd.DataFrame) -> None:
    apply_basic_replacements(doc, header, stoaa)
    for table in doc.tables:
        fill_header_cells(table, header, stoaa)
    fill_signatures(doc, officers)


def fill_docx(template_path: str, form_file: str, header: Dict[str, str], stoaa: Dict[str, str], officers: pd.DataFrame, voters: pd.DataFrame) -> bytes:
    doc = Document(template_path)
    fname = normalize_text(os.path.basename(form_file))

    if "ΚΑΤΑΣΤΑΣΗ_ΕΚΛ" in fname or "4_-_ΚΑΤΑΣΤΑΣ" in fname:
        fill_form4_katastasi(doc, header, stoaa, officers)
        fill_signatures(doc, officers)
    elif "ΟΝΟΜΑΣΤΙΚΗ_ΚΑΤΑΣ" in fname or "5_-_ΟΝΟΜΑΣΤ" in fname:
        fill_form5_psifisantes(doc, header, stoaa, voters)
        fill_signatures(doc, officers)
    elif "ΑΝΑΛΥΤΙΚΟΣ" in fname or "3_-_ΑΝΑΛΥΤ" in fname:
        fill_form3_analytikos(doc, header, stoaa, officers)
        fill_signatures(doc, officers)
    elif "ΑΠΟΣΠΑΣΜΑ" in fname or "2Α" in fname or "2A" in fname:
        fill_form2a_apospasma(doc, header, stoaa, officers)
        fill_signatures(doc, officers)
    elif "ΑΝΑΓΓΕΛΙΑ_ΕΚΛΟΓ" in fname or "1_-_ΑΝΑΓΓΕΛΙΑ" in fname:
        fill_form1_anaggelia(doc, header, stoaa, officers)
    else:
        fill_unknown_generic(doc, header, stoaa, officers, voters)

    return save_doc_to_bytes(doc)


# ══════════════════════════════════════════════════════════════
# UI
# ══════════════════════════════════════════════════════════════
st.markdown("# 📋 Διαδικασίες & Έντυπα ΜΣΤΕ")
st.caption("Συμπλήρωση προτυπωμένων εντύπων Word από το Μητρώο Στοάς.")

proc = PROCEDURES["ekloges"]
st.info(f"**{proc.title}** — {proc.subtitle}\n\n{proc.description}")
st.warning(proc.deadline_note)

members_df = load_members_df()
members_options = df_to_member_options(members_df)

if not members_options:
    st.error("Δεν βρέθηκαν μέλη στο μητρώο. Ελέγξτε το modules.database.get_all_members().")


tab_forms, tab_fill, tab_help = st.tabs(["📁 Έντυπα", "✍️ Συμπλήρωση", "🛠️ Debug / Οδηγίες"])

with tab_forms:
    st.markdown("### Διαθέσιμα έντυπα")
    blank_files: List[Tuple[str, bytes]] = []
    for form in proc.forms:
        path = os.path.join(FORMS_ROOT, form.file)
        st.markdown(f"#### {form.name}")
        st.caption(form.description)
        if not os.path.exists(path):
            st.error(f"Δεν βρέθηκε το αρχείο: `{path}`")
            continue
        with open(path, "rb") as fh:
            data = fh.read()
        blank_files.append((os.path.basename(form.file), data))
        c1, c2 = st.columns([1, 3])
        with c1:
            st.download_button(
                "⬇️ Κενό έντυπο",
                data=data,
                file_name=os.path.basename(form.file),
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                key=f"blank_{form.file}",
                use_container_width=True,
            )
        with c2:
            with st.expander("Προεπισκόπηση κειμένου"):
                st.text(read_docx_preview(path))
        st.divider()

    if blank_files:
        st.download_button(
            "📦 Λήψη όλων των κενών εντύπων",
            data=create_zip(blank_files),
            file_name="εντυπα_εκλογων_blank.zip",
            mime="application/zip",
            use_container_width=True,
        )

with tab_fill:
    st.markdown("### 1. Στοιχεία Στοάς & Αρχαιρεσιών")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        stoaa_name = st.text_input("Στοά", STOAA_DEFAULTS["name"])
        stoaa_number = st.text_input("Υπ’ αριθ.", STOAA_DEFAULTS["number"])
    with c2:
        stoaa_anatoli = st.text_input("Ανατολή", STOAA_DEFAULTS["anatoli"])
        diettia = st.text_input("Τεκτ. Διετία", "2024-2026")
    with c3:
        election_date = st.date_input("Ημ/νία Αρχαιρεσιών", value=date.today()).strftime("%d/%m/%Y")
        present_no = st.number_input("Παρόντες", min_value=0, value=0, step=1)
    with c4:
        eligible_no = st.number_input("Εκλογείς", min_value=0, value=0, step=1)
        # Θα ενημερωθεί από τη λίστα ψηφισάντων, αλλά αφήνουμε χειροκίνητη δυνατότητα.
        manual_voters_no = st.number_input("Ψηφίσαντες χειροκίνητα", min_value=0, value=0, step=1)

    with st.expander("Προαιρετικά: διεύθυνση Στοάς για έντυπα που τη ζητούν"):
        a1, a2, a3, a4 = st.columns(4)
        stoaa_street = a1.text_input("Οδός", STOAA_DEFAULTS["street"])
        stoaa_street_no = a2.text_input("Αριθ.", STOAA_DEFAULTS["street_no"])
        stoaa_city = a3.text_input("Πόλη", STOAA_DEFAULTS["city"])
        stoaa_zip = a4.text_input("Τ.Κ.", STOAA_DEFAULTS["zip"])

    stoaa_data = {
        "name": stoaa_name,
        "number": stoaa_number,
        "anatoli": stoaa_anatoli,
        "street": stoaa_street,
        "street_no": stoaa_street_no,
        "city": stoaa_city,
        "zip": stoaa_zip,
    }

    st.markdown("---")
    st.markdown("### 2. Επιλογή Αξιωματικών από Μητρώο")
    st.caption("Διάλεξε μέλη. Μετά μπορείς να διορθώσεις όλα τα στοιχεία στον πίνακα.")

    selected_officers: Dict[str, Optional[Dict[str, Any]]] = {}
    for section_name, rows in [
        ("Τακτικοί Αξιωματικοί", OFFICER_ROWS[:14]),
        ("Πρόσθετοι Αξιωματικοί", OFFICER_ROWS[14:]),
        ("Εξελεγκτική Επιτροπή", EXELEGKTIKI_ROWS),
    ]:
        with st.expander(section_name, expanded=(section_name == "Τακτικοί Αξιωματικοί")):
            cols = st.columns(2)
            for i, (field_key, office, section) in enumerate(rows):
                with cols[i % 2]:
                    selected_officers[field_key] = selected_member_selectbox(office, members_options, f"sel_{field_key}")

    officers_df = pd.DataFrame([
        officer_from_member(field_key, office, section, selected_officers.get(field_key))
        for field_key, office, section in OFFICER_ROWS + EXELEGKTIKI_ROWS
    ])

    st.markdown("---")
    st.markdown("### 3. Ψηφίσαντες Διδάσκαλοι")
    voter_ids = selected_member_ids_multiselect("Επιλέξτε όσους ψήφισαν", members_options, "voter_ids", max_count=60)
    voters_df = pd.DataFrame([voter_from_member(i + 1, members_options[mid]) for i, mid in enumerate(voter_ids)])
    voters_count = len(voters_df.index) if len(voters_df.index) else int(manual_voters_no)

    st.markdown("---")
    st.markdown("### 4. Έλεγχος / χειροκίνητη διόρθωση")
    st.caption("Οι πίνακες αυτοί είναι η τελική πηγή δεδομένων για τα Word.")

    edited_officers_df = st.data_editor(
        officers_df,
        use_container_width=True,
        hide_index=True,
        num_rows="fixed",
        disabled=["_field_key", "Ενότητα", "Αξίωμα"],
        key="officers_editor",
    )

    if voters_df.empty:
        voters_df = pd.DataFrame(columns=["Α/Α", "Α.Μ.Μ.Σ.", "Ονοματεπώνυμο"])

    edited_voters_df = st.data_editor(
        voters_df,
        use_container_width=True,
        hide_index=True,
        num_rows="dynamic",
        key="voters_editor",
    )

    header_data = {
        "Τεκτ. Διετία": diettia,
        "Ημ/νία Αρχαιρεσιών": election_date,
        "Εκλογείς": str(eligible_no),
        "Παρόντες": str(present_no),
        "Ψηφίσαντες": str(len(edited_voters_df.index) if len(edited_voters_df.index) else voters_count),
    }

    st.markdown("---")
    st.markdown("### 5. Δημιουργία εντύπων")

    selected_form_names = st.multiselect(
        "Ποια έντυπα θέλετε να δημιουργηθούν;",
        [f.name for f in proc.forms],
        default=[f.name for f in proc.forms],
    )

    if st.button("📄 Δημιουργία συμπληρωμένων εντύπων", type="primary", use_container_width=True):
        filled_files: List[Tuple[str, bytes]] = []
        progress = st.progress(0)
        forms_to_run = [f for f in proc.forms if f.name in selected_form_names]

        for i, form in enumerate(forms_to_run):
            progress.progress(int(i / max(1, len(forms_to_run)) * 90))
            path = os.path.join(FORMS_ROOT, form.file)
            if not os.path.exists(path):
                st.error(f"Δεν βρέθηκε: {path}")
                continue
            try:
                filled = fill_docx(path, form.file, header_data, stoaa_data, edited_officers_df, edited_voters_df)
                out_name = os.path.basename(form.file)
                filled_files.append((out_name, filled))
                st.download_button(
                    f"⬇️ {form.name}",
                    data=filled,
                    file_name=out_name,
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    key=f"filled_{form.file}_{i}",
                    use_container_width=True,
                )
                st.success(f"✅ Δημιουργήθηκε: {form.name}")
            except Exception as exc:
                st.error(f"❌ Σφάλμα στο {form.name}: {exc}")

        progress.progress(100)
        if len(filled_files) > 1:
            st.download_button(
                "📦 Λήψη όλων σε ZIP",
                data=create_zip(filled_files),
                file_name=f"εντυπα_εκλογων_{date_for_filename()}.zip",
                mime="application/zip",
                use_container_width=True,
            )

with tab_help:
    st.markdown("### Οδηγίες εγκατάστασης")
    st.code(
        """
# requirements.txt
streamlit
pandas
python-docx

# Το αρχείο να μπει εδώ:
pages/19_Διαδικασίες.py

# Τα templates να βρίσκονται εδώ:
forms/ekloges/1_-_ΑΝΑΓΓΕΛΙΑ_ΕΚΛΟΓΗΣ_ΣΕΒΑΣΜΙΟΥ___ΣΥΜΒΟΥΛΙΟΥ.docx
forms/ekloges/2Α_-_ΑΠΟΣΠΑΣΜΑ_ΕΚΛΟΓΗΣ_ΑΞΙΩΜΑΤΙΚΩΝ.docx
forms/ekloges/3_-_ΑΝΑΛΥΤΙΚΟΣ_ΠΙΝΑΚΑΣ__ΕΚΛΕΓΕΝΤΩΝ_ΑΞΙΩΜΑΤΙΚΩΝ.docx
forms/ekloges/4_-_ΚΑΤΑΣΤΑΣΗ_ΕΚΛΕΓΕΝΤΩΝ_ΑΞΙΩΜΑΤΙΚΩΝ.docx
forms/ekloges/5_-_ΟΝΟΜΑΣΤΙΚΗ_ΚΑΤΑΣΤΑΣΗ_ΨΗΦΙΣΑΝΤΩΝ.docx
        """.strip(),
        language="bash",
    )

    st.markdown("### Τι άλλαξε σε σχέση με την προηγούμενη έκδοση")
    st.markdown(
        """
- Προστέθηκε ξεχωριστή επιλογή **Ψηφισάντων Διδασκάλων**.
- Το έντυπο 5 συμπληρώνει πλέον τον κατάλογο 1–60.
- Οι αξιωματικοί περνούν από editable grid πριν γραφτούν στα Word.
- Δεν χρησιμοποιείται Claude για τα εκλογικά έντυπα.
- Η δημιουργία των Word γίνεται με συγκεκριμένες συναρτήσεις ανά έντυπο.
        """.strip()
    )

    with st.expander("Debug: paths"):
        st.write("BASE_DIR", BASE_DIR)
        st.write("FORMS_ROOT", FORMS_ROOT)
        st.write("Forms exist")
        for form in proc.forms:
            p = os.path.join(FORMS_ROOT, form.file)
            st.write(form.file, os.path.exists(p))

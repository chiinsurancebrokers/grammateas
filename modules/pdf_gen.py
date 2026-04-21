# -*- coding: utf-8 -*-
"""
PDF Generator — Γραμματεύς-Σφραγιδοφύλαξ
Δημιουργία PDF για: Πρακτικά, Εντάλματα, Καρτέλες Μελών
"""
import io
from datetime import date
from typing import Dict, List, Optional

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY

# ── LODGE CONFIG ──────────────────────────────────────────────
LODGE_NAME  = "ΣΤΟΑ ΑΚΡΟΠΟΛΙΣ ΥΠ. ΑΡΙΘΜ. 84"
LODGE_ORIENT = "ΕΝ ΤΗ ΑΝΑΤΟΛΗ ΤΩΝ ΑΘΗΝΩΝ"
SECRETARY   = "Ο Γραμματεύς-Σφραγιδοφύλαξ"

# ── COLORS ────────────────────────────────────────────────────
NAVY   = colors.HexColor("#1a2a4a")
GOLD   = colors.HexColor("#b8960c")
LIGHT  = colors.HexColor("#f0f4f8")
WHITE  = colors.white
BLACK  = colors.black

# ── BASE STYLES ───────────────────────────────────────────────
def _styles():
    base = getSampleStyleSheet()
    return {
        "lodge": ParagraphStyle("lodge", fontName="Helvetica-Bold",
                                fontSize=9, alignment=TA_CENTER, textColor=NAVY, spaceAfter=2),
        "title": ParagraphStyle("title", fontName="Helvetica-Bold",
                                fontSize=16, alignment=TA_CENTER, textColor=NAVY, spaceAfter=12),
        "subtitle": ParagraphStyle("subtitle", fontName="Helvetica-Bold",
                                   fontSize=12, alignment=TA_CENTER, textColor=NAVY, spaceAfter=8),
        "body": ParagraphStyle("body", fontName="Helvetica",
                               fontSize=10, alignment=TA_JUSTIFY, spaceAfter=6, leading=14),
        "bold": ParagraphStyle("bold", fontName="Helvetica-Bold",
                               fontSize=10, spaceAfter=4),
        "small": ParagraphStyle("small", fontName="Helvetica",
                                fontSize=9, textColor=colors.grey, spaceAfter=4),
        "sig": ParagraphStyle("sig", fontName="Helvetica-Oblique",
                              fontSize=10, alignment=TA_RIGHT, spaceAfter=4),
        "item": ParagraphStyle("item", fontName="Helvetica",
                               fontSize=10, leftIndent=20, spaceAfter=4, leading=14),
    }


def _header(styles) -> List:
    """Κεφαλίδα εγγράφου."""
    return [
        Paragraph(LODGE_NAME, styles["lodge"]),
        Paragraph(LODGE_ORIENT, styles["lodge"]),
        HRFlowable(width="100%", thickness=2, color=GOLD, spaceAfter=8),
    ]


def _footer_sig(styles) -> List:
    return [
        Spacer(1, 1.5*cm),
        HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey),
        Spacer(1, 0.4*cm),
        Paragraph(SECRETARY, styles["sig"]),
    ]


def _build_pdf(story: List) -> io.BytesIO:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        rightMargin=2.5*cm, leftMargin=2.5*cm,
        topMargin=2*cm, bottomMargin=2.5*cm
    )
    doc.build(story)
    buf.seek(0)
    return buf


# ═══════════════════════════════════════════════════════════════
# 1. ΠΡΑΚΤΙΚΑ ΣΥΝΕΔΡΙΑΣΗΣ
# ═══════════════════════════════════════════════════════════════

def generate_minutes_pdf(session: Dict, attendance_count: int = 0,
                         dikaiologithentes: List[str] = None) -> io.BytesIO:
    """
    Δημιουργεί PDF πρακτικών συνεδρίασης (Άρθρα 39-40).
    session: dict από get_session()
    """
    s   = _styles()
    story = []

    # Κεφαλίδα
    story.extend(_header(s))

    # Τίτλος
    βαθμός = session.get("βαθμός", "")
    story.append(Paragraph(f"ΠΡΑΚΤΙΚΑ ΣΥΝΕΔΡΙΑΣΗΣ — {βαθμός.upper()}", s["title"]))
    story.append(Spacer(1, 0.3*cm))

    # Βασικά στοιχεία σε πίνακα
    info = [
        ["Ημερομηνία:", session.get("ημερομηνία", ""), "Ώρα:", session.get("ώρα", "")],
        ["Τόπος:", session.get("τόπος", "Έδρα Στοάς"), "Βαθμός:", βαθμός],
        ["Αριθμός Παρόντων:", str(attendance_count), "", ""],
    ]
    t = Table(info, colWidths=[3.5*cm, 6*cm, 2.5*cm, 4*cm])
    t.setStyle(TableStyle([
        ("FONTNAME",  (0,0),(-1,-1), "Helvetica"),
        ("FONTNAME",  (0,0),(0,-1),  "Helvetica-Bold"),
        ("FONTNAME",  (2,0),(2,-1),  "Helvetica-Bold"),
        ("FONTSIZE",  (0,0),(-1,-1), 10),
        ("BOTTOMPADDING",(0,0),(-1,-1), 4),
        ("BACKGROUND",(0,0),(-1,-1), LIGHT),
        ("BOX",       (0,0),(-1,-1), 0.5, colors.lightgrey),
        ("GRID",      (0,0),(-1,-1), 0.25, colors.lightgrey),
        ("ROWBACKGROUNDS",(0,0),(-1,-1), [LIGHT, WHITE]),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.5*cm))

    def _section(title, items):
        if not items:
            return
        story.append(KeepTogether([
            Paragraph(title, s["bold"]),
            HRFlowable(width="100%", thickness=0.5, color=GOLD, spaceAfter=4),
        ]))
        for i, item in enumerate(items, 1):
            story.append(Paragraph(f"{i}. {item}", s["item"]))
        story.append(Spacer(1, 0.3*cm))

    _section("ΑΛΛΗΛΟΓΡΑΦΙΑ", session.get("αλληλογραφία") or [])
    _section("ΟΜΙΛΙΕΣ ΚΑΙ ΣΥΖΗΤΗΣΕΙΣ", session.get("ομιλίες") or [])
    _section("ΑΠΟΦΑΣΕΙΣ", session.get("αποφάσεις") or [])

    # Κορμός Αγαθοεργίας (Άρθρο 39 — ολογράφως και αριθμητικώς)
    kormos = session.get("κορμός_αγαθοεργίας") or 0
    kormos_olog = session.get("κορμός_ολογράφως") or ""
    story.append(KeepTogether([
        Paragraph("ΚΟΡΜΟΣ ΑΓΑΘΟΕΡΓΙΑΣ", s["bold"]),
        HRFlowable(width="100%", thickness=0.5, color=GOLD, spaceAfter=4),
        Paragraph(
            f"Ο Κορμός της Αγαθοεργίας ανήλθεν εις <b>{kormos_olog}</b> ({kormos:.2f} €).",
            s["body"]
        ),
        Spacer(1, 0.3*cm),
    ]))

    # Δικαιολογηθέντες (Άρθρο 40)
    if dikaiologithentes:
        story.append(Paragraph("ΔΙΚΑΙΟΛΟΓΗΘΕΝΤΕΣ", s["bold"]))
        story.append(Paragraph(", ".join(dikaiologithentes), s["item"]))
        story.append(Spacer(1, 0.3*cm))

    # Παρατηρήσεις
    if session.get("παρατηρήσεις"):
        story.append(Paragraph("ΠΑΡΑΤΗΡΗΣΕΙΣ", s["bold"]))
        story.append(Paragraph(session["παρατηρήσεις"], s["body"]))

    story.extend(_footer_sig(s))
    return _build_pdf(story)


# ═══════════════════════════════════════════════════════════════
# 2. ΕΝΤΑΛΜΑ ΠΛΗΡΩΜΗΣ
# ═══════════════════════════════════════════════════════════════

def generate_entalma_pdf(entalma: Dict) -> io.BytesIO:
    """
    Δημιουργεί PDF εντάλματος πληρωμής (Άρθρα 36§6,7).
    entalma: row από get_entalmata()
    """
    s     = _styles()
    story = []

    story.extend(_header(s))

    βιβλίο = entalma.get("βιβλίο", "Γενικό")
    story.append(Paragraph(f"ΕΝΤΑΛΜΑ ΠΛΗΡΩΜΗΣ — {βιβλίο.upper()}", s["title"]))
    story.append(Spacer(1, 0.3*cm))

    info = [
        ["Αριθμός Εντάλματος:", entalma.get("αρ_εντάλματος",""), "Ημερομηνία:", entalma.get("ημερομηνία","")],
        ["Ποσό:", f"{float(entalma.get('ποσό',0)):.2f} €", "Κατάσταση:", entalma.get("κατάσταση","")],
        ["Αρ. Απόφασης Στοάς:", entalma.get("αρ_απόφασης","—"), "", ""],
    ]
    t = Table(info, colWidths=[4*cm, 6*cm, 3*cm, 3*cm])
    t.setStyle(TableStyle([
        ("FONTNAME",  (0,0),(-1,-1), "Helvetica"),
        ("FONTNAME",  (0,0),(0,-1),  "Helvetica-Bold"),
        ("FONTNAME",  (2,0),(2,-1),  "Helvetica-Bold"),
        ("FONTSIZE",  (0,0),(-1,-1), 10),
        ("BOTTOMPADDING",(0,0),(-1,-1), 5),
        ("BACKGROUND", (0,0),(-1,-1), LIGHT),
        ("GRID",      (0,0),(-1,-1), 0.25, colors.lightgrey),
        ("BOX",       (0,0),(-1,-1), 1, NAVY),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.6*cm))

    # Αιτιολογία
    story.append(Paragraph("ΑΙΤΙΟΛΟΓΙΑ ΠΛΗΡΩΜΗΣ", s["bold"]))
    story.append(HRFlowable(width="100%", thickness=0.5, color=GOLD, spaceAfter=4))
    story.append(Paragraph(entalma.get("αιτιολογία",""), s["body"]))
    story.append(Spacer(1, 0.5*cm))

    # Δικαιολογητικά (Άρθρο 36§7)
    import json
    δικαιολ = entalma.get("δικαιολογητικά")
    if δικαιολ:
        try:
            items = json.loads(δικαιολ) if isinstance(δικαιολ, str) else δικαιολ
        except Exception:
            items = []
        if items:
            story.append(Paragraph("ΔΙΚΑΙΟΛΟΓΗΤΙΚΑ ΕΓΓΡΑΦΑ", s["bold"]))
            story.append(HRFlowable(width="100%", thickness=0.5, color=GOLD, spaceAfter=4))
            story.append(Paragraph("Επισυνάπτονται τα κάτωθι δικαιολογητικά (κατ' Άρθρον 36§7):", s["body"]))
            for i, d in enumerate(items, 1):
                story.append(Paragraph(f"{i}. {d}", s["item"]))
            story.append(Spacer(1, 0.5*cm))

    # Παρατηρήσεις
    if entalma.get("παρατηρήσεις"):
        story.append(Paragraph("ΠΑΡΑΤΗΡΗΣΕΙΣ", s["bold"]))
        story.append(Paragraph(entalma["παρατηρήσεις"], s["body"]))
        story.append(Spacer(1, 0.3*cm))

    # Θέσεις Υπογραφών
    story.append(Spacer(1, 1*cm))
    sig_table = Table(
        [["Ο Σεβάσμιος", "", "Ο Γραμματεύς-Σφραγιδοφύλαξ"]],
        colWidths=[6*cm, 4*cm, 6*cm]
    )
    sig_table.setStyle(TableStyle([
        ("FONTNAME",  (0,0),(-1,-1), "Helvetica-Bold"),
        ("FONTSIZE",  (0,0),(-1,-1), 10),
        ("ALIGN",     (0,0),(0,-1),  "CENTER"),
        ("ALIGN",     (2,0),(2,-1),  "CENTER"),
        ("TOPPADDING",(0,0),(-1,-1), 30),
        ("LINEABOVE", (0,0),(0,-1),  0.5, BLACK),
        ("LINEABOVE", (2,0),(2,-1),  0.5, BLACK),
    ]))
    story.append(sig_table)

    return _build_pdf(story)


# ═══════════════════════════════════════════════════════════════
# 3. ΚΑΡΤΕΛΑ ΜΕΛΟΥΣ
# ═══════════════════════════════════════════════════════════════

def generate_member_card_pdf(member: Dict) -> io.BytesIO:
    """Δημιουργεί PDF καρτέλα μέλους."""
    s     = _styles()
    story = []

    story.extend(_header(s))
    story.append(Paragraph("ΚΑΡΤΕΛΑ ΜΕΛΟΥΣ — ΜΗΤΡΩΟ ΣΤΟΑΣ", s["title"]))
    story.append(Spacer(1, 0.3*cm))

    def _row(lbl, val):
        return [Paragraph(lbl, s["bold"]),
                Paragraph(str(val or "—"), s["body"])]

    def sv(k): return member.get(k) or "—"

    # Αριθμοί Μητρώου
    reg_data = [
        [Paragraph("ΑΜ Στοάς", s["bold"]), Paragraph(sv("αρ_μητρώου_στοάς"), s["body"]),
         Paragraph("ΑΜ Μεγάλης Στοάς", s["bold"]), Paragraph(sv("αρ_μητρώου_μσ"), s["body"])],
    ]
    t0 = Table(reg_data, colWidths=[3.5*cm,4*cm,4.5*cm,4.5*cm])
    t0.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,-1), NAVY),
        ("TEXTCOLOR", (0,0),(-1,-1), WHITE),
        ("FONTNAME",  (0,0),(-1,-1), "Helvetica-Bold"),
        ("FONTSIZE",  (0,0),(-1,-1), 10),
        ("BOX",       (0,0),(-1,-1), 1, NAVY),
        ("BOTTOMPADDING",(0,0),(-1,-1), 6),
    ]))
    story.append(t0)
    story.append(Spacer(1, 0.4*cm))

    sections = [
        ("ΠΡΟΣΩΠΙΚΑ ΣΤΟΙΧΕΙΑ", [
            ("Επώνυμο:", sv("επώνυμο")),
            ("Όνομα:", sv("όνομα")),
            ("Πατρώνυμο:", sv("πατρώνυμο")),
            ("Ημ. Γέννησης:", sv("ημ_γέννησης")),
            ("Τόπος Γέννησης:", sv("τόπος_γέννησης")),
            ("Επάγγελμα:", sv("επάγγελμα")),
        ]),
        ("ΣΤΟΙΧΕΙΑ ΕΠΙΚΟΙΝΩΝΙΑΣ", [
            ("Διεύθυνση:", sv("διεύθυνση")),
            ("Πόλη / ΤΚ:", f"{sv('πόλη')} {sv('τκ')}"),
            ("Τηλέφωνο:", sv("τηλέφωνο")),
            ("Κινητό:", sv("κινητό")),
            ("Email:", sv("email")),
        ]),
        ("ΤΕΚΤΟΝΙΚΑ ΣΤΟΙΧΕΙΑ", [
            ("Τεκτονικός Βαθμός:", sv("τεκτονικός_βαθμός")),
            ("Κατάσταση:", sv("κατάσταση")),
            ("Ημ. Μύησης:", sv("ημ_μύησης")),
            ("Ημ. Εταίρου:", sv("ημ_εταίρου")),
            ("Ημ. Διδασκάλου:", sv("ημ_διδασκάλου")),
            ("Στοά Μύησης:", sv("στοά_μύησης")),
        ]),
    ]

    for sec_title, fields in sections:
        story.append(KeepTogether([
            Paragraph(sec_title, s["bold"]),
            HRFlowable(width="100%", thickness=1, color=GOLD, spaceAfter=4),
        ]))
        tdata = [[Paragraph(lbl, s["bold"]), Paragraph(val, s["body"])] for lbl, val in fields]
        t = Table(tdata, colWidths=[5*cm, 11*cm])
        t.setStyle(TableStyle([
            ("FONTSIZE",     (0,0),(-1,-1), 10),
            ("BOTTOMPADDING",(0,0),(-1,-1), 4),
            ("ROWBACKGROUNDS",(0,0),(-1,-1), [WHITE, LIGHT]),
        ]))
        story.append(t)
        story.append(Spacer(1, 0.4*cm))

    # Παρατηρήσεις
    if member.get("παρατηρήσεις"):
        story.append(Paragraph("ΠΑΡΑΤΗΡΗΣΕΙΣ", s["bold"]))
        story.append(HRFlowable(width="100%", thickness=0.5, color=GOLD, spaceAfter=4))
        story.append(Paragraph(member["παρατηρήσεις"], s["body"]))

    # Footer
    story.append(Spacer(1, 1*cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
    story.append(Paragraph(
        f"Εκτυπώθηκε: {date.today().strftime('%d/%m/%Y')} · {SECRETARY}",
        s["small"]
    ))

    return _build_pdf(story)


# ═══════════════════════════════════════════════════════════════
# 4. ΠΡΩΤΟΚΟΛΛΟ — ΕΚΤΥΠΩΣΗ ΒΙΒΛΙΟΥ
# ═══════════════════════════════════════════════════════════════

def generate_protokollon_pdf(rows, year: int) -> io.BytesIO:
    """Εκτύπωση βιβλίου πρωτοκόλλου για ένα έτος."""
    s     = _styles()
    story = []

    story.extend(_header(s))
    story.append(Paragraph(f"ΠΡΩΤΟΚΟΛΛΟ ΕΓΓΡΑΦΩΝ — ΕΤΟΣ {year}", s["title"]))
    story.append(Spacer(1, 0.4*cm))

    headers = ["ΑΠ", "Ημερ.", "Κατεύθ.", "Αποστολέας/Παραλήπτης", "Θέμα", "Κατάσταση"]
    data = [headers]
    for r in rows.to_dict("records"):
        recv = r.get("αποστολέας","") or r.get("παραλήπτης","")
        data.append([
            r.get("αρ_πρωτ",""),
            r.get("ημερομηνία",""),
            r.get("κατεύθυνση",""),
            str(recv)[:30],
            str(r.get("θέμα",""))[:50],
            r.get("κατάσταση",""),
        ])

    t = Table(data, colWidths=[2*cm, 2.2*cm, 2.2*cm, 3.8*cm, 5*cm, 2.3*cm])
    t.setStyle(TableStyle([
        ("BACKGROUND",  (0,0),(-1,0), NAVY),
        ("TEXTCOLOR",   (0,0),(-1,0), WHITE),
        ("FONTNAME",    (0,0),(-1,0), "Helvetica-Bold"),
        ("FONTSIZE",    (0,0),(-1,-1), 8),
        ("FONTNAME",    (0,1),(-1,-1), "Helvetica"),
        ("ROWBACKGROUNDS",(0,1),(-1,-1), [WHITE, LIGHT]),
        ("GRID",        (0,0),(-1,-1), 0.25, colors.lightgrey),
        ("BOX",         (0,0),(-1,-1), 1, NAVY),
        ("BOTTOMPADDING",(0,0),(-1,-1), 4),
        ("TOPPADDING",  (0,0),(-1,-1), 4),
    ]))
    story.append(t)

    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph(f"Σύνολο εγγραφών: {len(rows)}", s["small"]))
    story.extend(_footer_sig(s))
    return _build_pdf(story)


# ═══════════════════════════════════════════════════════════════
# 5. ΜΗΤΡΩΟ ΜΕΛΩΝ — ΛΙΣΤΑ
# ═══════════════════════════════════════════════════════════════

def generate_members_list_pdf(members_df) -> io.BytesIO:
    """Εκτύπωση Μητρώου Μελών."""
    s     = _styles()
    story = []

    story.extend(_header(s))
    story.append(Paragraph("ΜΗΤΡΩΟ ΜΕΛΩΝ ΣΤΟΑΣ", s["title"]))
    story.append(Paragraph(f"Ημερομηνία εκτύπωσης: {date.today().strftime('%d/%m/%Y')}", s["small"]))
    story.append(Spacer(1, 0.4*cm))

    headers = ["ΑΜ\nΣτοάς", "ΑΜ ΜΣ", "Επώνυμο", "Όνομα", "Βαθμός", "Ημ. Μύησης", "Κατάσταση"]
    data = [headers]
    for _, r in members_df.iterrows():
        data.append([
            str(r.get("αρ_μητρώου_στοάς","") or ""),
            str(r.get("αρ_μητρώου_μσ","") or ""),
            str(r.get("επώνυμο","") or ""),
            str(r.get("όνομα","") or ""),
            str(r.get("τεκτονικός_βαθμός","") or ""),
            str(r.get("ημ_μύησης","") or ""),
            str(r.get("κατάσταση","") or ""),
        ])

    t = Table(data, colWidths=[1.5*cm, 1.8*cm, 4*cm, 3*cm, 2.5*cm, 2.8*cm, 2.4*cm])
    t.setStyle(TableStyle([
        ("BACKGROUND",  (0,0),(-1,0), NAVY),
        ("TEXTCOLOR",   (0,0),(-1,0), WHITE),
        ("FONTNAME",    (0,0),(-1,0), "Helvetica-Bold"),
        ("FONTSIZE",    (0,0),(-1,-1), 8),
        ("FONTNAME",    (0,1),(-1,-1), "Helvetica"),
        ("ROWBACKGROUNDS",(0,1),(-1,-1), [WHITE, LIGHT]),
        ("GRID",        (0,0),(-1,-1), 0.25, colors.lightgrey),
        ("BOX",         (0,0),(-1,-1), 1, NAVY),
        ("BOTTOMPADDING",(0,0),(-1,-1), 4),
        ("TOPPADDING",  (0,0),(-1,-1), 4),
        ("VALIGN",      (0,0),(-1,-1), "MIDDLE"),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph(f"Σύνολο: {len(members_df)} μέλη", s["small"]))
    story.extend(_footer_sig(s))
    return _build_pdf(story)

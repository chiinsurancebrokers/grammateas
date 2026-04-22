# -*- coding: utf-8 -*-
"""
PDF Generator — Γραμματεύς-Σφραγιδοφύλαξ
Γραμματοσειρά: DejaVu Serif (πλήρης υποστήριξη ελληνικών)
"""
import io
import json
from datetime import date
from typing import Dict, List

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether, BaseDocTemplate, Frame, PageTemplate
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ── ΚΑΤΑΧΩΡΗΣΗ ΓΡΑΜΜΑΤΟΣΕΙΡΩΝ ─────────────────────────────────
def _register_fonts():
    """
    DejaVu Serif  → κείμενο (DSR/DSB/DSI/DSBI)
    DejaVu Sans   → επικεφαλίδες με σύμβολο ∴ (DSS/DSSB)
    Bundled στον φάκελο /fonts/ του project.
    """
    import os
    base      = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    fonts_dir = os.path.join(base, "fonts")
    system_dir= "/usr/share/fonts/truetype/dejavu"

    def fp(name):
        local = os.path.join(fonts_dir, name)
        if os.path.exists(local): return local
        system = os.path.join(system_dir, name)
        if os.path.exists(system): return system
        raise FileNotFoundError(f"Font not found: {name} — copy it to {fonts_dir}/")

    pdfmetrics.registerFont(TTFont("DSR",  fp("DejaVuSerif.ttf")))
    pdfmetrics.registerFont(TTFont("DSB",  fp("DejaVuSerif-Bold.ttf")))
    pdfmetrics.registerFont(TTFont("DSI",  fp("DejaVuSerif-Italic.ttf")))
    pdfmetrics.registerFont(TTFont("DSBI", fp("DejaVuSerif-BoldItalic.ttf")))
    pdfmetrics.registerFontFamily("DejaVuSerif",
                                   normal="DSR", bold="DSB",
                                   italic="DSI", boldItalic="DSBI")
    # DejaVu Sans — υποστηρίζει ∴ (U+2234), χρησιμοποιείται στις κεφαλίδες
    pdfmetrics.registerFont(TTFont("DSS",  fp("DejaVuSans.ttf")))
    pdfmetrics.registerFont(TTFont("DSSB", fp("DejaVuSans-Bold.ttf")))

_register_fonts()

# ── ΣΤΑΘΕΡΕΣ ─────────────────────────────────────────────────
# Χρησιμοποιούμε DSS (Sans) για το ∴ — Serif δεν έχει αυτό το glyph
LODGE_HDR1  = "Ε∴Δ∴Τ∴Μ∴Α∴Τ∴Σ∴"
LODGE_HDR2  = "Εν Ονόματι και Υπό την Αιγίδα"
LODGE_HDR3  = "της Μεγάλης Στοάς της Ελλάδος"
LODGE_HDR4  = "των Αρχαίων Ελευθέρων και Αποδεδεγμένων Τεκτόνων"
LODGE_NAME  = "Σ∴ Στ∴ ΑΚΡΟΠΟΛΙΣ υπ' αρ. 84     εν Αν∴ Αθ∴"
NAVY   = colors.HexColor("#1a2a4a")
GOLD   = colors.HexColor("#b8960c")
LIGHT  = colors.HexColor("#f5f5f0")
WHITE  = colors.white
BLACK  = colors.black
ΒΑΘΜΟΙ_ABBR = {"Μαθητής": "Μαθ∴", "Εταίρος": "Ετ∴", "Διδάσκαλος": "Διδ∴"}
ΜΗΝΕΣ = ["","Ιανουαρίου","Φεβρουαρίου","Μαρτίου","Απριλίου","Μαΐου","Ιουνίου",
          "Ιουλίου","Αυγούστου","Σεπτεμβρίου","Οκτωβρίου","Νοεμβρίου","Δεκεμβρίου"]

def _fmt_date(d_str: str) -> str:
    """'2025-03-13' → '13η μηνός Μαρτίου του έτους 2025'"""
    try:
        import pandas as pd
        d = pd.to_datetime(d_str)
        return f"{d.day}η μηνός {ΜΗΝΕΣ[d.month]} του έτους {d.year}"
    except Exception:
        return d_str

# ── STYLES (όλα DejaVu Serif) ─────────────────────────────────
def _S(**kw) -> ParagraphStyle:
    d = dict(fontName="DSR", fontSize=10, spaceAfter=5, leading=15, textColor=BLACK)
    d.update(kw)
    return ParagraphStyle(str(hash(str(sorted(kw.items())))), **d)

def _styles() -> Dict:
    return {
        # ── Κεφαλίδα (DejaVu Sans — υποστηρίζει ∴) ──────────
        "lodge":    _S(fontName="DSSB", fontSize=10,  alignment=TA_CENTER, spaceAfter=3, textColor=NAVY),
        "cc":       _S(fontName="DSS",  fontSize=10,  alignment=TA_CENTER, spaceAfter=3, textColor=NAVY),
        # ── Σώμα εγγράφου (DejaVu Serif) ─────────────────────
        "title":    _S(fontName="DSB",  fontSize=13,  alignment=TA_CENTER, spaceAfter=6, spaceBefore=6, textColor=NAVY),
        "bold":     _S(fontName="DSB",  fontSize=10,  spaceAfter=4),
        "body":     _S(fontName="DSR",  fontSize=10,  alignment=TA_JUSTIFY, spaceAfter=8, leading=16),
        "indent":   _S(fontName="DSR",  fontSize=10,  alignment=TA_JUSTIFY, leftIndent=20, spaceAfter=5, leading=15),
        "bullet":   _S(fontName="DSR",  fontSize=10,  leftIndent=30, spaceAfter=4, leading=14),
        "small":    _S(fontName="DSI",  fontSize=8,   textColor=colors.grey, spaceAfter=3, alignment=TA_CENTER),
        "tbl_hdr":  _S(fontName="DSSB", fontSize=6.5, textColor=WHITE, alignment=TA_CENTER),
        "tbl_cell": _S(fontName="DSR",  fontSize=7,   alignment=TA_LEFT),
        "sig":      _S(fontName="DSR",  fontSize=10,  alignment=TA_CENTER, spaceBefore=30),
        # ── Δίπλωμα ──────────────────────────────────────────
        "dip_hdr1": _S(fontName="DSSB", fontSize=18,  alignment=TA_CENTER, textColor=NAVY, spaceAfter=4, spaceBefore=4),
        "dip_hdr2": _S(fontName="DSI",  fontSize=12,  alignment=TA_CENTER, textColor=NAVY, spaceAfter=8),
        "dip_intro":_S(fontName="DSI",  fontSize=11,  alignment=TA_CENTER, textColor=NAVY, spaceAfter=4, leading=18),
        "dip_name": _S(fontName="DSB",  fontSize=22,  alignment=TA_CENTER, textColor=NAVY, spaceAfter=6, spaceBefore=6),
        "dip_body": _S(fontName="DSI",  fontSize=11,  alignment=TA_CENTER, textColor=BLACK, spaceAfter=4, leading=19),
        "dip_deg":  _S(fontName="DSB",  fontSize=26,  alignment=TA_CENTER, textColor=NAVY, spaceAfter=6, spaceBefore=4),
        "dip_date": _S(fontName="DSI",  fontSize=11,  alignment=TA_CENTER, textColor=NAVY, spaceAfter=12),
        "dip_sig":  _S(fontName="DSR",  fontSize=10,  alignment=TA_CENTER),
        "dip_wm":   _S(fontName="DSI",  fontSize=8,   alignment=TA_CENTER, textColor=colors.grey, spaceAfter=2),
    }

def _header(s: Dict) -> List:
    """Τεκτονική κεφαλίδα για όλα τα έγγραφα."""
    return [
        Paragraph(LODGE_HDR1, s["lodge"]),
        Paragraph(LODGE_HDR2, s["cc"]),
        Paragraph(LODGE_HDR3, s["cc"]),
        Paragraph(LODGE_HDR4, s["cc"]),
        Spacer(1, .2*cm),
        Paragraph(f"<b>{LODGE_NAME}</b>", s["lodge"]),
        Spacer(1, .2*cm),
        HRFlowable(width="100%", thickness=1.5, color=NAVY, spaceAfter=8),
    ]

def _hr(s: Dict, before: int = 5) -> HRFlowable:
    return HRFlowable(width="100%", thickness=.5, color=GOLD, spaceBefore=before, spaceAfter=before)

def _build(story: List) -> io.BytesIO:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            rightMargin=2.5*cm, leftMargin=2.5*cm,
                            topMargin=2*cm, bottomMargin=2.5*cm)
    doc.build(story)
    buf.seek(0)
    return buf

def _table_style(header_cols: int = -1) -> TableStyle:
    return TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0),  NAVY),
        ("TEXTCOLOR",     (0, 0), (-1, 0),  WHITE),
        ("FONTNAME",      (0, 0), (-1, 0),  "DSSB"),
        ("FONTSIZE",      (0, 0), (-1, -1), 7),
        ("FONTNAME",      (0, 1), (-1, -1), "DSR"),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [WHITE, LIGHT]),
        ("GRID",          (0, 0), (-1, -1), .25, colors.lightgrey),
        ("BOX",           (0, 0), (-1, -1), 1,  NAVY),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("TOPPADDING",    (0, 0), (-1, -1), 2),
        ("LEFTPADDING",   (0, 0), (-1, -1), 3),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 3),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
    ])


# ═══════════════════════════════════════════════════════════════
# 1. ΠΡΑΚΤΙΚΑ ΣΥΝΕΔΡΙΑΣΗΣ
# ═══════════════════════════════════════════════════════════════

def generate_minutes_pdf(session: Dict, attendance_list: List[str] = None,
                         dikaiologithentes: List[str] = None,
                         anaplirotai: Dict[str, str] = None) -> io.BytesIO:
    s = _styles()
    story = []
    story.extend(_header(s))

    ημερ = session.get("ημερομηνία", "")
    βαθμ = session.get("βαθμός", "Μαθητής")
    βα = ΒΑΘΜΟΙ_ABBR.get(βαθμ, βαθμ[:4] + "∴")
    story.append(Paragraph(f"<b>Πρακτικόν Συνεδρίας της {ημερ} εις Βαθμ∴ {βα}</b>", s["title"]))
    story.append(Spacer(1, .2*cm))

    # Ημερησία Διάταξη
    agenda = session.get("αλληλογραφία") or []
    if agenda:
        story.append(Paragraph("<b>Ημερησία Διάταξις:</b>", s["bold"]))
        for it in agenda:
            story.append(Paragraph(f"- {it}", s["bullet"]))
        story.append(Spacer(1, .3*cm))

    # Έναρξη
    topos = session.get("τόπος") or "τον Τεκτ∴ Ναόν"
    ora   = session.get("ώρα") or ""
    plithos = len(attendance_list) if attendance_list else (session.get("πλήθος_παρόντων") or 0)
    story.append(Paragraph(
        f"Σήμερον {ημερ}{', ώρα ' + ora if ora else ''}, εις {topos}, "
        f"υπό την Σφύραν του Σεβ∴ Διδ∴ της Σ∴ Στ∴ μας, "
        f"ανοίγουν αι Εργασίαι εις Βαθμόν {βαθμ}.", s["body"]))
    if plithos:
        story.append(Paragraph(
            f"Παρόντες είναι <b>{plithos}</b> Αδδ∴, ενεργά μέλη του πληρώματός της Στ∴ μας.",
            s["body"]))
    if anaplirotai:
        anap = ", ".join([f"η θέσις του {α} από τον Αδ∴ {ο}" for α, ο in anaplirotai.items()])
        story.append(Paragraph(
            f"Αι θέσεις των τακτικών Αξ/κών καταλαμβάνονται κανονικώς, ενώ {anap}.", s["body"]))
    story.append(_hr(s))

    # Αλληλογραφία
    if agenda:
        story.append(Paragraph(
            "Ακολούθως, ο Σεβ∴ Διδ∴ εκάλεσε τον Αδ∴ Ρήτορα όπως αναγνώσει την αλληλογραφίαν.",
            s["body"]))
        story.append(Paragraph("Ο Αδ∴ Ρήτωρ ανέγνωσεν των Αδδ∴ καθημένων:", s["body"]))
        for it in agenda:
            story.append(Paragraph(f"* {it}", s["indent"]))
        story.append(Spacer(1, .2*cm))

    # Ομιλίες
    omilies = session.get("ομιλίες") or []
    if omilies:
        story.append(_hr(s))
        story.append(Paragraph("<b>Ομιλίαι — Εργασίαι — Συζητήσεις</b>", s["bold"]))
        for it in omilies:
            story.append(Paragraph(it, s["body"]))

    # Αποφάσεις
    apof = session.get("αποφάσεις") or []
    if apof:
        story.append(_hr(s))
        story.append(Paragraph("<b>Αποφάσεις</b>", s["bold"]))
        for i, it in enumerate(apof, 1):
            story.append(Paragraph(f"{i}. {it}", s["indent"]))

    # Κορμός Αγαθοεργίας (Άρθρο 39)
    kormos = float(session.get("κορμός_αγαθοεργίας") or 0)
    olog   = session.get("κορμός_ολογράφως") or ""
    story.append(_hr(s))
    story.append(Paragraph(
        f"Εκ του Κορμού της Αγαθοεργίας εβλάστησαν "
        f"<b>{olog + ' ' if olog else ''}({kormos:.2f})</b> όστρακα.", s["body"]))

    if dikaiologithentes:
        story.append(Paragraph("Δικαιολογηθέντες: " + " · ".join(dikaiologithentes), s["body"]))
    if session.get("παρατηρήσεις"):
        story.append(Paragraph(session["παρατηρήσεις"], s["body"]))

    story.append(Spacer(1, .3*cm))
    story.append(Paragraph(
        "Τέλος, αι Εργασίαι έκλεισαν κανονικώς υπό την Σφύραν του Σεβ∴ Διδ∴ "
        "της Σ∴ Στ∴ μας, των Αδδ∴ ευχαριστημένων και ικανοποιημένων.", s["body"]))

    # Υπογραφές
    story.append(Spacer(1, 1.2*cm))
    sig = Table(
        [[Paragraph("Ο Σεβ∴ Διδ∴", s["sig"]),
          Paragraph("Ο Ρήτωρ", s["sig"]),
          Paragraph("Ο Γραμματεύς", s["sig"])]],
        colWidths=[5*cm, 5*cm, 6*cm])
    sig.setStyle(TableStyle([
        ("TOPPADDING",  (0,0), (-1,-1), 35),
        ("LINEABOVE",   (0,0), (-1,-1), .5, BLACK),
        ("ALIGN",       (0,0), (-1,-1), "CENTER"),
        ("FONTNAME",    (0,0), (-1,-1), "DSR"),
    ]))
    story.append(sig)
    return _build(story)


# ═══════════════════════════════════════════════════════════════
# 2. ΕΝΤΑΛΜΑ ΠΛΗΡΩΜΗΣ
# ═══════════════════════════════════════════════════════════════

def generate_entalma_pdf(entalma: Dict) -> io.BytesIO:
    s = _styles()
    story = []
    story.extend(_header(s))

    βιβλ = entalma.get("βιβλίο", "Γενικό")
    story.append(Paragraph(f"<b>ΕΝΤΑΛΜΑ ΠΛΗΡΩΜΗΣ — {βιβλ.upper()}</b>", s["title"]))
    story.append(Spacer(1, .4*cm))

    info = [
        [Paragraph("Αριθμός:", s["bold"]), Paragraph(entalma.get("αρ_εντάλματος",""), s["body"]),
         Paragraph("Ημερομηνία:", s["bold"]), Paragraph(entalma.get("ημερομηνία",""), s["body"])],
        [Paragraph("Ποσό:", s["bold"]), Paragraph(f"{float(entalma.get('ποσό',0)):.2f} €", s["body"]),
         Paragraph("Κατάσταση:", s["bold"]), Paragraph(entalma.get("κατάσταση",""), s["body"])],
        [Paragraph("Αρ. Απόφ.:", s["bold"]), Paragraph(entalma.get("αρ_απόφασης","—"), s["body"]),
         Paragraph("", s["body"]), Paragraph("", s["body"])],
    ]
    t = Table(info, colWidths=[2.5*cm, 5*cm, 3*cm, 5.5*cm])
    t.setStyle(TableStyle([
        ("FONTNAME",     (0,0), (-1,-1), "DSR"),
        ("FONTSIZE",     (0,0), (-1,-1), 10),
        ("BACKGROUND",   (0,0), (-1,-1), LIGHT),
        ("BOX",          (0,0), (-1,-1), 1, NAVY),
        ("GRID",         (0,0), (-1,-1), .25, colors.lightgrey),
        ("BOTTOMPADDING",(0,0), (-1,-1), 5),
    ]))
    story.append(t)
    story.append(Spacer(1, .5*cm))

    story.append(Paragraph("<b>Αιτιολογία Πληρωμής</b>", s["bold"]))
    story.append(_hr(s, 2))
    story.append(Paragraph(entalma.get("αιτιολογία",""), s["body"]))

    δικ = entalma.get("δικαιολογητικά")
    if δικ:
        try:
            items = json.loads(δικ) if isinstance(δικ, str) else δικ
        except Exception:
            items = []
        if items:
            story.append(Spacer(1, .3*cm))
            story.append(Paragraph("<b>Δικαιολογητικά (Άρθρο 36§7)</b>", s["bold"]))
            story.append(_hr(s, 2))
            for i, d in enumerate(items, 1):
                story.append(Paragraph(f"{i}. {d}", s["indent"]))

    story.append(Spacer(1, 1.2*cm))
    sig = Table(
        [[Paragraph("Ο Σεβ∴ Διδ∴", s["sig"]), Paragraph("", s["sig"]),
          Paragraph("Ο Γραμματεύς-Σφραγιδοφύλαξ", s["sig"])]],
        colWidths=[6*cm, 4*cm, 6*cm])
    sig.setStyle(TableStyle([
        ("TOPPADDING",  (0,0), (-1,-1), 35),
        ("LINEABOVE",   (0,0), (0,-1), .5, BLACK),
        ("LINEABOVE",   (2,0), (2,-1), .5, BLACK),
        ("ALIGN",       (0,0), (-1,-1), "CENTER"),
        ("FONTNAME",    (0,0), (-1,-1), "DSR"),
    ]))
    story.append(sig)
    return _build(story)


# ═══════════════════════════════════════════════════════════════
# 3. ΚΑΡΤΕΛΑ ΜΕΛΟΥΣ
# ═══════════════════════════════════════════════════════════════

def generate_member_card_pdf(member: Dict) -> io.BytesIO:
    s  = _styles()
    story = []
    story.extend(_header(s))
    story.append(Paragraph("ΚΑΡΤΕΛΑ ΜΕΛΟΥΣ — ΜΗΤΡΩΟ ΣΤΟΑΣ", s["title"]))
    story.append(Spacer(1, .3*cm))
    sv = lambda k: str(member.get(k) or "—")

    # ΑΜ banner
    reg = Table([[
        Paragraph(f"<b>ΑΜ Στοάς: {sv('αρ_μητρώου_στοάς')}</b>", _S(fontName="DSB", fontSize=11, alignment=TA_CENTER, textColor=WHITE)),
        Paragraph(f"<b>ΑΜ Μεγάλης Στοάς: {sv('αρ_μητρώου_μσ')}</b>", _S(fontName="DSB", fontSize=11, alignment=TA_CENTER, textColor=WHITE)),
    ]], colWidths=[8*cm, 8*cm])
    reg.setStyle(TableStyle([
        ("BACKGROUND",   (0,0), (-1,-1), NAVY),
        ("BOTTOMPADDING",(0,0), (-1,-1), 8),
        ("TOPPADDING",   (0,0), (-1,-1), 8),
    ]))
    story.append(reg)
    story.append(Spacer(1, .4*cm))

    sections = [
        ("ΠΡΟΣΩΠΙΚΑ ΣΤΟΙΧΕΙΑ", [
            ("Επώνυμο",       sv("επώνυμο")),
            ("Όνομα",         sv("όνομα")),
            ("Πατρώνυμο",     sv("πατρώνυμο")),
            ("Ημ. Γέννησης",  sv("ημ_γέννησης")),
            ("Τόπος Γέννησης",sv("τόπος_γέννησης")),
            ("Επάγγελμα",     sv("επάγγελμα")),
        ]),
        ("ΣΤΟΙΧΕΙΑ ΕΠΙΚΟΙΝΩΝΙΑΣ", [
            ("Διεύθυνση",  sv("διεύθυνση")),
            ("Πόλη / ΤΚ",  f"{sv('πόλη')}  {sv('τκ')}"),
            ("Τηλέφωνο",   sv("τηλέφωνο")),
            ("Κινητό",     sv("κινητό")),
            ("Email",      sv("email")),
        ]),
        ("ΤΕΚΤΟΝΙΚΑ ΣΤΟΙΧΕΙΑ", [
            ("Τεκτονικός Βαθμός",  sv("τεκτονικός_βαθμός")),
            ("Κατάσταση",          sv("κατάσταση")),
            ("Ημ. Μύησης (Α΄)",    sv("ημ_μύησης")),
            ("Ημ. Εταίρου (Β΄)",   sv("ημ_εταίρου")),
            ("Ημ. Διδασκάλου (Γ΄)",sv("ημ_διδασκάλου")),
            ("Στοά Μύησης",        sv("στοά_μύησης")),
            ("Αξίωμα Στοάς",       sv("αξίωμα_στοάς")),
            ("Αξίωμα Μεγάλης Στοάς", sv("αξίωμα_μεγάλης_στοάς")),
        ]),
    ]

    for title, fields in sections:
        story.append(KeepTogether([
            Paragraph(title, s["bold"]),
            HRFlowable(width="100%", thickness=1, color=GOLD, spaceAfter=4),
        ]))
        td = [[Paragraph(f"<b>{l}:</b>", s["body"]), Paragraph(v, s["body"])]
              for l, v in fields]
        t = Table(td, colWidths=[5*cm, 11*cm])
        t.setStyle(TableStyle([
            ("FONTNAME",     (0,0), (-1,-1), "DSR"),
            ("FONTSIZE",     (0,0), (-1,-1), 10),
            ("BOTTOMPADDING",(0,0), (-1,-1), 4),
            ("ROWBACKGROUNDS",(0,0),(-1,-1), [WHITE, LIGHT]),
        ]))
        story.append(t)
        story.append(Spacer(1, .3*cm))

    if member.get("παρατηρήσεις"):
        story.append(Paragraph("<b>Παρατηρήσεις:</b>", s["bold"]))
        story.append(Paragraph(member["παρατηρήσεις"], s["body"]))

    story.append(Spacer(1, .5*cm))
    story.append(HRFlowable(width="100%", thickness=.5, color=colors.lightgrey))
    story.append(Paragraph(
        f"Εκτυπώθηκε: {date.today().strftime('%d/%m/%Y')}  |  Ο Γραμματεύς-Σφραγιδοφύλαξ",
        s["small"]))
    return _build(story)


# ═══════════════════════════════════════════════════════════════
# 4. ΜΗΤΡΩΟ ΜΕΛΩΝ (λίστα)
# ═══════════════════════════════════════════════════════════════

def generate_members_list_pdf(members_df) -> io.BytesIO:
    s = _styles()
    story = []
    story.extend(_header(s))
    story.append(Paragraph("ΜΗΤΡΩΟ ΜΕΛΩΝ ΣΤΟΑΣ", s["title"]))
    story.append(Paragraph(f"Ημερομηνία: {date.today().strftime('%d/%m/%Y')}", s["small"]))
    story.append(Spacer(1, .4*cm))

    def clean(v):
        if v is None: return ""
        sv = str(v).strip()
        return "" if sv.lower() in ("nan","none","") else sv

    headers = [
        Paragraph("ΑΜ\nΣτοάς",    s["tbl_hdr"]),
        Paragraph("ΑΜ ΜΣ",         s["tbl_hdr"]),
        Paragraph("Επώνυμο",       s["tbl_hdr"]),
        Paragraph("Όνομα",         s["tbl_hdr"]),
        Paragraph("Βαθμός",        s["tbl_hdr"]),
        Paragraph("Κατάσταση",     s["tbl_hdr"]),
        Paragraph("Αξίωμα Στοάς",  s["tbl_hdr"]),
        Paragraph("Αξίωμα ΜΣ",     s["tbl_hdr"]),
    ]
    data = [headers]
    for _, r in members_df.iterrows():
        data.append([
            Paragraph(clean(r.get("αρ_μητρώου_στοάς")),         s["tbl_cell"]),
            Paragraph(clean(r.get("αρ_μητρώου_μσ")),            s["tbl_cell"]),
            Paragraph(clean(r.get("επώνυμο")),                   s["tbl_cell"]),
            Paragraph(clean(r.get("όνομα")),                     s["tbl_cell"]),
            Paragraph(clean(r.get("τεκτονικός_βαθμός")),        s["tbl_cell"]),
            Paragraph(clean(r.get("κατάσταση")),                 s["tbl_cell"]),
            Paragraph(clean(r.get("αξίωμα_στοάς","")),          s["tbl_cell"]),
            Paragraph(clean(r.get("αξίωμα_μεγάλης_στοάς","")), s["tbl_cell"]),
        ])

    col_w = [1.3*cm, 1.5*cm, 3.8*cm, 2.8*cm, 1.9*cm, 1.7*cm, 2.8*cm, 2.7*cm]
    t = Table(data, colWidths=col_w, repeatRows=1)
    t.setStyle(_table_style())
    story.append(t)
    story.append(Spacer(1, .3*cm))
    story.append(Paragraph(f"Σύνολο: {len(members_df)} μέλη", s["small"]))

    story.append(Spacer(1, 1*cm))
    sig = Table([["", Paragraph("Ο Γραμματεύς-Σφραγιδοφύλαξ", s["sig"])]],
                colWidths=[8*cm, 8*cm])
    sig.setStyle(TableStyle([
        ("TOPPADDING", (0,0), (-1,-1), 30),
        ("LINEABOVE",  (1,0), (1,-1), .5, BLACK),
        ("ALIGN",      (1,0), (1,-1), "CENTER"),
        ("FONTNAME",   (0,0), (-1,-1), "DSR"),
    ]))
    story.append(sig)
    return _build(story)


# ═══════════════════════════════════════════════════════════════
# 5. ΠΡΩΤΟΚΟΛΛΟ
# ═══════════════════════════════════════════════════════════════

def generate_protokollon_pdf(rows, year: int) -> io.BytesIO:
    s = _styles()
    story = []
    story.extend(_header(s))
    story.append(Paragraph(f"ΠΡΩΤΟΚΟΛΛΟ ΕΓΓΡΑΦΩΝ — ΕΤΟΣ {year}", s["title"]))
    story.append(Spacer(1, .4*cm))

    headers = [
        Paragraph("ΑΠ",          s["tbl_hdr"]),
        Paragraph("Ημερ.",       s["tbl_hdr"]),
        Paragraph("Κατεύθ.",     s["tbl_hdr"]),
        Paragraph("Αποστ./Παραλ.",s["tbl_hdr"]),
        Paragraph("Θέμα",        s["tbl_hdr"]),
        Paragraph("Κατάσταση",   s["tbl_hdr"]),
    ]
    data = [headers]
    for r in rows.to_dict("records"):
        recv = r.get("αποστολέας","") or r.get("παραλήπτης","") or ""
        data.append([
            Paragraph(str(r.get("αρ_πρωτ","")),     s["tbl_cell"]),
            Paragraph(str(r.get("ημερομηνία","")),   s["tbl_cell"]),
            Paragraph(str(r.get("κατεύθυνση","")),   s["tbl_cell"]),
            Paragraph(str(recv)[:25],                 s["tbl_cell"]),
            Paragraph(str(r.get("θέμα",""))[:45],    s["tbl_cell"]),
            Paragraph(str(r.get("κατάσταση","")),    s["tbl_cell"]),
        ])
    t = Table(data, colWidths=[1.8*cm, 2.2*cm, 2.2*cm, 3.5*cm, 5.8*cm, 2*cm])
    t.setStyle(_table_style())
    story.append(t)
    story.append(Spacer(1, .3*cm))
    story.append(Paragraph(f"Σύνολο: {len(rows)} εγγραφές", s["small"]))
    return _build(story)


# ═══════════════════════════════════════════════════════════════
# 6. ΔΙΠΛΩΜΑ (Αντίγραφο Αρχείου Στοάς)
# ═══════════════════════════════════════════════════════════════

def generate_diploma_pdf(member: Dict, βαθμός: str, ημ_βαθμού: str,
                         watermark: bool = True) -> io.BytesIO:
    """
    Αντίγραφο διπλώματος για το αρχείο της Στοάς.
    Το επίσημο εκδίδεται από τη Μεγάλη Στοά.
    """
    s = _styles()
    GOLD_D = colors.HexColor("#8B6914")

    ΒΑΘΜΟΣ_ΚΕΙΜ = {
        "Μαθητής":    ("εις τόν τοῦ Μαθητοῦ",       "Μαθητοῦ"),
        "Εταίρος":    ("εις τόν τοῦ Εταίρου",        "Εταίρου"),
        "Διδάσκαλος": ("εις τόν τοῦ Εταίρου βαθμόν\nκαί εἶτα εις τόν τοῦ", "Διδασκάλου"),
    }
    βαθμ_text, βαθμ_title = ΒΑΘΜΟΣ_ΚΕΙΜ.get(βαθμός, ("εις τόν τοῦ Μαθητοῦ", "Μαθητοῦ"))
    ονομα  = f"{member.get('επώνυμο','')} {member.get('όνομα','')}".strip()
    ημ_str = _fmt_date(ημ_βαθμού)

    # Εξαγωγή έτους
    try:
        import pandas as pd
        d = pd.to_datetime(ημ_βαθμού)
        ημ_short = f"{d.day}η {ΜΗΝΕΣ[d.month]} {d.year}"
    except Exception:
        ημ_short = ημ_βαθμού

    buf = io.BytesIO()

    def draw_border(c, doc):
        w, h = A4
        mg = 1.2*cm

        # Εξωτερικό & εσωτερικό πλαίσιο
        c.setStrokeColor(GOLD_D)
        c.setLineWidth(3)
        c.rect(mg, mg, w - 2*mg, h - 2*mg)
        c.setLineWidth(1)
        inn = mg + 0.35*cm
        c.rect(inn, inn, w - 2*inn, h - 2*inn)

        # Μαίανδρος — τετραγωνάκια
        c.setFillColor(GOLD_D)
        c.setLineWidth(0)
        sq, gap = 0.27*cm, 0.31*cm
        bm = mg + 0.04*cm

        x = bm + sq
        while x < w - bm - sq * 2:
            c.rect(x, h - bm - sq, sq, sq, fill=1, stroke=0)
            c.rect(x, bm, sq, sq, fill=1, stroke=0)
            x += gap + sq

        y = bm + sq
        while y < h - bm - sq * 2:
            c.rect(bm, y, sq, sq, fill=1, stroke=0)
            c.rect(w - bm - sq, y, sq, sq, fill=1, stroke=0)
            y += gap + sq

        # Watermark διαγώνιο
        if watermark:
            c.saveState()
            c.setFillColor(colors.Color(0.75, 0.75, 0.75, alpha=0.2))
            c.setFont("DSB", 32)
            c.translate(w / 2, h / 2)
            c.rotate(38)
            c.drawCentredString(0, 0, "ΑΝΤΙΓΡΑΦΟ ΑΡΧΕΙΟΥ ΣΤΟΑΣ")
            c.restoreState()

        # Κυκλικό έμβλημα κεφαλής
        c.setStrokeColor(GOLD_D)
        c.setFillColor(WHITE)
        c.setLineWidth(1.5)
        c.circle(w / 2, h - 3.0*cm, 0.85*cm, fill=1, stroke=1)
        c.setFillColor(NAVY)
        c.setFont("DSB", 5.5)
        c.drawCentredString(w / 2, h - 2.97*cm, "Μ.Σ.Τ.Ε.")

    frame = Frame(2.2*cm, 2.2*cm, A4[0] - 4.4*cm, A4[1] - 4.4*cm,
                  leftPadding=.5*cm, rightPadding=.5*cm,
                  topPadding=.3*cm, bottomPadding=.3*cm)
    tmpl  = PageTemplate(id="diploma", frames=[frame], onPage=draw_border)
    doc   = BaseDocTemplate(buf, pagesize=A4,
                            rightMargin=2.2*cm, leftMargin=2.2*cm,
                            topMargin=2.2*cm, bottomMargin=2.2*cm)
    doc.addPageTemplates([tmpl])

    story = []
    story.append(Spacer(1, 0.7*cm))

    # Ε.Λ.Τ.Μ.Α.Τ.Σ. κεφαλίδα
    story.append(Paragraph("Ε.Λ.Τ.Μ.Α.Τ.Σ.", s["dip_hdr2"]))
    story.append(Spacer(1, .4*cm))
    story.append(HRFlowable(width="80%", thickness=1.5, color=GOLD_D, hAlign="CENTER", spaceAfter=6))
    story.append(Paragraph("ΜΕΓΑΛΗ ΣΤΟΑ ΤΗΣ ΕΛΛΑΔΟΣ", s["dip_hdr1"]))
    story.append(Paragraph("Ἀρχαίου Ἐλευθέρου καὶ Ἀποδεδεγμένου Τεκτονισμοῦ", s["dip_hdr2"]))
    story.append(HRFlowable(width="80%", thickness=1.5, color=GOLD_D, hAlign="CENTER", spaceAfter=10))
    story.append(Spacer(1, .3*cm))

    # Κείμενο
    story.append(Paragraph("Γνωτοί πάντες",                                   s["dip_intro"]))
    story.append(Paragraph("οἱ τά γράμματα τάδε ἀναγνωσόμενοι,",             s["dip_intro"]))
    story.append(Paragraph("ὅτι ὁ ἀδελφός",                                   s["dip_intro"]))
    story.append(Spacer(1, .25*cm))
    story.append(Paragraph(ονομα,                                               s["dip_name"]))
    story.append(Spacer(1, .25*cm))
    story.append(Paragraph("ὁ τὸ ἑαυτοῦ ὄνομα ἐν τῷ περιζώματι τῇ ἑαυτοῦ χειρί γεγραφώς", s["dip_body"]))
    story.append(Paragraph("εἰς τήν τῶν Λατόμων ἤ Τεκτονικῶν Τεχνῶν μεμύηται",             s["dip_body"]))
    story.append(Paragraph("καί εἰσεληλύθεν εἰς τήν ὑπό τήν Ἡμετέραν Αἰγίδα Στοάν",        s["dip_body"]))
    story.append(Paragraph("τῷ ὀνόματι μέν <b>Ἀκρόπολις</b> ὑπό ἀριθμόν 84 δέ.",           s["dip_body"]))
    story.append(Paragraph("Οὗτος τόν νενομισμένον χρόνον ἀνύσας καί δοκιμασθείς",           s["dip_body"]))
    story.append(Paragraph(f"καί ἐξετασθείς, {βαθμ_text}",                   s["dip_body"]))
    story.append(Spacer(1, .2*cm))
    story.append(Paragraph(βαθμ_title,                                          s["dip_deg"]))
    story.append(Paragraph("ἀναδέδεκται ἐν τῇ τῆς Στοᾶς συνεδρίᾳ τῇ γενομένῃ",             s["dip_body"]))
    story.append(Paragraph(f"ἐν ἡμέρᾳ μέν {ημ_str}.",                        s["dip_body"]))
    story.append(Spacer(1, .2*cm))
    story.append(Paragraph("Τό ὄνομα αὐτοῦ ἐν ταῖς Ἐπισήμοις Πράξεσι",                     s["dip_body"]))
    story.append(Paragraph("τῆς Μεγάλης Στοᾶς τῆς Ἑλλάδος",                                 s["dip_body"]))
    story.append(Paragraph("ἀναγέγραπται καί τοῦτο, οὕτω δή γενόμενον,",                    s["dip_body"]))
    story.append(Paragraph("δηλοῦται τῷ Διπλώματι τῷδε",                                     s["dip_body"]))
    story.append(Paragraph("οὐ μόνον τοῖς Ἡμετέροις αὐτογράφοις,",                          s["dip_body"]))
    story.append(Paragraph("ἀλλά καί τῇ Σφραγῖδι τῆς Μεγάλης Στοᾶς κεκυρωμένον.",          s["dip_body"]))
    story.append(Spacer(1, .2*cm))
    story.append(Paragraph("Πίστευε δ' ὅτι, οὐδείς, εἰ μή πρότερον δοκιμασθείς",            s["dip_body"]))
    story.append(Paragraph("καί ἐξετασθείς, ἔξεστιν εἰσελθεῖν",                             s["dip_body"]))
    story.append(Paragraph("εἰς Λατόμον ἤ Τεκτονικήν Στοάν",                                s["dip_body"]))
    story.append(Spacer(1, .35*cm))
    story.append(Paragraph(f"Ἐν Ἀνατολῇ Ἀθηνῶν τῇ {ημ_short}", s["dip_date"]))

    # Υπογραφές
    story.append(Spacer(1, .2*cm))
    sig_data = [[
        Paragraph("ο Μέγας Διδάσκαλος<br/><br/><br/><br/>Γεώργιος Μπινιάρης", s["dip_sig"]),
        Paragraph("", s["dip_sig"]),
        Paragraph("ο Μέγας Γραμματεύς<br/><br/><br/><br/>Ανδρέας Αρχουζής",   s["dip_sig"]),
    ]]
    sig_t = Table(sig_data, colWidths=[5.5*cm, 3*cm, 5.5*cm])
    sig_t.setStyle(TableStyle([
        ("FONTNAME",   (0,0), (-1,-1), "DSR"),
        ("FONTSIZE",   (0,0), (-1,-1), 10),
        ("ALIGN",      (0,0), (-1,-1), "CENTER"),
        ("VALIGN",     (0,0), (-1,-1), "TOP"),
        ("TOPPADDING", (0,0), (-1,-1), 5),
        ("LINEABOVE",  (0,0), (0,-1), .5, GOLD_D),
        ("LINEABOVE",  (2,0), (2,-1), .5, GOLD_D),
    ]))
    story.append(sig_t)

    if watermark:
        story.append(Spacer(1, .2*cm))
        story.append(Paragraph(
            "⚠ ΑΝΤΙΓΡΑΦΟ ΑΡΧΕΙΟΥ ΣΤΟΑΣ — Το επίσημο εκδίδεται από τη Μεγάλη Στοά",
            s["dip_wm"]))

    doc.build(story)
    buf.seek(0)
    return buf


# ═══════════════════════════════════════════════════════════════
# 7. ΔΙΠΛΩΜΑ ΜΕ ΕΠΕΞΕΡΓΑΣΙΜΟ ΚΕΙΜΕΝΟ
# ═══════════════════════════════════════════════════════════════

def generate_diploma_custom_pdf(member: Dict, text: str,
                                 ημ_βαθμού: str, watermark: bool = True,
                                 sig1_title: str = "ο Μέγας Διδάσκαλος",
                                 sig1_name:  str = "Γεώργιος Μπινιάρης",
                                 sig2_title: str = "ο Μέγας Γραμματεύς",
                                 sig2_name:  str = "Ανδρέας Αρχουζής",
                                 hdr1: str = "Ε.Λ.Τ.Μ.Α.Τ.Σ.",
                                 hdr2: str = "ΜΕΓΑΛΗ ΣΤΟΑ ΤΗΣ ΕΛΛΑΔΟΣ",
                                 hdr3: str = "Ἀρχαίου Ἐλευθέρου καὶ Ἀποδεδεγμένου Τεκτονισμοῦ",
                                 ) -> io.BytesIO:
    """
    Δίπλωμα με ελεύθερα επεξεργάσιμο κείμενο.
    Markers στο κείμενο:
      --- ΤΙΤΛΟΣ ΒΑΘΜΟΥ ---  → επόμενη γραμμή = τίτλος βαθμού (bold 26pt)
      --- ΣΥΝΕΧΕΙΑ ---        → συνέχεια italic κειμένου
    """
    s = _styles()
    GOLD_D = colors.HexColor("#8B6914")

    ονομα  = f"{member.get('επώνυμο','')} {member.get('όνομα','')}".strip()
    ημ_str = _fmt_date(ημ_βαθμού)
    try:
        import pandas as pd
        d = pd.to_datetime(ημ_βαθμού)
        ημ_short = f"{d.day}η {ΜΗΝΕΣ[d.month]} {d.year}"
    except Exception:
        ημ_short = ημ_βαθμού

    buf = io.BytesIO()

    def draw_border(c, doc):
        w, h = A4
        mg = 1.2*cm
        c.setStrokeColor(GOLD_D)
        c.setLineWidth(3)
        c.rect(mg, mg, w - 2*mg, h - 2*mg)
        c.setLineWidth(1)
        inn = mg + 0.35*cm
        c.rect(inn, inn, w - 2*inn, h - 2*inn)
        # Μαίανδρος
        c.setFillColor(GOLD_D)
        c.setLineWidth(0)
        sq, gap = 0.27*cm, 0.31*cm
        bm = mg + 0.04*cm
        x = bm + sq
        while x < w - bm - sq * 2:
            c.rect(x, h - bm - sq, sq, sq, fill=1, stroke=0)
            c.rect(x, bm, sq, sq, fill=1, stroke=0)
            x += gap + sq
        y = bm + sq
        while y < h - bm - sq * 2:
            c.rect(bm, y, sq, sq, fill=1, stroke=0)
            c.rect(w - bm - sq, y, sq, sq, fill=1, stroke=0)
            y += gap + sq
        # Watermark
        if watermark:
            c.saveState()
            c.setFillColor(colors.Color(0.75, 0.75, 0.75, alpha=0.2))
            c.setFont("DSB", 32)
            c.translate(w / 2, h / 2)
            c.rotate(38)
            c.drawCentredString(0, 0, "ΑΝΤΙΓΡΑΦΟ ΑΡΧΕΙΟΥ ΣΤΟΑΣ")
            c.restoreState()
        # Κυκλικό έμβλημα
        c.setStrokeColor(GOLD_D)
        c.setFillColor(colors.white)
        c.setLineWidth(1.5)
        c.circle(w / 2, h - 3.0*cm, 0.85*cm, fill=1, stroke=1)
        c.setFillColor(NAVY)
        c.setFont("DSB", 5.5)
        c.drawCentredString(w / 2, h - 2.97*cm, "Μ.Σ.Τ.Ε.")

    frame = Frame(2.2*cm, 2.2*cm, A4[0] - 4.4*cm, A4[1] - 4.4*cm,
                  leftPadding=.5*cm, rightPadding=.5*cm,
                  topPadding=.3*cm, bottomPadding=.3*cm)
    tmpl  = PageTemplate(id="diploma_custom", frames=[frame], onPage=draw_border)
    doc   = BaseDocTemplate(buf, pagesize=A4,
                            rightMargin=2.2*cm, leftMargin=2.2*cm,
                            topMargin=2.2*cm, bottomMargin=2.2*cm)
    doc.addPageTemplates([tmpl])

    story = []
    story.append(Spacer(1, 0.7*cm))

    # Κεφαλίδα (επεξεργάσιμη)
    story.append(Paragraph(hdr1, s["dip_hdr2"]))
    story.append(Spacer(1, .4*cm))
    story.append(HRFlowable(width="80%", thickness=1.5, color=GOLD_D, hAlign="CENTER", spaceAfter=6))
    story.append(Paragraph(hdr2, s["dip_hdr1"]))
    story.append(Paragraph(hdr3, s["dip_hdr2"]))
    story.append(HRFlowable(width="80%", thickness=1.5, color=GOLD_D, hAlign="CENTER", spaceAfter=10))
    story.append(Spacer(1, .3*cm))

    # ── Parse του ελεύθερου κειμένου ──────────────────────────
    lines = text.split("\n")
    title_next = False

    for line in lines:
        stripped = line.strip()

        # Markers
        if stripped == "--- ΤΙΤΛΟΣ ΒΑΘΜΟΥ ---":
            title_next = True
            continue
        elif stripped == "--- ΣΥΝΕΧΕΙΑ ---":
            title_next = False
            continue
        elif not stripped:
            story.append(Spacer(1, .15*cm))
            continue

        # Τίτλος βαθμού (από marker)
        if title_next:
            story.append(Paragraph(stripped, s["dip_deg"]))
            title_next = False
            continue

        # Όνομα μέλους → bold μεγάλο
        if stripped == ονομα:
            story.append(Paragraph(stripped, s["dip_name"]))
            continue

        # Κανονικές γραμμές → italic
        story.append(Paragraph(stripped, s["dip_body"]))

    # Ημερομηνία
    story.append(Spacer(1, .35*cm))
    story.append(Paragraph(f"Ἐν Ἀνατολῇ Ἀθηνῶν τῇ {ημ_short}", s["dip_date"]))

    # Υπογραφές
    story.append(Spacer(1, .2*cm))
    sig_data = [[
        Paragraph(f"{sig1_title}<br/><br/><br/><br/>{sig1_name}", s["dip_sig"]),
        Paragraph("", s["dip_sig"]),
        Paragraph(f"{sig2_title}<br/><br/><br/><br/>{sig2_name}", s["dip_sig"]),
    ]]
    sig_t = Table(sig_data, colWidths=[5.5*cm, 3*cm, 5.5*cm])
    sig_t.setStyle(TableStyle([
        ("FONTNAME",   (0,0), (-1,-1), "DSR"),
        ("FONTSIZE",   (0,0), (-1,-1), 10),
        ("ALIGN",      (0,0), (-1,-1), "CENTER"),
        ("VALIGN",     (0,0), (-1,-1), "TOP"),
        ("TOPPADDING", (0,0), (-1,-1), 5),
        ("LINEABOVE",  (0,0), (0,-1), .5, GOLD_D),
        ("LINEABOVE",  (2,0), (2,-1), .5, GOLD_D),
    ]))
    story.append(sig_t)

    if watermark:
        story.append(Spacer(1, .2*cm))
        story.append(Paragraph(
            "⚠ ΑΝΤΙΓΡΑΦΟ ΑΡΧΕΙΟΥ ΣΤΟΑΣ — Το επίσημο εκδίδεται από τη Μεγάλη Στοά",
            s["dip_wm"]))

    doc.build(story)
    buf.seek(0)
    return buf

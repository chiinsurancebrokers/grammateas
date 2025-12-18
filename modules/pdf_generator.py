"""
PDF Generator για Καρτέλες Μελών (ΑΚΡΟΠΟΛΙΣ Υπ ΑΡΙΘΜ 84)
- Μόνο 2 αριθμοί μητρώου: Στοάς 84 & Μεγάλης Στοάς
- "ΤΕΚΤΟΝΙΚΕΣ ΠΛΗΡΟΦΟΡΙΕΣ"
- "Διδάσκαλος" (διορθώνει αν βρει "Δάσκαλος")
"""

import sqlite3
import io
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


# ---------------- Fonts (Greek-friendly) ----------------
def _register_fonts():
    try:
        pdfmetrics.registerFont(TTFont("DejaVuSans", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"))
        pdfmetrics.registerFont(TTFont("DejaVuSans-Bold", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"))
        return "DejaVuSans", "DejaVuSans-Bold"
    except Exception:
        return "Helvetica", "Helvetica-Bold"


FONT_NAME, FONT_NAME_BOLD = _register_fonts()


# ---------------- DB ----------------
def get_member(member_id: int, db_path: str = "lodge_members.db"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM members WHERE member_id = ?", (member_id,))
    columns = [d[0] for d in cursor.description] if cursor.description else []
    row = cursor.fetchone()
    conn.close()
    return dict(zip(columns, row)) if row else None


def _val(member: dict, key: str, fallback: str = "—") -> str:
    v = member.get(key)
    if v is None or str(v).strip() == "":
        return fallback
    return str(v)


def create_member_card_pdf(member_id: int, output_path: str | None = None, db_path: str = "lodge_members.db"):
    member = get_member(member_id, db_path=db_path)
    if not member:
        return None

    # Normalize degree label
    deg = member.get("current_degree", "Μαθητής") or "Μαθητής"
    if str(deg).strip() == "Δάσκαλος":
        deg = "Διδάσκαλος"

    # Only 2 registry numbers
    lodge_no = member.get("lodge_reg_no") or "—"
    gl_no = member.get("grand_lodge_reg_no") or "—"

    # Output buffer
    buffer = open(output_path, "wb") if output_path else io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        leftMargin=2.5 * cm,
        rightMargin=2.5 * cm,
    )

    story = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "Title",
        parent=styles["Heading1"],
        fontSize=18,
        textColor=colors.HexColor("#1e3a8a"),
        spaceAfter=10,
        alignment=TA_CENTER,
        fontName=FONT_NAME_BOLD,
    )

    heading_style = ParagraphStyle(
        "Heading",
        parent=styles["Heading2"],
        fontSize=12,
        textColor=colors.HexColor("#2563eb"),
        spaceAfter=10,
        spaceBefore=15,
        fontName=FONT_NAME_BOLD,
    )

    number_style = ParagraphStyle(
        "Number",
        fontSize=16,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#dc2626"),
        fontName=FONT_NAME_BOLD,
        spaceAfter=6,
    )

    table_style = TableStyle(
        [
            ("FONTNAME", (0, 0), (0, -1), FONT_NAME_BOLD),
            ("FONTNAME", (1, 0), (1, -1), FONT_NAME),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ]
    )

    # ---------------- Header ----------------
    story.append(Paragraph("ΚΑΡΤΕΛΑ ΜΕΛΟΥΣ", title_style))
    story.append(Paragraph("ΑΚΡΟΠΟΛΙΣ Υπ ΑΡΙΘΜ 84", title_style))
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph(f"Αριθμός Μητρώου (Στοάς 84): {lodge_no}", number_style))
    story.append(Paragraph(f"Αριθμός Μητρώου (Μεγάλης Στοάς): {gl_no}", number_style))
    story.append(Spacer(1, 0.6 * cm))

    # ---------------- Sections ----------------
    story.append(Paragraph("ΠΡΟΣΩΠΙΚΑ ΣΤΟΙΧΕΙΑ", heading_style))
    personal_data = [
        ["Επώνυμο:", _val(member, "last_name")],
        ["Όνομα:", _val(member, "first_name")],
        ["Πατρώνυμο:", _val(member, "fathers_name")],
        ["Ημ/νία Γέννησης:", _val(member, "birth_date")],
        ["Τόπος Γέννησης:", _val(member, "birth_place")],
        ["Επάγγελμα:", _val(member, "profession")],
        ["ΑΦΜ:", _val(member, "tax_id", _val(member, "afm"))],
        ["Αρ. Ταυτότητας:", _val(member, "id_number")],
    ]
    t1 = Table(personal_data, colWidths=[5 * cm, 10 * cm])
    t1.setStyle(table_style)
    story.append(t1)

    story.append(Paragraph("ΣΤΟΙΧΕΙΑ ΕΠΙΚΟΙΝΩΝΙΑΣ", heading_style))
    contact_data = [
        ["Διεύθυνση:", _val(member, "address")],
        ["ΤΚ:", _val(member, "postal_code")],
        ["Πόλη:", _val(member, "city")],
        ["Τηλ. Οικίας:", _val(member, "home_phone")],
        ["Κινητό:", _val(member, "mobile_phone")],
        ["E-mail:", _val(member, "email")],
    ]
    t2 = Table(contact_data, colWidths=[5 * cm, 10 * cm])
    t2.setStyle(table_style)
    story.append(t2)

    story.append(Paragraph("ΤΕΚΤΟΝΙΚΕΣ ΠΛΗΡΟΦΟΡΙΕΣ", heading_style))
    tectonic_data = [
        ["Ημ/νία Μύησης:", _val(member, "initiation_date")],
        ["Αρ. Διπλ. Μύησης:", _val(member, "initiation_diploma")],
        ["Ημ/νία 2ου Βαθμού:", _val(member, "second_degree_date")],
        ["Αρ. Διπλ. 2ου:", _val(member, "second_degree_diploma")],
        ["Ημ/νία 3ου Βαθμού:", _val(member, "third_degree_date")],
        ["Αρ. Διπλ. 3ου:", _val(member, "third_degree_diploma")],
        ["Τρέχων Βαθμός:", str(deg)],
        ["Στοά Μύησης:", _val(member, "initiation_lodge", "ΑΚΡΟΠΟΛΙΣ")],
        ["Αρ. Στοάς:", _val(member, "initiation_lodge_number")],
        ["Εισηγητής:", _val(member, "sponsor")],
    ]
    t3 = Table(tectonic_data, colWidths=[5 * cm, 10 * cm])
    t3.setStyle(table_style)
    story.append(t3)

    story.append(PageBreak())

    story.append(Paragraph("ΙΣΤΟΡΙΚΟ ΣΤΟΑΣ", heading_style))
    history_data = [
        ["Ημ/νία Εισόδου:", _val(member, "entry_date")],
        ["Αξιώματα:", _val(member, "offices_held")],
        ["Παράσημα:", _val(member, "honors")],
        ["Επιτροπές:", _val(member, "committees")],
    ]
    t4 = Table(history_data, colWidths=[5 * cm, 10 * cm])
    t4.setStyle(table_style)
    story.append(t4)

    story.append(Paragraph("ΟΙΚΟΓΕΝΕΙΑΚΑ ΣΤΟΙΧΕΙΑ", heading_style))
    family_data = [
        ["Οικογ. Κατάσταση:", _val(member, "marital_status")],
        ["Όνομα Συζύγου:", _val(member, "spouse_name")],
        ["Ονόματα Τέκνων:", _val(member, "children_names")],
        ["Επείγον Τηλ.:", _val(member, "emergency_phone")],
        ["Επαφή Έκτ. Ανάγκης:", _val(member, "emergency_contact")],
    ]
    t5 = Table(family_data, colWidths=[5 * cm, 10 * cm])
    t5.setStyle(table_style)
    story.append(t5)

    story.append(Paragraph("ΔΙΟΙΚΗΤΙΚΑ ΣΤΟΙΧΕΙΑ", heading_style))
    admin_data = [
        ["Κατάσταση Μέλους:", _val(member, "member_status", "Ενεργό")],
        ["Ημ/νία Αλλαγής:", _val(member, "status_change_date")],
        ["Λόγος Αλλαγής:", _val(member, "status_change_reason")],
        ["Οικον. Τακτοποίηση:", _val(member, "financial_status", "Ναι")],
        ["Τελ. Πληρωμή:", _val(member, "last_payment_date")],
    ]
    t6 = Table(admin_data, colWidths=[5 * cm, 10 * cm])
    t6.setStyle(table_style)
    story.append(t6)

    if member.get("notes"):
        story.append(Spacer(1, 0.4 * cm))
        story.append(Paragraph("ΠΑΡΑΤΗΡΗΣΕΙΣ", heading_style))
        story.append(Paragraph(str(member.get("notes")), styles["Normal"]))

    story.append(Spacer(1, 1.6 * cm))
    sig_data = [
        ["Ημερομηνία Έκδοσης:", datetime.now().strftime("%d/%m/%Y")],
        ["Γραμματεύς-Σφραγιδοφύλαξ:", "_____________________"],
    ]
    t_sig = Table(sig_data, colWidths=[6 * cm, 9 * cm])
    t_sig.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (0, -1), FONT_NAME_BOLD),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ]
        )
    )
    story.append(t_sig)

    doc.build(story)

    if output_path:
        buffer.close()
        return output_path

    buffer.seek(0)
    return buffer

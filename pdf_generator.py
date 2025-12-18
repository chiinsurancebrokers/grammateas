"""
Απλοποιημένος PDF Generator για Καρτέλες Μελών
"""

import sqlite3
import io
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Register Greek-supporting fonts
try:
    pdfmetrics.registerFont(TTFont('DejaVuSans', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
    pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'))
    FONT_NAME = 'DejaVuSans'
    FONT_NAME_BOLD = 'DejaVuSans-Bold'
except:
    FONT_NAME = FONT_NAME
    FONT_NAME_BOLD = FONT_NAME_BOLD


def get_member(member_id, db_path='lodge_members.db'):
    """Λήψη στοιχείων μέλους"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM members WHERE member_id = ?", (member_id,))
    columns = [description[0] for description in cursor.description]
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return dict(zip(columns, row))
    return None


def create_member_card_pdf(member_id, output_path=None):
    """Δημιουργία καρτέλας μέλους σε PDF"""
    
    member = get_member(member_id)
    if not member:
        print(f"Δεν βρέθηκε μέλος με ID: {member_id}")
        return None
    
    # Δημιουργία buffer
    if output_path:
        buffer = open(output_path, 'wb')
    else:
        buffer = io.BytesIO()
    
    # Ρυθμίσεις PDF
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                           topMargin=2*cm, bottomMargin=2*cm,
                           leftMargin=2.5*cm, rightMargin=2.5*cm)
    
    story = []
    styles = getSampleStyleSheet()
    
    # Custom Styles
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#1e3a8a'),
        spaceAfter=20,
        alignment=TA_CENTER,
        fontName=FONT_NAME_BOLD
    )
    
    heading_style = ParagraphStyle(
        'Heading',
        parent=styles['Heading2'],
        fontSize=12,
        textColor=colors.HexColor('#2563eb'),
        spaceAfter=10,
        spaceBefore=15,
        fontName=FONT_NAME_BOLD
    )
    
    # Τίτλος
    story.append(Paragraph("ΚΑΡΤΕΛΑ ΜΕΛΟΥΣ", title_style))
    story.append(Paragraph("ΑΚΡΟΠΟΛΙΣ Υπ ΑΡΙΘΜ 84", title_style))
    story.append(Spacer(1, 0.5*cm))
    
    # Αριθμός Μητρώου
    number_style = ParagraphStyle('Number', fontSize=20, alignment=TA_CENTER,
                                  textColor=colors.HexColor('#dc2626'), fontName=FONT_NAME_BOLD)
    story.append(Paragraph(f"Αριθμός Μητρώου: {member['member_id']}", number_style))
    story.append(Spacer(1, 1*cm))
    
    # Βασικό Table Style
    table_style = TableStyle([
        ('FONTNAME', (0, 0), (0, -1), FONT_NAME_BOLD),
        ('FONTNAME', (1, 0), (1, -1), FONT_NAME),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ])
    
    # ΠΡΟΣΩΠΙΚΑ ΣΤΟΙΧΕΙΑ
    story.append(Paragraph("ΠΡΟΣΩΠΙΚΑ ΣΤΟΙΧΕΙΑ", heading_style))
    personal_data = [
        ["Επώνυμο:", str(member.get('last_name', '—'))],
        ["Όνομα:", str(member.get('first_name', '—'))],
        ["Πατρώνυμο:", str(member.get('fathers_name') or '—')],
        ["Ημ/νία Γέννησης:", str(member.get('birth_date') or '—')],
        ["Τόπος Γέννησης:", str(member.get('birth_place') or '—')],
        ["Επάγγελμα:", str(member.get('profession', '—'))],
        ["ΑΦΜ:", str(member.get('tax_id') or '—')],
        ["Αρ. Ταυτότητας:", str(member.get('id_number') or '—')],
    ]
    t1 = Table(personal_data, colWidths=[5*cm, 10*cm])
    t1.setStyle(table_style)
    story.append(t1)
    
    # ΣΤΟΙΧΕΙΑ ΕΠΙΚΟΙΝΩΝΙΑΣ
    story.append(Paragraph("ΣΤΟΙΧΕΙΑ ΕΠΙΚΟΙΝΩΝΙΑΣ", heading_style))
    contact_data = [
        ["Διεύθυνση:", str(member.get('address') or '—')],
        ["ΤΚ:", str(member.get('postal_code') or '—')],
        ["Πόλη:", str(member.get('city') or '—')],
        ["Τηλ. Οικίας:", str(member.get('home_phone') or '—')],
        ["Κινητό:", str(member.get('mobile_phone') or '—')],
        ["E-mail:", str(member.get('email') or '—')],
    ]
    t2 = Table(contact_data, colWidths=[5*cm, 10*cm])
    t2.setStyle(table_style)
    story.append(t2)
    
    # ΣΤΟΙΧΕΙΑ ΜΕΓΑΛΗΣ ΣΤΟΑΣ
    story.append(Paragraph("ΣΤΟΙΧΕΙΑ ΜΕΓΑΛΗΣ ΣΤΟΑΣ", heading_style))
    masonic_data = [
        ["Ημ/νία Μύησης:", str(member.get('initiation_date') or '—')],
        ["Αρ. Διπλ. Μύησης:", str(member.get('initiation_diploma') or '—')],
        ["Ημ/νία 2ου Βαθμού:", str(member.get('second_degree_date') or '—')],
        ["Αρ. Διπλ. 2ου:", str(member.get('second_degree_diploma') or '—')],
        ["Ημ/νία 3ου Βαθμού:", str(member.get('third_degree_date') or '—')],
        ["Αρ. Διπλ. 3ου:", str(member.get('third_degree_diploma') or '—')],
        ["Τρέχων Βαθμός:", str(member.get('current_degree', 'Μαθητής'))],
        ["Στοά Μύησης:", str(member.get('initiation_lodge', 'ΑΚΡΟΠΟΛΙΣ'))],
        ["Αρ. Στοάς:", str(member.get('initiation_lodge_number') or '—')],
        ["Εισηγητής:", str(member.get('sponsor') or '—')],
    ]
    t3 = Table(masonic_data, colWidths=[5*cm, 10*cm])
    t3.setStyle(table_style)
    story.append(t3)
    
    # Page Break
    story.append(PageBreak())
    
    # ΙΣΤΟΡΙΚΟ ΣΤΟΑΣ
    story.append(Paragraph("ΙΣΤΟΡΙΚΟ ΣΤΟΑΣ", heading_style))
    history_data = [
        ["Ημ/νία Εισόδου:", str(member.get('entry_date') or '—')],
        ["Αξιώματα:", str(member.get('offices_held') or '—')],
        ["Παράσημα:", str(member.get('honors') or '—')],
        ["Επιτροπές:", str(member.get('committees') or '—')],
    ]
    t4 = Table(history_data, colWidths=[5*cm, 10*cm])
    t4.setStyle(table_style)
    story.append(t4)
    
    # ΟΙΚΟΓΕΝΕΙΑΚΑ
    story.append(Paragraph("ΟΙΚΟΓΕΝΕΙΑΚΑ ΣΤΟΙΧΕΙΑ", heading_style))
    family_data = [
        ["Οικογ. Κατάσταση:", str(member.get('marital_status') or '—')],
        ["Όνομα Συζύγου:", str(member.get('spouse_name') or '—')],
        ["Ονόματα Τέκνων:", str(member.get('children_names') or '—')],
        ["Επείγον Τηλ.:", str(member.get('emergency_phone') or '—')],
        ["Επαφή Έκτ. Ανάγκης:", str(member.get('emergency_contact') or '—')],
    ]
    t5 = Table(family_data, colWidths=[5*cm, 10*cm])
    t5.setStyle(table_style)
    story.append(t5)
    
    # ΔΙΟΙΚΗΤΙΚΑ
    story.append(Paragraph("ΔΙΟΙΚΗΤΙΚΑ ΣΤΟΙΧΕΙΑ", heading_style))
    admin_data = [
        ["Κατάσταση Μέλους:", str(member.get('member_status', 'Ενεργό'))],
        ["Ημ/νία Αλλαγής:", str(member.get('status_change_date') or '—')],
        ["Λόγος Αλλαγής:", str(member.get('status_change_reason') or '—')],
        ["Οικον. Τακτοποίηση:", str(member.get('financial_status', 'Ναι'))],
        ["Τελ. Πληρωμή:", str(member.get('last_payment_date') or '—')],
    ]
    t6 = Table(admin_data, colWidths=[5*cm, 10*cm])
    t6.setStyle(table_style)
    story.append(t6)
    
    # Παρατηρήσεις
    if member.get('notes'):
        story.append(Spacer(1, 0.5*cm))
        story.append(Paragraph("ΠΑΡΑΤΗΡΗΣΕΙΣ", heading_style))
        notes_text = str(member.get('notes', ''))
        story.append(Paragraph(notes_text, styles['Normal']))
    
    # Υπογραφή
    story.append(Spacer(1, 2*cm))
    sig_data = [
        ["Ημερομηνία Έκδοσης:", datetime.now().strftime('%d/%m/%Y')],
        ["Γραμματεύς-Σφραγιδοφύλαξ:", "_____________________"],
    ]
    t_sig = Table(sig_data, colWidths=[6*cm, 9*cm])
    t_sig.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), FONT_NAME_BOLD),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    ]))
    story.append(t_sig)
    
    # Build PDF
    doc.build(story)
    
    if output_path:
        buffer.close()
        return output_path
    else:
        buffer.seek(0)
        return buffer


# Test
if __name__ == "__main__":
    import sys
    
    member_id = 1 if len(sys.argv) < 2 else int(sys.argv[1])
    output = f"/mnt/user-data/outputs/Kartela_Melous_{member_id}.pdf"
    
    print(f"Δημιουργία καρτέλας για μέλος {member_id}...")
    result = create_member_card_pdf(member_id, output)
    
    if result:
        import os
        size = os.path.getsize(result)
        print(f"✅ Επιτυχία! Αρχείο: {result}")
        print(f"📄 Μέγεθος: {size:,} bytes ({size/1024:.1f} KB)")
    else:
        print("❌ Αποτυχία δημιουργίας καρτέλας")

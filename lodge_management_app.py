"""
Σύστημα Διαχείρισης Στοάς - Lodge Management System
Πλήρες σύστημα για τη διαχείριση Μασονικής Στοάς

Δημιουργήθηκε για τη Στοά ΑΚΡΟΠΟΛΙΣ
Γραμματεύς-Σφραγιδοφύλαξ: Χρήστος Ιατρόπουλος
"""
import os
import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import io
import zipfile
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Register Greek-supporting fonts
try:
    pdfmetrics.registerFont(TTFont('DejaVuSans', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
    pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'))
    FONT_NAME = 'DejaVuSans'
    FONT_NAME_BOLD = 'DejaVuSans-Bold'
except:
    # Fallback to Helvetica if DejaVu not available
    FONT_NAME = 'Helvetica'
    FONT_NAME_BOLD = 'Helvetica-Bold'

# =============================================================================
# CONFIGURATION
# =============================================================================

st.set_page_config(
    page_title="Σύστημα Διαχείρισης Στοάς",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1e3a8a;
        text-align: center;
        padding: 1rem 0;
        border-bottom: 3px solid #2563eb;
        margin-bottom: 2rem;
    }
    .stMetric {
        background-color: #f8fafc;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #e2e8f0;
    }
    .stButton>button {
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# DATABASE FUNCTIONS
# =============================================================================

def get_db_connection(db_path='lodge_members.db'):
    """Σύνδεση με τη βάση δεδομένων"""
    return sqlite3.connect(db_path)

def get_all_members():
    """Λήψη όλων των μελών"""
    conn = get_db_connection()
    query = """
        SELECT 
            member_id, last_name, first_name, profession,
            mobile_phone, email, current_degree, member_status,
            entry_date, last_payment_date, city
        FROM members
        ORDER BY last_name, first_name
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def get_member_details(member_id):
    """Λήψη πλήρων στοιχείων μέλους"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM members WHERE member_id = ?", (member_id,))
    columns = [description[0] for description in cursor.description]
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return dict(zip(columns, row))
    return None

def update_member(member_id, data):
    """Ενημέρωση στοιχείων μέλους"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    set_clause = ", ".join([f"{key} = ?" for key in data.keys()])
    set_clause += ", updated_at = ?"
    
    values = list(data.values()) + [datetime.now().strftime('%Y-%m-%d %H:%M:%S'), member_id]
    
    cursor.execute(f"UPDATE members SET {set_clause} WHERE member_id = ?", values)
    conn.commit()
    conn.close()

def get_statistics():
    """Στατιστικά μητρώου"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Συνολικά μέλη
    cursor.execute("SELECT COUNT(*) FROM members")
    total = cursor.fetchone()[0]
    
    # Ενεργά μέλη
    cursor.execute("SELECT COUNT(*) FROM members WHERE member_status = 'Ενεργό'")
    active = cursor.fetchone()[0]
    
    # Ανά βαθμό
    cursor.execute("SELECT current_degree, COUNT(*) FROM members GROUP BY current_degree")
    degrees = dict(cursor.fetchall())
    
    conn.close()
    
    return {
        'total': total,
        'active': active,
        'degrees': degrees
    }

# =============================================================================
# PDF GENERATION FUNCTIONS
# =============================================================================

def generate_member_card_pdf(member_id):
    """Δημιουργία καρτέλας μέλους σε PDF"""
    
    member = get_member_details(member_id)
    if not member:
        return None
    
    buffer = io.BytesIO()
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
    buffer.seek(0)
    
    return buffer

# =============================================================================
# STREAMLIT APP
# =============================================================================

def main():
    """Main application"""
    
    # Sidebar Navigation
    st.sidebar.markdown("## 🏛️ Στοά ΑΚΡΟΠΟΛΙΣ")
    st.sidebar.markdown("---")
    
    page = st.sidebar.radio(
        "Πλοήγηση",
        [
            "🏠 Αρχική",
            "📋 Μητρώο Μελών",
            "👤 Επεξεργασία Μέλους",
            "✏️ Μαζική Επεξεργασία",
            "📄 Καρτέλες PDF",
            "📈 Στατιστικά"
        ]
    )
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("**Γραμματεύς-Σφραγιδοφύλαξ**")
    st.sidebar.markdown("Χρήστος Ιατρόπουλος")
    st.sidebar.markdown(f"*{datetime.now().strftime('%d/%m/%Y')}*")
    
    # Main Content
    if page == "🏠 Αρχική":
        show_home()
    elif page == "📋 Μητρώο Μελών":
        show_member_list()
    elif page == "👤 Επεξεργασία Μέλους":
        show_member_edit()
    elif page == "✏️ Μαζική Επεξεργασία":
        show_bulk_edit()
    elif page == "📄 Καρτέλες PDF":
        show_pdf_generation()
    elif page == "📈 Στατιστικά":
        show_statistics()

def show_home():
    """Αρχική σελίδα"""
    st.markdown('<div class="main-header">🏛️ Σύστημα Διαχείρισης Στοάς</div>', unsafe_allow_html=True)
    
    st.markdown("""
    ### Καλώς ήρθατε στο Σύστημα Διαχείρισης της Στοάς ΑΚΡΟΠΟΛΙΣ
    
    Το σύστημα αυτό παρέχει:
    
    - **📋 Μητρώο Μελών**: Διαχείριση και αναζήτηση μελών
    - **👤 Επεξεργασία**: Ενημέρωση στοιχείων μελών
    - **📄 Καρτέλες PDF**: Δημιουργία επίσημων καρτελών
    - **📈 Στατιστικά**: Αναλυτικά στοιχεία μητρώου
    
    ---
    """)
    
    # Quick Stats
    stats = get_statistics()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Σύνολο Μελών", stats['total'])
    
    with col2:
        st.metric("Ενεργά Μέλη", stats['active'])
    
    with col3:
        mathites = stats['degrees'].get('Μαθητής', 0)
        st.metric("Μαθητές", mathites)
    
    with col4:
        etairoi = stats['degrees'].get('Εταίρος', 0)
        st.metric("Εταίροι", etairoi)
    
    st.markdown("---")
    
    # Recent Activity
    st.subheader("📌 Πρόσφατη Δραστηριότητα")
    
    df = get_all_members()
    recent = df.head(5)[['member_id', 'last_name', 'first_name', 'current_degree', 'member_status']]
    recent = recent.rename(columns={
        'member_id': 'Α/Α',
        'last_name': 'Επώνυμο',
        'first_name': 'Όνομα',
        'current_degree': 'Βαθμός',
        'member_status': 'Κατάσταση'
    })
    
    st.dataframe(recent, use_container_width=True, hide_index=True)

def show_member_list():
    """Λίστα μελών"""
    st.markdown('<div class="main-header">📋 Μητρώο Μελών</div>', unsafe_allow_html=True)
    
    # Φίλτρα
    col1, col2, col3 = st.columns(3)
    
    with col1:
        search_name = st.text_input("🔍 Αναζήτηση (Όνομα/Επώνυμο)", key="search_name")
    
    with col2:
        filter_status = st.selectbox(
            "Κατάσταση",
            ["Όλα", "Ενεργό", "Ανενεργό", "Αποχωρήσαν", "Διαγραφέν"],
            key="filter_status"
        )
    
    with col3:
        filter_degree = st.selectbox(
            "Βαθμός",
            ["Όλοι", "Μαθητής", "Εταίρος", "Δάσκαλος"],
            key="filter_degree"
        )
    
    # Λήψη δεδομένων
    df = get_all_members()
    
    # Εφαρμογή φίλτρων
    if search_name:
        df = df[
            df['last_name'].str.contains(search_name, case=False, na=False) |
            df['first_name'].str.contains(search_name, case=False, na=False)
        ]
    
    if filter_status != "Όλα":
        df = df[df['member_status'] == filter_status]
    
    if filter_degree != "Όλοι":
        df = df[df['current_degree'] == filter_degree]
    
    # Μετονομασία στηλών
    display_df = df.rename(columns={
        'member_id': 'Α/Α',
        'last_name': 'Επώνυμο',
        'first_name': 'Όνομα',
        'profession': 'Επάγγελμα',
        'mobile_phone': 'Κινητό',
        'email': 'Email',
        'current_degree': 'Βαθμός',
        'member_status': 'Κατάσταση',
        'city': 'Πόλη'
    })
    
    st.dataframe(
        display_df[['Α/Α', 'Επώνυμο', 'Όνομα', 'Επάγγελμα', 'Κινητό', 'Πόλη', 'Βαθμός', 'Κατάσταση']],
        use_container_width=True,
        hide_index=True
    )
    
    st.info(f"📊 **Σύνολο μελών:** {len(df)}")

def show_member_edit():
    """Επεξεργασία μέλους"""
    st.markdown('<div class="main-header">👤 Επεξεργασία Στοιχείων Μέλους</div>', unsafe_allow_html=True)
    
    # Επιλογή μέλους
    members_df = get_all_members()
    member_options = {
        f"{row['member_id']}: {row['last_name']} {row['first_name']}": row['member_id']
        for _, row in members_df.iterrows()
    }
    
    selected_member_str = st.selectbox(
        "Επιλέξτε Μέλος",
        options=list(member_options.keys()),
        key="selected_member"
    )
    
    if selected_member_str:
        member_id = member_options[selected_member_str]
        member = get_member_details(member_id)
        
        if member:
            with st.form("edit_member_form"):
                st.markdown("### 📝 Προσωπικά Στοιχεία")
                col1, col2 = st.columns(2)
                
                with col1:
                    last_name = st.text_input("Επώνυμο*", value=member.get('last_name', ''))
                    first_name = st.text_input("Όνομα*", value=member.get('first_name', ''))
                    fathers_name = st.text_input("Πατρώνυμο", value=member.get('fathers_name') or '')
                    birth_place = st.text_input("Τόπος Γέννησης", value=member.get('birth_place') or '')
                
                with col2:
                    profession = st.text_input("Επάγγελμα*", value=member.get('profession', ''))
                    tax_id = st.text_input("ΑΦΜ", value=member.get('tax_id') or '')
                    id_number = st.text_input("Αρ. Ταυτότητας", value=member.get('id_number') or '')
                
                st.markdown("### 📧 Στοιχεία Επικοινωνίας")
                col1, col2 = st.columns(2)
                
                with col1:
                    address = st.text_input("Διεύθυνση", value=member.get('address') or '')
                    postal_code = st.text_input("ΤΚ", value=member.get('postal_code') or '')
                    city = st.text_input("Πόλη", value=member.get('city') or '')
                
                with col2:
                    home_phone = st.text_input("Τηλ. Οικίας", value=member.get('home_phone') or '')
                    mobile_phone = st.text_input("Κινητό*", value=member.get('mobile_phone', ''))
                    email = st.text_input("Email*", value=member.get('email', ''))
                
                st.markdown("### 🔺 Μασονικά Στοιχεία")
                col1, col2 = st.columns(2)
                
                with col1:
                    initiation_date = st.text_input("Ημ/νία Μύησης (YYYY-MM-DD)", value=member.get('initiation_date') or '')
                    initiation_diploma = st.text_input("Αρ. Διπλώματος", value=member.get('initiation_diploma') or '')
                    current_degree = st.selectbox(
                        "Τρέχων Βαθμός",
                        ["Μαθητής", "Εταίρος", "Δάσκαλος"],
                        index=["Μαθητής", "Εταίρος", "Δάσκαλος"].index(member.get('current_degree', 'Μαθητής'))
                    )
                
                with col2:
                    initiation_lodge = st.text_input("Στοά Μύησης", value=member.get('initiation_lodge', 'ΑΚΡΟΠΟΛΙΣ'))
                    sponsor = st.text_input("Εισηγητής", value=member.get('sponsor') or '')
                
                st.markdown("### 📊 Διοικητικά")
                col1, col2 = st.columns(2)
                
                with col1:
                    member_status = st.selectbox(
                        "Κατάσταση Μέλους",
                        ["Ενεργό", "Ανενεργό", "Αποχωρήσαν", "Διαγραφέν"],
                        index=["Ενεργό", "Ανενεργό", "Αποχωρήσαν", "Διαγραφέν"].index(member.get('member_status', 'Ενεργό'))
                    )
                    financial_status = st.selectbox(
                        "Οικονομική Τακτοποίηση",
                        ["Ναι", "Όχι"],
                        index=["Ναι", "Όχι"].index(member.get('financial_status', 'Ναι'))
                    )
                
                with col2:
                    last_payment_date = st.text_input("Τελ. Πληρωμή (YYYY-MM-DD)", value=member.get('last_payment_date') or '')
                
                notes = st.text_area("Παρατηρήσεις", value=member.get('notes') or '', height=100)
                
                # Submit
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    submitted = st.form_submit_button("💾 Αποθήκευση Αλλαγών", type="primary", use_container_width=True)
                
                if submitted:
                    update_data = {
                        'last_name': last_name,
                        'first_name': first_name,
                        'fathers_name': fathers_name,
                        'birth_place': birth_place,
                        'profession': profession,
                        'tax_id': tax_id,
                        'id_number': id_number,
                        'address': address,
                        'postal_code': postal_code,
                        'city': city,
                        'home_phone': home_phone,
                        'mobile_phone': mobile_phone,
                        'email': email,
                        'initiation_date': initiation_date if initiation_date else None,
                        'initiation_diploma': initiation_diploma,
                        'current_degree': current_degree,
                        'initiation_lodge': initiation_lodge,
                        'sponsor': sponsor,
                        'member_status': member_status,
                        'financial_status': financial_status,
                        'last_payment_date': last_payment_date if last_payment_date else None,
                        'notes': notes
                    }
                    
                    update_member(member_id, update_data)
                    st.success("✅ Τα στοιχεία ενημερώθηκαν επιτυχώς!")
                    st.rerun()

def show_pdf_generation():
    """Δημιουργία καρτελών PDF"""
    st.markdown('<div class="main-header">📄 Δημιουργία Καρτελών</div>', unsafe_allow_html=True)
    
    members_df = get_all_members()
    
    # Μεμονωμένη καρτέλα
    st.subheader("📝 Μεμονωμένη Καρτέλα")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        member_options = {
            f"{row['member_id']}: {row['last_name']} {row['first_name']}": row['member_id']
            for _, row in members_df.iterrows()
        }
        
        selected_member = st.selectbox(
            "Επιλέξτε Μέλος",
            options=list(member_options.keys()),
            key="pdf_member"
        )
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("📄 Δημιουργία", type="primary", use_container_width=True):
            if selected_member:
                member_id = member_options[selected_member]
                
                with st.spinner("Δημιουργία καρτέλας..."):
                    pdf_buffer = generate_member_card_pdf(member_id)
                    
                    if pdf_buffer:
                        member = get_member_details(member_id)
                        filename = f"Kartela_{member['last_name']}_{member['first_name']}.pdf"
                        
                        st.download_button(
                            label="⬇️ Λήψη Καρτέλας",
                            data=pdf_buffer,
                            file_name=filename,
                            mime="application/pdf",
                            type="primary",
                            use_container_width=True
                        )
                        
                        st.success("✅ Η καρτέλα δημιουργήθηκε επιτυχώς!")
    
    st.markdown("---")
    
    # Μαζική δημιουργία
    st.subheader("📦 Μαζική Δημιουργία Καρτελών")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        if st.button("📦 Δημιουργία Όλων των Καρτελών (ZIP)", type="secondary", use_container_width=True):
            with st.spinner(f"Δημιουργία {len(members_df)} καρτελών..."):
                zip_buffer = io.BytesIO()
                
                with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                    for _, row in members_df.iterrows():
                        pdf_buffer = generate_member_card_pdf(row['member_id'])
                        if pdf_buffer:
                            filename = f"Kartela_{row['last_name']}_{row['first_name']}.pdf"
                            zip_file.writestr(filename, pdf_buffer.getvalue())
                
                zip_buffer.seek(0)
                
                st.download_button(
                    label="⬇️ Λήψη Όλων (ZIP)",
                    data=zip_buffer,
                    file_name=f"Karteles_Melon_{datetime.now().strftime('%Y%m%d')}.zip",
                    mime="application/zip",
                    type="primary",
                    use_container_width=True
                )
                
                st.success(f"✅ Δημιουργήθηκαν {len(members_df)} καρτέλες!")

def show_statistics():
    """Στατιστικά μητρώου"""
    st.markdown('<div class="main-header">📈 Στατιστικά Μητρώου</div>', unsafe_allow_html=True)
    
    df = get_all_members()
    stats = get_statistics()
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Σύνολο Μελών", stats['total'])
    
    with col2:
        active = stats['active']
        st.metric("Ενεργά Μέλη", active)
    
    with col3:
        mathites = stats['degrees'].get('Μαθητής', 0)
        st.metric("Μαθητές", mathites)
    
    with col4:
        etairoi = stats['degrees'].get('Εταίρος', 0)
        st.metric("Εταίροι", etairoi)
    
    st.markdown("---")
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Κατανομή ανά Βαθμό")
        degree_counts = df['current_degree'].value_counts()
        st.bar_chart(degree_counts)
    
    with col2:
        st.markdown("#### Κατανομή ανά Κατάσταση")
        status_counts = df['member_status'].value_counts()
        st.bar_chart(status_counts)
    
    st.markdown("---")
    
    # Detailed table
    st.markdown("#### Λεπτομερή Στοιχεία")
    
    summary_data = {
        'Κατηγορία': ['Σύνολο', 'Ενεργά', 'Ανενεργά', 'Μαθητές', 'Εταίροι', 'Δάσκαλοι'],
        'Αριθμός': [
            stats['total'],
            stats['active'],
            stats['total'] - stats['active'],
            stats['degrees'].get('Μαθητής', 0),
            stats['degrees'].get('Εταίρος', 0),
            stats['degrees'].get('Δάσκαλος', 0)
        ]
    }
    
    summary_df = pd.DataFrame(summary_data)
    st.dataframe(summary_df, use_container_width=True, hide_index=True)

def show_bulk_edit():
    """Μαζική επεξεργασία μελών"""
    st.markdown('<div class="main-header">✏️ Μαζική Επεξεργασία Μελών</div>', unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["📊 Export/Import Excel", "🔄 Ομαδική Αλλαγή", "📝 Προβολή & Διόρθωση"])
    
    # Tab 1: Export/Import Excel
    with tab1:
        st.subheader("📥 Export σε Excel για Επεξεργασία")
        
        st.info("💡 **Οδηγίες**: Κατέβασε το Excel, επεξεργάσου τα δεδομένα, και ανέβασέ το πίσω!")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📥 Λήψη Excel με Όλα τα Μέλη", type="primary", use_container_width=True):
                df = get_all_members()
                
                # Πρόσθεση επιπλέον στηλών
                conn = get_db_connection()
                detailed_df = pd.read_sql_query("""
                    SELECT 
                        member_id, last_name, first_name, fathers_name,
                        birth_date, birth_place, profession, tax_id, id_number,
                        address, postal_code, city, home_phone, mobile_phone, email,
                        initiation_date, initiation_diploma, current_degree,
                        initiation_lodge, sponsor, member_status, financial_status,
                        last_payment_date, notes
                    FROM members
                    ORDER BY last_name, first_name
                """, conn)
                conn.close()
                
                # Μετονομασία στηλών σε ελληνικά
                detailed_df = detailed_df.rename(columns={
                    'member_id': 'Α/Α',
                    'last_name': 'Επώνυμο',
                    'first_name': 'Όνομα',
                    'fathers_name': 'Πατρώνυμο',
                    'birth_date': 'Ημ/νία Γέννησης',
                    'birth_place': 'Τόπος Γέννησης',
                    'profession': 'Επάγγελμα',
                    'tax_id': 'ΑΦΜ',
                    'id_number': 'Αρ. Ταυτότητας',
                    'address': 'Διεύθυνση',
                    'postal_code': 'ΤΚ',
                    'city': 'Πόλη',
                    'home_phone': 'Τηλ. Οικίας',
                    'mobile_phone': 'Κινητό',
                    'email': 'Email',
                    'initiation_date': 'Ημ/νία Μύησης',
                    'initiation_diploma': 'Αρ. Διπλώματος',
                    'current_degree': 'Βαθμός',
                    'initiation_lodge': 'Στοά Μύησης',
                    'sponsor': 'Εισηγητής',
                    'member_status': 'Κατάσταση',
                    'financial_status': 'Οικον. Τακτοποίηση',
                    'last_payment_date': 'Τελ. Πληρωμή',
                    'notes': 'Παρατηρήσεις'
                })
                
                # Export to Excel
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    detailed_df.to_excel(writer, index=False, sheet_name='Μέλη')
                output.seek(0)
                
                st.download_button(
                    label="⬇️ Κατέβασμα Excel",
                    data=output,
                    file_name=f"Μητρωο_Μελων_{datetime.now().strftime('%Y%m%d')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    type="primary",
                    use_container_width=True
                )
                
                st.success(f"✅ Έτοιμο! {len(detailed_df)} μέλη στο Excel")
        
        with col2:
            st.markdown("### 📤 Import από Excel")
            uploaded_file = st.file_uploader("Ανέβασε το επεξεργασμένο Excel", type=['xlsx', 'xls'])
            
            if uploaded_file is not None:
                try:
                    df_import = pd.read_excel(uploaded_file)
                    
                    st.success(f"✅ Διαβάστηκαν {len(df_import)} εγγραφές")
                    
                    st.dataframe(df_import.head(5), use_container_width=True)
                    
                    if st.button("💾 Αποθήκευση Αλλαγών στη Βάση", type="primary"):
                        # Αντιστροφή μετονομασίας
                        df_import = df_import.rename(columns={
                            'Α/Α': 'member_id',
                            'Επώνυμο': 'last_name',
                            'Όνομα': 'first_name',
                            'Πατρώνυμο': 'fathers_name',
                            'Ημ/νία Γέννησης': 'birth_date',
                            'Τόπος Γέννησης': 'birth_place',
                            'Επάγγελμα': 'profession',
                            'ΑΦΜ': 'tax_id',
                            'Αρ. Ταυτότητας': 'id_number',
                            'Διεύθυνση': 'address',
                            'ΤΚ': 'postal_code',
                            'Πόλη': 'city',
                            'Τηλ. Οικίας': 'home_phone',
                            'Κινητό': 'mobile_phone',
                            'Email': 'email',
                            'Ημ/νία Μύησης': 'initiation_date',
                            'Αρ. Διπλώματος': 'initiation_diploma',
                            'Βαθμός': 'current_degree',
                            'Στοά Μύησης': 'initiation_lodge',
                            'Εισηγητής': 'sponsor',
                            'Κατάσταση': 'member_status',
                            'Οικον. Τακτοποίηση': 'financial_status',
                            'Τελ. Πληρωμή': 'last_payment_date',
                            'Παρατηρήσεις': 'notes'
                        })
                        
                        # Update βάσης
                        updated = 0
                        for _, row in df_import.iterrows():
                            member_id = row['member_id']
                            update_data = row.drop('member_id').to_dict()
                            
                            # Καθαρισμός NaN values
                            update_data = {k: (None if pd.isna(v) else v) for k, v in update_data.items()}
                            
                            update_member(member_id, update_data)
                            updated += 1
                        
                        st.success(f"✅ Ενημερώθηκαν {updated} μέλη επιτυχώς!")
                        st.rerun()
                        
                except Exception as e:
                    st.error(f"❌ Σφάλμα: {e}")
    
    # Tab 2: Ομαδική Αλλαγή
    with tab2:
        st.subheader("🔄 Ομαδική Αλλαγή Πεδίων")
        
        df = get_all_members()
        
        st.markdown("### Επιλογή Μελών")
        
        col1, col2 = st.columns(2)
        
        with col1:
            filter_status_bulk = st.selectbox(
                "Φίλτρο Κατάστασης",
                ["Όλα", "Ενεργό", "Ανενεργό"],
                key="bulk_status_filter"
            )
        
        with col2:
            filter_degree_bulk = st.selectbox(
                "Φίλτρο Βαθμού",
                ["Όλοι", "Μαθητής", "Εταίρος", "Δάσκαλος"],
                key="bulk_degree_filter"
            )
        
        # Εφαρμογή φίλτρων
        filtered_df = df.copy()
        if filter_status_bulk != "Όλα":
            filtered_df = filtered_df[filtered_df['member_status'] == filter_status_bulk]
        if filter_degree_bulk != "Όλοι":
            filtered_df = filtered_df[filtered_df['current_degree'] == filter_degree_bulk]
        
        st.info(f"📊 Επιλεγμένα: **{len(filtered_df)}** μέλη")
        
        st.markdown("---")
        st.markdown("### Πεδίο προς Αλλαγή")
        
        field_to_update = st.selectbox(
            "Επέλεξε Πεδίο",
            [
                "Βαθμός",
                "Κατάσταση Μέλους",
                "Οικονομική Τακτοποίηση",
                "Στοά Μύησης"
            ]
        )
        
        new_value = None
        
        if field_to_update == "Βαθμός":
            new_value = st.selectbox("Νέα Τιμή", ["Μαθητής", "Εταίρος", "Δάσκαλος"])
            field_name = 'current_degree'
        elif field_to_update == "Κατάσταση Μέλους":
            new_value = st.selectbox("Νέα Τιμή", ["Ενεργό", "Ανενεργό", "Αποχωρήσαν", "Διαγραφέν"])
            field_name = 'member_status'
        elif field_to_update == "Οικονομική Τακτοποίηση":
            new_value = st.selectbox("Νέα Τιμή", ["Ναι", "Όχι"])
            field_name = 'financial_status'
        elif field_to_update == "Στοά Μύησης":
            new_value = st.text_input("Νέα Τιμή", value="ΑΚΡΟΠΟΛΙΣ")
            field_name = 'initiation_lodge'
        
        if st.button("🔄 Εφαρμογή Αλλαγής σε Όλα τα Επιλεγμένα Μέλη", type="primary"):
            updated_count = 0
            for _, row in filtered_df.iterrows():
                update_member(row['member_id'], {field_name: new_value})
                updated_count += 1
            
            st.success(f"✅ Ενημερώθηκαν {updated_count} μέλη!")
            st.balloons()
            st.rerun()
    
    # Tab 3: Προβολή & Διόρθωση
    with tab3:
        st.subheader("📝 Γρήγορη Διόρθωση Στοιχείων")
        
        df = get_all_members()
        
        st.markdown("### Πίνακας με Δυνατότητα Επεξεργασίας")
        
        # Editable dataframe
        st.info("💡 Κάνε κλικ σε οποιοδήποτε κελί για επεξεργασία!")
        
        edited_df = st.data_editor(
            df[['member_id', 'last_name', 'first_name', 'mobile_phone', 'email', 'current_degree', 'member_status']],
            column_config={
                "member_id": st.column_config.NumberColumn("Α/Α", disabled=True),
                "last_name": st.column_config.TextColumn("Επώνυμο", required=True),
                "first_name": st.column_config.TextColumn("Όνομα", required=True),
                "mobile_phone": st.column_config.TextColumn("Κινητό"),
                "email": st.column_config.TextColumn("Email"),
                "current_degree": st.column_config.SelectboxColumn(
                    "Βαθμός",
                    options=["Μαθητής", "Εταίρος", "Δάσκαλος"]
                ),
                "member_status": st.column_config.SelectboxColumn(
                    "Κατάσταση",
                    options=["Ενεργό", "Ανενεργό", "Αποχωρήσαν", "Διαγραφέν"]
                )
            },
            hide_index=True,
            use_container_width=True
        )
        
        if st.button("💾 Αποθήκευση Όλων των Αλλαγών", type="primary"):
            # Σύγκριση και ενημέρωση
            changes_made = 0
            for idx in range(len(df)):
                original_row = df.iloc[idx]
                edited_row = edited_df.iloc[idx]
                
                # Έλεγχος αν έγιναν αλλαγές
                if not original_row.equals(edited_row):
                    member_id = edited_row['member_id']
                    update_data = {
                        'last_name': edited_row['last_name'],
                        'first_name': edited_row['first_name'],
                        'mobile_phone': edited_row['mobile_phone'],
                        'email': edited_row['email'],
                        'current_degree': edited_row['current_degree'],
                        'member_status': edited_row['member_status']
                    }
                    update_member(member_id, update_data)
                    changes_made += 1
            
            if changes_made > 0:
                st.success(f"✅ Ενημερώθηκαν {changes_made} μέλη!")
                st.rerun()
            else:
                st.info("ℹ️ Δεν εντοπίστηκαν αλλαγές")

# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    main()

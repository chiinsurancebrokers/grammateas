import streamlit as st
import sys
sys.path.append('..')
from modules.database import get_database

st.set_page_config(page_title="Επεξεργασία Μέλους", page_icon="👤", layout="wide")

st.markdown("""
<style>
.main-header {font-size: 2.5rem; font-weight: bold; color: #1f4788; padding: 1rem; background: linear-gradient(90deg, #f0f2f6 0%, #ffffff 100%); border-radius: 10px; margin-bottom: 2rem;}
</style>
""", unsafe_allow_html=True)

db = get_database()

st.markdown('<div class="main-header">👤 Επεξεργασία Μέλους</div>', unsafe_allow_html=True)

# Select member
df = db.get_all_members()
member_options = {f"{row['member_id']} - {row['last_name']} {row['first_name']}": row['member_id'] 
                  for _, row in df.iterrows()}

selected = st.selectbox("Επιλογή Μέλους", options=list(member_options.keys()))

if selected:
    member_id = member_options[selected]
    member = db.get_member_by_id(member_id)
    
    if member:
        st.markdown("---")
        
        with st.form("edit_member_form"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.subheader("Προσωπικά Στοιχεία")
                last_name = st.text_input("Επώνυμο", value=member.get('last_name', ''))
                first_name = st.text_input("Όνομα", value=member.get('first_name', ''))
                fathers_name = st.text_input("Πατρώνυμο", value=member.get('fathers_name', ''))
                birth_date = st.date_input("Ημ/νία Γέννησης", value=None)
                birth_place = st.text_input("Τόπος Γέννησης", value=member.get('birth_place', ''))
                profession = st.text_input("Επάγγελμα", value=member.get('profession', ''))
            
            with col2:
                st.subheader("Επικοινωνία")
                address = st.text_input("Διεύθυνση", value=member.get('address', ''))
                city = st.text_input("Πόλη", value=member.get('city', ''))
                postal_code = st.text_input("ΤΚ", value=member.get('postal_code', ''))
                mobile_phone = st.text_input("Κινητό", value=member.get('mobile_phone', ''))
                home_phone = st.text_input("Τηλ. Οικίας", value=member.get('home_phone', ''))
                email = st.text_input("Email", value=member.get('email', ''))
            
            with col3:
                st.subheader("Μασονικά Στοιχεία")
                current_degree = st.selectbox("Βαθμός", ["Μαθητής", "Εταίρος", "Δάσκαλος"], 
                                             index=["Μαθητής", "Εταίρος", "Δάσκαλος"].index(member.get('current_degree', 'Μαθητής')))
                member_status = st.selectbox("Κατάσταση", ["Ενεργό", "Ανενεργό", "Αποχωρήσαν", "Διαγραφέν"],
                                            index=["Ενεργό", "Ανενεργό", "Αποχωρήσαν", "Διαγραφέν"].index(member.get('member_status', 'Ενεργό')))
                financial_status = st.selectbox("Οικονομική Τακτοποίηση", ["Ναι", "Όχι"],
                                               index=["Ναι", "Όχι"].index(member.get('financial_status', 'Ναι')))
                sponsor = st.text_input("Εισηγητής", value=member.get('sponsor', ''))
                initiation_lodge = st.text_input("Στοά Μύησης", value=member.get('initiation_lodge', ''))
            
            submitted = st.form_submit_button("💾 Αποθήκευση Αλλαγών", type="primary", use_container_width=True)
            
            if submitted:
                update_data = {
                    'last_name': last_name, 'first_name': first_name, 'fathers_name': fathers_name,
                    'birth_place': birth_place, 'profession': profession, 'address': address,
                    'city': city, 'postal_code': postal_code, 'mobile_phone': mobile_phone,
                    'home_phone': home_phone, 'email': email, 'current_degree': current_degree,
                    'member_status': member_status, 'financial_status': financial_status,
                    'sponsor': sponsor, 'initiation_lodge': initiation_lodge
                }
                db.update_member(member_id, update_data)
                st.success("✅ Το μέλος ενημερώθηκε επιτυχώς!")
                st.rerun()

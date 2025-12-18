import streamlit as st
from pathlib import Path
import sys

# Path-safe import για modules/
sys.path.append(str(Path(__file__).resolve().parents[1]))

from modules.database import get_database
import pandas as pd
import io
from datetime import datetime

st.set_page_config(
    page_title="Μαζική Επεξεργασία",
    page_icon="✏️",
    layout="wide"
)


st.markdown("""
<style>
.main-header {font-size: 2.5rem; font-weight: bold; color: #1f4788; padding: 1rem; background: linear-gradient(90deg, #f0f2f6 0%, #ffffff 100%); border-radius: 10px; margin-bottom: 2rem;}
</style>
""", unsafe_allow_html=True)

db = get_database()

st.markdown('<div class="main-header">✏️ Μαζική Επεξεργασία Μελών</div>', unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["📊 Export/Import Excel", "🔄 Ομαδική Αλλαγή", "📝 Προβολή & Διόρθωση"])

# Tab 1: Excel
with tab1:
    st.subheader("📥 Export σε Excel για Επεξεργασία")
    st.info("💡 Κατέβασε το Excel, επεξεργάσου, και ανέβασέ το πίσω!")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📥 Λήψη Excel με Όλα τα Μέλη", type="primary", use_container_width=True):
            conn = db.get_connection()
            detailed_df = pd.read_sql_query("""
                SELECT member_id, last_name, first_name, fathers_name, birth_date, birth_place, 
                       profession, tax_id, id_number, address, postal_code, city, home_phone, 
                       mobile_phone, email, initiation_date, initiation_diploma, current_degree,
                       initiation_lodge, sponsor, member_status, financial_status, last_payment_date, notes
                FROM members ORDER BY last_name, first_name
            """, conn)
            conn.close()
            
            detailed_df = detailed_df.rename(columns={
                'member_id': 'Α/Α', 'last_name': 'Επώνυμο', 'first_name': 'Όνομα', 
                'fathers_name': 'Πατρώνυμο', 'birth_date': 'Ημ/νία Γέννησης', 
                'birth_place': 'Τόπος Γέννησης', 'profession': 'Επάγγελμα', 'tax_id': 'ΑΦΜ',
                'id_number': 'Αρ. Ταυτότητας', 'address': 'Διεύθυνση', 'postal_code': 'ΤΚ',
                'city': 'Πόλη', 'home_phone': 'Τηλ. Οικίας', 'mobile_phone': 'Κινητό',
                'email': 'Email', 'initiation_date': 'Ημ/νία Μύησης', 
                'initiation_diploma': 'Αρ. Διπλώματος', 'current_degree': 'Βαθμός',
                'initiation_lodge': 'Στοά Μύησης', 'sponsor': 'Εισηγητής',
                'member_status': 'Κατάσταση', 'financial_status': 'Οικον. Τακτοποίηση',
                'last_payment_date': 'Τελ. Πληρωμή', 'notes': 'Παρατηρήσεις'
            })
            
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
                    df_import = df_import.rename(columns={
                        'Α/Α': 'member_id', 'Επώνυμο': 'last_name', 'Όνομα': 'first_name',
                        'Πατρώνυμο': 'fathers_name', 'Ημ/νία Γέννησης': 'birth_date',
                        'Τόπος Γέννησης': 'birth_place', 'Επάγγελμα': 'profession',
                        'ΑΦΜ': 'tax_id', 'Αρ. Ταυτότητας': 'id_number', 'Διεύθυνση': 'address',
                        'ΤΚ': 'postal_code', 'Πόλη': 'city', 'Τηλ. Οικίας': 'home_phone',
                        'Κινητό': 'mobile_phone', 'Email': 'email', 'Ημ/νία Μύησης': 'initiation_date',
                        'Αρ. Διπλώματος': 'initiation_diploma', 'Βαθμός': 'current_degree',
                        'Στοά Μύησης': 'initiation_lodge', 'Εισηγητής': 'sponsor',
                        'Κατάσταση': 'member_status', 'Οικον. Τακτοποίηση': 'financial_status',
                        'Τελ. Πληρωμή': 'last_payment_date', 'Παρατηρήσεις': 'notes'
                    })
                    
                    updated = 0
                    for _, row in df_import.iterrows():
                        member_id = row['member_id']
                        update_data = row.drop('member_id').to_dict()
                        update_data = {k: (None if pd.isna(v) else v) for k, v in update_data.items()}
                        db.update_member(member_id, update_data)
                        updated += 1
                    
                    st.success(f"✅ Ενημερώθηκαν {updated} μέλη επιτυχώς!")
                    st.rerun()
            except Exception as e:
                st.error(f"❌ Σφάλμα: {e}")

# Tab 2: Bulk change
with tab2:
    st.subheader("🔄 Ομαδική Αλλαγή Πεδίων")
    
    df = db.get_all_members()
    
    col1, col2 = st.columns(2)
    with col1:
        filter_status_bulk = st.selectbox("Φίλτρο Κατάστασης", ["Όλα", "Ενεργό", "Ανενεργό"], key="bulk_status_filter")
    with col2:
        filter_degree_bulk = st.selectbox("Φίλτρο Βαθμού", ["Όλοι", "Μαθητής", "Εταίρος", "Δάσκαλος"], key="bulk_degree_filter")
    
    filtered_df = df.copy()
    if filter_status_bulk != "Όλα":
        filtered_df = filtered_df[filtered_df['member_status'] == filter_status_bulk]
    if filter_degree_bulk != "Όλοι":
        filtered_df = filtered_df[filtered_df['current_degree'] == filter_degree_bulk]
    
    st.info(f"📊 Επιλεγμένα: **{len(filtered_df)}** μέλη")
    
    st.markdown("---")
    field_to_update = st.selectbox("Πεδίο προς Αλλαγή", ["Βαθμός", "Κατάσταση Μέλους", "Οικονομική Τακτοποίηση", "Στοά Μύησης"])
    
    if field_to_update == "Βαθμός":
        new_value = st.selectbox("Νέα Τιμή", ["Μαθητής", "Εταίρος", "Δάσκαλος"])
        field_name = 'current_degree'
    elif field_to_update == "Κατάσταση Μέλους":
        new_value = st.selectbox("Νέα Τιμή", ["Ενεργό", "Ανενεργό", "Αποχωρήσαν", "Διαγραφέν"])
        field_name = 'member_status'
    elif field_to_update == "Οικονομική Τακτοποίηση":
        new_value = st.selectbox("Νέα Τιμή", ["Ναι", "Όχι"])
        field_name = 'financial_status'
    else:
        new_value = st.text_input("Νέα Τιμή", value="ΑΚΡΟΠΟΛΙΣ")
        field_name = 'initiation_lodge'
    
    if st.button("🔄 Εφαρμογή Αλλαγής σε Όλα τα Επιλεγμένα Μέλη", type="primary"):
        updated_count = 0
        for _, row in filtered_df.iterrows():
            db.update_member(row['member_id'], {field_name: new_value})
            updated_count += 1
        st.success(f"✅ Ενημερώθηκαν {updated_count} μέλη!")
        st.balloons()
        st.rerun()

# Tab 3: In-table editing
with tab3:
    st.subheader("📝 Γρήγορη Διόρθωση Στοιχείων")
    st.info("💡 Κάνε κλικ σε οποιοδήποτε κελί για επεξεργασία!")
    
    df = db.get_all_members()
    
    edited_df = st.data_editor(
        df[['member_id', 'last_name', 'first_name', 'mobile_phone', 'email', 'current_degree', 'member_status']],
        column_config={
            "member_id": st.column_config.NumberColumn("Α/Α", disabled=True),
            "last_name": st.column_config.TextColumn("Επώνυμο", required=True),
            "first_name": st.column_config.TextColumn("Όνομα", required=True),
            "mobile_phone": st.column_config.TextColumn("Κινητό"),
            "email": st.column_config.TextColumn("Email"),
            "current_degree": st.column_config.SelectboxColumn("Βαθμός", options=["Μαθητής", "Εταίρος", "Δάσκαλος"]),
            "member_status": st.column_config.SelectboxColumn("Κατάσταση", options=["Ενεργό", "Ανενεργό", "Αποχωρήσαν", "Διαγραφέν"])
        },
        hide_index=True,
        use_container_width=True
    )
    
    if st.button("💾 Αποθήκευση Όλων των Αλλαγών", type="primary"):
        changes_made = 0
        for idx in range(len(df)):
            original_row = df.iloc[idx]
            edited_row = edited_df.iloc[idx]
            
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
                db.update_member(member_id, update_data)
                changes_made += 1
        
        if changes_made > 0:
            st.success(f"✅ Ενημερώθηκαν {changes_made} μέλη!")
            st.rerun()
        else:
            st.info("ℹ️ Δεν εντοπίστηκαν αλλαγές")

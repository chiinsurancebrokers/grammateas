import streamlit as st
import sys
sys.path.append('..')
from modules.database import get_database
from modules.pdf_generator import create_member_card_pdf
import zipfile
from datetime import datetime
import io

st.set_page_config(page_title="Καρτέλες PDF", page_icon="📄", layout="wide")

st.markdown("""
<style>
.main-header {font-size: 2.5rem; font-weight: bold; color: #1f4788; padding: 1rem; background: linear-gradient(90deg, #f0f2f6 0%, #ffffff 100%); border-radius: 10px; margin-bottom: 2rem;}
</style>
""", unsafe_allow_html=True)

db = get_database()

st.markdown('<div class="main-header">📄 Καρτέλες PDF</div>', unsafe_allow_html=True)

tab1, tab2 = st.tabs(["📄 Μεμονωμένη Καρτέλα", "📦 Μαζική Δημιουργία"])

# Tab 1: Single card
with tab1:
    st.subheader("Δημιουργία Καρτέλας για Ένα Μέλος")
    
    df = db.get_all_members()
    member_options = {f"{row['member_id']} - {row['last_name']} {row['first_name']}": row['member_id'] 
                      for _, row in df.iterrows()}
    
    selected = st.selectbox("Επιλογή Μέλους", options=list(member_options.keys()))
    
    if st.button("📄 Δημιουργία Καρτέλας", type="primary"):
        member_id = member_options[selected]
        
        with st.spinner("Δημιουργία PDF..."):
            pdf_buffer = create_member_card_pdf(member_id, None)
            
            if pdf_buffer:
                member = db.get_member_by_id(member_id)
                filename = f"Kartela_{member['last_name']}_{member['first_name']}.pdf"
                
                st.success("✅ Η καρτέλα δημιουργήθηκε επιτυχώς!")
                
                st.download_button(
                    label="⬇️ Λήψη Καρτέλας PDF",
                    data=pdf_buffer.getvalue(),
                    file_name=filename,
                    mime="application/pdf",
                    type="primary"
                )
            else:
                st.error("❌ Σφάλμα κατά τη δημιουργία της καρτέλας")

# Tab 2: Bulk cards
with tab2:
    st.subheader("Μαζική Δημιουργία Καρτελών")
    
    st.info("💡 Δημιουργία καρτελών για όλα τα μέλη σε ένα ZIP αρχείο")
    
    col1, col2 = st.columns(2)
    
    with col1:
        filter_status = st.selectbox("Φίλτρο Κατάστασης", ["Όλα", "Ενεργό", "Ανενεργό"], key="pdf_status")
    
    with col2:
        filter_degree = st.selectbox("Φίλτρο Βαθμού", ["Όλοι", "Μαθητής", "Εταίρος", "Δάσκαλος"], key="pdf_degree")
    
    df_filter = df.copy()
    if filter_status != "Όλα":
        df_filter = df_filter[df_filter['member_status'] == filter_status]
    if filter_degree != "Όλοι":
        df_filter = df_filter[df_filter['current_degree'] == filter_degree]
    
    st.markdown(f"**Θα δημιουργηθούν:** {len(df_filter)} καρτέλες")
    
    if st.button("📦 Δημιουργία Όλων των Καρτελών", type="primary"):
        with st.spinner(f"Δημιουργία {len(df_filter)} καρτελών..."):
            zip_buffer = io.BytesIO()
            
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
                progress_bar = st.progress(0)
                
                for idx, (_, row) in enumerate(df_filter.iterrows()):
                    pdf_buffer = create_member_card_pdf(row['member_id'], None)
                    if pdf_buffer:
                        filename = f"Kartela_{row['last_name']}_{row['first_name']}.pdf"
                        zipf.writestr(filename, pdf_buffer.getvalue())
                    
                    progress_bar.progress((idx + 1) / len(df_filter))
            
            zip_buffer.seek(0)
            
            st.success(f"✅ Δημιουργήθηκαν {len(df_filter)} καρτέλες!")
            
            st.download_button(
                label="⬇️ Λήψη ZIP με Όλες τις Καρτέλες",
                data=zip_buffer.getvalue(),
                file_name=f"Karteles_Melon_{datetime.now().strftime('%Y%m%d_%H%M')}.zip",
                mime="application/zip",
                type="primary"
            )

st.markdown("---")
st.info("""
**Σημειώσεις:**
- Οι καρτέλες δημιουργούνται με πλήρη ελληνική υποστήριξη (DejaVu Sans font)
- Περιλαμβάνουν όλα τα στοιχεία του μέλους
- Κατάλληλες για εκτύπωση ή ψηφιακή αρχειοθέτηση
""")

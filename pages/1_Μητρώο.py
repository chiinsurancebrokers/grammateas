"""
Σελίδα Μητρώου Μελών
Προβολή, αναζήτηση και φιλτράρισμα μελών
"""

from pathlib import Path
import sys
sys.path.append(str(Path(__file__).resolve().parents[1]))


from modules.database import get_database
from modules.config import get_config

st.set_page_config(page_title="Μητρώο Μελών", page_icon="📋", layout="wide")

# CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f4788;
        padding: 1rem;
        background: linear-gradient(90deg, #f0f2f6 0%, #ffffff 100%);
        border-radius: 10px;
        margin-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)

config = get_config()
db = get_database()

st.markdown('<div class="main-header">📋 Μητρώο Μελών</div>', unsafe_allow_html=True)

# Filters
col1, col2, col3, col4 = st.columns(4)

with col1:
    search_term = st.text_input("🔍 Αναζήτηση", placeholder="Επώνυμο, Όνομα, Τηλέφωνο...")

with col2:
    status_filter = st.selectbox("Κατάσταση", ["Όλες", "Ενεργό", "Ανενεργό", "Αποχωρήσαν"])

with col3:
    degree_filter = st.selectbox("Βαθμός", ["Όλοι", "Μαθητής", "Εταίρος", "Δάσκαλος"])

with col4:
    financial_filter = st.selectbox("Οικονομική Κατάσταση", ["Όλες", "Ναι", "Όχι"])

# Get data
if search_term:
    df = db.search_members(search_term)
else:
    df = db.get_all_members()

# Apply filters
if status_filter != "Όλες":
    df = df[df['member_status'] == status_filter]

if degree_filter != "Όλοι":
    df = df[df['current_degree'] == degree_filter]

if financial_filter != "Όλες":
    df = df[df['financial_status'] == financial_filter]

# Display
st.markdown(f"**Αποτελέσματα:** {len(df)} μέλη")

if len(df) > 0:
    # Rename columns for display
    display_df = df.rename(columns={
        'member_id': 'Α/Α',
        'last_name': 'Επώνυμο',
        'first_name': 'Όνομα',
        'fathers_name': 'Πατρώνυμο',
        'birth_date': 'Ημ/νία Γέννησης',
        'mobile_phone': 'Κινητό',
        'email': 'Email',
        'initiation_date': 'Ημ/νία Μύησης',
        'current_degree': 'Βαθμός',
        'member_status': 'Κατάσταση',
        'financial_status': 'Οικον. Τακτοποίηση'
    })
    
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )
    
    # Export options
    st.markdown("---")
    col1, col2 = st.columns([3, 1])
    
    with col2:
        csv = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="📥 Λήψη CSV",
            data=csv,
            file_name="mhtrwo_melon.csv",
            mime="text/csv",
            use_container_width=True
        )
else:
    st.info("📭 Δεν βρέθηκαν μέλη με αυτά τα κριτήρια")

# Quick stats
st.markdown("---")
st.subheader("📊 Γρήγορα Στατιστικά")

col1, col2, col3, col4 = st.columns(4)

stats = db.get_member_statistics()

with col1:
    st.metric("Σύνολο", stats['total'])

with col2:
    st.metric("Ενεργά", stats['active'])

with col3:
    degrees = stats.get('by_degree', {})
    st.metric("Δάσκαλοι", degrees.get('Δάσκαλος', 0))

with col4:
    st.metric("Μαθητές", degrees.get('Μαθητής', 0))

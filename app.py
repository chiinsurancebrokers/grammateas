import streamlit as st

from modules.database import get_database
from modules.config import get_config


# ======================
# PAGE CONFIG
# ======================
st.set_page_config(
    page_title="Στοά ΑΚΡΟΠΟΛΙΣ",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ======================
# INIT CORE OBJECTS
# ======================
config = get_config()
db = get_database()
stats = db.get_member_statistics()


# ======================
# SIDEBAR (ONLY INFO – NO NAVIGATION)
# ======================
with st.sidebar:
    st.markdown(
        f"""
        <div style="text-align:center; padding:1rem;">
            <h1 style="color:#1f4788;">🏛️</h1>
            <h2 style="margin:0;">{config.app_name}</h2>
            <p style="color:#666; font-size:0.9rem;">Σύστημα Διαχείρισης Μελών</p>
            <p style="color:#999; font-size:0.75rem;">v{config.app_version}</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("---")
    st.subheader("📊 Κατάσταση Συστήματος")

    st.metric("Σύνολο Μελών", stats["total"])
    st.metric("Ενεργά Μέλη", stats["active"])

    st.markdown("---")
    st.info("⬅️ Χρησιμοποίησε το μενού αριστερά για πλοήγηση")


# ======================
# MAIN DASHBOARD
# ======================
st.markdown(
    """
    <div style="
        font-size:2.3rem;
        font-weight:bold;
        color:#1f4788;
        text-align:center;
        padding:1rem;
        background:linear-gradient(90deg,#f0f2f6 0%,#ffffff 100%);
        border-radius:10px;
        margin-bottom:2rem;">
        🏛️ Σύστημα Διαχείρισης Στοάς ΑΚΡΟΠΟΛΙΣ
    </div>
    """,
    unsafe_allow_html=True
)


# ======================
# INFO CARDS
# ======================
c1, c2, c3 = st.columns(3)

with c1:
    st.metric("📋 Μέλη", stats["total"])

with c2:
    st.metric("🟢 Ενεργά", stats["active"])

with c3:
    inactive = stats["total"] - stats["active"]
    st.metric("🔴 Ανενεργά", inactive)


st.markdown("---")


# ======================
# SYSTEM OVERVIEW
# ======================
st.subheader("📊 Σύνοψη")

left, right = st.columns(2)

with left:
    st.markdown(
        """
        ### Διαθέσιμες Ενότητες
        - 📋 Μητρώο Μελών  
        - ✏️ Επεξεργασία & Μαζική Ενημέρωση  
        - 📄 Καρτέλες PDF  
        - 📈 Στατιστικά & Αναφορές  
        - 🗂️ Εργασίες & Υπενθυμίσεις  
        """
    )

with right:
    total = stats["total"]
    active = stats["active"]
    pct = (active / total * 100) if total else 0

    st.metric("Ποσοστό Ενεργών", f"{pct:.0f}%")


# ======================
# FOOTER
# ======================
st.markdown("---")
st.markdown(
    """
    <div style="text-align:center; color:#666; padding:2rem;">
        <p><strong>🏛️ Στοά ΑΚΡΟΠΟΛΙΣ Υπ’ Αριθμ. 84</strong></p>
        <p style="font-size:0.85rem;">Σύστημα Διαχείρισης Μελών v2.0</p>
    </div>
    """,
    unsafe_allow_html=True
)

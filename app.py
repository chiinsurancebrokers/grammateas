import streamlit as st

from modules.database import get_database
from modules.config import get_config


# =======================
# PAGE CONFIG
# =======================
st.set_page_config(
    page_title="Στοά ΑΚΡΟΠΟΛΙΣ",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =======================
# CUSTOM CSS
# =======================
st.markdown(
    """
    <style>
        .main-header {
            font-size: 2.5rem;
            font-weight: bold;
            color: #1f4788;
            text-align: center;
            padding: 1rem;
            background: linear-gradient(90deg, #f0f2f6 0%, #ffffff 100%);
            border-radius: 10px;
            margin-bottom: 2rem;
        }

        .stat-card {
            background-color: #f8f9fa;
            padding: 1.5rem;
            border-radius: 10px;
            border-left: 4px solid #1f4788;
            margin: 1rem 0;
        }

        .stat-number {
            font-size: 2rem;
            font-weight: bold;
            color: #1f4788;
        }

        .stat-label {
            font-size: 1rem;
            color: #666;
            margin-top: 0.5rem;
        }

        .feature-badge {
            display: inline-block;
            padding: 0.3rem 0.8rem;
            border-radius: 15px;
            font-size: 0.85rem;
            font-weight: 500;
            margin: 0.2rem;
        }

        .feature-enabled {
            background-color: #d4edda;
            color: #155724;
        }

        .feature-disabled {
            background-color: #f8d7da;
            color: #721c24;
        }

        .stButton > button {
            width: 100%;
        }
    </style>
    """,
    unsafe_allow_html=True
)


# =======================
# INITIALIZE CORE OBJECTS
# =======================
config = get_config()
db = get_database()
stats = db.get_member_statistics()


# =======================
# SIDEBAR
# =======================
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

    features = {
        "Βασικές Λειτουργίες": True,
        "Εργασίες & Υπενθυμίσεις": True,
        "Email Notifications": config.is_feature_enabled("email"),
        "AI Assistant": config.is_feature_enabled("ai"),
    }

    for label, enabled in features.items():
        css_class = "feature-enabled" if enabled else "feature-disabled"
        icon = "✅" if enabled else "⚪"
        st.markdown(
            f"<div class='feature-badge {css_class}'>{icon} {label}</div>",
            unsafe_allow_html=True
        )

    st.markdown("---")
    st.metric("Σύνολο Μελών", stats["total"])
    st.metric("Ενεργά Μέλη", stats["active"])

    st.markdown("---")
    with st.expander("ℹ️ Βοήθεια"):
        st.markdown(
            """
            **Πλοήγηση**
            - Χρησιμοποίησε το μενού αριστερά
            - Κάθε σελίδα έχει συγκεκριμένη λειτουργία

            **Υποστήριξη**
            - Email: xiatropoulos@gmail.com
            """
        )


# =======================
# MAIN CONTENT
# =======================
st.markdown(
    '<div class="main-header">🏛️ Σύστημα Διαχείρισης Στοάς ΑΚΡΟΠΟΛΙΣ</div>',
    unsafe_allow_html=True
)

# Info cards
cols = st.columns(3)
cards = [
    ("📋", "Πλήρες Μητρώο Μελών"),
    ("✏️", "Μαζική Επεξεργασία"),
    ("📄", "Δημιουργία Καρτελών"),
]

for col, (icon, label) in zip(cols, cards):
    with col:
        st.markdown(
            f"""
            <div class="stat-card">
                <div class="stat-number">{icon}</div>
                <div class="stat-label">{label}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

st.markdown("---")


# =======================
# SYSTEM OVERVIEW
# =======================
st.subheader("📊 Σύνοψη Συστήματος")

left, right = st.columns(2)

with left:
    st.markdown(
        """
        ### 🎯 Διαθέσιμες Λειτουργίες
        - Μητρώο Μελών
        - Επεξεργασία & Μαζική Ενημέρωση
        - PDF Καρτέλες
        - Στατιστικά & Αναφορές
        - Εργασίες & Υπενθυμίσεις
        """
    )

with right:
    total = stats["total"]
    active = stats["active"]
    pct = (active / total * 100) if total else 0

    st.metric("Συνολικά Μέλη", total)
    st.metric("Ενεργά Μέλη", active, delta=f"{pct:.0f}%")

    st.markdown("#### Κατανομή Βαθμών")
    for degree, count in stats.get("by_degree", {}).items():
        st.progress(count / total if total else 0, text=f"{degree}: {count}")


st.markdown("---")


# =======================
# QUICK ACTIONS
# =======================
st.subheader("⚡ Γρήγορες Ενέργειες")

c1, c2, c3, c4 = st.columns(4)

with c1:
    if st.button("📋 Προβολή Μητρώου"):
        st.switch_page("pages/1_Μητρώο.py")

with c2:
    if st.button("✏️ Μαζική Επεξεργασία"):
        st.switch_page("pages/3_Μαζική_Επεξεργασία.py")

with c3:
    if st.button("📄 Δημιουργία Καρτελών"):
        st.switch_page("pages/4_Καρτέλες.py")

with c4:
    if st.button("📊 Στατιστικά"):
        st.switch_page("pages/5_Στατιστικά.py")


# =======================
# FOOTER
# =======================
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

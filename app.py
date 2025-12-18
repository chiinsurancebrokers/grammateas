import os
from datetime import datetime

import streamlit as st

from modules.database import get_database
from modules.config import get_config

# Optional AI (Anthropic). App works without it.
try:
    import anthropic  # type: ignore
except Exception:
    anthropic = None


# ======================
# PAGE CONFIG
# ======================
st.set_page_config(
    page_title="Στοά ΑΚΡΟΠΟΛΙΣ",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ======================
# CUSTOM CSS
# ======================
st.markdown(
    """
    <style>
        .main-header {
            font-size: 2.3rem;
            font-weight: 800;
            color: #1f4788;
            text-align: center;
            padding: 1rem;
            background: linear-gradient(90deg, #f0f2f6 0%, #ffffff 100%);
            border-radius: 12px;
            margin-bottom: 1.5rem;
        }
        .card {
            background: #ffffff;
            border: 1px solid #e9ecef;
            border-radius: 12px;
            padding: 1rem 1.2rem;
            margin: 0.5rem 0;
            box-shadow: 0 2px 10px rgba(0,0,0,0.03);
        }
        .muted { color: #6c757d; }
        .badge {
            display:inline-block; padding: 0.25rem 0.6rem; border-radius: 999px;
            font-size: 0.85rem; margin-right: 0.4rem; border: 1px solid #e9ecef;
        }
        .ok { background:#d4edda; color:#155724; border-color:#c3e6cb; }
        .off { background:#f8d7da; color:#721c24; border-color:#f5c6cb; }
        .stButton>button { width: 100%; }
        hr { margin: 1.25rem 0; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ======================
# INIT CORE OBJECTS
# ======================
config = get_config()
db = get_database()
stats = db.get_member_statistics()

# Pages (ASCII filenames) — update if you changed names
PAGES = {
    "📋 Μητρώο": "pages/1_registry.py",
    "✏️ Επεξεργασία": "pages/2_edit.py",
    "🧩 Μαζική Επεξεργασία": "pages/3_bulk_edit.py",
    "📄 Καρτέλες PDF": "pages/4_cards.py",
    "📈 Στατιστικά": "pages/5_stats.py",
    "🗂️ Εργασίες": "pages/6_tasks.py",
}


# ======================
# AI HELPERS
# ======================
def _get_anthropic_api_key() -> str | None:
    # Prefer Streamlit secrets, then env var
    key = None
    try:
        key = st.secrets.get("ANTHROPIC_API_KEY", None)
    except Exception:
        key = None
    if not key:
        key = os.getenv("ANTHROPIC_API_KEY")
    return key


def ai_available() -> bool:
    return anthropic is not None and bool(_get_anthropic_api_key())


def call_ai(prompt: str) -> str:
    """
    Minimal Anthropic call. Safe fallback if not configured.
    """
    if anthropic is None:
        return "Το AI module δεν είναι διαθέσιμο (λείπει το package 'anthropic')."

    api_key = _get_anthropic_api_key()
    if not api_key:
        return "Δεν έχει οριστεί ANTHROPIC_API_KEY (Streamlit secrets ή environment)."

    client = anthropic.Anthropic(api_key=api_key)

    system = (
        "Είσαι βοηθός για τον Γραμματέα μιας στοάς. "
        "Απαντάς στα Ελληνικά, πρακτικά και σύντομα. "
        "Όταν ζητούνται πρότυπα κειμένων, δίνεις έτοιμο κείμενο."
    )

    # Keep it robust across Anthropic SDK versions
    try:
        msg = client.messages.create(
            model="claude-3-5-sonnet-latest",
            max_tokens=700,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
        # SDK returns content as list of blocks
        if isinstance(msg.content, list) and msg.content:
            # Prefer first text block
            for block in msg.content:
                if getattr(block, "type", None) == "text":
                    return block.text
            return str(msg.content[0])
        return str(msg)
    except Exception as e:
        return f"Σφάλμα κλήσης AI: {e}"


# ======================
# SIDEBAR
# ======================
with st.sidebar:
    st.markdown(
        f"""
        <div style="text-align:center; padding: 0.75rem 0.75rem 0.25rem 0.75rem;">
            <div style="font-size:2rem;">🏛️</div>
            <div style="font-weight:800; color:#1f4788; font-size:1.1rem;">{config.app_name}</div>
            <div class="muted" style="font-size:0.9rem;">Σύστημα Διαχείρισης Μελών</div>
            <div class="muted" style="font-size:0.8rem;">v{config.app_version}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")
    st.subheader("🧭 Πλοήγηση")

    # Stable navigation with ASCII page paths
    for label, path in PAGES.items():
        st.page_link(path, label=label, use_container_width=True)

    st.markdown("---")
    st.subheader("📊 Κατάσταση")

    total = int(stats.get("total", 0))
    active = int(stats.get("active", 0))
    inactive = total - active

    st.metric("Σύνολο Μελών", total)
    st.metric("Ενεργά", active)
    st.metric("Ανενεργά", inactive)

    st.markdown("---")
    st.subheader("✨ Features")

    email_on = bool(getattr(config, "is_feature_enabled", lambda *_: False)("email"))
    ai_on = ai_available()

    st.markdown(
        f"<span class='badge ok'>✅ Core</span>"
        f"<span class='badge ok'>✅ Tasks</span>"
        f"<span class='badge {'ok' if email_on else 'off'}'>{'✅' if email_on else '⚪'} Email</span>"
        f"<span class='badge {'ok' if ai_on else 'off'}'>{'✅' if ai_on else '⚪'} AI</span>",
        unsafe_allow_html=True,
    )

    st.markdown("---")
    with st.expander("ℹ️ Βοήθεια / Ρυθμίσεις"):
        st.markdown(
            """
            **Πλοήγηση:** από το μενού αριστερά.  
            **Συμβουλή:** κράτησε τα filenames των pages σε ASCII (π.χ. `3_bulk_edit.py`).  
            """
        )
        if not ai_on:
            st.info(
                "AI: Για ενεργοποίηση βάλε `ANTHROPIC_API_KEY` στα Streamlit secrets "
                "ή ως environment variable, και βεβαιώσου ότι υπάρχει το package `anthropic`."
            )


# ======================
# MAIN HEADER
# ======================
st.markdown(
    '<div class="main-header">🏛️ Σύστημα Διαχείρισης Στοάς ΑΚΡΟΠΟΛΙΣ</div>',
    unsafe_allow_html=True,
)

# ======================
# TOP METRICS
# ======================
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric("Μέλη", total)
with c2:
    st.metric("Ενεργά", active)
with c3:
    st.metric("Ανενεργά", inactive)
with c4:
    pct = (active / total * 100) if total else 0
    st.metric("Ποσοστό Ενεργών", f"{pct:.0f}%")

st.markdown("---")

# ======================
# QUICK ACTIONS (optional)
# ======================
st.subheader("⚡ Γρήγορες Ενέργειες")
qc1, qc2, qc3, qc4, qc5, qc6 = st.columns(6)

# Use page_link (always safe)
with qc1:
    st.page_link(PAGES["📋 Μητρώο"], label="📋 Μητρώο", use_container_width=True)
with qc2:
    st.page_link(PAGES["✏️ Επεξεργασία"], label="✏️ Επεξεργασία", use_container_width=True)
with qc3:
    st.page_link(PAGES["🧩 Μαζική Επεξεργασία"], label="🧩 Μαζική", use_container_width=True)
with qc4:
    st.page_link(PAGES["📄 Καρτέλες PDF"], label="📄 Καρτέλες", use_container_width=True)
with qc5:
    st.page_link(PAGES["📈 Στατιστικά"], label="📈 Στατιστικά", use_container_width=True)
with qc6:
    st.page_link(PAGES["🗂️ Εργασίες"], label="🗂️ Εργασίες", use_container_width=True)

st.markdown("---")

# ======================
# CONTENT: GENERAL REGULATION / SECRETARY DUTIES
# ======================
left, right = st.columns([1.2, 0.8], gap="large")

with left:
    st.subheader("📜 Γενικός Κανονισμός (Σύνοψη)")
    st.markdown(
        """
        <div class="card">
        <ul>
          <li><strong>Τήρηση πρακτικών:</strong> Καταγραφή αποφάσεων, παρουσιών, θεμάτων ημερήσιας διάταξης.</li>
          <li><strong>Εμπιστευτικότητα:</strong> Διαχείριση δεδομένων με διακριτικότητα και περιορισμένη πρόσβαση.</li>
          <li><strong>Μητρώο μελών:</strong> Ενημέρωση στοιχείων, βαθμών, κατάστασης και οικονομικής τακτοποίησης.</li>
          <li><strong>Αρχειοθέτηση:</strong> Έγγραφα, αλληλογραφία, αποφάσεις, καρτέλες σε ασφαλή μορφή.</li>
          <li><strong>Συνεδριάσεις:</strong> Πρόσκληση, agenda, πρακτικά, follow-up ενεργειών.</li>
        </ul>
        <div class="muted">Σημ.: Προσαρμόζεται στον εσωτερικό κανονισμό της Στοάς.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.subheader("🧾 Υποχρεώσεις Γραμματέα (Checklist)")
    st.markdown(
        """
        <div class="card">
        <ol>
          <li>Ενημέρωση μητρώου μελών μετά από κάθε μεταβολή.</li>
          <li>Καταγραφή πρακτικών και διαβίβαση αποφάσεων στους αρμόδιους.</li>
          <li>Οργάνωση αλληλογραφίας (εισερχόμενα/εξερχόμενα) και αρχειοθέτηση.</li>
          <li>Έκδοση/ενημέρωση καρτελών και τήρηση αρχείου PDF.</li>
          <li>Παρακολούθηση εργασιών & υπενθυμίσεων (tasks) και προθεσμιών.</li>
          <li>Συντονισμός με Ταμία για οικονομική εικόνα μελών (όπου απαιτείται).</li>
        </ol>
        </div>
        """,
        unsafe_allow_html=True,
    )

with right:
    st.subheader("🤖 AI Assistant (Γραμματέας)")
    st.markdown(
        "<div class='card'>"
        "<div class='muted'>Ρώτα για πρότυπα κειμένων, πρακτικά, λίστες ενεργειών, emails, υπενθυμίσεις.</div>"
        "</div>",
        unsafe_allow_html=True,
    )

    if "ai_chat" not in st.session_state:
        st.session_state.ai_chat = []

    # Show chat history
    for item in st.session_state.ai_chat[-8:]:
        role = item.get("role", "user")
        content = item.get("content", "")
        if role == "user":
            st.markdown(f"**Εσύ:** {content}")
        else:
            st.markdown(f"**AI:** {content}")

    st.markdown("")

    user_prompt = st.text_area(
        "Γράψε το αίτημά σου",
        placeholder="π.χ. Φτιάξε πρότυπο πρακτικών για συνεδρίαση με ημερήσια διάταξη...",
        height=110,
    )

    col_send, col_clear = st.columns([1, 1])
    with col_send:
        send = st.button("🚀 Αποστολή", use_container_width=True, disabled=not user_prompt.strip())
    with col_clear:
        clear = st.button("🧹 Καθαρισμός", use_container_width=True)

    if clear:
        st.session_state.ai_chat = []
        st.rerun()

    if send:
        st.session_state.ai_chat.append({"role": "user", "content": user_prompt.strip()})
        with st.spinner("Το AI συντάσσει απάντηση..."):
            reply = call_ai(user_prompt.strip())
        st.session_state.ai_chat.append({"role": "assistant", "content": reply})
        st.rerun()

st.markdown("---")

# ======================
# FOOTER
# ======================
st.markdown(
    f"""
    <div style="text-align:center; color:#6c757d; padding: 1.5rem 0;">
        <div style="font-weight:700;">🏛️ Στοά ΑΚΡΟΠΟΛΙΣ Υπ’ Αριθμ. 84</div>
        <div style="font-size:0.9rem;">Σύστημα Διαχείρισης Μελών v{config.app_version} • {datetime.now().strftime('%d/%m/%Y')}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

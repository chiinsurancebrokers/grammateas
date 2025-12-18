import os
from datetime import datetime

import streamlit as st

from modules.database import get_database
from modules.config import get_config

# Optional AI
try:
    import anthropic  # type: ignore
except Exception:
    anthropic = None


# ======================
# HELPERS: Secrets / Env
# ======================
def sget(path: str, default=None):
    """
    Read from st.secrets with dot-path, fallback to env.
    Example: sget("AI.ANTHROPIC_API_KEY")
    Env fallback: AI_ANTHROPIC_API_KEY
    """
    # env fallback
    env_key = path.replace(".", "_").upper()
    env_val = os.getenv(env_key, None)

    try:
        node = st.secrets
        for part in path.split("."):
            node = node.get(part)
        return node if node is not None else (env_val if env_val is not None else default)
    except Exception:
        return env_val if env_val is not None else default


def ai_enabled() -> bool:
    return anthropic is not None and bool(sget("AI.ANTHROPIC_API_KEY"))


def email_enabled() -> bool:
    return bool(sget("EMAIL.ENABLED", False)) and bool(sget("EMAIL.SMTP_HOST"))


def call_ai(prompt: str) -> str:
    if not ai_enabled():
        return "AI δεν είναι ενεργό. Πρόσθεσε AI.ANTHROPIC_API_KEY στα Streamlit Secrets."
    if anthropic is None:
        return "Λείπει το package 'anthropic' από requirements.txt."

    api_key = sget("AI.ANTHROPIC_API_KEY")
    model = sget("AI.MODEL", "claude-3-5-sonnet-latest")

    client = anthropic.Anthropic(api_key=api_key)
    system = (
        "Είσαι βοηθός για τον Γραμματέα μιας στοάς. "
        "Απαντάς στα Ελληνικά, πρακτικά και σύντομα. "
        "Όταν ζητούνται πρότυπα κειμένων, δίνεις έτοιμα templates."
    )

    try:
        msg = client.messages.create(
            model=model,
            max_tokens=700,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
        if isinstance(msg.content, list) and msg.content:
            for block in msg.content:
                if getattr(block, "type", None) == "text":
                    return block.text
            return str(msg.content[0])
        return str(msg)
    except Exception as e:
        return f"Σφάλμα AI: {e}"


# ======================
# PAGE CONFIG
# ======================
config = get_config()
st.set_page_config(
    page_title=sget("APP_NAME", getattr(config, "app_name", "Στοά ΑΚΡΟΠΟΛΙΣ")),
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
        .main-header {
            font-size: 2.2rem;
            font-weight: 800;
            color: #1f4788;
            text-align: center;
            padding: 1rem;
            background: linear-gradient(90deg, #f0f2f6 0%, #ffffff 100%);
            border-radius: 12px;
            margin-bottom: 1.25rem;
        }
        .card {
            background: #ffffff;
            border: 1px solid #e9ecef;
            border-radius: 12px;
            padding: 1rem 1.2rem;
            margin: 0.5rem 0;
        }
        .muted { color: #6c757d; }
        .badge { display:inline-block; padding:0.25rem 0.6rem; border-radius:999px; font-size:0.85rem; margin-right:0.4rem; border:1px solid #e9ecef; }
        .ok { background:#d4edda; color:#155724; border-color:#c3e6cb; }
        .off { background:#f8d7da; color:#721c24; border-color:#f5c6cb; }
        .stButton>button { width: 100%; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ======================
# INIT DATA
# ======================
db = get_database()
stats = db.get_member_statistics()
total = int(stats.get("total", 0))
active = int(stats.get("active", 0))
inactive = total - active
pct = (active / total * 100) if total else 0.0

APP_NAME = sget("APP_NAME", getattr(config, "app_name", "Στοά ΑΚΡΟΠΟΛΙΣ"))
APP_VERSION = sget("APP_VERSION", getattr(config, "app_version", "2.0"))

# ASCII pages (your screenshot confirms these names)
PAGES = [
    ("📋 Μητρώο", "pages/1_registry.py"),
    ("✏️ Επεξεργασία", "pages/2_edit.py"),
    ("🧩 Μαζική Επεξεργασία", "pages/3_bulk.py"),
    ("📄 Καρτέλες PDF", "pages/4_cards.py"),
    ("📈 Στατιστικά", "pages/5_stats.py"),
    ("🗂️ Εργασίες", "pages/6_tasks.py"),
]

# ======================
# SIDEBAR
# ======================
with st.sidebar:
    st.markdown(
        f"""
        <div style="text-align:center; padding: 0.75rem 0.75rem 0.25rem 0.75rem;">
            <div style="font-size:2rem;">🏛️</div>
            <div style="font-weight:800; color:#1f4788; font-size:1.05rem;">{APP_NAME}</div>
            <div class="muted" style="font-size:0.85rem;">Σύστημα Διαχείρισης Μελών</div>
            <div class="muted" style="font-size:0.8rem;">v{APP_VERSION}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("---")
    st.subheader("🧭 Πλοήγηση")
    for label, path in PAGES:
        st.page_link(path, label=label, use_container_width=True)

    st.markdown("---")
    st.subheader("📊 Κατάσταση")
    st.metric("Σύνολο Μελών", total)
    st.metric("Ενεργά", active)
    st.metric("Ανενεργά", inactive)

    st.markdown("---")
    st.subheader("✨ Features")
    st.markdown(
        f"<span class='badge ok'>✅ Core</span>"
        f"<span class='badge ok'>✅ Tasks</span>"
        f"<span class='badge {'ok' if email_enabled() else 'off'}'>{'✅' if email_enabled() else '⚪'} Email</span>"
        f"<span class='badge {'ok' if ai_enabled() else 'off'}'>{'✅' if ai_enabled() else '⚪'} AI</span>",
        unsafe_allow_html=True,
    )

    with st.expander("⚙️ Ρυθμίσεις / Secrets"):
        st.write("AI key:", "✅" if ai_enabled() else "❌")
        st.write("Email:", "✅" if email_enabled() else "❌")
        st.caption("Τα κλειδιά μπαίνουν στο Streamlit Cloud → Manage app → Secrets.")


# ======================
# MAIN
# ======================
st.markdown('<div class="main-header">🏛️ Dashboard</div>', unsafe_allow_html=True)

m1, m2, m3, m4 = st.columns(4)
with m1:
    st.metric("Μέλη", total)
with m2:
    st.metric("Ενεργά", active)
with m3:
    st.metric("Ανενεργά", inactive)
with m4:
    st.metric("Ποσοστό Ενεργών", f"{pct:.0f}%")

st.markdown("---")

left, right = st.columns([1.2, 0.8], gap="large")

with left:
    st.subheader("📜 Γενικός Κανονισμός (Σύνοψη)")
    st.markdown(
        """
        <div class="card">
        <ul>
          <li><strong>Τήρηση πρακτικών:</strong> καταγραφή αποφάσεων, παρουσιών και θεμάτων ημερήσιας διάταξης.</li>
          <li><strong>Εμπιστευτικότητα:</strong> προστασία δεδομένων και περιορισμένη πρόσβαση.</li>
          <li><strong>Μητρώο μελών:</strong> ενημέρωση στοιχείων, βαθμών, κατάστασης, οικονομικής τακτοποίησης.</li>
          <li><strong>Αρχειοθέτηση:</strong> έγγραφα/αλληλογραφία/αποφάσεις σε ασφαλή μορφή.</li>
          <li><strong>Συνεδριάσεις:</strong> πρόσκληση, agenda, πρακτικά, follow-up ενεργειών.</li>
        </ul>
        <div class="muted">Προσαρμόζεται στον εσωτερικό κανονισμό της Στοάς.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.subheader("🧾 Υποχρεώσεις Γραμματέα (Checklist)")
    st.markdown(
        """
        <div class="card">
        <ol>
          <li>Ενημέρωση μητρώου μετά από κάθε μεταβολή.</li>
          <li>Καταγραφή πρακτικών και διαβίβαση αποφάσεων.</li>
          <li>Οργάνωση αλληλογραφίας και αρχειοθέτηση.</li>
          <li>Έκδοση/ενημέρωση καρτελών και τήρηση αρχείου PDF.</li>
          <li>Παρακολούθηση εργασιών (tasks) και προθεσμιών.</li>
          <li>Συντονισμός με Ταμία όπου απαιτείται.</li>
        </ol>
        </div>
        """,
        unsafe_allow_html=True,
    )

with right:
    st.subheader("🤖 AI Assistant")
    st.markdown("<div class='card'><div class='muted'>Ζήτησε πρακτικά, emails, templates, λίστες ενεργειών.</div></div>", unsafe_allow_html=True)

    if "ai_chat" not in st.session_state:
        st.session_state.ai_chat = []

    for item in st.session_state.ai_chat[-8:]:
        role = item.get("role", "user")
        content = item.get("content", "")
        st.markdown(f"**{'Εσύ' if role=='user' else 'AI'}:** {content}")

    prompt = st.text_area("Γράψε το αίτημά σου", height=110)

    b1, b2 = st.columns(2)
    with b1:
        send = st.button("🚀 Αποστολή", use_container_width=True, disabled=not prompt.strip())
    with b2:
        clear = st.button("🧹 Καθαρισμός", use_container_width=True)

    if clear:
        st.session_state.ai_chat = []
        st.rerun()

    if send:
        st.session_state.ai_chat.append({"role": "user", "content": prompt.strip()})
        with st.spinner("Σύνταξη απάντησης..."):
            reply = call_ai(prompt.strip())
        st.session_state.ai_chat.append({"role": "assistant", "content": reply})
        st.rerun()


st.markdown("---")
st.markdown(
    f"""
    <div style="text-align:center; color:#6c757d; padding: 1.25rem 0;">
        <div style="font-weight:700;">🏛️ Στοά ΑΚΡΟΠΟΛΙΣ Υπ’ Αριθμ. 84</div>
        <div style="font-size:0.9rem;">v{APP_VERSION} • {datetime.now().strftime('%d/%m/%Y')}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

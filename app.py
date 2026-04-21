# -*- coding: utf-8 -*-
"""
🏛️ Γραμματεύς-Σφραγιδοφύλαξ
Σύστημα Διαχείρισης Στοάς — Βάσει Άρθρων 35-41 ΓΚ ΜΣΕ
"""
import streamlit as st
from datetime import date
from modules.database import init_db, get_member_stats, get_pending_announcements, get_overdue_ergasies, get_deltia

# ── CONFIG ────────────────────────────────────────────────────
LODGE_NAME = "ΑΚΡΟΠΟΛΙΣ Υπ. Αριθμ. 84"

st.set_page_config(
    page_title=f"Γραμματεύς | {LODGE_NAME}",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── INIT DB ───────────────────────────────────────────────────
init_db()

# ── CSS ───────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .lodge-header {
        background: linear-gradient(135deg, #1a2a4a 0%, #2d4a7a 100%);
        color: white; padding: 1.5rem 2rem; border-radius: 12px;
        margin-bottom: 1.5rem; text-align: center;
    }
    .lodge-header h1 { margin: 0; font-size: 1.8rem; font-weight: 700; }
    .lodge-header p  { margin: 0.3rem 0 0; opacity: 0.8; font-size: 0.95rem; }
    .stat-card {
        background: white; border: 1px solid #e2e8f0; border-radius: 10px;
        padding: 1rem 1.2rem; text-align: center;
    }
    .stat-card .val { font-size: 2rem; font-weight: 700; color: #1a2a4a; }
    .stat-card .lbl { font-size: 0.85rem; color: #64748b; margin-top: 0.2rem; }
    .alert-card {
        border-left: 4px solid #f59e0b; background: #fffbeb;
        padding: 0.75rem 1rem; border-radius: 0 8px 8px 0; margin: 0.5rem 0;
    }
    .alert-card.red { border-color: #ef4444; background: #fef2f2; }
    .nav-link { padding: 0.5rem 0.75rem; border-radius: 6px; display: block;
                text-decoration: none; color: #374151; font-size: 0.9rem; margin: 0.15rem 0; }
    .nav-link:hover { background: #f1f5f9; }
    [data-testid="stSidebar"] { background: #f8fafc; }
    div[data-testid="metric-container"] {
        background: white; border: 1px solid #e2e8f0;
        border-radius: 10px; padding: 0.75rem 1rem;
    }
</style>
""", unsafe_allow_html=True)

# ── SIDEBAR ───────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"""
    <div style="text-align:center; padding: 1rem 0 0.5rem;">
        <div style="font-size:2.5rem;">🏛️</div>
        <div style="font-weight:700; color:#1a2a4a; font-size:0.95rem;">{LODGE_NAME}</div>
        <div style="color:#64748b; font-size:0.8rem;">Γραμματεύς-Σφραγιδοφύλαξ</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("### 📚 Βιβλία & Μητρώα")
    pages = [
        ("📋", "Μητρώο Μελών",      "pages/01_Μητρώο.py"),
        ("📝", "Συνεδριάσεις",       "pages/02_Συνεδριάσεις.py"),
        ("✍️", "Παρουσίες",          "pages/03_Παρουσίες.py"),
        ("💰", "Εντάλματα",          "pages/04_Εντάλματα.py"),
        ("📬", "Πρωτόκολλο",         "pages/05_Πρωτόκολλο.py"),
        ("🔄", "Μεταβολές Μητρώου",  "pages/06_Μεταβολές.py"),
        ("📜", "Διαβεβαιώσεις",      "pages/07_Διαβεβαιώσεις.py"),
        ("🚫", "Απορριφθέντες",      "pages/08_Απορριφθέντες.py"),
        ("📖", "Χρυσή Βίβλος",       "pages/09_Χρυσή_Βίβλος.py"),
        ("🪪", "Δελτία & Διπλώματα", "pages/10_Δελτία.py"),
        ("🏛️", "Συμβούλιο",          "pages/11_Συμβούλιο.py"),
        ("✅", "Εργασίες",            "pages/12_Εργασίες.py"),
    ]
    for icon, label, path in pages:
        st.page_link(path, label=f"{icon} {label}", use_container_width=True)

    st.markdown("---")
    stats = get_member_stats()
    st.metric("Ενεργά Μέλη", stats.get("ενεργοί", 0))

# ── DASHBOARD ─────────────────────────────────────────────────
st.markdown(f"""
<div class="lodge-header">
    <h1>🏛️ {LODGE_NAME}</h1>
    <p>Σύστημα Γραμματέα-Σφραγιδοφύλακα · {date.today().strftime('%d %B %Y')}</p>
</div>
""", unsafe_allow_html=True)

# Stats row
stats = get_member_stats()
c1, c2, c3, c4, c5 = st.columns(5)
with c1: st.metric("👥 Σύνολο Μελών",    stats.get("σύνολο", 0))
with c2: st.metric("✅ Ενεργοί",          stats.get("ενεργοί", 0))
with c3: st.metric("🎓 Διδάσκαλοι",      stats.get("Διδάσκαλος", 0))
with c4: st.metric("🤝 Εταίροι",          stats.get("Εταίρος", 0))
with c5: st.metric("📚 Μαθητές",          stats.get("Μαθητής", 0))

st.markdown("---")

left, right = st.columns(2, gap="large")

with left:
    st.subheader("⚠️ Εκκρεμότητες")

    # Αναγγελίες προς ΜΣ
    pending_ms = get_pending_announcements()
    if not pending_ms.empty:
        st.markdown(f"""<div class="alert-card red">
            <strong>📨 {len(pending_ms)} μεταβολές</strong> δεν έχουν αναγγελθεί στη Μεγάλη Στοά
        </div>""", unsafe_allow_html=True)

    # Εκπρόθεσμες εργασίες
    overdue = get_overdue_ergasies()
    if not overdue.empty:
        st.markdown(f"""<div class="alert-card red">
            <strong>🕐 {len(overdue)} εκπρόθεσμες εργασίες</strong>
        </div>""", unsafe_allow_html=True)

    # Εκκρεμή δελτία
    pending_del = get_deltia(status="Εκκρεμής")
    if not pending_del.empty:
        st.markdown(f"""<div class="alert-card">
            <strong>🪪 {len(pending_del)} εκκρεμή δελτία/διπλώματα</strong> προς έκδοση από ΜΣ
        </div>""", unsafe_allow_html=True)

    if pending_ms.empty and overdue.empty and pending_del.empty:
        st.success("✅ Δεν υπάρχουν εκκρεμότητες!")

with right:
    st.subheader("📋 Υποχρεώσεις Γραμματέα")
    st.markdown("""
    | Άρθρο | Υποχρέωση |
    |-------|-----------|
    | 36§2  | Τήρηση 3 Βιβλίων Πρακτικών (ανά Βαθμό) |
    | 36§5  | Μητρώο Μελών — παρακολούθηση μεταβολών |
    | 36§6,7| Εντάλματα Πληρωμής (Γενικό + Ελεονομείο) |
    | 36§10 | Βιβλίο Παρουσιών σε κάθε Συνεδρίαση |
    | 37    | Αλληλογραφία — Πρωτόκολλο Εγγράφων |
    | 38    | Αναγγελία νέων μελών & μεταβολών στη ΜΣ |
    | 39    | Καταγραφή Κορμού Αγαθοεργίας (ολογράφως+αριθμ.) |
    | 40    | Πρακτικά: παρόντες, αναπλ/τές, αλληλ., ομιλίες |
    | 41    | Δελτία Αναγνωρίσεως & Διπλώματα Διδασκάλων |
    """)

st.markdown("---")
st.caption(f"🏛️ {LODGE_NAME} · Σύστημα Γραμματέα v3.0 · {date.today().year}")

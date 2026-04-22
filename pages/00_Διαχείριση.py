# -*- coding: utf-8 -*-
"""Σελίδα 00 — Διαχείριση & Διαγραφή Δεδομένων (για δοκιμές)"""
import sys; sys.path.append("..")
import streamlit as st
from modules.database import init_db, get_conn

init_db()
st.set_page_config(page_title="Διαχείριση", page_icon="⚙️", layout="wide")

st.markdown("# ⚙️ Διαχείριση Δεδομένων")
st.caption("Διαγραφή εγγραφών κατά τη διάρκεια δοκιμών")

st.warning("⚠️ **Προσοχή:** Οι διαγραφές είναι μόνιμες και δεν αναιρούνται.")

# ── ΣΤΑΤΙΣΤΙΚΑ ΠΙΝΑΚΩΝ ───────────────────────────────────────
st.subheader("📊 Κατάσταση Βάσης Δεδομένων")

TABLES = {
    "μέλη":                      "👥 Μέλη",
    "συνεδριάσεις":               "📝 Συνεδριάσεις",
    "παρουσίες":                  "✍️ Παρουσίες",
    "πρωτόκολλο":                 "📬 Πρωτόκολλο",
    "εντάλματα":                  "💰 Εντάλματα",
    "μεταβολές":                  "🔄 Μεταβολές",
    "διαβεβαιώσεις_αξιωματικών": "📜 Διαβεβαιώσεις Αξ/κών",
    "διαβεβαιώσεις_μυουμένων":   "📜 Διαβεβαιώσεις Μυουμένων",
    "απορριφθέντες":              "🚫 Απορριφθέντες",
    "χρυσή_βίβλος":               "📖 Χρυσή Βίβλος",
    "δελτία_διπλώματα":           "🪪 Δελτία/Διπλώματα",
    "πρακτικά_συμβουλίου":        "🏛️ Πρακτικά Συμβουλίου",
    "εργασίες":                   "✅ Εργασίες",
}

conn = get_conn()
cols = st.columns(4)
for i, (tbl, lbl) in enumerate(TABLES.items()):
    cnt = conn.execute(f"SELECT COUNT(*) FROM {tbl}").fetchone()[0]
    cols[i % 4].metric(lbl, cnt)
conn.close()

st.markdown("---")

# ── ΔΙΑΓΡΑΦΗ ΜΕΜΟΝΩΜΕΝΩΝ ΕΓΓΡΑΦΩΝ ────────────────────────────
st.subheader("🗑️ Διαγραφή Μεμονωμένης Εγγραφής")

col1, col2, col3 = st.columns(3)
with col1:
    table_sel = st.selectbox("Πίνακας", list(TABLES.keys()),
                              format_func=lambda x: TABLES[x])
with col2:
    rec_id = st.number_input("ID Εγγραφής", min_value=1, step=1)
with col3:
    st.write("")
    st.write("")
    if st.button("🗑️ Διαγραφή Εγγραφής", use_container_width=True):
        conn = get_conn()
        affected = conn.execute(f"DELETE FROM {table_sel} WHERE id=?", (rec_id,)).rowcount
        conn.commit(); conn.close()
        if affected:
            st.success(f"✅ Διαγράφηκε η εγγραφή #{rec_id} από {TABLES[table_sel]}")
        else:
            st.warning(f"⚠️ Δεν βρέθηκε εγγραφή #{rec_id} στον πίνακα {TABLES[table_sel]}")

st.markdown("---")

# ── ΔΙΑΓΡΑΦΗ ΟΛΩ ΕΓΓΡΑΦΩΝ ΠΙΝΑΚΑ ────────────────────────────
st.subheader("🧹 Εκκαθάριση Πίνακα")
st.error("Αυτή η ενέργεια διαγράφει **ΟΛΑ** τα δεδομένα του επιλεγμένου πίνακα.")

# Εξαιρούμε τον πίνακα μελών από γρήγορη εκκαθάριση
CLEARABLE = {k:v for k,v in TABLES.items() if k != "μέλη"}

col1, col2 = st.columns([2,1])
with col1:
    clear_table = st.selectbox("Πίνακας για εκκαθάριση",
                                list(CLEARABLE.keys()),
                                format_func=lambda x: CLEARABLE[x],
                                key="clear_tbl")
    confirm_text = st.text_input(f"Πληκτρολογήστε **ΔΙΑΓΡΑΦΗ** για επιβεβαίωση:")
with col2:
    st.write("")
    st.write("")
    if st.button("🧹 Εκκαθάριση Πίνακα", use_container_width=True, type="primary"):
        if confirm_text == "ΔΙΑΓΡΑΦΗ":
            conn = get_conn()
            conn.execute(f"DELETE FROM {clear_table}")
            conn.execute(f"DELETE FROM sqlite_sequence WHERE name='{clear_table}'")
            conn.commit(); conn.close()
            st.success(f"✅ Ο πίνακας {CLEARABLE[clear_table]} εκκαθαρίστηκε!")
            st.rerun()
        else:
            st.error("❌ Πληκτρολογήστε ΔΙΑΓΡΑΦΗ για επιβεβαίωση")

st.markdown("---")

# ── ΔΙΑΓΡΑΦΗ ΜΕΛΩΝ ────────────────────────────────────────────
st.subheader("👥 Διαγραφή Μεμονωμένου Μέλους")
import pandas as pd
from modules.database import get_all_members, delete_member

df = get_all_members()
if not df.empty:
    df["display"] = df["επώνυμο"] + " " + df["όνομα"] + " (ID:" + df["id"].astype(str) + ")"
    sel = st.selectbox("Επιλογή μέλους για διαγραφή:",
                       df["id"].tolist(),
                       format_func=lambda x: df.loc[df["id"]==x,"display"].iloc[0])
    col1, col2 = st.columns([3,1])
    with col1:
        st.info(f"Θα διαγραφεί: **{df.loc[df['id']==sel,'display'].iloc[0]}**")
    with col2:
        if st.button("🗑️ Διαγραφή Μέλους", use_container_width=True):
            delete_member(int(sel))
            st.success("✅ Διαγράφηκε!"); st.rerun()

st.markdown("---")

# ── ΠΡΟΒΟΛΗ ΤΕΛΕΥΤΑΙΩΝ ΕΓΓΡΑΦΩΝ ──────────────────────────────
st.subheader("🔍 Προβολή Τελευταίων Εγγραφών")
view_table = st.selectbox("Πίνακας προβολής", list(TABLES.keys()),
                           format_func=lambda x: TABLES[x], key="view_tbl")
limit = st.slider("Αριθμός εγγραφών", 5, 50, 10)

conn = get_conn()
try:
    df_view = pd.read_sql_query(
        f"SELECT * FROM {view_table} ORDER BY id DESC LIMIT {limit}", conn
    )
    st.dataframe(df_view, use_container_width=True, hide_index=True)
    st.caption(f"Εμφάνιση τελευταίων {limit} εγγραφών από {TABLES[view_table]}")
except Exception as e:
    st.error(f"Σφάλμα: {e}")
finally:
    conn.close()

# ── SUPABASE ΟΔΗΓΟΣ ───────────────────────────────────────────
st.markdown("---")
st.subheader("☁️ Μόνιμη Αποθήκευση — Supabase")

pg_configured = False
try:
    import streamlit as st2
    pg_url = st2.secrets.get("database", {}).get("url", "")
    pg_configured = bool(pg_url and pg_url.startswith("postgresql"))
except Exception:
    pass

if pg_configured:
    st.success("✅ **Supabase PostgreSQL ενεργό** — Τα δεδομένα αποθηκεύονται μόνιμα!")
else:
    st.warning("""
⚠️ **Χρησιμοποιείτε SQLite** — Τα δεδομένα χάνονται κάθε φορά που κάνει restart η εφαρμογή.

### Οδηγός ρύθμισης Supabase (δωρεάν):

**Βήμα 1 — Δημιουργία account:**
Πηγαίνετε στο [supabase.com](https://supabase.com) → Sign Up (δωρεάν)

**Βήμα 2 — Νέο Project:**
- New Project → Ονομάστε το `akropolis`
- Επιλέξτε region: `West EU (Ireland)`
- Σημειώστε το **Database Password**

**Βήμα 3 — Connection String:**
- Settings → Database → Connection string → **URI**
- Αντιγράψτε το (μοιάζει με `postgresql://postgres:PASSWORD@db.xxx.supabase.co:5432/postgres`)

**Βήμα 4 — Streamlit Secrets:**
Streamlit Cloud → Manage app → Settings → **Secrets** → προσθέστε:
```toml
[database]
url = "postgresql://postgres:ΤΟ_PASSWORD_ΣΑΣ@db.XXXXX.supabase.co:5432/postgres"
```

**Βήμα 5 — Reboot app** → η εφαρμογή αναγνωρίζει αυτόματα το Supabase!

> Η εφαρμογή δημιουργεί αυτόματα όλους τους πίνακες στο Supabase.
> Θα χρειαστεί να εισάγετε ξανά τα δεδομένα (ή να χρησιμοποιήσετε το παρακάτω εργαλείο).
""")

# Backup/Restore SQLite
st.markdown("---")
st.subheader("💾 Backup & Restore Βάσης (SQLite)")
st.caption("Κατεβάστε την τρέχουσα βάση ή επαναφέρετε από αντίγραφο")

import os
col1, col2 = st.columns(2)
with col1:
    if os.path.exists("grammateas.db"):
        with open("grammateas.db", "rb") as f:
            st.download_button(
                "📥 Download Βάσης (.db)",
                data=f.read(),
                file_name=f"grammateas_backup_{date.today()}.db",
                mime="application/octet-stream",
                use_container_width=True,
                type="primary"
            )
        st.caption("Κρατήστε αυτό το αρχείο ως backup!")

with col2:
    uploaded_db = st.file_uploader("📤 Restore από backup", type=["db"])
    if uploaded_db:
        with open("grammateas.db", "wb") as f:
            f.write(uploaded_db.read())
        st.success("✅ Η βάση επαναφέρθηκε!")
        st.rerun()

# -*- coding: utf-8 -*-
"""Σελίδα 03 — Βιβλίο Παρουσιών (Άρθρα 36§10, 40)"""
import sys; sys.path.append("..")
import streamlit as st
from modules.database import init_db, get_sessions, get_all_members, get_attendance, save_attendance_bulk, get_attendance_stats, ΑΞΙΩΜΑΤΑ

init_db()
st.set_page_config(page_title="Παρουσίες", page_icon="✍️", layout="wide")
st.markdown("# ✍️ Βιβλίο Παρουσιών")
st.caption("Άρθρο 36§10 & 40 — Υπογράφουν άπαντες οι προσελθόντες · Αριθμός παρόντων, αναπληρωτές, δικαιολογηθέντες")

tab_entry, tab_stats = st.tabs(["✍️ Καταγραφή", "📊 Ανάλυση Παρουσιών"])

with tab_entry:
    df_sessions = get_sessions()
    if df_sessions.empty:
        st.warning("Δεν υπάρχουν συνεδριάσεις. Προσθέστε πρώτα μία.")
        st.stop()

    sel_sid = st.selectbox("Συνεδρίαση",
                           df_sessions["id"].tolist(),
                           format_func=lambda x: f"#{x} — {df_sessions.loc[df_sessions['id']==x,'ημερομηνία'].values[0]} ({df_sessions.loc[df_sessions['id']==x,'βαθμός'].values[0]})")

    members = get_all_members(status="Ενεργός")
    if members.empty:
        st.info("Δεν υπάρχουν ενεργά μέλη."); st.stop()

    existing = get_attendance(int(sel_sid))
    existing_map = {}
    if not existing.empty:
        for _, row in existing.iterrows():
            existing_map[int(row["μέλος_id"])] = row

    st.info(f"Σύνολο ενεργών μελών: **{len(members)}** | Καταγεγραμμένοι: **{len(existing)}**")

    rows_data = []
    for _, m in members.iterrows():
        mid = int(m["id"])
        ex = existing_map.get(mid, {})
        col1, col2, col3, col4 = st.columns([3, 1, 1, 2])
        with col1: st.write(f"**{m['επώνυμο']} {m['όνομα']}** *({m['τεκτονικός_βαθμός']})*")
        with col2: parwn = st.checkbox("Παρών", value=bool(ex.get("παρών", True)), key=f"p_{mid}")
        with col3: dik = st.checkbox("Δικ/θηκε", value=bool(ex.get("δικαιολογήθηκε", False)), key=f"d_{mid}")
        with col4: anap = st.text_input("Ανεπλήρωσε", value=ex.get("αναπλήρωσε_θέση",""), key=f"a_{mid}", placeholder="Αξίωμα...")
        rows_data.append({"μέλος_id": mid, "παρών": int(parwn), "δικαιολογήθηκε": int(dik), "αναπλήρωσε_θέση": anap})

    if st.button("💾 Αποθήκευση Παρουσιών", type="primary", use_container_width=True):
        save_attendance_bulk(int(sel_sid), rows_data)
        total = sum(1 for r in rows_data if r["παρών"])
        st.success(f"✅ Αποθηκεύτηκαν! Παρόντες: {total}/{len(rows_data)}")
        st.rerun()

with tab_stats:
    df_stats = get_attendance_stats()
    if df_stats.empty:
        st.info("Δεν υπάρχουν δεδομένα παρουσιών.")
    else:
        st.dataframe(df_stats, use_container_width=True, hide_index=True)
        low = df_stats[df_stats["ποσοστό"] < 50]
        if not low.empty:
            st.warning(f"⚠️ {len(low)} μέλη με παρουσία < 50%:")
            st.dataframe(low, use_container_width=True, hide_index=True)

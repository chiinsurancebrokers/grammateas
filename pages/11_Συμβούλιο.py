# -*- coding: utf-8 -*-
"""Σελίδα 11 — Πρακτικά Συμβουλίου Αξιωματικών (Άρθρο 36§11)"""
import sys; sys.path.append("..")
import streamlit as st
from datetime import date, time
from modules.database import init_db, get_symvoulio_minutes, get_symvoulio_minute, save_symvoulio_minute

init_db()
st.set_page_config(page_title="Συμβούλιο", page_icon="🏛️", layout="wide")
st.markdown("# 🏛️ Πρακτικά Συμβουλίου Αξιωματικών")
st.caption("Άρθρο 36§11 — Βιβλίο Πρακτικών Συμβουλίου Αξιωματικών Στοάς")

tab_list, tab_new = st.tabs(["📋 Λίστα", "➕ Νέα Συνεδρίαση Συμβουλίου"])

with tab_list:
    df = get_symvoulio_minutes()
    if df.empty:
        st.info("Δεν υπάρχουν καταγεγραμμένες συνεδριάσεις Συμβουλίου.")
    else:
        st.dataframe(df, use_container_width=True, hide_index=True)
        sel_id = st.selectbox("Προβολή",
                              df["id"].tolist(),
                              format_func=lambda x: f"#{x} — {df.loc[df['id']==x,'ημερομηνία'].values[0]}")
        s = get_symvoulio_minute(int(sel_id))
        if s:
            st.markdown(f"**Ημερομηνία:** {s['ημερομηνία']}  |  **Ώρα:** {s.get('ώρα','')}")
            c1,c2 = st.columns(2)
            with c1:
                st.markdown("**Παρόντες:**")
                for p in (s.get("παρόντες") or []): st.write(f"• {p}")
                st.markdown("**Θέματα:**")
                for i,t in enumerate(s.get("θέματα") or [],1): st.write(f"{i}. {t}")
            with c2:
                st.markdown("**Αποφάσεις:**")
                for i,a in enumerate(s.get("αποφάσεις") or [],1): st.write(f"{i}. {a}")

with tab_new:
    with st.form("symvoulio_form"):
        c1,c2 = st.columns(2)
        with c1: ημερ = st.date_input("Ημερομηνία *", value=date.today())
        with c2: ωρα = st.time_input("Ώρα", value=time(18,0))
        παρ = st.text_area("Παρόντες *(ένας ανά γραμμή)*", height=100)
        θεμ = st.text_area("Θέματα ΗΔ *(ένα ανά γραμμή)*", height=100)
        απο = st.text_area("Αποφάσεις *(μία ανά γραμμή)*", height=120)
        notes = st.text_area("Παρατηρήσεις", height=60)
        if st.form_submit_button("💾 Αποθήκευση", use_container_width=True, type="primary"):
            save_symvoulio_minute({
                "ημερομηνία": str(ημερ), "ώρα": str(ωρα),
                "παρόντες": [x.strip() for x in παρ.splitlines() if x.strip()],
                "θέματα": [x.strip() for x in θεμ.splitlines() if x.strip()],
                "αποφάσεις": [x.strip() for x in απο.splitlines() if x.strip()],
                "παρατηρήσεις": notes,
            })
            st.success("✅ Καταχωρήθηκε!"); st.rerun()

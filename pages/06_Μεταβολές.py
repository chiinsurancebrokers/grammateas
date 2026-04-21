# -*- coding: utf-8 -*-
"""Σελίδα 06 — Μεταβολές Μητρώου & Αναγγελίες ΜΣ (Άρθρα 36§5, 38)"""
import sys; sys.path.append("..")
import streamlit as st
from datetime import date
from modules.database import init_db, get_metavoles, save_metavoli, get_pending_announcements, get_members_dropdown, ΤΥΠΟΙ_ΜΕΤΑΒΟΛΗΣ

init_db()
st.set_page_config(page_title="Μεταβολές", page_icon="🔄", layout="wide")
st.markdown("# 🔄 Μεταβολές Μητρώου")
st.caption("Άρθρα 36§5, 38 — Παρακολούθηση μεταβολών · Αναγγελία στη Μεγάλη Στοά")

tab_hist, tab_new, tab_pending = st.tabs(["📋 Ιστορικό", "➕ Νέα Μεταβολή", "📨 Εκκρεμείς Αναγγελίες ΜΣ"])

with tab_hist:
    members_dd = get_members_dropdown(active_only=False)
    filt_m = st.selectbox("Φίλτρο μέλους", [0] + members_dd["id"].tolist(),
                          format_func=lambda x: "Όλα" if x==0 else members_dd.loc[members_dd["id"]==x,"fullname"].values[0])
    df = get_metavoles(mid=filt_m if filt_m else None)
    if df.empty:
        st.info("Δεν υπάρχουν μεταβολές.")
    else:
        st.dataframe(df[["id","μέλος","ημερομηνία","τύπος","περιγραφή","αναγγελία_μσ","αρ_πρωτ_μσ"]],
                     use_container_width=True, hide_index=True)

with tab_new:
    st.subheader("➕ Καταχώρηση Μεταβολής")
    members_dd = get_members_dropdown(active_only=False)
    if members_dd.empty:
        st.info("Δεν υπάρχουν μέλη."); st.stop()

    with st.form("new_metavoli_form"):
        c1, c2 = st.columns(2)
        with c1:
            sel_m = st.selectbox("Μέλος *", members_dd["id"].tolist(),
                                 format_func=lambda x: members_dd.loc[members_dd["id"]==x,"fullname"].values[0])
            ημερ = st.date_input("Ημερομηνία Μεταβολής *", value=date.today())
        with c2:
            τύπος = st.selectbox("Τύπος Μεταβολής *", ΤΥΠΟΙ_ΜΕΤΑΒΟΛΗΣ)
            αναγγ = st.date_input("Ημ. Αναγγελίας στη ΜΣ", value=None, help="Αφήστε κενό αν δεν έχει αναγγελθεί")
        περιγρ = st.text_area("Περιγραφή / Λεπτομέρειες", height=80)
        αρ_πρωτ_μσ = st.text_input("ΑΠ Μεγάλης Στοάς", placeholder="π.χ. 145/2025")
        notes = st.text_area("Παρατηρήσεις", height=60)

        if st.form_submit_button("💾 Καταχώρηση", use_container_width=True, type="primary"):
            save_metavoli({
                "μέλος_id": int(sel_m), "ημερομηνία": str(ημερ),
                "τύπος": τύπος, "περιγραφή": περιγρ,
                "αναγγελία_μσ": str(αναγγ) if αναγγ else None,
                "αρ_πρωτ_μσ": αρ_πρωτ_μσ, "παρατηρήσεις": notes,
            })
            st.success(f"✅ Μεταβολή ({τύπος}) καταχωρήθηκε!"); st.rerun()

with tab_pending:
    df_pend = get_pending_announcements()
    if df_pend.empty:
        st.success("✅ Όλες οι μεταβολές έχουν αναγγελθεί στη Μεγάλη Στοά!")
    else:
        st.warning(f"⚠️ Εκκρεμούν **{len(df_pend)}** αναγγελίες προς τη Μεγάλη Στοά (Άρθρο 38)")
        st.dataframe(df_pend, use_container_width=True, hide_index=True)

        st.subheader("📨 Ενημέρωση Αναγγελίας")
        c1, c2, c3 = st.columns(3)
        with c1: mid_upd = st.number_input("ID Μεταβολής", min_value=1, step=1)
        with c2: αναγγ_ημ = st.date_input("Ημ. Αναγγελίας", value=date.today())
        with c3: αρ_πρωτ = st.text_input("ΑΠ ΜΣ")
        if st.button("✅ Σήμανση ως Αναγγελθείσα", use_container_width=True, type="primary"):
            save_metavoli({"id": mid_upd, "αναγγελία_μσ": str(αναγγ_ημ), "αρ_πρωτ_μσ": αρ_πρωτ}, auto_update_member=False)
            st.success("✅ Ενημερώθηκε!"); st.rerun()

# -*- coding: utf-8 -*-
"""Σελίδα 05 — Πρωτόκολλο Εγγράφων (Άρθρο 37)"""
import sys; sys.path.append("..")
import streamlit as st
from datetime import date
from modules.database import init_db, get_protokollon, save_proto, next_proto_number

init_db()
st.set_page_config(page_title="Πρωτόκολλο", page_icon="📬", layout="wide")
st.markdown("# 📬 Πρωτόκολλο Εγγράφων")
st.caption("Άρθρο 37 — Πρωτόκολλο εισερχομένων & εξερχομένων εγγράφων · Διεξαγωγή αλληλογραφίας")

tab_list, tab_new = st.tabs(["📋 Πρωτόκολλο", "➕ Νέα Εγγραφή"])

with tab_list:
    c1, c2, c3, c4 = st.columns(4)
    with c1: year = st.selectbox("Έτος", list(range(date.today().year, 2019, -1)))
    with c2: direction = st.selectbox("Κατεύθυνση", ["Όλα", "Εισερχόμενο", "Εξερχόμενο"])
    with c3: status_f = st.selectbox("Κατάσταση", ["Όλες", "Εκκρεμές", "Απαντήθηκε", "Αρχειοθετήθηκε"])
    with c4: search = st.text_input("🔍 Θέμα")

    df = get_protokollon(year=year, direction="all" if direction=="Όλα" else direction)
    if status_f != "Όλες": df = df[df["κατάσταση"] == status_f]
    if search: df = df[df["θέμα"].str.contains(search, case=False, na=False)]

    # Badges
    ekk = len(df[df["κατάσταση"]=="Εκκρεμές"])
    if ekk: st.warning(f"⚠️ {ekk} εκκρεμή έγγραφα")

    if df.empty:
        st.info("Δεν υπάρχουν εγγραφές.")
    else:
        st.dataframe(df[["αρ_πρωτ","ημερομηνία","κατεύθυνση","αποστολέας","παραλήπτης","θέμα","κατάσταση"]],
                     use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader("✏️ Ενημέρωση Κατάστασης")
    c1, c2, c3 = st.columns(3)
    with c1: pid = st.number_input("ID Εγγραφής", min_value=1, step=1)
    with c2: new_st = st.selectbox("Νέα Κατάσταση", ["Εκκρεμές","Απαντήθηκε","Αρχειοθετήθηκε"])
    with c3:
        st.write("")
        if st.button("✅ Αποθήκευση", use_container_width=True):
            save_proto({"id": pid, "κατάσταση": new_st,
                        "ημ_απάντησης": str(date.today()) if new_st=="Απαντήθηκε" else None})
            st.success("✅ Ενημερώθηκε!"); st.rerun()

with tab_new:
    st.subheader("➕ Νέα Εγγραφή Πρωτοκόλλου")
    year_now = date.today().year
    auto_num = next_proto_number(year_now)

    with st.form("new_proto_form"):
        c1, c2, c3 = st.columns(3)
        with c1:
            αρ = st.text_input("Αριθμός Πρωτοκόλλου", value=auto_num)
            ημερ = st.date_input("Ημερομηνία *", value=date.today())
        with c2:
            κατ = st.radio("Κατεύθυνση *", ["Εισερχόμενο", "Εξερχόμενο"], horizontal=True)
            st_val = st.selectbox("Κατάσταση", ["Εκκρεμές","Απαντήθηκε","Αρχειοθετήθηκε"])
        with c3:
            αποστ = st.text_input("Αποστολέας")
            παραλ = st.text_input("Παραλήπτης")

        θέμα = st.text_input("Θέμα *")
        περιγρ = st.text_area("Περιγραφή / Σύνοψη", height=80)
        σχετ = st.text_input("Σχετικό (αρ. πρωτ.)")
        notes = st.text_area("Παρατηρήσεις", height=60)

        if st.form_submit_button("💾 Καταχώρηση", use_container_width=True, type="primary"):
            if not θέμα:
                st.error("Το θέμα είναι υποχρεωτικό!")
            else:
                save_proto({
                    "αρ_πρωτ": αρ, "ημερομηνία": str(ημερ), "κατεύθυνση": κατ,
                    "αποστολέας": αποστ, "παραλήπτης": παραλ, "θέμα": θέμα,
                    "περιγραφή": περιγρ, "αρ_σχετικού": σχετ,
                    "κατάσταση": st_val, "παρατηρήσεις": notes,
                })
                st.success(f"✅ Εγγράφηκε με ΑΠ {αρ}!"); st.rerun()

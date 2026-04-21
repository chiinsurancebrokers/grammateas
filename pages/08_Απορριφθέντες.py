# -*- coding: utf-8 -*-
"""Σελίδα 08 — Βιβλίο Απορριφθέντων (Άρθρο 36§9)"""
import sys; sys.path.append("..")
import streamlit as st
from datetime import date
from modules.database import init_db, get_aporriphthentes, save_aporriphtheis

init_db()
st.set_page_config(page_title="Απορριφθέντες", page_icon="🚫", layout="wide")
st.markdown("# 🚫 Βιβλίο Απορριφθέντων")
st.caption("Άρθρο 36§9 — Ανακοινώσεις Μεγάλης Στοάς, αλφαβητικά & χρονολογικά")

col_list, col_form = st.columns([3,2])

with col_list:
    search = st.text_input("🔍 Αναζήτηση ονόματος")
    df = get_aporriphthentes(search=search)
    st.metric("Σύνολο Εγγραφών", len(df))
    if not df.empty:
        st.dataframe(df[["id","επώνυμο","όνομα","ημ_απόρριψης","απορρίπτουσα_στοά","αιτία","αρ_πρωτ_μσ"]],
                     use_container_width=True, hide_index=True)

with col_form:
    st.subheader("➕ Νέα Εγγραφή")
    with st.form("aporriphtheis_form"):
        ep = st.text_input("Επώνυμο *")
        on = st.text_input("Όνομα")
        ημερ = st.date_input("Ημερομηνία Απόρριψης *", value=date.today())
        στοά = st.text_input("Απορρίπτουσα Στοά")
        αιτ = st.text_area("Αιτία Απόρριψης", height=80)
        αρ_πρωτ_μσ = st.text_input("ΑΠ Ανακοίνωσης ΜΣ")
        notes = st.text_area("Παρατηρήσεις", height=60)

        if st.form_submit_button("💾 Καταχώρηση", use_container_width=True, type="primary"):
            if not ep:
                st.error("Το επώνυμο είναι υποχρεωτικό!")
            else:
                save_aporriphtheis({
                    "επώνυμο": ep.upper(), "όνομα": on, "ημ_απόρριψης": str(ημερ),
                    "απορρίπτουσα_στοά": στοά, "αιτία": αιτ,
                    "αρ_πρωτ_μσ": αρ_πρωτ_μσ, "παρατηρήσεις": notes,
                })
                st.success(f"✅ Εγγράφηκε!"); st.rerun()

# -*- coding: utf-8 -*-
"""Σελίδα 04 — Εντάλματα Πληρωμής (Άρθρο 36§6,7)"""
import sys; sys.path.append("..")
import streamlit as st
from datetime import date
import json
from modules.database import init_db, get_entalmata, save_entalma, get_entalma_stats, next_entalma_number

init_db()
st.set_page_config(page_title="Εντάλματα", page_icon="💰", layout="wide")
st.markdown("# 💰 Εντάλματα Πληρωμής")
st.caption("Άρθρο 36§6 — Γενικό Βιβλίο Ενταλμάτων · Άρθρο 36§7 — Ελεονομείο")

# Stats
stats = get_entalma_stats()
c1, c2, c3, c4 = st.columns(4)
c1.metric("Γενικό — Σύνολο", f"{stats['Γενικό']['σύνολο']:.2f} €")
c2.metric("Γενικό — Εκκρεμή", f"{stats['Γενικό']['εκκρεμή']:.2f} €")
c3.metric("Ελεονομείο — Σύνολο", f"{stats['Ελεονομείο']['σύνολο']:.2f} €")
c4.metric("Ελεονομείο — Εκκρεμή", f"{stats['Ελεονομείο']['εκκρεμή']:.2f} €")

tab_gen, tab_eleo, tab_new = st.tabs(["📒 Γενικό Βιβλίο", "📗 Ελεονομείο", "➕ Νέο Ένταλμα"])

def show_entalmata_table(βιβλίο):
    df = get_entalmata(βιβλίο=βιβλίο)
    if df.empty:
        st.info("Δεν υπάρχουν εντάλματα.")
        return
    st.dataframe(df[["id","αρ_εντάλματος","ημερομηνία","αιτιολογία","ποσό","κατάσταση","αρ_απόφασης"]],
                 use_container_width=True, hide_index=True,
                 column_config={"ποσό": st.column_config.NumberColumn("Ποσό (€)", format="%.2f")})
    # Ενημέρωση κατάστασης
    c1, c2, c3 = st.columns(3)
    with c1: eid = st.number_input("ID Εντάλματος", min_value=1, step=1, key=f"eid_{βιβλίο}")
    with c2: new_st = st.selectbox("Νέα Κατάσταση", ["Εκκρεμές", "Πληρωμένο", "Ακυρωθέν"], key=f"nst_{βιβλίο}")
    with c3:
        st.write("")
        if st.button("✅ Ενημέρωση", key=f"upd_{βιβλίο}", use_container_width=True):
            ημ_πλ = str(date.today()) if new_st == "Πληρωμένο" else None
            save_entalma({"id": eid, "κατάσταση": new_st, "ημ_πληρωμής": ημ_πλ})
            st.success("✅ Ενημερώθηκε!"); st.rerun()

with tab_gen:  show_entalmata_table("Γενικό")
with tab_eleo: show_entalmata_table("Ελεονομείο")

with tab_new:
    st.subheader("➕ Νέο Ένταλμα Πληρωμής")
    with st.form("new_entalma_form"):
        c1, c2, c3 = st.columns(3)
        with c1:
            βιβλίο = st.selectbox("Βιβλίο *", ["Γενικό", "Ελεονομείο"])
            ημερ = st.date_input("Ημερομηνία *", value=date.today())
        with c2:
            year = date.today().year
            auto_num = next_entalma_number(βιβλίο if βιβλίο else "Γενικό", year)
            αρ = st.text_input("Αριθμός Εντάλματος", value=auto_num)
            ποσό = st.number_input("Ποσό (€) *", min_value=0.01, step=0.01)
        with c3:
            αρ_απόφ = st.text_input("Αριθμός Απόφασης Στοάς")
            κατ = st.selectbox("Κατάσταση", ["Εκκρεμές", "Πληρωμένο"])

        αιτ = st.text_input("Αιτιολογία *")
        st.markdown("**Δικαιολογητικά** *(ένα ανά γραμμή — συνάπτονται αντίγραφα κατά Άρθρο 36§7)*")
        δικαιολ = st.text_area("", height=80)
        notes = st.text_area("Παρατηρήσεις")

        if st.form_submit_button("💾 Έκδοση Εντάλματος", use_container_width=True, type="primary"):
            if not αιτ:
                st.error("Η αιτιολογία είναι υποχρεωτική!")
            else:
                δικ_list = [x.strip() for x in δικαιολ.splitlines() if x.strip()]
                save_entalma({
                    "αρ_εντάλματος": αρ, "ημερομηνία": str(ημερ), "βιβλίο": βιβλίο,
                    "ποσό": ποσό, "αιτιολογία": αιτ,
                    "δικαιολογητικά": δικ_list, "αρ_απόφασης": αρ_απόφ,
                    "κατάσταση": κατ, "παρατηρήσεις": notes,
                })
                st.success(f"✅ Ένταλμα {αρ} εκδόθηκε!"); st.rerun()

# -*- coding: utf-8 -*-
"""Σελίδα 12 — Εργασίες & Υπενθυμίσεις"""
import sys; sys.path.append("..")
import streamlit as st
from datetime import date
from modules.database import init_db, get_ergasies, save_ergasia, get_overdue_ergasies

init_db()
st.set_page_config(page_title="Εργασίες", page_icon="✅", layout="wide")
st.markdown("# ✅ Εργασίες & Υπενθυμίσεις")
st.caption("Παρακολούθηση εκκρεμών ενεργειών και προθεσμιών Γραμματέα")

# Εκπρόθεσμες
overdue = get_overdue_ergasies()
if not overdue.empty:
    st.error(f"🔴 **{len(overdue)} εκπρόθεσμες εργασίες!**")
    st.dataframe(overdue[["id","τίτλος","κατηγορία","προτεραιότητα","ημ_λήξης"]],
                 use_container_width=True, hide_index=True)

tab_list, tab_new = st.tabs(["📋 Λίστα Εργασιών", "➕ Νέα Εργασία"])

with tab_list:
    c1,c2 = st.columns(2)
    with c1: filter_st = st.selectbox("Κατάσταση", ["Εκκρεμής","Σε Εξέλιξη","Ολοκληρώθηκε","Όλες"])
    with c2: filter_pr = st.selectbox("Προτεραιότητα", ["Όλες","Υψηλή","Μεσαία","Χαμηλή"])

    df = get_ergasies(status="all" if filter_st=="Όλες" else filter_st)
    if filter_pr != "Όλες": df = df[df["προτεραιότητα"]==filter_pr] if not df.empty else df

    if df.empty:
        st.info("Δεν υπάρχουν εργασίες.")
    else:
        st.dataframe(df[["id","τίτλος","κατηγορία","προτεραιότητα","κατάσταση","ημ_λήξης"]],
                     use_container_width=True, hide_index=True)
        # Ενημέρωση
        st.markdown("---")
        c1,c2,c3 = st.columns(3)
        with c1: eid = st.number_input("ID Εργασίας", min_value=1, step=1)
        with c2: new_st = st.selectbox("Νέα Κατάσταση", ["Εκκρεμής","Σε Εξέλιξη","Ολοκληρώθηκε"])
        with c3:
            st.write("")
            if st.button("✅ Ενημέρωση", use_container_width=True, type="primary"):
                ημ_ολ = str(date.today()) if new_st=="Ολοκληρώθηκε" else None
                save_ergasia({"id": eid, "κατάσταση": new_st, "ημ_ολοκλήρωσης": ημ_ολ})
                st.success("✅ Ενημερώθηκε!"); st.rerun()

with tab_new:
    with st.form("new_task_form"):
        τίτλ = st.text_input("Τίτλος *")
        c1,c2,c3 = st.columns(3)
        with c1: κατηγ = st.selectbox("Κατηγορία", ["Γενικά","Μητρώο","Συνεδριάσεις","Αλληλογραφία","Εντάλματα","ΜΣ","Άλλο"])
        with c2: προτ = st.selectbox("Προτεραιότητα", ["Υψηλή","Μεσαία","Χαμηλή"])
        with c3: ημ_λήξ = st.date_input("Ημερομηνία Λήξης", value=None)
        περιγρ = st.text_area("Περιγραφή", height=100)
        if st.form_submit_button("💾 Προσθήκη", use_container_width=True, type="primary"):
            if not τίτλ:
                st.error("Ο τίτλος είναι υποχρεωτικός!")
            else:
                save_ergasia({
                    "τίτλος": τίτλ, "περιγραφή": περιγρ, "κατηγορία": κατηγ,
                    "προτεραιότητα": προτ, "κατάσταση": "Εκκρεμής",
                    "ημ_λήξης": str(ημ_λήξ) if ημ_λήξ else None,
                })
                st.success("✅ Προστέθηκε!"); st.rerun()

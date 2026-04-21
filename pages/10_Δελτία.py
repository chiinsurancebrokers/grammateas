# -*- coding: utf-8 -*-
"""Σελίδα 10 — Δελτία Αναγνωρίσεως & Διπλώματα (Άρθρο 41)"""
import sys; sys.path.append("..")
import streamlit as st
from datetime import date
from modules.database import init_db, get_deltia, save_deltio, get_members_dropdown, ΒΑΘΜΟΙ

init_db()
st.set_page_config(page_title="Δελτία & Διπλώματα", page_icon="🪪", layout="wide")
st.markdown("# 🪪 Δελτία Αναγνωρίσεως & Διπλώματα")
st.caption("Άρθρο 41 — Έκδοση από Μεγάλη Στοά, παρακολούθηση & παράδοση")

tab_list, tab_new = st.tabs(["📋 Κατάσταση", "➕ Νέα Αίτηση"])

with tab_list:
    c1, c2 = st.columns(2)
    with c1: filter_type = st.selectbox("Τύπος", ["Όλα","Δελτίο Αναγνωρίσεως","Δίπλωμα Διδασκάλου"])
    with c2: filter_st = st.selectbox("Κατάσταση", ["Όλες","Εκκρεμής","Εκδόθηκε","Παραδόθηκε"])

    df = get_deltia(status="all" if filter_st=="Όλες" else filter_st)
    if filter_type != "Όλα": df = df[df["τύπος"]==filter_type] if not df.empty else df

    pending = len(df[df["κατάσταση"]!="Παραδόθηκε"]) if not df.empty else 0
    if pending: st.warning(f"⚠️ {pending} εκκρεμείς αιτήσεις")

    if df.empty:
        st.info("Δεν υπάρχουν εγγραφές.")
    else:
        st.dataframe(df[["id","μέλος","τύπος","βαθμός","ημ_αίτησης","ημ_έκδοσης","ημ_παράδοσης","κατάσταση","τέλη"]],
                     use_container_width=True, hide_index=True,
                     column_config={"τέλη": st.column_config.NumberColumn("Τέλη (€)", format="%.2f")})

    st.markdown("---")
    st.subheader("✏️ Ενημέρωση")
    c1,c2,c3,c4 = st.columns(4)
    with c1: did = st.number_input("ID", min_value=1, step=1)
    with c2: new_st = st.selectbox("Κατάσταση", ["Εκκρεμής","Εκδόθηκε","Παραδόθηκε"])
    with c3: new_date = st.date_input("Ημερομηνία", value=date.today())
    with c4:
        st.write("")
        if st.button("✅ Αποθήκευση", use_container_width=True, type="primary"):
            field_map = {"Εκδόθηκε": "ημ_έκδοσης", "Παραδόθηκε": "ημ_παράδοσης", "Εκκρεμής": "ημ_αίτησης"}
            save_deltio({"id": did, "κατάσταση": new_st, field_map[new_st]: str(new_date)})
            st.success("✅ Ενημερώθηκε!"); st.rerun()

with tab_new:
    st.subheader("➕ Νέα Αίτηση Δελτίου / Διπλώματος")
    members_dd = get_members_dropdown()
    if members_dd.empty:
        st.info("Δεν υπάρχουν ενεργά μέλη."); st.stop()

    with st.form("deltio_form"):
        c1,c2 = st.columns(2)
        with c1:
            sel_m = st.selectbox("Μέλος *", members_dd["id"].tolist(),
                                 format_func=lambda x: members_dd.loc[members_dd["id"]==x,"fullname"].values[0])
            τύπος = st.selectbox("Τύπος *", ["Δελτίο Αναγνωρίσεως","Δίπλωμα Διδασκάλου"])
        with c2:
            βαθμός = st.selectbox("Βαθμός", ΒΑΘΜΟΙ)
            ημ_αίτ = st.date_input("Ημ. Αίτησης στη ΜΣ", value=date.today())
        τέλη = st.number_input("Τέλη (€)", min_value=0.0, step=0.50)
        notes = st.text_area("Παρατηρήσεις")

        if st.form_submit_button("📤 Υποβολή Αίτησης", use_container_width=True, type="primary"):
            save_deltio({
                "μέλος_id": int(sel_m), "τύπος": τύπος, "βαθμός": βαθμός,
                "ημ_αίτησης": str(ημ_αίτ), "κατάσταση": "Εκκρεμής",
                "τέλη": τέλη, "παρατηρήσεις": notes,
            })
            st.success("✅ Αίτηση καταχωρήθηκε!"); st.rerun()

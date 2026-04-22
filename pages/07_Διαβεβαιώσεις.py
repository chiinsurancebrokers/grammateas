# -*- coding: utf-8 -*-
"""Σελίδα 07 — Βιβλία Επίσημης Διαβεβαίωσης (Άρθρο 36§3,4)"""
import sys; sys.path.append("..")
import streamlit as st
from datetime import date
from modules.database import (init_db, get_diabevaiosis_axiomatikon, save_diabevaiosi_axiomatikou,
                               get_diabevaiosis_myoumenon, save_diabevaiosi_myoumenou,
                               get_members_dropdown, ΑΞΙΩΜΑΤΑ, ΒΑΘΜΟΙ)

init_db()
st.set_page_config(page_title="Διαβεβαιώσεις", page_icon="📜", layout="wide")
st.markdown("# 📜 Βιβλία Επίσημης Διαβεβαίωσης")
st.caption("Άρθρο 36§3 — Βιβλίο Διαβεβαίωσης Αξιωματικών · Άρθρο 36§4 — Τρία Βιβλία Διαβεβαίωσης Μυουμένων")

tab_ax, tab_my = st.tabs(["🏅 Αξιωματικοί (§3)", "🎓 Μυούμενοι (§4)"])

with tab_ax:
    col_list, col_form = st.columns([3,2])
    with col_list:
        st.subheader("📋 Διαβεβαιώσεις Αξιωματικών")
        df = get_diabevaiosis_axiomatikon()
        if df.empty:
            st.info("Δεν υπάρχουν εγγραφές.")
        else:
            df["υπέγραψε"] = df["υπέγραψε"].apply(lambda x: "✅" if x else "❌")
            st.dataframe(df[["μέλος","αξίωμα","ημ_εκλογής","ημ_διαβεβαίωσης","υπέγραψε"]],
                         use_container_width=True, hide_index=True)

    with col_form:
        st.subheader("➕ Νέα Εγγραφή")
        members_dd = get_members_dropdown()
        if not members_dd.empty:
            with st.form("ax_form"):
                sel_m = st.selectbox("Μέλος *", members_dd["id"].tolist(),
                                     format_func=lambda x: members_dd.loc[members_dd["id"]==x,"fullname"].values[0])
                αξίωμα = st.selectbox("Αξίωμα *", ΑΞΙΩΜΑΤΑ)
                c1,c2 = st.columns(2)
                with c1: ημ_εκλ = st.date_input("Ημ. Εκλογής *", value=date.today())
                with c2: ημ_δια = st.date_input("Ημ. Διαβεβαίωσης", value=None)
                υπ = st.checkbox("Έχει υπογράψει")
                κείμ = st.text_area("Επίσημο κείμενο διαβεβαίωσης", height=100,
                                    value="Εγώ ο κάτωθι υπογεγραμμένος, διαβεβαιώ επισήμως...")
                notes = st.text_area("Παρατηρήσεις", height=50)
                if st.form_submit_button("💾 Αποθήκευση", use_container_width=True, type="primary"):
                    save_diabevaiosi_axiomatikou({
                        "μέλος_id": int(sel_m), "αξίωμα": αξίωμα,
                        "ημ_εκλογής": str(ημ_εκλ),
                        "ημ_διαβεβαίωσης": str(ημ_δια) if ημ_δια else None,
                        "υπέγραψε": int(υπ), "κείμενο_διαβεβαίωσης": κείμ, "παρατηρήσεις": notes,
                    })
                    st.success("✅ Αποθηκεύτηκε!"); st.rerun()

with tab_my:
    st.subheader("🎓 Βιβλία Διαβεβαίωσης Μυουμένων")
    deg_filter = st.radio("Βαθμός", ["Όλοι"] + ΒΑΘΜΟΙ, horizontal=True)
    col_list2, col_form2 = st.columns([3,2])

    with col_list2:
        df2 = get_diabevaiosis_myoumenon(βαθμός="all" if deg_filter=="Όλοι" else deg_filter)
        if df2.empty:
            st.info("Δεν υπάρχουν εγγραφές.")
        else:
            df2["υπέγραψε"] = df2["υπέγραψε"].apply(lambda x: "✅" if x else "❌")
            st.dataframe(df2[["μέλος","βαθμός","ημ_μύησης","υπέγραψε"]],
                         use_container_width=True, hide_index=True)

    with col_form2:
        st.subheader("➕ Νέα Εγγραφή")
        members_dd2 = get_members_dropdown(active_only=False)
        if not members_dd2.empty:
            with st.form("my_form"):
                sel_m2 = st.selectbox("Μέλος *", members_dd2["id"].tolist(),
                                      format_func=lambda x: members_dd2.loc[members_dd2["id"]==x,"fullname"].values[0])
                βαθμός = st.selectbox("Βαθμός Μύησης *", ΒΑΘΜΟΙ)
                ημ_μύης = st.date_input("Ημερομηνία Μύησης *", value=date.today())
                υπ2 = st.checkbox("Έχει υπογράψει")
                notes2 = st.text_area("Παρατηρήσεις", height=50)
                if st.form_submit_button("💾 Αποθήκευση", use_container_width=True, type="primary"):
                    save_diabevaiosi_myoumenou({
                        "μέλος_id": int(sel_m2), "βαθμός": βαθμός,
                        "ημ_μύησης": str(ημ_μύης), "υπέγραψε": int(υπ2), "παρατηρήσεις": notes2,
                    })
                    st.success("✅ Αποθηκεύτηκε!"); st.rerun()

# -*- coding: utf-8 -*-
"""Σελίδα 09 — Χρυσή Βίβλος (Άρθρο 36§1)"""
import sys; sys.path.append("..")
import streamlit as st
from datetime import date
from modules.database import init_db, get_chrysi_vivlos, save_chrysi_vivlos_entry, get_sessions

init_db()
st.set_page_config(page_title="Χρυσή Βίβλος", page_icon="📖", layout="wide")
st.markdown("# 📖 Χρυσή Βίβλος")
st.caption("Άρθρο 36§1 — Χρυσή Βίβλος της Στοάς · Αποφάσεις, αναμνηστικές εγγραφές")

col_list, col_form = st.columns([3,2])

with col_list:
    df = get_chrysi_vivlos()
    if df.empty:
        st.info("Δεν υπάρχουν εγγραφές.")
    else:
        st.dataframe(df[["id","ημερομηνία","τίτλος","είδος","καταχωρήθηκε_από"]],
                     use_container_width=True, hide_index=True)
        st.markdown("---")
        sel_id = st.selectbox("Ανάγνωση εγγραφής",
                              df["id"].tolist(),
                              format_func=lambda x: f"#{x} — {df.loc[df['id']==x,'τίτλος'].values[0]}")
        rec = df.loc[df["id"]==sel_id].iloc[0]
        st.markdown(f"### {rec['τίτλος']}")
        st.caption(f"{rec['ημερομηνία']} · {rec['είδος']} · {rec['καταχωρήθηκε_από']}")
        st.write(rec.get("κείμενο",""))

with col_form:
    st.subheader("✍️ Νέα Εγγραφή")
    sessions = get_sessions()
    with st.form("chrysi_form"):
        τίτλ = st.text_input("Τίτλος *")
        ημερ = st.date_input("Ημερομηνία", value=date.today())
        είδος = st.selectbox("Είδος", ["Απόφαση","Αναμνηστική Εγγραφή","Ανακοίνωση","Επισκεπτήριο","Άλλο"])
        κείμ = st.text_area("Κείμενο", height=200)
        καταχ = st.text_input("Καταχωρήθηκε από", value="Γραμματεύς-Σφραγιδοφύλαξ")
        # Link to session optionally
        if not sessions.empty:
            sess_opts = [0] + sessions["id"].tolist()
            sel_sess = st.selectbox("Σχετική Συνεδρίαση (προαιρετικό)", sess_opts,
                                    format_func=lambda x: "—" if x==0 else f"#{x} {sessions.loc[sessions['id']==x,'ημερομηνία'].values[0]}")
        else:
            sel_sess = 0

        if st.form_submit_button("✍️ Εγγραφή στη Χρυσή Βίβλο", use_container_width=True, type="primary"):
            if not τίτλ:
                st.error("Ο τίτλος είναι υποχρεωτικός!")
            else:
                save_chrysi_vivlos_entry({
                    "ημερομηνία": str(ημερ), "τίτλος": τίτλ, "κείμενο": κείμ,
                    "είδος": είδος, "καταχωρήθηκε_από": καταχ,
                    "συνεδρίαση_id": int(sel_sess) if sel_sess else None,
                })
                st.success("✅ Εγγράφηκε στη Χρυσή Βίβλο!"); st.rerun()

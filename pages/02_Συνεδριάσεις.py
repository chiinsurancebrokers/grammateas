# -*- coding: utf-8 -*-
"""Σελίδα 02 — Συνεδριάσεις & Πρακτικά (Άρθρο 36§2, 39, 40)"""
import sys; sys.path.append("..")
import streamlit as st
from datetime import date, time
from modules.database import init_db, get_sessions, get_session, save_session, ΒΑΘΜΟΙ

init_db()
st.set_page_config(page_title="Συνεδριάσεις", page_icon="📝", layout="wide")
st.markdown("# 📝 Συνεδριάσεις & Πρακτικά")
st.caption("Άρθρο 36§2 — Τρία Βιβλία Πρακτικών · Άρθρα 39-40 — Κορμός Αγαθοεργίας & Παρουσίες")

tab_view, tab_new, tab_edit = st.tabs(["📋 Βιβλία Πρακτικών", "➕ Νέα Συνεδρίαση", "✏️ Επεξεργασία"])

# ── ΤΑΒ 1: ΒΙΒΛΙΑ ────────────────────────────────────────────
with tab_view:
    deg_sel = st.radio("Βιβλίο Πρακτικών", ["Όλα"] + ΒΑΘΜΟΙ, horizontal=True)
    df = get_sessions(βαθμός="all" if deg_sel == "Όλα" else deg_sel)

    if df.empty:
        st.info("Δεν υπάρχουν καταγεγραμμένες συνεδριάσεις.")
    else:
        st.dataframe(df[["id","ημερομηνία","ώρα","βαθμός","πλήθος_παρόντων","κορμός_αγαθοεργίας","κορμός_ολογράφως"]],
                     use_container_width=True, hide_index=True,
                     column_config={
                         "κορμός_αγαθοεργίας": st.column_config.NumberColumn("Αγαθοεργία (€)", format="%.2f"),
                     })

        # Προβολή πρακτικών
        st.markdown("---")
        st.subheader("📄 Προβολή Πρακτικών")
        sel_id = st.selectbox("Επιλογή Συνεδρίασης",
                              df["id"].tolist(),
                              format_func=lambda x: f"#{x} — {df.loc[df['id']==x,'ημερομηνία'].values[0]} ({df.loc[df['id']==x,'βαθμός'].values[0]})")
        s = get_session(int(sel_id))
        if s:
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"**Ημερομηνία:** {s['ημερομηνία']}  |  **Ώρα:** {s.get('ώρα','')}  |  **Βαθμός:** {s['βαθμός']}")
                st.markdown(f"**Παρόντες:** {s.get('πλήθος_παρόντων', 0)}  |  **Κορμός:** {s.get('κορμός_αγαθοεργίας',0):.2f}€ ({s.get('κορμός_ολογράφως','')})")
            with c2:
                if s.get("τόπος"): st.markdown(f"**Τόπος:** {s['τόπος']}")
                if s.get("παρατηρήσεις"): st.info(s["παρατηρήσεις"])

            if s.get("αλληλογραφία"):
                st.markdown("**Αλληλογραφία:**")
                for i, item in enumerate(s["αλληλογραφία"], 1): st.write(f"{i}. {item}")
            if s.get("ομιλίες"):
                st.markdown("**Ομιλίες & Συζητήσεις:**")
                for i, item in enumerate(s["ομιλίες"], 1): st.write(f"{i}. {item}")
            if s.get("αποφάσεις"):
                st.markdown("**Αποφάσεις:**")
                for i, item in enumerate(s["αποφάσεις"], 1): st.write(f"{i}. {item}")

# ── ΤΑΒ 2: ΝΕΑ ΣΥΝΕΔΡΙΑΣΗ ────────────────────────────────────
with tab_new:
    st.subheader("➕ Καταχώρηση Νέας Συνεδρίασης")
    with st.form("new_session_form"):
        c1, c2, c3, c4 = st.columns(4)
        with c1: hm = st.date_input("Ημερομηνία *", value=date.today())
        with c2: ora = st.time_input("Ώρα", value=time(19, 0))
        with c3: βαθμός = st.selectbox("Βαθμός *", ΒΑΘΜΟΙ)
        with c4: topos = st.text_input("Τόπος")

        st.markdown("**Αλληλογραφία** *(μία ανά γραμμή)*")
        allilogr = st.text_area("", height=80, key="allilogr")
        st.markdown("**Ομιλίες & Συζητήσεις** *(μία ανά γραμμή)*")
        omilies = st.text_area("", height=80, key="omilies")
        st.markdown("**Αποφάσεις** *(μία ανά γραμμή)*")
        apof = st.text_area("", height=80, key="apof")

        st.markdown("**Κορμός Αγαθοεργίας** *(Άρθρο 39 — ολογράφως και αριθμητικώς)*")
        c1, c2 = st.columns(2)
        with c1: kormos = st.number_input("Ποσό (€)", min_value=0.0, step=0.01)
        with c2: kormos_olog = st.text_input("Ολογράφως", placeholder="π.χ. Είκοσι ευρώ")

        notes = st.text_area("Παρατηρήσεις")

        if st.form_submit_button("💾 Αποθήκευση Πρακτικών", use_container_width=True, type="primary"):
            sid = save_session({
                "ημερομηνία": str(hm), "ώρα": str(ora), "βαθμός": βαθμός, "τόπος": topos,
                "αλληλογραφία": [x.strip() for x in allilogr.splitlines() if x.strip()],
                "ομιλίες": [x.strip() for x in omilies.splitlines() if x.strip()],
                "αποφάσεις": [x.strip() for x in apof.splitlines() if x.strip()],
                "κορμός_αγαθοεργίας": kormos, "κορμός_ολογράφως": kormos_olog,
                "παρατηρήσεις": notes,
            })
            st.success(f"✅ Πρακτικά συνεδρίασης #{sid} αποθηκεύτηκαν!")
            st.rerun()

# ── ΤΑΒ 3: ΕΠΕΞΕΡΓΑΣΙΑ ───────────────────────────────────────
with tab_edit:
    st.subheader("✏️ Επεξεργασία Πρακτικών")
    df_all = get_sessions()
    if df_all.empty:
        st.info("Δεν υπάρχουν συνεδριάσεις.")
    else:
        sel_id = st.selectbox("Επιλογή",
                              df_all["id"].tolist(),
                              format_func=lambda x: f"#{x} — {df_all.loc[df_all['id']==x,'ημερομηνία'].values[0]} ({df_all.loc[df_all['id']==x,'βαθμός'].values[0]})")
        s = get_session(int(sel_id))
        if s:
            with st.form("edit_session_form"):
                c1, c2, c3 = st.columns(3)
                with c1: hm = st.date_input("Ημερομηνία", value=st.session_state.get("_hm") or __import__("pandas").to_datetime(s["ημερομηνία"]).date())
                with c2:
                    deg_idx = ΒΑΘΜΟΙ.index(s["βαθμός"]) if s["βαθμός"] in ΒΑΘΜΟΙ else 0
                    βαθμός = st.selectbox("Βαθμός", ΒΑΘΜΟΙ, index=deg_idx)
                with c3: topos = st.text_input("Τόπος", value=s.get("τόπος",""))

                allilogr = st.text_area("Αλληλογραφία", value="\n".join(s.get("αλληλογραφία",[]) or []), height=80)
                omilies  = st.text_area("Ομιλίες", value="\n".join(s.get("ομιλίες",[]) or []), height=80)
                apof     = st.text_area("Αποφάσεις", value="\n".join(s.get("αποφάσεις",[]) or []), height=80)
                c1, c2 = st.columns(2)
                with c1: kormos = st.number_input("Κορμός (€)", value=float(s.get("κορμός_αγαθοεργίας") or 0), step=0.01)
                with c2: kormos_olog = st.text_input("Ολογράφως", value=s.get("κορμός_ολογράφως",""))
                notes = st.text_area("Παρατηρήσεις", value=s.get("παρατηρήσεις",""))

                if st.form_submit_button("💾 Αποθήκευση", use_container_width=True, type="primary"):
                    save_session({
                        "id": sel_id, "ημερομηνία": str(hm), "βαθμός": βαθμός, "τόπος": topos,
                        "αλληλογραφία": [x.strip() for x in allilogr.splitlines() if x.strip()],
                        "ομιλίες": [x.strip() for x in omilies.splitlines() if x.strip()],
                        "αποφάσεις": [x.strip() for x in apof.splitlines() if x.strip()],
                        "κορμός_αγαθοεργίας": kormos, "κορμός_ολογράφως": kormos_olog,
                        "παρατηρήσεις": notes,
                    })
                    st.success("✅ Αποθηκεύτηκε!"); st.rerun()

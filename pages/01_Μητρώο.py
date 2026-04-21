# -*- coding: utf-8 -*-
"""Σελίδα 01 — Μητρώο Μελών (Άρθρο 36§5)"""
import sys; sys.path.append("..")
import streamlit as st
import pandas as pd
from datetime import date
from modules.database import (
    init_db, get_all_members, get_member, save_member, delete_member,
    ΒΑΘΜΟΙ, ΚΑΤΑΣΤΑΣΕΙΣ_ΜΕΛΟΥΣ
)

init_db()
st.set_page_config(page_title="Μητρώο Μελών", page_icon="📋", layout="wide")
st.markdown("# 📋 Μητρώο Μελών")
st.caption("Άρθρο 36§5 — Μητρώο Στοάς · Αύξων αριθμός, στοιχεία, βαθμός, κατάσταση")

tab_list, tab_add, tab_edit = st.tabs(["📋 Λίστα Μελών", "➕ Νέο Μέλος", "✏️ Επεξεργασία"])

# ── ΤΑΒ 1: ΛΙΣΤΑ ─────────────────────────────────────────────
with tab_list:
    col1, col2, col3, col4 = st.columns([3,1,1,1])
    with col1: search = st.text_input("🔍 Αναζήτηση", placeholder="Επώνυμο, όνομα, ΑΜ...")
    with col2: filter_status = st.selectbox("Κατάσταση", ["Όλες"] + ΚΑΤΑΣΤΑΣΕΙΣ_ΜΕΛΟΥΣ)
    with col3: filter_deg = st.selectbox("Βαθμός", ["Όλοι"] + ΒΑΘΜΟΙ)
    with col4: st.write("")

    df = get_all_members()
    if search:
        mask = (df["επώνυμο"].str.contains(search, case=False, na=False) |
                df["όνομα"].str.contains(search, case=False, na=False) |
                df["αρ_μητρώου_στοάς"].str.contains(search, case=False, na=False))
        df = df[mask]
    if filter_status != "Όλες":
        df = df[df["κατάσταση"] == filter_status]
    if filter_deg != "Όλοι":
        df = df[df["τεκτονικός_βαθμός"] == filter_deg]

    st.markdown(f"**{len(df)} μέλη**")

    if not df.empty:
        show_cols = ["id", "αρ_μητρώου_στοάς", "αρ_μητρώου_μσ", "επώνυμο", "όνομα",
                     "πατρώνυμο", "τεκτονικός_βαθμός", "ημ_μύησης", "κατάσταση",
                     "κινητό", "email"]
        show_cols = [c for c in show_cols if c in df.columns]
        st.dataframe(df[show_cols], use_container_width=True, hide_index=True,
                     column_config={
                         "id": st.column_config.NumberColumn("ID", width="small"),
                         "αρ_μητρώου_στοάς": "ΑΜ Στοάς",
                         "αρ_μητρώου_μσ": "ΑΜ ΜΣ",
                         "τεκτονικός_βαθμός": "Βαθμός",
                         "κατάσταση": "Κατάσταση",
                     })
        csv = df.to_csv(index=False).encode("utf-8-sig")
        st.download_button("📥 Εξαγωγή CSV", csv, "μητρώο_μελών.csv", "text/csv")
    else:
        st.info("Δεν βρέθηκαν μέλη.")

# ── ΤΑΒ 2: ΝΕΟ ΜΕΛΟΣ ─────────────────────────────────────────
with tab_add:
    st.subheader("➕ Εγγραφή Νέου Μέλους")
    with st.form("new_member_form"):
        st.markdown("**Προσωπικά Στοιχεία**")
        c1, c2, c3 = st.columns(3)
        with c1:
            ep = st.text_input("Επώνυμο *")
            on = st.text_input("Όνομα *")
            pat = st.text_input("Πατρώνυμο")
        with c2:
            hm_gen = st.date_input("Ημ. Γέννησης", value=None)
            topos_gen = st.text_input("Τόπος Γέννησης")
            epaggelma = st.text_input("Επάγγελμα")
        with c3:
            dieuth = st.text_input("Διεύθυνση")
            poli = st.text_input("Πόλη")
            tk = st.text_input("ΤΚ")

        st.markdown("**Στοιχεία Επικοινωνίας**")
        c1, c2, c3 = st.columns(3)
        with c1: tel = st.text_input("Τηλέφωνο")
        with c2: kin = st.text_input("Κινητό")
        with c3: em = st.text_input("Email")

        st.markdown("**Τεκτονικά Στοιχεία**")
        c1, c2, c3, c4 = st.columns(4)
        with c1: am_stoas = st.text_input("ΑΜ Στοάς")
        with c2: am_ms = st.text_input("ΑΜ Μεγάλης Στοάς")
        with c3: βαθμός = st.selectbox("Βαθμός", ΒΑΘΜΟΙ)
        with c4: κατ = st.selectbox("Κατάσταση", ΚΑΤΑΣΤΑΣΕΙΣ_ΜΕΛΟΥΣ)

        c1, c2, c3 = st.columns(3)
        with c1: hm_my = st.date_input("Ημ. Μύησης", value=None)
        with c2: hm_et = st.date_input("Ημ. Εταίρου", value=None)
        with c3: hm_did = st.date_input("Ημ. Διδασκάλου", value=None)

        stoa_myisis = st.text_input("Στοά Μύησης (αν υιοθετήθηκε από άλλη Στοά)")
        notes = st.text_area("Παρατηρήσεις")

        submitted = st.form_submit_button("💾 Αποθήκευση", use_container_width=True, type="primary")
        if submitted:
            if not ep or not on:
                st.error("Επώνυμο και Όνομα είναι υποχρεωτικά!")
            else:
                save_member({
                    "επώνυμο": ep.upper(), "όνομα": on, "πατρώνυμο": pat,
                    "ημ_γέννησης": str(hm_gen) if hm_gen else None,
                    "τόπος_γέννησης": topos_gen, "επάγγελμα": epaggelma,
                    "διεύθυνση": dieuth, "πόλη": poli, "τκ": tk,
                    "τηλέφωνο": tel, "κινητό": kin, "email": em,
                    "αρ_μητρώου_στοάς": am_stoas, "αρ_μητρώου_μσ": am_ms,
                    "τεκτονικός_βαθμός": βαθμός, "κατάσταση": κατ,
                    "ημ_μύησης": str(hm_my) if hm_my else None,
                    "ημ_εταίρου": str(hm_et) if hm_et else None,
                    "ημ_διδασκάλου": str(hm_did) if hm_did else None,
                    "στοά_μύησης": stoa_myisis, "παρατηρήσεις": notes,
                })
                st.success(f"✅ Ο/Η {ep} {on} εγγράφηκε επιτυχώς!")
                st.rerun()

# ── ΤΑΒ 3: ΕΠΕΞΕΡΓΑΣΙΑ ───────────────────────────────────────
with tab_edit:
    st.subheader("✏️ Επεξεργασία Μέλους")
    df_all = get_all_members()
    if df_all.empty:
        st.info("Δεν υπάρχουν μέλη."); st.stop()

    df_all["display"] = df_all["επώνυμο"] + " " + df_all["όνομα"] + " (ID:" + df_all["id"].astype(str) + ")"
    sel_id = st.selectbox("Επιλογή Μέλους", df_all["id"].tolist(),
                          format_func=lambda x: df_all.loc[df_all["id"]==x, "display"].iloc[0])

    m = get_member(int(sel_id))
    if not m:
        st.error("Μέλος δεν βρέθηκε"); st.stop()

    def sv(k, default=""): return m.get(k) or default
    def sd(k):
        v = m.get(k)
        if not v: return None
        try: return pd.to_datetime(v).date()
        except: return None

    with st.form("edit_member_form"):
        c1, c2, c3 = st.columns(3)
        with c1:
            ep = st.text_input("Επώνυμο *", value=sv("επώνυμο"))
            on = st.text_input("Όνομα *", value=sv("όνομα"))
            pat = st.text_input("Πατρώνυμο", value=sv("πατρώνυμο"))
        with c2:
            hm_gen = st.date_input("Ημ. Γέννησης", value=sd("ημ_γέννησης"))
            topos_gen = st.text_input("Τόπος Γέννησης", value=sv("τόπος_γέννησης"))
            epaggelma = st.text_input("Επάγγελμα", value=sv("επάγγελμα"))
        with c3:
            dieuth = st.text_input("Διεύθυνση", value=sv("διεύθυνση"))
            poli = st.text_input("Πόλη", value=sv("πόλη"))
            tk = st.text_input("ΤΚ", value=sv("τκ"))

        c1, c2, c3 = st.columns(3)
        with c1: tel = st.text_input("Τηλέφωνο", value=sv("τηλέφωνο"))
        with c2: kin = st.text_input("Κινητό", value=sv("κινητό"))
        with c3: em = st.text_input("Email", value=sv("email"))

        c1, c2, c3, c4 = st.columns(4)
        with c1: am_stoas = st.text_input("ΑΜ Στοάς", value=sv("αρ_μητρώου_στοάς"))
        with c2: am_ms = st.text_input("ΑΜ ΜΣ", value=sv("αρ_μητρώου_μσ"))
        with c3:
            deg_idx = ΒΑΘΜΟΙ.index(m.get("τεκτονικός_βαθμός", "Μαθητής")) if m.get("τεκτονικός_βαθμός") in ΒΑΘΜΟΙ else 0
            βαθμός = st.selectbox("Βαθμός", ΒΑΘΜΟΙ, index=deg_idx)
        with c4:
            kat_idx = ΚΑΤΑΣΤΑΣΕΙΣ_ΜΕΛΟΥΣ.index(m.get("κατάσταση", "Ενεργός")) if m.get("κατάσταση") in ΚΑΤΑΣΤΑΣΕΙΣ_ΜΕΛΟΥΣ else 0
            κατ = st.selectbox("Κατάσταση", ΚΑΤΑΣΤΑΣΕΙΣ_ΜΕΛΟΥΣ, index=kat_idx)

        c1, c2, c3 = st.columns(3)
        with c1: hm_my = st.date_input("Ημ. Μύησης", value=sd("ημ_μύησης"))
        with c2: hm_et = st.date_input("Ημ. Εταίρου", value=sd("ημ_εταίρου"))
        with c3: hm_did = st.date_input("Ημ. Διδασκάλου", value=sd("ημ_διδασκάλου"))

        stoa_myisis = st.text_input("Στοά Μύησης", value=sv("στοά_μύησης"))
        notes = st.text_area("Παρατηρήσεις", value=sv("παρατηρήσεις"))

        c1, c2 = st.columns(2)
        with c1: save_btn = st.form_submit_button("💾 Αποθήκευση", use_container_width=True, type="primary")
        with c2: del_btn  = st.form_submit_button("🗑️ Διαγραφή", use_container_width=True)

        if save_btn:
            save_member({
                "id": sel_id,
                "επώνυμο": ep.upper(), "όνομα": on, "πατρώνυμο": pat,
                "ημ_γέννησης": str(hm_gen) if hm_gen else None,
                "τόπος_γέννησης": topos_gen, "επάγγελμα": epaggelma,
                "διεύθυνση": dieuth, "πόλη": poli, "τκ": tk,
                "τηλέφωνο": tel, "κινητό": kin, "email": em,
                "αρ_μητρώου_στοάς": am_stoas, "αρ_μητρώου_μσ": am_ms,
                "τεκτονικός_βαθμός": βαθμός, "κατάσταση": κατ,
                "ημ_μύησης": str(hm_my) if hm_my else None,
                "ημ_εταίρου": str(hm_et) if hm_et else None,
                "ημ_διδασκάλου": str(hm_did) if hm_did else None,
                "στοά_μύησης": stoa_myisis, "παρατηρήσεις": notes,
            })
            st.success("✅ Αποθηκεύτηκε!"); st.rerun()
        if del_btn:
            delete_member(int(sel_id))
            st.success("🗑️ Διαγράφηκε!"); st.rerun()

# ── PDF ΕΞΑΓΩΓΗ ──────────────────────────────────────────────
with tab_list:
    st.markdown("---")
    col_pdf1, col_pdf2 = st.columns(2)
    with col_pdf1:
        if st.button("📄 Εκτύπωση Μητρώου PDF", use_container_width=True):
            from modules.pdf_gen import generate_members_list_pdf
            df_print = get_all_members()
            pdf_buf = generate_members_list_pdf(df_print)
            st.download_button("⬇️ Λήψη PDF Μητρώου", pdf_buf,
                               file_name="μητρώο_μελών.pdf", mime="application/pdf",
                               use_container_width=True)
    with col_pdf2:
        if st.button("👤 Καρτέλα Επιλεγμένου Μέλους PDF", use_container_width=True):
            from modules.pdf_gen import generate_member_card_pdf
            # Shows for last searched result — pick first member
            df_first = get_all_members()
            if not df_first.empty:
                m_data = get_member(int(df_first.iloc[0]["id"]))
                if m_data:
                    pdf_buf = generate_member_card_pdf(m_data)
                    st.download_button("⬇️ Λήψη Καρτέλας PDF", pdf_buf,
                                       file_name=f"καρτέλα_{df_first.iloc[0]['επώνυμο']}.pdf",
                                       mime="application/pdf", use_container_width=True)

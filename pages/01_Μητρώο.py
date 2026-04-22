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
st.caption("Άρθρο 36§5 — Μητρώο Στοάς · Αύξων αριθμός, στοιχεία, βαθμός, κατάσταση, αξιώματα")

# Αξιώματα Στοάς
ΑΞΙΩΜΑΤΑ_ΣΤΟΑΣ = [
    "", "Σεβάσμιος", "Α' Επόπτης", "Β' Επόπτης", "Ρήτωρ", "Γραμματεύς-Σφραγιδοφύλαξ",
    "Ταμίας", "Α' Δοκιμαστής", "Β' Δοκιμαστής", "Ελεονόμος", "Τελετάρχης", "Στεγαστής",
    "Α' Στύλος", "Β' Στύλος", "Πρόσθετος Ρήτωρ", "Μέγας Επιθεωρητής",
]
ΑΞΙΩΜΑΤΑ_ΜΣ = [
    "", "Μέγας Διδάσκαλος", "Πρόσθετος Μέγας Διδάσκαλος", "Α' Μέγας Επόπτης",
    "Β' Μέγας Επόπτης", "Μέγας Ρήτωρ", "Μέγας Γενικός Γραμματεύς",
    "Μέγας Δοκιμαστής", "Μέγας Θησαυροφύλαξ", "Μέγας Ελεονόμος",
    "Μέγας Τελετάρχης", "Μέγας Στεγαστής", "Μέγας Καγκελάριος",
    "Μέγας Επιθεωρητής", "Κοσμήτωρ", "Πρόσθετος Μέγας Αξιωματικός",
    "Αντιπρόσωπος ΜΣ",
]

tab_list, tab_add, tab_edit, tab_card = st.tabs([
    "📋 Λίστα Μελών", "➕ Νέο Μέλος", "✏️ Επεξεργασία", "📄 Καρτέλα Μέλους"
])

# ── ΤΑΒ 1: ΛΙΣΤΑ ─────────────────────────────────────────────
with tab_list:
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1: search = st.text_input("🔍 Αναζήτηση", placeholder="Επώνυμο, όνομα, ΑΜ, αξίωμα...")
    with col2: filter_status = st.selectbox("Κατάσταση", ["Όλες"] + ΚΑΤΑΣΤΑΣΕΙΣ_ΜΕΛΟΥΣ)
    with col3: filter_deg = st.selectbox("Βαθμός", ["Όλοι"] + ΒΑΘΜΟΙ)

    df = get_all_members()
    if search:
        mask = (
            df["επώνυμο"].str.contains(search, case=False, na=False) |
            df["όνομα"].str.contains(search, case=False, na=False) |
            df["αρ_μητρώου_στοάς"].fillna("").str.contains(search, case=False) |
            df.get("αξίωμα_στοάς", pd.Series([""])).fillna("").str.contains(search, case=False) |
            df.get("αξίωμα_μεγάλης_στοάς", pd.Series([""])).fillna("").str.contains(search, case=False)
        )
        df = df[mask]
    if filter_status != "Όλες":
        df = df[df["κατάσταση"] == filter_status]
    if filter_deg != "Όλοι":
        df = df[df["τεκτονικός_βαθμός"] == filter_deg]

    st.markdown(f"**{len(df)} μέλη**")

    if not df.empty:
        # Στήλες: χωρίς πατρώνυμο & ημ_μύησης, με αξιώματα
        show_cols = [
            "id", "αρ_μητρώου_στοάς", "αρ_μητρώου_μσ",
            "επώνυμο", "όνομα",
            "τεκτονικός_βαθμός", "κατάσταση",
            "αξίωμα_στοάς", "αξίωμα_μεγάλης_στοάς",
            "κινητό", "email",
        ]
        show_cols = [c for c in show_cols if c in df.columns]
        st.dataframe(
            df[show_cols],
            use_container_width=True,
            hide_index=True,
            column_config={
                "id":                    st.column_config.NumberColumn("ID", width="small"),
                "αρ_μητρώου_στοάς":     st.column_config.TextColumn("ΑΜ Στοάς", width="small"),
                "αρ_μητρώου_μσ":        st.column_config.TextColumn("ΑΜ ΜΣ", width="small"),
                "επώνυμο":              st.column_config.TextColumn("Επώνυμο"),
                "όνομα":                st.column_config.TextColumn("Όνομα"),
                "τεκτονικός_βαθμός":   st.column_config.TextColumn("Βαθμός", width="small"),
                "κατάσταση":            st.column_config.TextColumn("Κατάσταση", width="small"),
                "αξίωμα_στοάς":        st.column_config.TextColumn("Αξίωμα Στοάς"),
                "αξίωμα_μεγάλης_στοάς":st.column_config.TextColumn("Αξίωμα ΜΣ"),
                "κινητό":              st.column_config.TextColumn("Κινητό"),
                "email":                st.column_config.TextColumn("Email"),
            }
        )
        st.markdown("---")
        col_a, col_b = st.columns(2)
        with col_a:
            csv = df.to_csv(index=False).encode("utf-8-sig")
            st.download_button("📥 Εξαγωγή CSV", csv, "μητρώο_μελών.csv",
                               "text/csv", use_container_width=True)
        with col_b:
            if st.button("📄 PDF Ολόκληρου Μητρώου", use_container_width=True):
                from modules.pdf_gen import generate_members_list_pdf
                buf = generate_members_list_pdf(get_all_members())
                st.download_button("⬇️ Λήψη PDF Μητρώου", buf,
                                   file_name="μητρώο_μελών.pdf",
                                   mime="application/pdf",
                                   use_container_width=True)
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

        st.markdown("**Επικοινωνία**")
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

        st.markdown("**Αξιώματα**")
        c1, c2 = st.columns(2)
        with c1: ax_stoas = st.selectbox("Αξίωμα Στοάς", ΑΞΙΩΜΑΤΑ_ΣΤΟΑΣ)
        with c2: ax_ms = st.selectbox("Αξίωμα Μεγάλης Στοάς", ΑΞΙΩΜΑΤΑ_ΜΣ)

        stoa_myisis = st.text_input("Στοά Μύησης")
        notes = st.text_area("Παρατηρήσεις")

        if st.form_submit_button("💾 Αποθήκευση", use_container_width=True, type="primary"):
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
                    "στοά_μύησης": stoa_myisis,
                    "αξίωμα_στοάς": ax_stoas,
                    "αξίωμα_μεγάλης_στοάς": ax_ms,
                    "παρατηρήσεις": notes,
                })
                st.success(f"✅ Ο/Η {ep} {on} εγγράφηκε!"); st.rerun()

# ── ΤΑΒ 3: ΕΠΕΞΕΡΓΑΣΙΑ ───────────────────────────────────────
with tab_edit:
    st.subheader("✏️ Επεξεργασία Μέλους")
    df_all = get_all_members()
    if df_all.empty:
        st.info("Δεν υπάρχουν μέλη.")
    else:
        df_all["display"] = (df_all["επώνυμο"] + " " + df_all["όνομα"] +
                             " (ID:" + df_all["id"].astype(str) + ")")
        sel_id = st.selectbox("Επιλογή Μέλους", df_all["id"].tolist(),
                              format_func=lambda x: df_all.loc[df_all["id"]==x, "display"].iloc[0])
        m = get_member(int(sel_id))
        if m:
            def sv(k, default=""): return m.get(k) or default
            def sd(k):
                v = m.get(k)
                if not v: return None
                try: return pd.to_datetime(v).date()
                except: return None

            with st.form("edit_member_form"):
                tab_personal, tab_contact, tab_masonic, tab_roles = st.tabs([
                    "👤 Προσωπικά", "📞 Επικοινωνία", "⚒️ Τεκτονικά", "🏛️ Αξιώματα"
                ])

                with tab_personal:
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        ep  = st.text_input("Επώνυμο *", value=sv("επώνυμο"))
                        on  = st.text_input("Όνομα *",   value=sv("όνομα"))
                        pat = st.text_input("Πατρώνυμο", value=sv("πατρώνυμο"))
                    with c2:
                        hm_gen    = st.date_input("Ημ. Γέννησης",   value=sd("ημ_γέννησης"))
                        topos_gen = st.text_input("Τόπος Γέννησης",  value=sv("τόπος_γέννησης"))
                        epaggelma = st.text_input("Επάγγελμα",       value=sv("επάγγελμα"))
                    with c3:
                        dieuth = st.text_input("Διεύθυνση", value=sv("διεύθυνση"))
                        poli   = st.text_input("Πόλη",      value=sv("πόλη"))
                        tk     = st.text_input("ΤΚ",        value=sv("τκ"))
                    notes = st.text_area("Παρατηρήσεις", value=sv("παρατηρήσεις"))

                with tab_contact:
                    c1, c2, c3 = st.columns(3)
                    with c1: tel = st.text_input("Τηλέφωνο", value=sv("τηλέφωνο"))
                    with c2: kin = st.text_input("Κινητό",   value=sv("κινητό"))
                    with c3: em  = st.text_input("Email",    value=sv("email"))

                with tab_masonic:
                    c1, c2, c3, c4 = st.columns(4)
                    with c1: am_stoas = st.text_input("ΑΜ Στοάς", value=sv("αρ_μητρώου_στοάς"))
                    with c2: am_ms    = st.text_input("ΑΜ ΜΣ",   value=sv("αρ_μητρώου_μσ"))
                    with c3:
                        deg_idx = ΒΑΘΜΟΙ.index(m.get("τεκτονικός_βαθμός","Μαθητής")) if m.get("τεκτονικός_βαθμός") in ΒΑΘΜΟΙ else 0
                        βαθμός = st.selectbox("Βαθμός", ΒΑΘΜΟΙ, index=deg_idx)
                    with c4:
                        kat_idx = ΚΑΤΑΣΤΑΣΕΙΣ_ΜΕΛΟΥΣ.index(m.get("κατάσταση","Ενεργός")) if m.get("κατάσταση") in ΚΑΤΑΣΤΑΣΕΙΣ_ΜΕΛΟΥΣ else 0
                        κατ = st.selectbox("Κατάσταση", ΚΑΤΑΣΤΑΣΕΙΣ_ΜΕΛΟΥΣ, index=kat_idx)

                    c1, c2, c3 = st.columns(3)
                    with c1: hm_my  = st.date_input("Ημ. Μύησης (Α')",    value=sd("ημ_μύησης"))
                    with c2: hm_et  = st.date_input("Ημ. Εταίρου (Β')",   value=sd("ημ_εταίρου"))
                    with c3: hm_did = st.date_input("Ημ. Διδασκάλου (Γ')",value=sd("ημ_διδασκάλου"))
                    stoa_myisis = st.text_input("Στοά Μύησης", value=sv("στοά_μύησης"))

                with tab_roles:
                    st.markdown("#### 🏛️ Αξίωμα Στοάς ΑΚΡΟΠΟΛΙΣ #84")
                    cur_ax_stoas = sv("αξίωμα_στοάς")
                    try:    ax_stoas_idx = ΑΞΙΩΜΑΤΑ_ΣΤΟΑΣ.index(cur_ax_stoas)
                    except: ax_stoas_idx = 0
                    ax_stoas = st.selectbox("Αξίωμα Στοάς", ΑΞΙΩΜΑΤΑ_ΣΤΟΑΣ, index=ax_stoas_idx)

                    st.markdown("#### 🏛️ Αξίωμα Μεγάλης Στοάς")
                    cur_ax_ms = sv("αξίωμα_μεγάλης_στοάς")
                    try:    ax_ms_idx = ΑΞΙΩΜΑΤΑ_ΜΣ.index(cur_ax_ms)
                    except: ax_ms_idx = 0
                    ax_ms = st.selectbox("Αξίωμα Μεγάλης Στοάς", ΑΞΙΩΜΑΤΑ_ΜΣ, index=ax_ms_idx)

                    if cur_ax_stoas or cur_ax_ms:
                        st.info(f"**Τρέχοντα αξιώματα:**  "
                                f"Στοάς: **{cur_ax_stoas or '—'}**  |  "
                                f"ΜΣ: **{cur_ax_ms or '—'}**")

                c1, c2 = st.columns(2)
                with c1: save_btn = st.form_submit_button("💾 Αποθήκευση", use_container_width=True, type="primary")
                with c2: del_btn  = st.form_submit_button("🗑️ Διαγραφή",  use_container_width=True)

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
                        "στοά_μύησης": stoa_myisis,
                        "αξίωμα_στοάς": ax_stoas,
                        "αξίωμα_μεγάλης_στοάς": ax_ms,
                        "παρατηρήσεις": notes,
                    })
                    st.success("✅ Αποθηκεύτηκε!"); st.rerun()
                if del_btn:
                    delete_member(int(sel_id))
                    st.success("🗑️ Διαγράφηκε!"); st.rerun()

# ── ΤΑΒ 4: ΚΑΡΤΕΛΑ ΜΕΛΟΥΣ (PDF) ──────────────────────────────
with tab_card:
    st.subheader("📄 Εκτύπωση Καρτέλας Αδ∴")
    st.caption("Περιλαμβάνει πλήρη στοιχεία, αξιώματα και ημερομηνίες")

    df_card = get_all_members()
    if df_card.empty:
        st.info("Δεν υπάρχουν μέλη.")
    else:
        col1, col2 = st.columns([2, 1])
        with col1:
            search_card = st.text_input("🔍 Αναζήτηση Αδ∴",
                                        placeholder="Πληκτρολογήστε επώνυμο...",
                                        key="search_card")
        with col2:
            deg_card = st.selectbox("Βαθμός", ["Όλοι"] + ΒΑΘΜΟΙ, key="deg_card")

        df_f = df_card.copy()
        if search_card:
            df_f = df_f[df_f["επώνυμο"].str.contains(search_card, case=False, na=False) |
                        df_f["όνομα"].str.contains(search_card, case=False, na=False)]
        if deg_card != "Όλοι":
            df_f = df_f[df_f["τεκτονικός_βαθμός"] == deg_card]

        if df_f.empty:
            st.warning("Δεν βρέθηκαν μέλη.")
        else:
            df_f["display"] = (
                df_f["επώνυμο"] + "  " + df_f["όνομα"] +
                "  |  " + df_f["τεκτονικός_βαθμός"].fillna("") +
                "  |  ΑΜ: " + df_f["αρ_μητρώου_στοάς"].fillna("—")
            )
            sel_card_id = st.selectbox(
                "Επιλογή Αδ∴", df_f["id"].tolist(),
                format_func=lambda x: df_f.loc[df_f["id"]==x, "display"].iloc[0],
                key="sel_card"
            )
            m_card = get_member(int(sel_card_id))
            if m_card:
                st.markdown("---")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.markdown("**Ονοματεπώνυμο**")
                    st.info(f"{m_card.get('επώνυμο','')} {m_card.get('όνομα','')}")
                    st.markdown("**Πατρώνυμο**");  st.write(m_card.get('πατρώνυμο') or '—')
                    st.markdown("**Επάγγελμα**");  st.write(m_card.get('επάγγελμα') or '—')
                with col2:
                    deg = m_card.get('τεκτονικός_βαθμός','')
                    badge = {"Μαθητής":"🔵","Εταίρος":"🟡","Διδάσκαλος":"🔴"}.get(deg,"⚪")
                    st.markdown("**Τεκτονικός Βαθμός**"); st.info(f"{badge} {deg}")
                    st.markdown("**Κατάσταση**"); st.write(m_card.get('κατάσταση') or '—')
                    st.markdown("**ΑΜ Στοάς / ΑΜ ΜΣ**")
                    st.write(f"{m_card.get('αρ_μητρώου_στοάς') or '—'} / {m_card.get('αρ_μητρώου_μσ') or '—'}")
                with col3:
                    st.markdown("**Αξίωμα Στοάς**")
                    st.write(m_card.get('αξίωμα_στοάς') or '—')
                    st.markdown("**Αξίωμα Μεγάλης Στοάς**")
                    st.write(m_card.get('αξίωμα_μεγάλης_στοάς') or '—')
                    st.markdown("**Κινητό**"); st.write(m_card.get('κινητό') or '—')

                st.markdown("---")
                from modules.pdf_gen import generate_member_card_pdf
                pdf_buf = generate_member_card_pdf(m_card)
                ep_name = m_card.get('επώνυμο','').replace(' ','_')
                on_name = m_card.get('όνομα','').replace(' ','_')
                st.download_button(
                    label=f"📄 Λήψη Καρτέλας PDF — {m_card.get('επώνυμο','')} {m_card.get('όνομα','')}",
                    data=pdf_buf,
                    file_name=f"καρτέλα_{ep_name}_{on_name}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                    type="primary"
                )

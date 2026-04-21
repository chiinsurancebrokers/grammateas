# -*- coding: utf-8 -*-
"""Σελίδα 15 — Δίπλωμα (Επεξεργάσιμο κείμενο)"""
import sys; sys.path.append("..")
import streamlit as st
import pandas as pd
from datetime import date
from modules.database import init_db, get_all_members, get_member, ΒΑΘΜΟΙ

init_db()
st.set_page_config(page_title="Δίπλωμα", page_icon="📜", layout="wide")
st.markdown("# 📜 Δημιουργία Διπλώματος")
st.caption("Επεξεργαστείτε το κείμενο ελεύθερα και δημιουργήστε PDF")

ΜΗΝΕΣ = ["","Ιανουαρίου","Φεβρουαρίου","Μαρτίου","Απριλίου","Μαΐου","Ιουνίου",
          "Ιουλίου","Αυγούστου","Σεπτεμβρίου","Οκτωβρίου","Νοεμβρίου","Δεκεμβρίου"]

ΒΑΘΜΟΣ_ΚΕΙΜ = {
    "Μαθητής":    ("εις τόν τοῦ Μαθητοῦ",                              "Μαθητοῦ"),
    "Εταίρος":    ("εις τόν τοῦ Εταίρου",                               "Εταίρου"),
    "Διδάσκαλος": ("εις τόν τοῦ Εταίρου βαθμόν\nκαί εἶτα εις τόν τοῦ", "Διδασκάλου"),
}

def fmt_date(d):
    try:
        d = pd.to_datetime(str(d))
        return f"{d.day}η μηνός {ΜΗΝΕΣ[d.month]} τοῦ ἔτους {d.year}"
    except Exception:
        return str(d)

def build_default_text(ονομα, βαθμός, ημ_str):
    βαθμ_text, βαθμ_title = ΒΑΘΜΟΣ_ΚΕΙΜ.get(βαθμός, ("εις τόν τοῦ Μαθητοῦ","Μαθητοῦ"))
    return f"""Γνωτοί πάντες
οἱ τά γράμματα τάδε ἀναγνωσόμενοι,
ὅτι ὁ ἀδελφός
{ονομα}
ὁ τὸ ἑαυτοῦ ὄνομα ἐν τῷ περιζώματι τῇ ἑαυτοῦ χειρί γεγραφώς
εἰς τήν τῶν Λατόμων ἤ Τεκτονικῶν Τεχνῶν μεμύηται
καί εἰσεληλύθεν εἰς τήν ὑπό τήν Ἡμετέραν Αἰγίδα Στοάν
τῷ ὀνόματι μέν Ἀκρόπολις ὑπό ἀριθμόν 84 δέ.
Οὗτος τόν νενομισμένον χρόνον ἀνύσας καί δοκιμασθείς
καί ἐξετασθείς, {βαθμ_text}

--- ΤΙΤΛΟΣ ΒΑΘΜΟΥ ---
{βαθμ_title}

--- ΣΥΝΕΧΕΙΑ ---
ἀναδέδεκται ἐν τῇ τῆς Στοᾶς συνεδρίᾳ τῇ γενομένῃ
ἐν ἡμέρᾳ μέν {ημ_str}.
Τό ὄνομα αὐτοῦ ἐν ταῖς Ἐπισήμοις Πράξεσι
τῆς Μεγάλης Στοᾶς τῆς Ἑλλάδος
ἀναγέγραπται καί τοῦτο, οὕτω δή γενόμενον,
δηλοῦται τῷ Διπλώματι τῷδε
οὐ μόνον τοῖς Ἡμετέροις αὐτογράφοις,
ἀλλά καί τῇ Σφραγῖδι τῆς Μεγάλης Στοᾶς κεκυρωμένον.
Πίστευε δ' ὅτι, οὐδείς, εἰ μή πρότερον δοκιμασθείς
καί ἐξετασθείς, ἔξεστιν εἰσελθεῖν
εἰς Λατόμον ἤ Τεκτονικήν Στοάν"""

# ── ΣΤΗΛΕΣ ──────────────────────────────────────────────────
col_left, col_right = st.columns([1, 1], gap="large")

with col_left:
    st.subheader("⚙️ Στοιχεία")

    # Επιλογή μέλους
    df_all = get_all_members()
    if df_all.empty:
        st.warning("Δεν υπάρχουν μέλη."); st.stop()

    search = st.text_input("🔍 Αναζήτηση Αδ∴", placeholder="Επώνυμο...")
    df_f = df_all.copy()
    if search:
        df_f = df_f[df_f["επώνυμο"].str.contains(search, case=False, na=False) |
                    df_f["όνομα"].str.contains(search, case=False, na=False)]

    df_f["display"] = df_f["επώνυμο"] + "  " + df_f["όνομα"] + \
                      "   |  " + df_f["τεκτονικός_βαθμός"].fillna("")
    sel_id = st.selectbox("Αδ∴",
                          df_f["id"].tolist(),
                          format_func=lambda x: df_f.loc[df_f["id"]==x,"display"].iloc[0])
    m = get_member(int(sel_id))

    c1, c2 = st.columns(2)
    with c1:
        βαθμός = st.selectbox("Βαθμός Διπλώματος", ΒΑΘΜΟΙ,
                               index=ΒΑΘΜΟΙ.index(m.get("τεκτονικός_βαθμός","Μαθητής"))
                               if m.get("τεκτονικός_βαθμός") in ΒΑΘΜΟΙ else 0)
    with c2:
        def _auto_date(m, β):
            if β == "Μαθητής": return m.get("ημ_μύησης","")
            if β == "Εταίρος": return m.get("ημ_εταίρου","")
            return m.get("ημ_διδασκάλου","")
        auto_d = _auto_date(m, βαθμός)
        try:    default_d = pd.to_datetime(auto_d).date() if auto_d else date.today()
        except: default_d = date.today()
        ημ = st.date_input("Ημερομηνία Ανάδειξης", value=default_d)

    watermark = st.checkbox("Ένδειξη 'ΑΝΤΙΓΡΑΦΟ ΑΡΧΕΙΟΥ'", value=True)

    st.markdown("---")
    st.subheader("✍️ Υπογράφοντες")
    c1, c2 = st.columns(2)
    with c1:
        sig1_title = st.text_input("Τίτλος 1ου υπογράφοντος",
                                    value="ο Μέγας Διδάσκαλος")
        sig1_name  = st.text_input("Όνομα 1ου υπογράφοντος",
                                    value="Γεώργιος Μπινιάρης")
    with c2:
        sig2_title = st.text_input("Τίτλος 2ου υπογράφοντος",
                                    value="ο Μέγας Γραμματεύς")
        sig2_name  = st.text_input("Όνομα 2ου υπογράφοντος",
                                    value="Ανδρέας Αρχουζής")

    st.markdown("---")
    st.subheader("✏️ Κείμενο Διπλώματος")
    st.caption("Επεξεργαστείτε ελεύθερα. Χρησιμοποιήστε τα markers --- για δομή.")

    ονομα = f"{m.get('επώνυμο','')} {m.get('όνομα','')}".strip()
    ημ_str = fmt_date(ημ)

    # Κουμπί reset στο default κείμενο
    if st.button("🔄 Επαναφορά Προεπιλεγμένου Κειμένου", use_container_width=True):
        st.session_state["diploma_text"] = build_default_text(ονομα, βαθμός, ημ_str)
        st.session_state["diploma_member"] = sel_id
        st.session_state["diploma_βαθμός"] = βαθμός
        st.rerun()

    # Αν άλλαξε μέλος ή βαθμός → reset κειμένου
    prev_m = st.session_state.get("diploma_member")
    prev_β = st.session_state.get("diploma_βαθμός")
    if prev_m != sel_id or prev_β != βαθμός:
        st.session_state["diploma_text"] = build_default_text(ονομα, βαθμός, ημ_str)
        st.session_state["diploma_member"] = sel_id
        st.session_state["diploma_βαθμός"] = βαθμός

    diploma_text = st.text_area(
        "Κείμενο:",
        value=st.session_state.get("diploma_text", build_default_text(ονομα, βαθμός, ημ_str)),
        height=520,
        key="diploma_text_area",
        label_visibility="collapsed"
    )
    st.session_state["diploma_text"] = diploma_text

    st.markdown("---")
    st.caption("""**Οδηγός markers:**
- Κείμενο πριν `--- ΤΙΤΛΟΣ ΒΑΘΜΟΥ ---` → εισαγωγικές παράγραφοι (italic)
- `--- ΤΙΤΛΟΣ ΒΑΘΜΟΥ ---` → ο τίτλος σε επόμενη γραμμή (μεγάλα, bold)
- `--- ΣΥΝΕΧΕΙΑ ---` → συνέχεια κειμένου (italic)
- Κενή γραμμή → μικρό κενό
""")

with col_right:
    st.subheader("👁️ Προεπισκόπηση & Εξαγωγή")

    # Preview κειμένου
    lines = diploma_text.split("\n")
    preview_html = '<div style="font-family:Georgia,serif; font-size:13px; line-height:1.8; text-align:center; padding:20px; background:#faf7f0; border:2px solid #b8960c; border-radius:8px;">'
    preview_html += f'<p style="font-size:10px;color:#888;">Ε.Λ.Τ.Μ.Α.Τ.Σ.</p>'
    preview_html += f'<p style="font-size:16px;font-weight:bold;color:#1a2a4a;">ΜΕΓΑΛΗ ΣΤΟΑ ΤΗΣ ΕΛΛΑΔΟΣ</p>'
    preview_html += f'<p style="font-size:11px;color:#1a2a4a;font-style:italic;">Ἀρχαίου Ἐλευθέρου καὶ Ἀποδεδεγμένου Τεκτονισμοῦ</p>'
    preview_html += '<hr style="border-color:#b8960c;">'

    in_title = False
    in_cont  = False
    title_next = False

    for line in lines:
        stripped = line.strip()
        if stripped == "--- ΤΙΤΛΟΣ ΒΑΘΜΟΥ ---":
            title_next = True
            continue
        elif stripped == "--- ΣΥΝΕΧΕΙΑ ---":
            title_next = False
            in_cont = True
            continue
        elif title_next and stripped:
            preview_html += f'<p style="font-size:22px;font-weight:bold;color:#1a2a4a;margin:8px 0;">{stripped}</p>'
            title_next = False
            continue
        elif not stripped:
            preview_html += '<br>'
        else:
            # Έλεγχος αν είναι το όνομα (εμφανίζεται bold μεγάλο)
            if stripped == ονομα:
                preview_html += f'<p style="font-size:17px;font-weight:bold;color:#1a2a4a;margin:6px 0;">{stripped}</p>'
            else:
                preview_html += f'<p style="font-style:italic;color:#333;margin:2px 0;">{stripped}</p>'

    preview_html += f'<hr style="border-color:#b8960c;margin-top:12px;">'
    preview_html += f'<p style="font-style:italic;color:#1a2a4a;">Ἐν Ἀνατολῇ Ἀθηνῶν τῇ {ημ_str[:ημ_str.find(" τοῦ")] if " τοῦ" in ημ_str else ημ_str}</p>'
    preview_html += '<div style="display:flex;justify-content:space-between;margin-top:20px;padding:0 20px;">'
    preview_html += f'<div style="text-align:center;width:40%;"><div style="border-top:1px solid #333;padding-top:4px;font-size:11px;">{sig1_title}<br/>{sig1_name}</div></div>'
    preview_html += f'<div style="text-align:center;width:40%;"><div style="border-top:1px solid #333;padding-top:4px;font-size:11px;">{sig2_title}<br/>{sig2_name}</div></div>'
    preview_html += '</div></div>'

    st.markdown(preview_html, unsafe_allow_html=True)

    st.markdown("---")

    if st.button("📄 Δημιουργία PDF", type="primary", use_container_width=True):
        from modules.pdf_gen import generate_diploma_custom_pdf
        pdf_buf = generate_diploma_custom_pdf(
            member=m,
            text=diploma_text,
            ημ_βαθμού=str(ημ),
            watermark=watermark,
            sig1_title=sig1_title,
            sig1_name=sig1_name,
            sig2_title=sig2_title,
            sig2_name=sig2_name,
        )
        ep = m.get('επώνυμο','').replace(' ','_')
        on = m.get('όνομα','').replace(' ','_')
        st.download_button(
            f"⬇️ Λήψη PDF — {m.get('επώνυμο','')} {m.get('όνομα','')} ({βαθμός})",
            data=pdf_buf,
            file_name=f"δίπλωμα_{ep}_{on}_{βαθμός}.pdf",
            mime="application/pdf",
            use_container_width=True
        )

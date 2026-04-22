# -*- coding: utf-8 -*-
"""Σελίδα 15 — Δίπλωμα (Πλήρως επεξεργάσιμο)"""
import sys; sys.path.append("..")
import streamlit as st
import pandas as pd
from datetime import date
from modules.database import init_db, get_all_members, get_member, ΒΑΘΜΟΙ

init_db()
st.set_page_config(page_title="Δίπλωμα", page_icon="📜", layout="wide")
st.markdown("# 📜 Δημιουργία Διπλώματος")
st.caption("Πλήρης επεξεργασία κεφαλίδας, κειμένου και υπογραφόντων")

ΜΗΝΕΣ = ["","Ιανουαρίου","Φεβρουαρίου","Μαρτίου","Απριλίου","Μαΐου","Ιουνίου",
          "Ιουλίου","Αυγούστου","Σεπτεμβρίου","Οκτωβρίου","Νοεμβρίου","Δεκεμβρίου"]

ΒΑΘΜΟΣ_ΚΕΙΜ = {
    "Μαθητής":    ("εις τόν τοῦ Μαθητοῦ",                               "Μαθητοῦ"),
    "Εταίρος":    ("εις τόν τοῦ Εταίρου",                                "Εταίρου"),
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

# ── ΑΡΙΣΤΕΡΑ: ΕΠΕΞΕΡΓΑΣΙΑ ────────────────────────────────────
col_left, col_right = st.columns([1, 1], gap="large")

with col_left:

    # ── Μέλος & Βαθμός ──────────────────────────────────────
    st.subheader("⚙️ Στοιχεία")
    df_all = get_all_members()
    if df_all.empty:
        st.warning("Δεν υπάρχουν μέλη."); st.stop()

    search = st.text_input("🔍 Αναζήτηση Αδ∴", placeholder="Επώνυμο...")
    df_f = df_all.copy()
    if search:
        df_f = df_f[df_f["επώνυμο"].str.contains(search, case=False, na=False) |
                    df_f["όνομα"].str.contains(search, case=False, na=False)]

    df_f["display"] = (df_f["επώνυμο"] + "  " + df_f["όνομα"] +
                       "  |  " + df_f["τεκτονικός_βαθμός"].fillna(""))
    sel_id = st.selectbox("Αδ∴", df_f["id"].tolist(),
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

    # ── Κεφαλίδα ─────────────────────────────────────────────
    st.markdown("---")
    st.subheader("🏛️ Κεφαλίδα Διπλώματος")

    hdr1 = st.text_input("Γραμμή 1 (Συντομογραφία)",
                          value=st.session_state.get("dip_hdr1","Ε.Λ.Τ.Μ.Α.Τ.Σ."),
                          key="dip_hdr1")
    hdr2 = st.text_input("Γραμμή 2 (Τίτλος)",
                          value=st.session_state.get("dip_hdr2","ΜΕΓΑΛΗ ΣΤΟΑ ΤΗΣ ΕΛΛΑΔΟΣ"),
                          key="dip_hdr2")
    hdr3 = st.text_input("Γραμμή 3 (Υπότιτλος — italic)",
                          value=st.session_state.get("dip_hdr3","Ἀρχαίου Ἐλευθέρου καὶ Ἀποδεδεγμένου Τεκτονισμοῦ"),
                          key="dip_hdr3")

    # ── Υπογράφοντες ─────────────────────────────────────────
    st.markdown("---")
    st.subheader("✍️ Υπογράφοντες")
    c1, c2 = st.columns(2)
    with c1:
        sig1_title = st.text_input("Τίτλος 1ου", value="ο Μέγας Διδάσκαλος")
        sig1_name  = st.text_input("Όνομα 1ου",  value="Γεώργιος Μπινιάρης")
    with c2:
        sig2_title = st.text_input("Τίτλος 2ου", value="ο Μέγας Γραμματεύς")
        sig2_name  = st.text_input("Όνομα 2ου",  value="Ανδρέας Αρχουζής")

    # ── Κείμενο ──────────────────────────────────────────────
    st.markdown("---")
    st.subheader("✏️ Κείμενο Διπλώματος")
    st.caption("Χρησιμοποιήστε τα markers για δομή (βλ. οδηγό κάτω).")

    ονομα  = f"{m.get('επώνυμο','')} {m.get('όνομα','')}".strip()
    ημ_str = fmt_date(ημ)

    # Reset αν αλλάξει μέλος ή βαθμός
    prev_m = st.session_state.get("diploma_member")
    prev_β = st.session_state.get("diploma_βαθμός")
    if prev_m != sel_id or prev_β != βαθμός:
        st.session_state["diploma_text"] = build_default_text(ονομα, βαθμός, ημ_str)
        st.session_state["diploma_member"] = sel_id
        st.session_state["diploma_βαθμός"] = βαθμός

    col_r1, col_r2 = st.columns(2)
    with col_r1:
        if st.button("🔄 Επαναφορά Κειμένου", use_container_width=True):
            st.session_state["diploma_text"] = build_default_text(ονομα, βαθμός, ημ_str)
            st.rerun()
    with col_r2:
        if st.button("🔄 Επαναφορά Κεφαλίδας", use_container_width=True):
            for k,v in [("dip_hdr1","Ε.Λ.Τ.Μ.Α.Τ.Σ."),
                        ("dip_hdr2","ΜΕΓΑΛΗ ΣΤΟΑ ΤΗΣ ΕΛΛΑΔΟΣ"),
                        ("dip_hdr3","Ἀρχαίου Ἐλευθέρου καὶ Ἀποδεδεγμένου Τεκτονισμοῦ")]:
                st.session_state[k] = v
            st.rerun()

    diploma_text = st.text_area(
        "Κείμενο:",
        value=st.session_state.get("diploma_text", build_default_text(ονομα, βαθμός, ημ_str)),
        height=480,
        key="diploma_text_area",
        label_visibility="collapsed"
    )
    st.session_state["diploma_text"] = diploma_text

    with st.expander("📖 Οδηγός markers"):
        st.markdown("""
| Marker | Αποτέλεσμα |
|--------|-----------|
| `--- ΤΙΤΛΟΣ ΒΑΘΜΟΥ ---` | Η επόμενη γραμμή → μεγάλος bold τίτλος βαθμού |
| `--- ΣΥΝΕΧΕΙΑ ---` | Συνέχεια κανονικού italic κειμένου |
| Κενή γραμμή | Κενό διάστημα |
| Γραμμή = ονοματεπώνυμο | Αυτόματα bold + μεγάλο |
""")

# ── ΔΕΞΙΑ: PREVIEW & PDF ─────────────────────────────────────
with col_right:
    st.subheader("👁️ Προεπισκόπηση")

    # Live HTML preview
    lines = diploma_text.split("\n")
    title_next = False
    body_html = ""
    for line in lines:
        stripped = line.strip()
        if stripped == "--- ΤΙΤΛΟΣ ΒΑΘΜΟΥ ---":
            title_next = True; continue
        elif stripped == "--- ΣΥΝΕΧΕΙΑ ---":
            title_next = False; continue
        elif title_next and stripped:
            body_html += f'<p style="font-size:20px;font-weight:bold;color:#1a2a4a;margin:8px 0;">{stripped}</p>'
            title_next = False
        elif not stripped:
            body_html += "<br>"
        elif stripped == ονομα:
            body_html += f'<p style="font-size:16px;font-weight:bold;color:#1a2a4a;margin:6px 0;">{stripped}</p>'
        else:
            body_html += f'<p style="font-style:italic;color:#333;margin:1px 0;font-size:12px;">{stripped}</p>'

    # Ημερομηνία σύντομα
    ημ_short = ημ_str.replace(" τοῦ ἔτους"," ").strip()

    preview_html = f"""
    <div style="font-family:Georgia,serif;line-height:1.7;text-align:center;
                padding:18px 16px;background:#faf7f0;border:2px solid #b8960c;
                border-radius:8px;max-height:620px;overflow-y:auto;">
      <p style="font-size:9px;color:#999;letter-spacing:2px;">{hdr1}</p>
      <div style="border-top:1.5px solid #b8960c;border-bottom:1.5px solid #b8960c;
                  padding:4px 0;margin:4px 0;">
        <p style="font-size:15px;font-weight:bold;color:#1a2a4a;margin:2px 0;">{hdr2}</p>
        <p style="font-size:10px;color:#1a2a4a;font-style:italic;margin:2px 0;">{hdr3}</p>
      </div>
      <div style="margin:12px 0;">{body_html}</div>
      <hr style="border-color:#b8960c;margin:10px 0;">
      <p style="font-style:italic;color:#1a2a4a;font-size:11px;">Ἐν Ἀνατολῇ Ἀθηνῶν τῇ {ημ_short}</p>
      <div style="display:flex;justify-content:space-around;margin-top:16px;">
        <div style="text-align:center;width:42%;">
          <div style="border-top:1px solid #333;padding-top:3px;font-size:10px;">
            {sig1_title}<br/><strong>{sig1_name}</strong>
          </div>
        </div>
        <div style="text-align:center;width:42%;">
          <div style="border-top:1px solid #333;padding-top:3px;font-size:10px;">
            {sig2_title}<br/><strong>{sig2_name}</strong>
          </div>
        </div>
      </div>
    </div>"""
    st.markdown(preview_html, unsafe_allow_html=True)

    st.markdown("---")

    if st.button("📄 Δημιουργία & Λήψη PDF", type="primary", use_container_width=True):
        from modules.pdf_gen import generate_diploma_custom_pdf
        pdf_buf = generate_diploma_custom_pdf(
            member=m,
            text=diploma_text,
            ημ_βαθμού=str(ημ),
            watermark=watermark,
            sig1_title=sig1_title, sig1_name=sig1_name,
            sig2_title=sig2_title, sig2_name=sig2_name,
            hdr1=hdr1, hdr2=hdr2, hdr3=hdr3,
        )
        ep = m.get("επώνυμο","").replace(" ","_")
        on = m.get("όνομα","").replace(" ","_")
        st.download_button(
            f"⬇️ Λήψη PDF — {m.get('επώνυμο','')} {m.get('όνομα','')} ({βαθμός})",
            data=pdf_buf,
            file_name=f"δίπλωμα_{ep}_{on}_{βαθμός}.pdf",
            mime="application/pdf",
            use_container_width=True
        )

# -*- coding: utf-8 -*-
"""
Σελίδα 13 — Plaud NotePIN Integration
Ανέβασμα περίληψης → Claude AI → Επίσημα Πρακτικά ΜΣΤΕ
"""
import sys; sys.path.append("..")
import streamlit as st
import json
from datetime import date, time
from modules.database import init_db, save_session, get_sessions, ΒΑΘΜΟΙ

init_db()
st.set_page_config(page_title="Plaud AI", page_icon="🎙️", layout="wide")

st.markdown("# 🎙️ Plaud NotePIN → Πρακτικά")
st.caption("Ανεβάστε την περίληψη από το Plaud app · Claude AI τη μετατρέπει σε επίσημα πρακτικά ΜΣΤΕ")

# ── TABS ──────────────────────────────────────────────────────
tab_upload, tab_result, tab_templates = st.tabs([
    "📤 Ανέβασμα Περίληψης",
    "📄 Επεξεργασία & Αποθήκευση",
    "📋 Πρότυπα Πρακτικών",
])

# ── SYSTEM PROMPT για Claude ──────────────────────────────────
SYSTEM_PROMPT = """Είσαι βοηθός Γραμματέα-Σφραγιδοφύλακα της Στοάς ΑΚΡΟΠΟΛΙΣ υπ' αρ. 84 (ΜΣΤΕ).

Μετατρέπεις περιλήψεις/σημειώσεις συνεδριάσεων σε επίσημα Πρακτικά στυλ ΜΣΤΕ.

Κανόνες:
- Χρησιμοποίησε τεκτονική ορολογία: Σεβ∴ Διδ∴, Αδ∴, Σ∴ Στ∴, Βαθμ∴ Μαθ∴/Ετ∴/Διδ∴ κλπ.
- Γράψε σε επίσημο αρχαιοπρεπές ύφος (όπως το δείγμα: «ανοίγουν αι Εργασίαι», «Παρόντες είναι», κλπ.)
- Δομή: Έναρξη → Αλληλογραφία → Ομιλίες/Εργασίες → Αποφάσεις → Κορμός Αγαθοεργίας → Κλείσιμο

Επίστρεψε ΜΟΝΟ ένα JSON αντικείμενο με αυτά τα πεδία (χωρίς backticks):
{
  "ημερομηνία": "YYYY-MM-DD",
  "βαθμός": "Μαθητής" ή "Εταίρος" ή "Διδάσκαλος",
  "τόπος": "...",
  "ώρα": "HH:MM",
  "πλήθος_παρόντων": 0,
  "αλληλογραφία": ["item1", "item2"],
  "ομιλίες": ["Πλήρης παράγραφος περιγραφής ομιλίας 1", "..."],
  "αποφάσεις": ["Απόφαση 1", "..."],
  "κορμός_αγαθοεργίας": 0.0,
  "κορμός_ολογράφως": "Είκοσι",
  "παρατηρήσεις": "..."
}"""


def call_claude(prompt: str) -> str:
    """Κλήση Claude API."""
    try:
        import anthropic
        api_key = st.secrets.get("AI", {}).get("ANTHROPIC_API_KEY") or \
                  st.secrets.get("ANTHROPIC_API_KEY", "")
        if not api_key:
            return None, "❌ Δεν βρέθηκε ANTHROPIC_API_KEY στα Streamlit Secrets."

        client = anthropic.Anthropic(api_key=api_key)
        msg = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2000,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}]
        )
        text = msg.content[0].text if msg.content else ""
        return text, None
    except ImportError:
        return None, "❌ Προσθέστε 'anthropic' στο requirements.txt"
    except Exception as e:
        return None, f"❌ Σφάλμα AI: {e}"


# ── TAB 1: UPLOAD ─────────────────────────────────────────────
with tab_upload:
    st.markdown("""
    ### Πώς λειτουργεί:
    1. 🎙️ Καταγράφετε τη συνεδρίαση με το **Plaud NotePIN**
    2. 📱 Στο Plaud app → Summary → Αντιγράψτε το κείμενο
    3. 📋 Επικολλήστε παρακάτω → **Δημιουργία Πρακτικών**
    4. ✏️ Ελέγξτε, επεξεργαστείτε → 💾 Αποθηκεύστε + 📄 PDF
    """)

    st.markdown("---")

    col1, col2 = st.columns([2, 1])

    with col1:
        # Επιλογή εισόδου
        input_mode = st.radio(
            "Τρόπος εισαγωγής:",
            ["📋 Επικόλληση κειμένου (Plaud Summary)", "📁 Ανέβασμα αρχείου .txt"],
            horizontal=True
        )

        if input_mode == "📋 Επικόλληση κειμένου (Plaud Summary)":
            plaud_text = st.text_area(
                "Επικολλήστε την περίληψη από το Plaud app:",
                height=300,
                placeholder="""Παράδειγμα εισόδου:
Meeting date: 5 March 2024
Degree: First
Attendees: 14 brothers
Topics: Increase in salary for two brothers, 
        Presentation by Bro. Karamanou on Ethics,
        Speech by Secretary on Homer's Odyssey...
Charity collection: 20 euros
..."""
            )
        else:
            uploaded = st.file_uploader("Ανεβάστε αρχείο .txt:", type=["txt", "md"])
            plaud_text = uploaded.read().decode("utf-8") if uploaded else ""
            if plaud_text:
                st.text_area("Περιεχόμενο:", plaud_text, height=200, disabled=True)

    with col2:
        st.markdown("**Συμπληρωματικά στοιχεία:**")
        sup_date = st.date_input("Ημερομηνία Συνεδρίασης", value=date.today())
        sup_deg  = st.selectbox("Βαθμός", ΒΑΘΜΟΙ)
        sup_ora  = st.time_input("Ώρα", value=time(19, 0))
        sup_topos = st.text_input("Τόπος", value="τον Τεκτ∴ Ναόν Απόλλων, Τεκτ∴ Μεγάρου Αθηνών")
        sup_plithos = st.number_input("Αριθμός Παρόντων", min_value=0, step=1)

        st.markdown("---")
        st.info("💡 Τα συμπληρωματικά στοιχεία χρησιμοποιούνται αν δεν υπάρχουν στο κείμενο.")

    if st.button("🤖 Δημιουργία Πρακτικών με AI", type="primary",
                 use_container_width=True, disabled=not plaud_text):
        with st.spinner("Claude AI επεξεργάζεται το κείμενο..."):
            prompt = f"""Μετέτρεψε αυτή την περίληψη συνεδρίασης σε επίσημα Πρακτικά ΜΣΤΕ.

Συμπληρωματικά στοιχεία (χρησιμοποίησέ τα αν λείπουν από το κείμενο):
- Ημερομηνία: {sup_date}
- Βαθμός: {sup_deg}
- Ώρα: {sup_ora}
- Τόπος: {sup_topos}
- Παρόντες: {sup_plithos if sup_plithos else "δεν γνωρίζω"}

ΚΕΙΜΕΝΟ PLAUD:
{plaud_text}"""

            result, error = call_claude(prompt)

            if error:
                st.error(error)
            else:
                # Parse JSON
                try:
                    # Καθαρισμός αν υπάρχουν backticks
                    clean = result.strip().strip("```json").strip("```").strip()
                    data = json.loads(clean)
                    st.session_state["plaud_result"] = data
                    st.session_state["plaud_raw"] = result
                    st.success("✅ Τα πρακτικά δημιουργήθηκαν! Πηγαίνετε στην καρτέλα **Επεξεργασία & Αποθήκευση**.")
                except json.JSONDecodeError:
                    # Αν δεν είναι valid JSON, αποθηκεύουμε το raw
                    st.warning("⚠️ Το AI επέστρεψε κείμενο (όχι JSON). Μπορείτε να το επεξεργαστείτε χειροκίνητα.")
                    st.session_state["plaud_result"] = None
                    st.session_state["plaud_raw"] = result
                    with st.expander("📄 Κείμενο AI (για χειροκίνητη αντιγραφή)"):
                        st.write(result)

# ── TAB 2: ΑΠΟΤΕΛΕΣΜΑ & ΑΠΟΘΗΚΕΥΣΗ ──────────────────────────
with tab_result:
    data = st.session_state.get("plaud_result")

    if not data:
        st.info("👈 Πρώτα ανεβάστε περίληψη στην καρτέλα **Ανέβασμα Περίληψης**")
    else:
        st.success("✅ Τα πρακτικά είναι έτοιμα για επεξεργασία!")
        st.markdown("---")

        with st.form("plaud_save_form"):
            st.subheader("📝 Επαλήθευση & Επεξεργασία Πρακτικών")

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                import pandas as pd
                try: hm = pd.to_datetime(data.get("ημερομηνία","")).date()
                except: hm = date.today()
                ημερ = st.date_input("Ημερομηνία", value=hm)
            with col2:
                deg = data.get("βαθμός","Μαθητής")
                deg_idx = ΒΑΘΜΟΙ.index(deg) if deg in ΒΑΘΜΟΙ else 0
                βαθμός = st.selectbox("Βαθμός", ΒΑΘΜΟΙ, index=deg_idx)
            with col3:
                ωρα = st.text_input("Ώρα", value=data.get("ώρα","19:00"))
            with col4:
                plith = st.number_input("Παρόντες", value=int(data.get("πλήθος_παρόντων") or 0), min_value=0)

            topos = st.text_input("Τόπος", value=data.get("τόπος",""))

            st.markdown("**Αλληλογραφία / Ημερησία Διάταξη** *(μία ανά γραμμή)*")
            allilogr_val = "\n".join(data.get("αλληλογραφία") or [])
            allilogr = st.text_area("", value=allilogr_val, height=100, key="al")

            st.markdown("**Ομιλίες & Εργασίες** *(μία ανά γραμμή)*")
            omilies_val = "\n".join(data.get("ομιλίες") or [])
            omilies = st.text_area("", value=omilies_val, height=150, key="om")

            st.markdown("**Αποφάσεις** *(μία ανά γραμμή)*")
            apof_val = "\n".join(data.get("αποφάσεις") or [])
            apof = st.text_area("", value=apof_val, height=100, key="ap")

            col1, col2 = st.columns(2)
            with col1: kormos = st.number_input("Κορμός (€)", value=float(data.get("κορμός_αγαθοεργίας") or 0), step=0.01)
            with col2: kormos_olog = st.text_input("Ολογράφως", value=data.get("κορμός_ολογράφως",""))

            notes = st.text_area("Παρατηρήσεις", value=data.get("παρατηρήσεις",""), height=80)

            col1, col2 = st.columns(2)
            with col1: save_btn = st.form_submit_button("💾 Αποθήκευση Πρακτικών", use_container_width=True, type="primary")
            with col2: pdf_preview = st.form_submit_button("📄 Αποθήκευση + Λήψη PDF", use_container_width=True)

            if save_btn or pdf_preview:
                session_data = {
                    "ημερομηνία": str(ημερ), "βαθμός": βαθμός, "ώρα": ωρα, "τόπος": topos,
                    "πλήθος_παρόντων": plith,
                    "αλληλογραφία": [x.strip() for x in allilogr.splitlines() if x.strip()],
                    "ομιλίες":      [x.strip() for x in omilies.splitlines() if x.strip()],
                    "αποφάσεις":    [x.strip() for x in apof.splitlines() if x.strip()],
                    "κορμός_αγαθοεργίας": kormos, "κορμός_ολογράφως": kormos_olog,
                    "παρατηρήσεις": notes,
                }
                sid = save_session(session_data)
                st.success(f"✅ Πρακτικά αποθηκεύτηκαν (ID #{sid})!")

                if pdf_preview:
                    from modules.pdf_gen import generate_minutes_pdf
                    pdf_buf = generate_minutes_pdf(session_data)
                    st.download_button(
                        "⬇️ Λήψη PDF Πρακτικών",
                        data=pdf_buf,
                        file_name=f"πρακτικά_{str(ημερ)}_{βαθμός}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                st.session_state["plaud_result"] = None

# ── TAB 3: ΠΡΟΤΥΠΑ ───────────────────────────────────────────
with tab_templates:
    st.subheader("📋 Πρότυπα Πρακτικών για PDF")
    st.markdown("Επιλέξτε υπάρχουσα συνεδρίαση και δημιουργήστε PDF στην επίσημη μορφή ΜΣΤΕ.")

    df = get_sessions()
    if df.empty:
        st.info("Δεν υπάρχουν συνεδριάσεις.")
    else:
        from modules.database import get_session, get_attendance
        sel_id = st.selectbox(
            "Συνεδρίαση:",
            df["id"].tolist(),
            format_func=lambda x: f"#{x} — {df.loc[df['id']==x,'ημερομηνία'].values[0]} ({df.loc[df['id']==x,'βαθμός'].values[0]})"
        )

        s = get_session(int(sel_id))
        att = get_attendance(int(sel_id))
        attendance_names = list(att["fullname"]) if not att.empty else []
        dik_names = list(att[att["δικαιολογήθηκε"]==1]["fullname"]) if not att.empty else []

        col1, col2 = st.columns(2)
        with col1:
            if st.button("📄 Λήψη PDF Πρακτικών", use_container_width=True, type="primary"):
                from modules.pdf_gen import generate_minutes_pdf
                pdf_buf = generate_minutes_pdf(
                    s,
                    attendance_list=attendance_names,
                    dikaiologithentes=dik_names,
                )
                st.download_button(
                    "⬇️ Λήψη PDF",
                    data=pdf_buf,
                    file_name=f"πρακτικά_{s['ημερομηνία']}_{s['βαθμός']}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )

        # Preview
        with st.expander("👁️ Προεπισκόπηση περιεχομένου"):
            st.markdown(f"**{s['ημερομηνία']} | {s['βαθμός']} | Παρόντες: {s.get('πλήθος_παρόντων',0)}**")
            if s.get("αλληλογραφία"):
                st.markdown("*Αλληλογραφία:*")
                for i in s["αλληλογραφία"]: st.write(f"• {i}")
            if s.get("ομιλίες"):
                st.markdown("*Ομιλίες:*")
                for i in s["ομιλίες"]: st.write(f"• {i}")
            if s.get("αποφάσεις"):
                st.markdown("*Αποφάσεις:*")
                for i in s["αποφάσεις"]: st.write(f"• {i}")
            st.markdown(f"**Κορμός: {s.get('κορμός_αγαθοεργίας',0):.2f}€** ({s.get('κορμός_ολογράφως','')})")

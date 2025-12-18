import streamlit as st
from pathlib import Path
import sys
import pandas as pd
from datetime import date

sys.path.append(str(Path(__file__).resolve().parents[1]))

from modules.database import get_database

st.set_page_config(page_title="Επεξεργασία Μέλους", page_icon="👤", layout="wide")

st.markdown("""
<style>
.main-header {font-size: 2.2rem; font-weight: 800; color: #1f4788; padding: 1rem; background: linear-gradient(90deg, #f0f2f6 0%, #ffffff 100%); border-radius: 12px; margin-bottom: 1.5rem;}
.section {padding: 0.75rem 1rem; border: 1px solid #e9ecef; border-radius: 12px; background: #fff;}
</style>
""", unsafe_allow_html=True)

db = get_database()

st.markdown('<div class="main-header">👤 Επεξεργασία Μέλους</div>', unsafe_allow_html=True)

# -------- helpers --------
def _safe(v, default=""):
    return default if v is None else v

def _parse_date(v):
    if not v:
        return None
    try:
        return pd.to_datetime(v).date()
    except Exception:
        return None

def _to_iso(d):
    if d is None:
        return None
    if isinstance(d, date):
        return d.isoformat()
    return str(d)

def _normalize_degree(v: str) -> str:
    if not v:
        return "Μαθητής"
    v = str(v).strip()
    if v == "Δάσκαλος":
        return "Διδάσκαλος"
    return v

# -------- select member --------
df = db.get_all_members()
if df is None or len(df) == 0:
    st.info("Δεν βρέθηκαν μέλη στη βάση.")
    st.stop()

df["display"] = df["last_name"].fillna("").astype(str) + " " + df["first_name"].fillna("").astype(str) + "  (ID: " + df["member_id"].astype(str) + ")"
selected_id = st.selectbox("Επιλογή Μέλους", df["member_id"].tolist(), format_func=lambda x: df.loc[df["member_id"] == x, "display"].iloc[0])

member = db.get_member_by_id(int(selected_id)) or {}
member["current_degree"] = _normalize_degree(member.get("current_degree", "Μαθητής"))

st.markdown("---")

with st.form("edit_member_form", clear_on_submit=False):
    # =====================
    # PERSONAL
    # =====================
    st.subheader("🧾 Προσωπικά Στοιχεία")
    c1, c2, c3 = st.columns(3)
    with c1:
        last_name = st.text_input("Επώνυμο", value=_safe(member.get("last_name")))
        fathers_name = st.text_input("Πατρώνυμο", value=_safe(member.get("fathers_name")))
        profession = st.text_input("Επάγγελμα", value=_safe(member.get("profession")))
    with c2:
        first_name = st.text_input("Όνομα", value=_safe(member.get("first_name")))
        birth_date = st.date_input("Ημ/νία Γέννησης", value=_parse_date(member.get("birth_date")))
        birth_place = st.text_input("Τόπος Γέννησης", value=_safe(member.get("birth_place")))
    with c3:
        # υποστήριξη και για tax_id και για afm (για συμβατότητα)
        afm = st.text_input("ΑΦΜ", value=_safe(member.get("tax_id") or member.get("afm")))
        id_number = st.text_input("Αρ. Ταυτότητας", value=_safe(member.get("id_number")))

    # =====================
    # CONTACT
    # =====================
    st.subheader("📞 Στοιχεία Επικοινωνίας")
    c1, c2, c3 = st.columns(3)
    with c1:
        address = st.text_input("Διεύθυνση", value=_safe(member.get("address")))
        city = st.text_input("Πόλη", value=_safe(member.get("city")))
    with c2:
        postal_code = st.text_input("ΤΚ", value=_safe(member.get("postal_code")))
        home_phone = st.text_input("Τηλ. Οικίας", value=_safe(member.get("home_phone")))
    with c3:
        mobile_phone = st.text_input("Κινητό", value=_safe(member.get("mobile_phone")))
        email = st.text_input("E-mail", value=_safe(member.get("email")))

    # =====================
    # REGISTRY NUMBERS (ONLY TWO)
    # =====================
    st.subheader("🗂️ Αριθμοί Μητρώου")
    c1, c2 = st.columns(2)
    with c1:
        lodge_reg_no = st.text_input("Αριθμός Μητρώου Στοάς Ακρόπολις Υπ’ Αριθμ 84", value=_safe(member.get("lodge_reg_no")))
    with c2:
        grand_lodge_reg_no = st.text_input("Αριθμός Μητρώου Μεγάλης Στοάς", value=_safe(member.get("grand_lodge_reg_no")))

    # =====================
    # TECTONIC INFO (rename header + ΔΙΔΑΣΚΑΛΟΣ)
    # =====================
    st.subheader("🧩 ΤΕΚΤΟΝΙΚΕΣ ΠΛΗΡΟΦΟΡΙΕΣ")

    # Dates & diploma numbers
    c1, c2, c3 = st.columns(3)
    with c1:
        degree1_date = st.date_input("Ημ/νία Μύησης (Μαθητής)", value=_parse_date(member.get("initiation_date") or member.get("degree1_date")))
        degree1_diploma_no = st.text_input("Αρ. Διπλ. Μύησης", value=_safe(member.get("initiation_diploma") or member.get("degree1_diploma_no")))
    with c2:
        degree2_date = st.date_input("Ημ/νία 2ου Βαθμού (Εταίρος)", value=_parse_date(member.get("second_degree_date") or member.get("degree2_date")))
        degree2_diploma_no = st.text_input("Αρ. Διπλ. 2ου", value=_safe(member.get("second_degree_diploma") or member.get("degree2_diploma_no")))
    with c3:
        degree3_date = st.date_input("Ημ/νία 3ου Βαθμού (Διδάσκαλος)", value=_parse_date(member.get("third_degree_date") or member.get("degree3_date")))
        degree3_diploma_no = st.text_input("Αρ. Διπλ. 3ου", value=_safe(member.get("third_degree_diploma") or member.get("degree3_diploma_no")))

    c1, c2, c3 = st.columns(3)
    degrees = ["Μαθητής", "Εταίρος", "Διδάσκαλος"]
    with c1:
        current_degree = st.selectbox("Τρέχων Βαθμός", degrees, index=degrees.index(_normalize_degree(member.get("current_degree", "Μαθητής"))))
    with c2:
        initiation_lodge = st.text_input("Στοά Μύησης", value=_safe(member.get("initiation_lodge")))
        initiation_lodge_no = st.text_input("Αρ. Στοάς", value=_safe(member.get("initiation_lodge_number") or member.get("initiation_lodge_no")))
    with c3:
        # συμβατότητα: sponsor/introducer
        introducer = st.text_input("Εισηγητής", value=_safe(member.get("sponsor") or member.get("introducer")))

    # =====================
    # LODGE HISTORY
    # =====================
    st.subheader("📚 Ιστορικό Στοάς")
    c1, c2 = st.columns(2)
    with c1:
        entry_date = st.date_input("Ημ/νία Εισόδου", value=_parse_date(member.get("entry_date")))
        offices = st.text_area("Αξιώματα", value=_safe(member.get("offices_held") or member.get("offices")))
    with c2:
        medals = st.text_area("Παράσημα", value=_safe(member.get("honors") or member.get("medals")))
        committees = st.text_area("Επιτροπές", value=_safe(member.get("committees")))

    # =====================
    # FAMILY
    # =====================
    st.subheader("👨‍👩‍👧‍👦 Οικογενειακά Στοιχεία")
    c1, c2, c3 = st.columns(3)
    with c1:
        marital_status = st.text_input("Οικογ. Κατάσταση", value=_safe(member.get("marital_status")))
        spouse_name = st.text_input("Όνομα Συζύγου", value=_safe(member.get("spouse_name")))
    with c2:
        children_names = st.text_area("Ονόματα Τέκνων", value=_safe(member.get("children_names")))
    with c3:
        emergency_phone = st.text_input("Επείγον Τηλ.", value=_safe(member.get("emergency_phone")))
        emergency_contact = st.text_input("Επαφή Έκτ. Ανάγκης", value=_safe(member.get("emergency_contact") or member.get("emergency_contact_name")))

    # =====================
    # ADMIN
    # =====================
    st.subheader("🧾 Διοικητικά Στοιχεία")
    c1, c2, c3 = st.columns(3)
    with c1:
        status_list = ["Ενεργό", "Ανενεργό", "Αποχωρήσαν", "Διαγραφέν"]
        member_status = st.selectbox("Κατάσταση", status_list, index=status_list.index(member.get("member_status", "Ενεργό")))
        status_change_date = st.date_input("Ημ/νία Αλλαγής", value=_parse_date(member.get("status_change_date")))
    with c2:
        status_change_reason = st.text_input("Λόγος Αλλαγής", value=_safe(member.get("status_change_reason")))
        fin_list = ["Ναι", "Όχι"]
        financial_status = st.selectbox("Οικονομική Τακτοποίηση", fin_list, index=fin_list.index(member.get("financial_status", "Ναι")))
    with c3:
        last_payment_date = st.date_input("Τελ. Πληρωμή", value=_parse_date(member.get("last_payment_date")))
        notes = st.text_area("Σημειώσεις", value=_safe(member.get("notes")))

    st.markdown("---")
    submitted = st.form_submit_button("💾 Αποθήκευση Αλλαγών", type="primary", use_container_width=True)

if submitted:
    # IMPORTANT: κρατάμε τα ονόματα πεδίων που χρησιμοποιεί ήδη το PDF generator,
    # ώστε να μην χρειαστείς μεγάλα refactors.
    update_data = {
        # personal
        "last_name": last_name.strip() or None,
        "first_name": first_name.strip() or None,
        "fathers_name": fathers_name.strip() or None,
        "birth_date": _to_iso(birth_date),
        "birth_place": birth_place.strip() or None,
        "profession": profession.strip() or None,
        "tax_id": afm.strip() or None,           # για συμβατότητα με pdf_generator
        "afm": afm.strip() or None,              # κρατάμε και afm αν υπάρχει
        "id_number": id_number.strip() or None,

        # contact
        "address": address.strip() or None,
        "city": city.strip() or None,
        "postal_code": postal_code.strip() or None,
        "mobile_phone": mobile_phone.strip() or None,
        "home_phone": home_phone.strip() or None,
        "email": email.strip() or None,

        # only 2 registries
        "lodge_reg_no": lodge_reg_no.strip() or None,
        "grand_lodge_reg_no": grand_lodge_reg_no.strip() or None,

        # tectonic (keep pdf names)
        "initiation_date": _to_iso(degree1_date),
        "initiation_diploma": degree1_diploma_no.strip() or None,
        "second_degree_date": _to_iso(degree2_date),
        "second_degree_diploma": degree2_diploma_no.strip() or None,
        "third_degree_date": _to_iso(degree3_date),
        "third_degree_diploma": degree3_diploma_no.strip() or None,
        "current_degree": current_degree,
        "initiation_lodge": initiation_lodge.strip() or None,
        "initiation_lodge_number": initiation_lodge_no.strip() or None,
        "sponsor": introducer.strip() or None,

        # history (keep pdf names)
        "entry_date": _to_iso(entry_date),
        "offices_held": offices.strip() or None,
        "honors": medals.strip() or None,
        "committees": committees.strip() or None,

        # family (keep pdf names)
        "marital_status": marital_status.strip() or None,
        "spouse_name": spouse_name.strip() or None,
        "children_names": children_names.strip() or None,
        "emergency_phone": emergency_phone.strip() or None,
        "emergency_contact": emergency_contact.strip() or None,

        # admin
        "member_status": member_status,
        "status_change_date": _to_iso(status_change_date),
        "status_change_reason": status_change_reason.strip() or None,
        "financial_status": financial_status,
        "last_payment_date": _to_iso(last_payment_date),
        "notes": notes.strip() or None,
    }

    try:
        db.update_member(int(selected_id), update_data)
        st.success("✅ Το μέλος ενημερώθηκε επιτυχώς!")
        st.rerun()
    except Exception as e:
        st.error(f"❌ Σφάλμα αποθήκευσης: {e}")

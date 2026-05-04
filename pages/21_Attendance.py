# -*- coding: utf-8 -*-
"""
Σελίδα 21 — Ενημέρωση Παρουσίας
Ενημέρωση Παρουσίας — ΑΚΡΟΠΟΛΙΣ ΥΠ. ΑΡΙΘΜ. 84
"""
import sys, os; sys.path.append("..")
import sqlite3
import streamlit as st
import pandas as pd
from datetime import datetime, date

# ── CONFIG ────────────────────────────────────────────────────────────────────
# Absolute path so it works on Streamlit Cloud too
_HERE = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(os.path.dirname(_HERE), "grammateas.db")
LODGE_NAME = "ΑΚΡΟΠΟΛΙΣ ΥΠ. ΑΡΙΘΜ. 84"

st.set_page_config(
    page_title="Ενημέρωση Παρουσίας",
    page_icon="🔑",
    layout="wide",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=IM+Fell+English:ital@0;1&family=Libre+Baskerville:ital,wght@0,400;0,700;1,400&display=swap');

  html, body, [class*="css"] {
    font-family: 'Libre Baskerville', Georgia, serif;
  }

  /* ── Invitation card ── */
  .invitation-card {
    background: #fffdf5;
    border: 2px solid #c8a84b;
    border-radius: 4px;
    padding: 2.5rem 3rem;
    margin: 1rem 0 2rem;
    box-shadow: 0 4px 20px rgba(0,0,0,0.08);
    position: relative;
  }
  .invitation-card::before {
    content: '';
    position: absolute;
    inset: 6px;
    border: 1px solid #e8d08a;
    border-radius: 2px;
    pointer-events: none;
  }

  /* Header of invitation */
  .inv-header {
    text-align: center;
    margin-bottom: 1.5rem;
    padding-bottom: 1.2rem;
    border-bottom: 1px solid #d4af37;
  }
  .inv-org {
    font-size: 0.78rem;
    letter-spacing: 0.12em;
    color: #7a6a30;
    text-transform: uppercase;
    margin-bottom: 0.3rem;
  }
  .inv-lodge {
    font-size: 1.3rem;
    font-weight: 700;
    color: #2c2210;
    letter-spacing: 0.05em;
  }
  .inv-location {
    font-size: 0.85rem;
    color: #7a6a30;
    font-style: italic;
    margin-top: 0.2rem;
  }

  /* Body */
  .inv-salutation {
    font-style: italic;
    color: #3a2e10;
    margin-bottom: 1rem;
    font-size: 1rem;
  }
  .inv-body {
    color: #2c2210;
    line-height: 1.85;
    font-size: 0.97rem;
    text-align: justify;
  }
  .inv-date-highlight {
    font-weight: 700;
    color: #1a1005;
  }
  .inv-teacher {
    font-weight: 700;
    font-style: italic;
    display: block;
    text-align: center;
    font-size: 1.05rem;
    margin: 0.5rem 0;
    color: #1a1005;
  }
  .inv-closing {
    margin-top: 1.5rem;
    padding-top: 1rem;
    border-top: 1px solid #e8d08a;
    text-align: center;
    color: #3a2e10;
    font-style: italic;
    font-size: 0.9rem;
  }
  .inv-signature {
    font-weight: 700;
    font-style: normal;
    font-size: 1rem;
    color: #1a1005;
    display: block;
    margin-top: 0.3rem;
  }
  .inv-title {
    font-size: 0.85rem;
    color: #7a6a30;
  }

  /* ── Form card ── */
  .form-header {
    background: linear-gradient(135deg, #1a2a4a 0%, #2d4a7a 100%);
    color: white;
    padding: 1.5rem 2rem;
    border-radius: 8px 8px 0 0;
    margin-bottom: 0;
    text-align: center;
  }
  .form-header h2 { margin: 0; font-size: 1.3rem; letter-spacing: 0.05em; }
  .form-header p  { margin: 0.3rem 0 0; opacity: 0.75; font-size: 0.85rem; }

  /* ── Stat pills ── */
  .stat-row {
    display: flex; gap: 1rem; margin: 1rem 0;
    flex-wrap: wrap;
  }
  .stat-pill {
    background: white; border: 1px solid #e2e8f0;
    border-radius: 50px; padding: 0.4rem 1.2rem;
    font-size: 0.85rem; color: #374151;
    display: flex; align-items: center; gap: 0.5rem;
  }
  .stat-pill .num { font-weight: 700; font-size: 1.1rem; color: #1a2a4a; }

  /* ── Response rows ── */
  .response-parwn {
    background: #f0fdf4; border-left: 3px solid #22c55e;
    padding: 0.5rem 0.75rem; border-radius: 0 4px 4px 0;
    margin: 0.3rem 0; font-size: 0.9rem;
  }
  .response-apwn {
    background: #fff7ed; border-left: 3px solid #f97316;
    padding: 0.5rem 0.75rem; border-radius: 0 4px 4px 0;
    margin: 0.3rem 0; font-size: 0.9rem;
  }

  /* ── Section title ── */
  .section-title {
    font-size: 0.75rem; font-weight: 700; letter-spacing: 0.12em;
    text-transform: uppercase; color: #6b7280; margin-bottom: 0.5rem;
  }

  /* Gold divider */
  .gold-divider {
    height: 2px;
    background: linear-gradient(90deg, transparent, #c8a84b, transparent);
    border: none; margin: 2rem 0;
  }
</style>
""", unsafe_allow_html=True)


# ── DB HELPERS ────────────────────────────────────────────────────────────────
def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def init_edtmats_table():
    """Δημιουργία πίνακα για αποκρίσεις Ε∴Δ∴Τ∴Μ∴Α∴Τ∴Σ∴"""
    conn = get_conn()
    conn.execute("""
    CREATE TABLE IF NOT EXISTS εδτματσ_αποκρίσεις (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        συνεδρίαση_id   INTEGER NOT NULL,
        μέλος_id        INTEGER,
        ονοματεπώνυμο   TEXT NOT NULL,
        παρών           INTEGER DEFAULT 1,
        λόγος_απουσίας  TEXT,
        σχόλια          TEXT,
        ημ_απόκρισης    TEXT DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(συνεδρίαση_id, ονοματεπώνυμο)
    )""")
    conn.execute("""
    CREATE TABLE IF NOT EXISTS εδτματσ_συνεδριάσεις (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        τίτλος          TEXT NOT NULL,
        ημερομηνία      TEXT NOT NULL,
        ώρα             TEXT DEFAULT '20:00',
        χωρ_λόγος       TEXT,
        κεφάλαιο        TEXT DEFAULT 'ΑΚΡΟΠΟΛΙΣ ΥΠ. ΑΡΙΘΜ. 84',
        διδάσκαλος      TEXT,
        ομιλητής        TEXT,
        τίτλος_ομιλίας  TEXT,
        ενεργή          INTEGER DEFAULT 1,
        ημ_εγγραφής     TEXT DEFAULT CURRENT_TIMESTAMP
    )""")
    for col, typedef in [("ομιλητής", "TEXT"), ("τίτλος_ομιλίας", "TEXT")]:
        try:
            conn.execute(f"ALTER TABLE εδτματσ_συνεδριάσεις ADD COLUMN {col} {typedef}")
        except Exception:
            pass
    conn.commit()
    conn.close()


def get_edtmats_sessions():
    conn = get_conn()
    try:
        df = pd.read_sql_query(
            "SELECT * FROM εδτματσ_συνεδριάσεις ORDER BY ημερομηνία DESC", conn)
    except Exception:
        df = pd.DataFrame()
    conn.close()
    return df


def save_edtmats_session(data: dict) -> int:
    conn = get_conn()
    if data.get("id"):
        conn.execute("""
        UPDATE εδτματσ_συνεδριάσεις SET τίτλος=?,ημερομηνία=?,ώρα=?,χωρ_λόγος=?,
        κεφάλαιο=?,διδάσκαλος=?,ομιλητής=?,τίτλος_ομιλίας=?,ενεργή=? WHERE id=?""",
        (data["τίτλος"], data["ημερομηνία"], data["ώρα"],
         data.get("χωρ_λόγος",""), data.get("κεφάλαιο",""),
         data.get("διδάσκαλος",""), data.get("ομιλητής",""), data.get("τίτλος_ομιλίας",""),
         int(data.get("ενεργή",1)), data["id"]))
    else:
        cur = conn.execute("""
        INSERT INTO εδτματσ_συνεδριάσεις
        (τίτλος,ημερομηνία,ώρα,χωρ_λόγος,κεφάλαιο,διδάσκαλος,ομιλητής,τίτλος_ομιλίας,ενεργή)
        VALUES (?,?,?,?,?,?,?,?,?)""",
        (data["τίτλος"], data["ημερομηνία"], data["ώρα"],
         data.get("χωρ_λόγος",""), data.get("κεφάλαιο","ΑΚΡΟΠΟΛΙΣ ΥΠ. ΑΡΙΘΜ. 84"),
         data.get("διδάσκαλος",""), data.get("ομιλητής",""), data.get("τίτλος_ομιλίας",""),
         int(data.get("ενεργή",1))))
        data["id"] = cur.lastrowid
    conn.commit()
    conn.close()
    return data["id"]


def get_responses(session_id: int) -> pd.DataFrame:
    conn = get_conn()
    try:
        df = pd.read_sql_query(
            "SELECT * FROM εδτματσ_αποκρίσεις WHERE συνεδρίαση_id=? ORDER BY ημ_απόκρισης",
            conn, params=(session_id,))
    except Exception:
        df = pd.DataFrame()
    conn.close()
    return df


def save_response(session_id: int, ονοματεπώνυμο: str, μέλος_id,
                  παρών: int, λόγος: str, σχόλια: str):
    conn = get_conn()
    conn.execute("""
    INSERT INTO εδτματσ_αποκρίσεις
    (συνεδρίαση_id, μέλος_id, ονοματεπώνυμο, παρών, λόγος_απουσίας, σχόλια, ημ_απόκρισης)
    VALUES (?,?,?,?,?,?,?)
    ON CONFLICT(συνεδρίαση_id, ονοματεπώνυμο) DO UPDATE SET
      παρών=excluded.παρών,
      λόγος_απουσίας=excluded.λόγος_απουσίας,
      σχόλια=excluded.σχόλια,
      ημ_απόκρισης=excluded.ημ_απόκρισης
    """, (session_id, μέλος_id, ονοματεπώνυμο, παρών, λόγος, σχόλια,
          datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()


def get_members():
    conn = get_conn()
    try:
        df = pd.read_sql_query(
            "SELECT id, επώνυμο, όνομα FROM μέλη WHERE κατάσταση='Ενεργός' ORDER BY επώνυμο, όνομα",
            conn)
    except Exception:
        df = pd.DataFrame()
    conn.close()
    return df


# ── INIT ──────────────────────────────────────────────────────────────────────
init_edtmats_table()

# ── PAGE HEADER ───────────────────────────────────────────────────────────────
col_logo, col_title = st.columns([1, 5])
with col_title:
    st.markdown(f"""
    <div style="padding: 0.5rem 0;">
      <div style="font-size:0.75rem;letter-spacing:0.15em;text-transform:uppercase;
                  color:#c8a84b;font-weight:700;margin-bottom:0.2rem;">
        {LODGE_NAME}
      </div>
      <h1 style="margin:0;font-family:'IM Fell English',Georgia,serif;
                 font-size:1.8rem;color:#1a2a4a;">
        🏛️ ΑΚΡΟΠΟΛΙΣ — Ενημέρωση Παρουσίας
      </h1>
      <div style="color:#6b7280;font-size:0.85rem;margin-top:0.3rem;">
        Ενημερώστε για παρουσία ή απουσία σας στη συνεδρία
      </div>
    </div>
    """, unsafe_allow_html=True)

st.markdown('<hr class="gold-divider">', unsafe_allow_html=True)

# ── TABS ──────────────────────────────────────────────────────────────────────
tab_form, tab_results, tab_sessions = st.tabs([
    "📋 Ενημέρωση Παρουσίας",
    "📊 Ενημερώσεις",
    "⚙️ Διαχείριση Συνεδριάσεων",
])


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — ΦΟΡΜΑ ΠΑΡΟΥΣΙΑΣ (Google Forms style)
# ══════════════════════════════════════════════════════════════════════════════
with tab_form:
    df_sessions = get_edtmats_sessions()
    active_sessions = df_sessions[df_sessions["ενεργή"] == 1] if not df_sessions.empty else pd.DataFrame()

    if active_sessions.empty:
        st.info("⚠️ Δεν υπάρχει ενεργή συνεδρίαση. Δημιουργήστε μία από την καρτέλα **⚙️ Διαχείριση Συνεδριάσεων**.")
        st.stop()

    # Επιλογή ενεργής συνεδρίασης
    session_options = {
        row["id"]: f"{row['τίτλος']} — {row['ημερομηνία']} {row['ώρα']}"
        for _, row in active_sessions.iterrows()
    }
    if len(session_options) == 1:
        sel_sid = list(session_options.keys())[0]
        sel_session = active_sessions[active_sessions["id"] == sel_sid].iloc[0]
    else:
        sel_sid = st.selectbox("Επιλογή Συνεδρίασης", options=list(session_options.keys()),
                               format_func=lambda x: session_options[x])
        sel_session = active_sessions[active_sessions["id"] == sel_sid].iloc[0]

    # ── INVITATION CARD ───────────────────────────────────────────────────────
    inv_date = sel_session["ημερομηνία"]
    inv_time = sel_session["ώρα"]
    inv_chapter = sel_session.get("κεφάλαιο", "ΑΚΡΟΠΟΛΙΣ ΥΠ. ΑΡΙΘΜ. 84")
    inv_teacher = sel_session.get("διδάσκαλος", "")
    inv_title = sel_session.get("τίτλος", "")
    inv_ομιλητής = sel_session.get("ομιλητής", "") or ""
    inv_τίτλος_ομιλίας = sel_session.get("τίτλος_ομιλίας", "") or ""

    st.markdown(f"""
    <div class="invitation-card">
      <div class="inv-header">
        <div class="inv-org">Μεγάλη Στοά της Ελλάδος</div>
        <div class="inv-lodge">Στ∴ {LODGE_NAME}</div>
        <div class="inv-location">ἐν Ἀθήναις</div>
      </div>

      <div class="inv-salutation">Φίλτατε Ἀδελφέ,</div>

      <div class="inv-body">
        Σᾶς γνωστοποιοῦμε ὅτι τήν <span class="inv-date-highlight">{inv_title}</span>
        καί ὥρα <span class="inv-date-highlight">{inv_time} μ.μ.</span>, ἡ
        <span class="inv-date-highlight">{LODGE_NAME}</span>
        πραγματοποιεῖ τακτική συνεδρία.
        {'<br><br>Κατά τήν συνεδρία θά λάβει χώρα διδασκαλία ἀπό τόν,' if inv_teacher else ''}
        {'<span class="inv-teacher">' + inv_teacher + '</span>' if inv_teacher else ''}
        {'Παρακαλοῦνται ἅπαντες οἱ Ἀδελφοί ὅπως τιμήσουν διά τῆς παρουσίας τους.' if inv_teacher else ''}
        {'<br><br>Ἡ ἡμερησία διάταξις περιλαμβάνει ὁμιλία τοῦ Ἀδ∴ <b>' + inv_ομιλητής + '</b> μέ τίτλο: <em>«' + inv_τίτλος_ομιλίας + '»</em>.' if inv_ομιλητής and inv_τίτλος_ομιλίας else ''}
        <br><br>Θά ἀκολουθήσει — Ποτήριον Ἀγάπης.
      </div>

      <div class="inv-closing">
        Μετ᾿ ἀδελφικῶν χαιρετισμῶν<br>
        Διά τῶν Ι∴Α∴<br>
        <span class="inv-signature">Γραμματεύς-Σφραγιδοφύλαξ</span>
        <span class="inv-title">{LODGE_NAME}</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── FORM ──────────────────────────────────────────────────────────────────
    st.markdown("""
    <div class="form-header">
      <h2>📋 ΕΝΗΜΕΡΩΣΗ ΠΑΡΟΥΣΙΑΣ</h2>
      <p>Ενημερώστε τον Γραμματέα για παρουσία ή απουσία σας</p>
    </div>
    """, unsafe_allow_html=True)

    with st.container(border=True):
        members_df = get_members()

        # Επιλογή μέλους
        st.markdown('<div class="section-title">Στοιχεία Αδελφού</div>', unsafe_allow_html=True)

        μέλος_id = None
        if not members_df.empty:
            member_options = {"": "— Επιλέξτε Αδελφό —"}
            member_options.update({
                str(row["id"]): f"{row['επώνυμο']} {row['όνομα']}"
                for _, row in members_df.iterrows()
            })
            sel_member_key = st.selectbox(
                "Αδελφός *",
                options=list(member_options.keys()),
                format_func=lambda x: member_options[x],
                help="Επιλέξτε το όνομά σας από τη λίστα"
            )
            if sel_member_key:
                μέλος_id = int(sel_member_key)
                ονοματεπώνυμο = member_options[sel_member_key]
            else:
                ονοματεπώνυμο = ""
        else:
            ονοματεπώνυμο = st.text_input(
                "Ονοματεπώνυμο *",
                placeholder="π.χ. Παπαδόπουλος Γεώργιος",
                help="Αν δεν εμφανίζεται το όνομά σας, πληκτρολογήστε το"
            )

        st.markdown('<div style="height:1rem"></div>', unsafe_allow_html=True)

        # Παρουσία / Απουσία
        st.markdown('<div class="section-title">Ενημέρωση Παρουσίας</div>', unsafe_allow_html=True)
        παρουσία = st.radio(
            "Ενημέρωση παρουσίας",
            options=["✅ Θα παραστώ", "❌ Δεν θα παραστώ — Ενημέρωση Απουσίας"],
            horizontal=True,
        )
        παρών = 1 if παρουσία.startswith("✅") else 0

        λόγος = ""
        σχόλια = ""

        if παρών == 0:
            st.markdown('<div style="height:0.5rem"></div>', unsafe_allow_html=True)
            st.markdown('<div class="section-title">Λόγος Απουσίας</div>', unsafe_allow_html=True)
            λόγος = st.selectbox(
                "Αιτία απουσίας *",
                options=[
                    "",
                    "Ασθένεια / Λόγοι Υγείας",
                    "Επαγγελματικοί Λόγοι",
                    "Οικογενειακοί Λόγοι",
                    "Ταξίδι / Απουσία από Αθήνα",
                    "Προηγούμενη Δέσμευση",
                    "Άλλος Λόγος",
                ],
                format_func=lambda x: x if x else "— Επιλέξτε —"
            )
            σχόλια = st.text_area(
                "Σχόλια / Διευκρινίσεις",
                placeholder="Προαιρετικό — Αν επιθυμείτε, προσθέστε επιπλέον πληροφορίες...",
                max_chars=400,
                height=100,
            )
        else:
            σχόλια = st.text_input(
                "Σχόλια (προαιρετικό)",
                placeholder="π.χ. Θα φέρω κάποιον επισκέπτη...",
                max_chars=200,
            )

        st.markdown('<div style="height:0.5rem"></div>', unsafe_allow_html=True)

        submitted = st.button(
            "📨 Αποστολή Ενημέρωσης",
            type="primary",
            use_container_width=True,
            disabled=(not ονοματεπώνυμο),
        )

        if submitted:
            if not ονοματεπώνυμο:
                st.error("❌ Παρακαλώ επιλέξτε ή εισάγετε το ονοματεπώνυμό σας.")
            elif παρών == 0 and not λόγος:
                st.error("❌ Παρακαλώ επιλέξτε αιτία απουσίας.")
            else:
                save_response(sel_sid, ονοματεπώνυμο, μέλος_id, παρών, λόγος, σχόλια)
                if παρών:
                    st.success(f"✅ Καταχωρήθηκε η ενημέρωση **παρουσίας** σας, Αδ∴ {ονοματεπώνυμο}. Σας αναμένουμε!")
                else:
                    st.warning(f"📝 Καταχωρήθηκε η ενημέρωση **απουσίας** σας, Αδ∴ {ονοματεπώνυμο}. Ευχαριστούμε για την ενημέρωση.")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — ΑΠΟΤΕΛΕΣΜΑΤΑ
# ══════════════════════════════════════════════════════════════════════════════
with tab_results:
    df_sessions = get_edtmats_sessions()
    if df_sessions.empty:
        st.info("Δεν υπάρχουν συνεδριάσεις ακόμα.")
        st.stop()

    session_options_r = {
        row["id"]: f"{row['τίτλος']} — {row['ημερομηνία']}"
        for _, row in df_sessions.iterrows()
    }
    sel_sid_r = st.selectbox(
        "Επιλογή Συνεδρίασης",
        options=list(session_options_r.keys()),
        format_func=lambda x: session_options_r[x],
        key="results_sel",
    )

    df_resp = get_responses(sel_sid_r)

    if df_resp.empty:
        st.info("Δεν υπάρχουν ενημερώσεις για αυτή τη συνεδρίαση.")
    else:
        n_parwntes = int(df_resp["παρών"].sum())
        n_apwntes = len(df_resp) - n_parwntes

        st.markdown(f"""
        <div class="stat-row">
          <div class="stat-pill">📨 Σύνολο ενημερώσεων: <span class="num">{len(df_resp)}</span></div>
          <div class="stat-pill">✅ Παρόντες: <span class="num" style="color:#16a34a">{n_parwntes}</span></div>
          <div class="stat-pill">❌ Απόντες: <span class="num" style="color:#dc2626">{n_apwntes}</span></div>
        </div>
        """, unsafe_allow_html=True)

        col_p, col_a = st.columns(2)

        with col_p:
            st.markdown("**✅ Παρόντες**")
            parwntes = df_resp[df_resp["παρών"] == 1]
            if parwntes.empty:
                st.caption("Κανένας ακόμα.")
            for _, row in parwntes.iterrows():
                st.markdown(
                    f'<div class="response-parwn">🔑 <b>{row["ονοματεπώνυμο"]}</b>'
                    f'{"<br><small>" + row["σχόλια"] + "</small>" if row["σχόλια"] else ""}'
                    f'</div>',
                    unsafe_allow_html=True,
                )

        with col_a:
            st.markdown("**❌ Απόντες**")
            apwntes = df_resp[df_resp["παρών"] == 0]
            if apwntes.empty:
                st.caption("Κανένας ακόμα.")
            for _, row in apwntes.iterrows():
                st.markdown(
                    f'<div class="response-apwn">👤 <b>{row["ονοματεπώνυμο"]}</b>'
                    f'{"<br><small>Αιτία: " + row["λόγος_απουσίας"] + "</small>" if row["λόγος_απουσίας"] else ""}'
                    f'{"<br><small>" + row["σχόλια"] + "</small>" if row["σχόλια"] else ""}'
                    f'</div>',
                    unsafe_allow_html=True,
                )

        st.markdown("---")
        st.markdown("**📥 Εξαγωγή**")
        export_df = df_resp[["ονοματεπώνυμο", "παρών", "λόγος_απουσίας", "σχόλια", "ημ_απόκρισης"]].copy()
        export_df["παρών"] = export_df["παρών"].map({1: "Παρών", 0: "Απών"})
        export_df.columns = ["Ονοματεπώνυμο", "Κατάσταση", "Λόγος Απουσίας", "Σχόλια", "Ημ. Απόκρισης"]
        st.download_button(
            "⬇️ Λήψη CSV",
            data=export_df.to_csv(index=False, encoding="utf-8-sig"),
            file_name=f"ενημερωσεις_{sel_sid_r}.csv",
            mime="text/csv",
        )
        st.dataframe(export_df, use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — ΔΙΑΧΕΙΡΙΣΗ ΣΥΝΕΔΡΙΑΣΕΩΝ
# ══════════════════════════════════════════════════════════════════════════════
with tab_sessions:
    st.markdown("### ➕ Νέα Συνεδρίαση ΑΚΡΟΠΟΛΙΣ ΥΠ. ΑΡΙΘΜ. 84")

    with st.form("new_session_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            f_τίτλος = st.text_input(
                "Τίτλος / Περιγραφή *",
                placeholder="π.χ. Τετάρτη 4 Φεβρουαρίου 2026",
            )
            f_ημερομηνία = st.date_input("Ημερομηνία *", value=date.today())
            f_ώρα = st.text_input("Ώρα", value="20:00", max_chars=5)
        with c2:
            f_κεφάλαιο = st.text_input(
                "Κεφάλαιο",
                value="ΑΚΡΟΠΟΛΙΣ ΥΠ. ΑΡΙΘΜ. 84",
            )
            f_διδάσκαλος = st.text_input(
                "Διδάσκαλος / Ομιλητής Βαθμού",
                placeholder="π.χ. Αδ∴ Λέανδρος Λεφάκης",
            )
            f_ενεργή = st.checkbox("Ενεργή (εμφάνιση στη φόρμα)", value=True)
        st.markdown("**Ημερήσια Διάταξη — Ομιλία**")
        col_om1, col_om2 = st.columns(2)
        with col_om1:
            f_ομιλητής = st.text_input(
                "Ομιλητής (Αδελφός)",
                placeholder="π.χ. Γεώργιος Παπαδόπουλος",
            )
        with col_om2:
            f_τίτλος_ομιλίας = st.text_input(
                "Τίτλος Ομιλίας",
                placeholder="π.χ. Η συμβολική σημασία του ...",
            )

        submit_session = st.form_submit_button("💾 Αποθήκευση Συνεδρίασης", type="primary", use_container_width=True)
        if submit_session:
            if not f_τίτλος:
                st.error("❌ Εισάγετε τίτλο συνεδρίασης.")
            else:
                try:
                    save_edtmats_session({
                        "τίτλος": f_τίτλος,
                        "ημερομηνία": f_ημερομηνία.isoformat(),
                        "ώρα": f_ώρα,
                        "κεφάλαιο": f_κεφάλαιο,
                        "διδάσκαλος": f_διδάσκαλος,
                        "ομιλητής": f_ομιλητής,
                        "τίτλος_ομιλίας": f_τίτλος_ομιλίας,
                        "ενεργή": int(f_ενεργή),
                    })
                    st.session_state["session_saved"] = f_τίτλος
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Σφάλμα αποθήκευσης: {e}")

    if st.session_state.get("session_saved"):
        st.success(f"✅ Η συνεδρίαση «{st.session_state.pop('session_saved')}» αποθηκεύτηκε!")

    st.markdown("---")
    st.markdown("### 📋 Καταχωρημένες Συνεδριάσεις")
    df_all = get_edtmats_sessions()
    if df_all.empty:
        st.info("Δεν υπάρχουν συνεδριάσεις ακόμα.")
    else:
        df_display = df_all[["id","τίτλος","ημερομηνία","ώρα","κεφάλαιο","διδάσκαλος","ενεργή"]].copy()
        df_display["ενεργή"] = df_display["ενεργή"].map({1: "✅ Ενεργή", 0: "—"})
        st.dataframe(df_display, use_container_width=True, hide_index=True)

        # Toggle ενεργή
        st.markdown("**Αλλαγή Κατάστασης**")
        tog_id = st.number_input("ID Συνεδρίασης", min_value=1, step=1, value=1)
        tog_active = st.checkbox("Ενεργή", value=True, key="tog_active")
        if st.button("🔄 Ενημέρωση Κατάστασης"):
            conn = get_conn()
            conn.execute("UPDATE εδτματσ_συνεδριάσεις SET ενεργή=? WHERE id=?",
                         (int(tog_active), tog_id))
            conn.commit()
            conn.close()
            st.success("Ενημερώθηκε!")
            st.rerun()

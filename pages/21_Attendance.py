# -*- coding: utf-8 -*-
"""
Σελίδα 21 — Ενημέρωση Παρουσίας — ΑΚΡΟΠΟΛΙΣ ΥΠ. ΑΡΙΘΜ. 84
"""
import sys, os; sys.path.append("..")
import sqlite3
import streamlit as st
import pandas as pd
from datetime import datetime, date

# ── CONFIG ────────────────────────────────────────────────────────────────────
_HERE   = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(os.path.dirname(_HERE), "grammateas.db")
LODGE_NAME = "ΑΚΡΟΠΟΛΙΣ ΥΠ. ΑΡΙΘΜ. 84"

st.set_page_config(page_title="Ενημέρωση Παρουσίας", page_icon="🏛️", layout="wide")

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=IM+Fell+English:ital@0;1&family=Libre+Baskerville:ital,wght@0,400;0,700;1,400&display=swap');
  html, body, [class*="css"] { font-family: 'Libre Baskerville', Georgia, serif; }

  .invitation-card {
    background:#fffdf5; border:2px solid #c8a84b; border-radius:4px;
    padding:2.5rem 3rem; margin:1rem 0 2rem;
    box-shadow:0 4px 20px rgba(0,0,0,0.08); position:relative;
  }
  .invitation-card::before {
    content:''; position:absolute; inset:6px;
    border:1px solid #e8d08a; border-radius:2px; pointer-events:none;
  }
  .inv-header    { text-align:center; margin-bottom:1.5rem; padding-bottom:1.2rem; border-bottom:1px solid #d4af37; }
  .inv-org       { font-size:0.78rem; letter-spacing:0.12em; color:#7a6a30; text-transform:uppercase; margin-bottom:0.3rem; }
  .inv-lodge     { font-size:1.3rem; font-weight:700; color:#2c2210; letter-spacing:0.05em; }
  .inv-location  { font-size:0.85rem; color:#7a6a30; font-style:italic; margin-top:0.2rem; }
  .inv-salutation{ font-style:italic; color:#3a2e10; margin-bottom:1rem; font-size:1rem; }
  .inv-body      { color:#2c2210; line-height:1.85; font-size:0.97rem; text-align:justify; }
  .inv-date-highlight { font-weight:700; color:#1a1005; }
  .inv-teacher   { font-weight:700; font-style:italic; display:block; text-align:center; font-size:1.05rem; margin:0.5rem 0; color:#1a1005; }
  .inv-closing   { margin-top:1.5rem; padding-top:1rem; border-top:1px solid #e8d08a; text-align:center; color:#3a2e10; font-style:italic; font-size:0.9rem; }
  .inv-signature { font-weight:700; font-style:normal; font-size:1rem; color:#1a1005; display:block; margin-top:0.3rem; }

  .form-header   { background:linear-gradient(135deg,#1a2a4a,#2d4a7a); color:white; padding:1.5rem 2rem; border-radius:8px 8px 0 0; text-align:center; }
  .form-header h2{ margin:0; font-size:1.3rem; letter-spacing:0.05em; }
  .form-header p { margin:0.3rem 0 0; opacity:0.75; font-size:0.85rem; }

  .stat-row  { display:flex; gap:1rem; margin:1rem 0; flex-wrap:wrap; }
  .stat-pill { background:white; border:1px solid #e2e8f0; border-radius:50px; padding:0.4rem 1.2rem; font-size:0.85rem; color:#374151; display:flex; align-items:center; gap:0.5rem; }
  .stat-pill .num { font-weight:700; font-size:1.1rem; color:#1a2a4a; }

  .response-parwn{ background:#f0fdf4; border-left:3px solid #22c55e; padding:0.5rem 0.75rem; border-radius:0 4px 4px 0; margin:0.3rem 0; font-size:0.9rem; }
  .response-apwn { background:#fff7ed; border-left:3px solid #f97316; padding:0.5rem 0.75rem; border-radius:0 4px 4px 0; margin:0.3rem 0; font-size:0.9rem; }
  .section-title { font-size:0.75rem; font-weight:700; letter-spacing:0.12em; text-transform:uppercase; color:#6b7280; margin-bottom:0.5rem; }
  .gold-divider  { height:2px; background:linear-gradient(90deg,transparent,#c8a84b,transparent); border:none; margin:2rem 0; }
</style>
""", unsafe_allow_html=True)


# ── DB ────────────────────────────────────────────────────────────────────────
def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def init_db():
    conn = get_conn()
    conn.execute("""
    CREATE TABLE IF NOT EXISTS εδτματσ_αποκρίσεις (
        id             INTEGER PRIMARY KEY AUTOINCREMENT,
        συνεδρίαση_id  INTEGER NOT NULL,
        μέλος_id       INTEGER,
        ονοματεπώνυμο  TEXT NOT NULL,
        παρών          INTEGER DEFAULT 1,
        λόγος_απουσίας TEXT,
        σχόλια         TEXT,
        ημ_απόκρισης   TEXT DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(συνεδρίαση_id, ονοματεπώνυμο)
    )""")
    conn.execute("""
    CREATE TABLE IF NOT EXISTS εδτματσ_συνεδριάσεις (
        id             INTEGER PRIMARY KEY AUTOINCREMENT,
        τίτλος         TEXT NOT NULL,
        ημερομηνία     TEXT NOT NULL,
        ώρα            TEXT DEFAULT '20:00',
        κεφάλαιο       TEXT DEFAULT 'ΑΚΡΟΠΟΛΙΣ ΥΠ. ΑΡΙΘΜ. 84',
        διδάσκαλος     TEXT,
        ομιλητής       TEXT,
        τίτλος_ομιλίας TEXT,
        ενεργή         INTEGER DEFAULT 1,
        ημ_εγγραφής    TEXT DEFAULT CURRENT_TIMESTAMP
    )""")
    for col in ["ομιλητής", "τίτλος_ομιλίας"]:
        try:
            conn.execute(f"ALTER TABLE εδτματσ_συνεδριάσεις ADD COLUMN {col} TEXT")
        except Exception:
            pass
    conn.commit()
    conn.close()


def get_sessions():
    conn = get_conn()
    try:
        df = pd.read_sql_query(
            "SELECT * FROM εδτματσ_συνεδριάσεις ORDER BY ημερομηνία DESC", conn)
    except Exception:
        df = pd.DataFrame()
    conn.close()
    return df


def save_session(data: dict) -> int:
    conn = get_conn()
    if data.get("id"):
        conn.execute("""
            UPDATE εδτματσ_συνεδριάσεις
            SET τίτλος=?,ημερομηνία=?,ώρα=?,κεφάλαιο=?,
                διδάσκαλος=?,ομιλητής=?,τίτλος_ομιλίας=?,ενεργή=?
            WHERE id=?""",
            (data["τίτλος"], data["ημερομηνία"], data["ώρα"],
             data.get("κεφάλαιο", LODGE_NAME), data.get("διδάσκαλος", ""),
             data.get("ομιλητής", ""), data.get("τίτλος_ομιλίας", ""),
             int(data.get("ενεργή", 1)), data["id"]))
    else:
        cur = conn.execute("""
            INSERT INTO εδτματσ_συνεδριάσεις
            (τίτλος,ημερομηνία,ώρα,κεφάλαιο,διδάσκαλος,ομιλητής,τίτλος_ομιλίας,ενεργή)
            VALUES (?,?,?,?,?,?,?,?)""",
            (data["τίτλος"], data["ημερομηνία"], data["ώρα"],
             data.get("κεφάλαιο", LODGE_NAME), data.get("διδάσκαλος", ""),
             data.get("ομιλητής", ""), data.get("τίτλος_ομιλίας", ""),
             int(data.get("ενεργή", 1))))
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


def save_response(session_id, ονοματεπώνυμο, μέλος_id, παρών, λόγος, σχόλια):
    conn = get_conn()
    conn.execute("""
        INSERT INTO εδτματσ_αποκρίσεις
        (συνεδρίαση_id,μέλος_id,ονοματεπώνυμο,παρών,λόγος_απουσίας,σχόλια,ημ_απόκρισης)
        VALUES (?,?,?,?,?,?,?)
        ON CONFLICT(συνεδρίαση_id,ονοματεπώνυμο) DO UPDATE SET
          παρών=excluded.παρών, λόγος_απουσίας=excluded.λόγος_απουσίας,
          σχόλια=excluded.σχόλια, ημ_απόκρισης=excluded.ημ_απόκρισης""",
        (session_id, μέλος_id, ονοματεπώνυμο, παρών, λόγος, σχόλια,
         datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()


def get_members():
    conn = get_conn()
    try:
        df = pd.read_sql_query(
            "SELECT id,επώνυμο,όνομα FROM μέλη WHERE κατάσταση='Ενεργός' ORDER BY επώνυμο,όνομα",
            conn)
    except Exception:
        df = pd.DataFrame()
    conn.close()
    return df


# ── INIT ──────────────────────────────────────────────────────────────────────
init_db()

# ── PAGE HEADER ───────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="padding:0.5rem 0;">
  <div style="font-size:0.75rem;letter-spacing:0.15em;text-transform:uppercase;
              color:#c8a84b;font-weight:700;margin-bottom:0.2rem;">{LODGE_NAME}</div>
  <h1 style="margin:0;font-family:'IM Fell English',Georgia,serif;font-size:1.8rem;color:#1a2a4a;">
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
# TAB 1 — ΦΟΡΜΑ ΠΑΡΟΥΣΙΑΣ
# ══════════════════════════════════════════════════════════════════════════════
with tab_form:
    df_all = get_sessions()
    active = df_all[df_all["ενεργή"] == 1] if not df_all.empty else pd.DataFrame()

    if active.empty:
        st.info("⚠️ Δεν υπάρχει ενεργή συνεδρίαση. Δημιουργήστε μία από την καρτέλα **⚙️ Διαχείριση Συνεδριάσεων**.")
    else:
        if len(active) == 1:
            sel_sid = int(active.iloc[0]["id"])
            sess = active.iloc[0]
        else:
            opts = {int(r["id"]): f"{r['τίτλος']} — {r['ημερομηνία']}" for _, r in active.iterrows()}
            sel_sid = st.selectbox("Επιλογή Συνεδρίασης", list(opts.keys()), format_func=lambda x: opts[x])
            sess = active[active["id"] == sel_sid].iloc[0]

        inv_title   = sess.get("τίτλος", "")
        inv_time    = sess.get("ώρα", "")
        inv_teacher = sess.get("διδάσκαλος", "") or ""
        inv_speaker = sess.get("ομιλητής", "") or ""
        inv_talk    = sess.get("τίτλος_ομιλίας", "") or ""

        teacher_html = (
            f"<br><br>Κατά τήν συνεδρία θά λάβει χώρα διδασκαλία ἀπό τόν,"
            f"<span class='inv-teacher'>{inv_teacher}</span>"
            f"Παρακαλοῦνται ἅπαντες οἱ Ἀδελφοί ὅπως τιμήσουν διά τῆς παρουσίας τους."
        ) if inv_teacher else ""
        talk_html = (
            f"<br><br>Ἡ ἡμερησία διάταξις περιλαμβάνει ὁμιλία τοῦ Ἀδ∴ <b>{inv_speaker}</b>"
            f" μέ τίτλο: <em>«{inv_talk}»</em>."
        ) if inv_speaker and inv_talk else ""

        st.markdown(f"""
        <div class="invitation-card">
          <div class="inv-header">
            <div class="inv-org">Μεγάλη Στοά της Ελλάδος</div>
            <div class="inv-lodge">Στ∴ {LODGE_NAME}</div>
            <div class="inv-location">ἐν Ἀθήναις</div>
          </div>
          <div class="inv-salutation">Φίλτατε Ἀδελφέ,</div>
          <div class="inv-body">
            Σᾶς γνωστοποιοῦμε ὅτι τήν
            <span class="inv-date-highlight">{inv_title}</span>
            καί ὥρα <span class="inv-date-highlight">{inv_time} μ.μ.</span>,
            ἡ <span class="inv-date-highlight">{LODGE_NAME}</span> πραγματοποιεῖ τακτική συνεδρία.
            {teacher_html}{talk_html}
            <br><br>Θά ἀκολουθήσει — Ποτήριον Ἀγάπης.
          </div>
          <div class="inv-closing">
            Μετ᾿ ἀδελφικῶν χαιρετισμῶν<br>Διά τῶν Ι∴Α∴<br>
            <span class="inv-signature">Γραμματεύς-Σφραγιδοφύλαξ</span>
            <span style="font-size:0.85rem;color:#7a6a30;">{LODGE_NAME}</span>
          </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="form-header">
          <h2>📋 ΕΝΗΜΕΡΩΣΗ ΠΑΡΟΥΣΙΑΣ</h2>
          <p>Ενημερώστε τον Γραμματέα για παρουσία ή απουσία σας</p>
        </div>
        """, unsafe_allow_html=True)

        with st.container(border=True):
            members_df = get_members()
            st.markdown('<div class="section-title">Στοιχεία Αδελφού</div>', unsafe_allow_html=True)

            μέλος_id = None
            ονοματεπώνυμο = ""
            if not members_df.empty:
                mopts = {"": "— Επιλέξτε Αδελφό —"}
                mopts.update({str(r["id"]): f"{r['επώνυμο']} {r['όνομα']}" for _, r in members_df.iterrows()})
                mkey = st.selectbox("Αδελφός *", list(mopts.keys()), format_func=lambda x: mopts[x])
                if mkey:
                    μέλος_id = int(mkey)
                    ονοματεπώνυμο = mopts[mkey]
            else:
                ονοματεπώνυμο = st.text_input("Ονοματεπώνυμο *", placeholder="π.χ. Παπαδόπουλος Γεώργιος")

            st.markdown('<div style="height:1rem"></div>', unsafe_allow_html=True)
            st.markdown('<div class="section-title">Ενημέρωση Παρουσίας</div>', unsafe_allow_html=True)
            παρουσία = st.radio(
                "Ενημέρωση παρουσίας",
                options=["✅ Θα παραστώ", "❌ Δεν θα παραστώ — Ενημέρωση Απουσίας"],
                horizontal=True,
            )
            παρών = 1 if παρουσία.startswith("✅") else 0
            λόγος = σχόλια = ""

            if παρών == 0:
                st.markdown('<div style="height:0.5rem"></div>', unsafe_allow_html=True)
                st.markdown('<div class="section-title">Λόγος Απουσίας</div>', unsafe_allow_html=True)
                λόγος = st.selectbox(
                    "Αιτία απουσίας *",
                    options=["", "Ασθένεια / Λόγοι Υγείας", "Επαγγελματικοί Λόγοι",
                             "Οικογενειακοί Λόγοι", "Ταξίδι / Απουσία από Αθήνα",
                             "Προηγούμενη Δέσμευση", "Άλλος Λόγος"],
                    format_func=lambda x: x if x else "— Επιλέξτε —"
                )
                σχόλια = st.text_area("Σχόλια / Διευκρινίσεις", placeholder="Προαιρετικό...",
                                      max_chars=400, height=100)
            else:
                σχόλια = st.text_input("Σχόλια (προαιρετικό)",
                                       placeholder="π.χ. Θα φέρω κάποιον επισκέπτη...", max_chars=200)

            st.markdown('<div style="height:0.5rem"></div>', unsafe_allow_html=True)
            submitted = st.button("📨 Αποστολή Ενημέρωσης", type="primary",
                                  use_container_width=True, disabled=(not ονοματεπώνυμο))

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
                        st.warning(f"📝 Καταχωρήθηκε η ενημέρωση **απουσίας** σας, Αδ∴ {ονοματεπώνυμο}. Ευχαριστούμε!")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — ΑΠΟΤΕΛΕΣΜΑΤΑ
# ══════════════════════════════════════════════════════════════════════════════
with tab_results:
    df_all2 = get_sessions()
    if df_all2.empty:
        st.info("Δεν υπάρχουν συνεδριάσεις ακόμα.")
    else:
        opts2 = {int(r["id"]): f"{r['τίτλος']} — {r['ημερομηνία']}" for _, r in df_all2.iterrows()}
        sel_sid_r = st.selectbox("Επιλογή Συνεδρίασης", list(opts2.keys()),
                                 format_func=lambda x: opts2[x], key="res_sel")
        df_resp = get_responses(sel_sid_r)

        if df_resp.empty:
            st.info("Δεν υπάρχουν ενημερώσεις για αυτή τη συνεδρίαση.")
        else:
            n_p = int(df_resp["παρών"].sum())
            n_a = len(df_resp) - n_p
            st.markdown(f"""
            <div class="stat-row">
              <div class="stat-pill">📨 Σύνολο: <span class="num">{len(df_resp)}</span></div>
              <div class="stat-pill">✅ Παρόντες: <span class="num" style="color:#16a34a">{n_p}</span></div>
              <div class="stat-pill">❌ Απόντες: <span class="num" style="color:#dc2626">{n_a}</span></div>
            </div>
            """, unsafe_allow_html=True)

            col_p, col_a = st.columns(2)
            with col_p:
                st.markdown("**✅ Παρόντες**")
                for _, r in df_resp[df_resp["παρών"] == 1].iterrows():
                    extra = f"<br><small>{r['σχόλια']}</small>" if r["σχόλια"] else ""
                    st.markdown(f'<div class="response-parwn">🔑 <b>{r["ονοματεπώνυμο"]}</b>{extra}</div>',
                                unsafe_allow_html=True)
            with col_a:
                st.markdown("**❌ Απόντες**")
                for _, r in df_resp[df_resp["παρών"] == 0].iterrows():
                    extra = f"<br><small>Αιτία: {r['λόγος_απουσίας']}</small>" if r["λόγος_απουσίας"] else ""
                    extra += f"<br><small>{r['σχόλια']}</small>" if r["σχόλια"] else ""
                    st.markdown(f'<div class="response-apwn">👤 <b>{r["ονοματεπώνυμο"]}</b>{extra}</div>',
                                unsafe_allow_html=True)

            st.markdown("---")
            exp = df_resp[["ονοματεπώνυμο", "παρών", "λόγος_απουσίας", "σχόλια", "ημ_απόκρισης"]].copy()
            exp["παρών"] = exp["παρών"].map({1: "Παρών", 0: "Απών"})
            exp.columns = ["Ονοματεπώνυμο", "Κατάσταση", "Λόγος Απουσίας", "Σχόλια", "Ημ. Απόκρισης"]
            st.download_button("⬇️ Λήψη CSV",
                               data=exp.to_csv(index=False, encoding="utf-8-sig"),
                               file_name=f"ενημερωσεις_{sel_sid_r}.csv", mime="text/csv")
            st.dataframe(exp, use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — ΔΙΑΧΕΙΡΙΣΗ ΣΥΝΕΔΡΙΑΣΕΩΝ
# ══════════════════════════════════════════════════════════════════════════════
with tab_sessions:
    st.markdown(f"### ➕ Νέα Συνεδρίαση — {LODGE_NAME}")

    if st.session_state.get("session_saved"):
        st.success(f"✅ Η συνεδρίαση «{st.session_state.pop('session_saved')}» αποθηκεύτηκε!")

    with st.form("new_session_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            f_τίτλος     = st.text_input("Τίτλος / Περιγραφή *", placeholder="π.χ. Τετάρτη 4 Φεβρουαρίου 2026")
            f_ημερομηνία = st.date_input("Ημερομηνία *", value=date.today())
            f_ώρα        = st.text_input("Ώρα", value="20:00", max_chars=5)
        with c2:
            f_κεφάλαιο   = st.text_input("Στοά", value=LODGE_NAME)
            f_διδάσκαλος = st.text_input("Διδάσκαλος Βαθμού", placeholder="π.χ. Αδ∴ Λέανδρος Λεφάκης")
            f_ενεργή     = st.checkbox("Ενεργή (εμφάνιση στη φόρμα)", value=True)

        st.markdown("**Ημερήσια Διάταξη — Ομιλία** *(προαιρετικό)*")
        co1, co2 = st.columns(2)
        with co1:
            f_ομιλητής = st.text_input("Ομιλητής (Αδελφός)", placeholder="π.χ. Γεώργιος Παπαδόπουλος")
        with co2:
            f_τίτλος_ομιλίας = st.text_input("Τίτλος Ομιλίας", placeholder="π.χ. Η συμβολική σημασία...")

        submit_session = st.form_submit_button("💾 Αποθήκευση Συνεδρίασης", type="primary",
                                               use_container_width=True)
        if submit_session:
            if not f_τίτλος:
                st.error("❌ Εισάγετε τίτλο συνεδρίασης.")
            else:
                try:
                    save_session({
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

    st.markdown("---")
    st.markdown("### 📋 Καταχωρημένες Συνεδριάσεις")
    df_list = get_sessions()
    if df_list.empty:
        st.info("Δεν υπάρχουν συνεδριάσεις ακόμα.")
    else:
        disp = df_list[["id", "τίτλος", "ημερομηνία", "ώρα", "διδάσκαλος", "ενεργή"]].copy()
        disp["ενεργή"] = disp["ενεργή"].map({1: "✅ Ενεργή", 0: "—"})
        st.dataframe(disp, use_container_width=True, hide_index=True)

        st.markdown("**Αλλαγή Κατάστασης Συνεδρίασης**")
        col_t, col_c, col_b = st.columns([1, 1, 2])
        with col_t:
            tog_id = st.number_input("ID", min_value=1, step=1, value=1)
        with col_c:
            tog_active = st.checkbox("Ενεργή", value=True, key="tog_active")
        with col_b:
            if st.button("🔄 Ενημέρωση", use_container_width=True):
                try:
                    conn = get_conn()
                    conn.execute("UPDATE εδτματσ_συνεδριάσεις SET ενεργή=? WHERE id=?",
                                 (int(tog_active), tog_id))
                    conn.commit()
                    conn.close()
                    st.success("✅ Ενημερώθηκε!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ {e}")

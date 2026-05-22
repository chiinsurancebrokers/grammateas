# -*- coding: utf-8 -*-
"""
Βάση Δεδομένων — Γραμματεύς-Σφραγιδοφύλαξ
Καλύπτει Άρθρα 35-41 Γενικού Κανονισμού Μεγάλης Στοάς Ελλάδος
"""
import os
import sqlite3
import pandas as pd
from datetime import datetime, date, timedelta
from typing import Optional, Dict, List
import json

DB_PATH = os.environ.get("DB_PATH", "/data/grammateas.db")

ΒΑΘΜΟΙ = ["Μαθητής", "Εταίρος", "Διδάσκαλος"]
ΚΑΤΑΣΤΑΣΕΙΣ_ΜΕΛΟΥΣ = ["Ενεργός", "Ανενεργός", "Επίτιμος", "Αποχωρήσας", "Αποβιώσας", "Διαγραφείς"]
ΑΞΙΩΜΑΤΑ = [
    "Σεβάσμιος", "Α΄ Επιτηρητής", "Β΄ Επιτηρητής", "Ρήτωρ",
    "Γραμματεύς-Σφραγιδοφύλαξ", "Ταμίας", "Α΄ Διάκονος", "Β΄ Διάκονος",
    "Ελεωνόμος", "Τελετάρχης", "Θυρωρός", "Μουσουργός",
    "Α΄ Εξεταστής", "Β΄ Εξεταστής", "Επίτιμος Σεβάσμιος",
]
ΤΥΠΟΙ_ΜΕΤΑΒΟΛΗΣ = [
    "Μύηση", "Ανύψωση σε Εταίρο", "Ανύψωση σε Διδάσκαλο",
    "Υιοθεσία από άλλη Στοά", "Τακτοποίηση από άλλη Στοά",
    "Χορήγηση Άδειας", "Θέση σε Ανενεργό", "Επιστροφή σε Ενεργό",
    "Πειθαρχική Κύρωση", "Διαγραφή", "Αποχώρηση", "Αποβίωση",
    "Αλλαγή Στοιχείων Επικοινωνίας", "Άλλο",
]


def get_conn() -> sqlite3.Connection:
    # Δημιουργία φακέλου αν δεν υπάρχει (π.χ. /data στο Railway)
    db_dir = os.path.dirname(DB_PATH)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Δημιουργία όλων των πινάκων (idempotent)."""
    conn = get_conn()
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS μέλη (
        id                  INTEGER PRIMARY KEY AUTOINCREMENT,
        επώνυμο             TEXT NOT NULL,
        όνομα               TEXT NOT NULL,
        πατρώνυμο           TEXT,
        ημ_γέννησης         TEXT,
        τόπος_γέννησης      TEXT,
        επάγγελμα           TEXT,
        διεύθυνση           TEXT,
        πόλη                TEXT,
        τκ                  TEXT,
        τηλέφωνο            TEXT,
        κινητό              TEXT,
        email               TEXT,
        αρ_μητρώου_στοάς    TEXT,
        αρ_μητρώου_μσ       TEXT,
        τεκτονικός_βαθμός   TEXT DEFAULT 'Μαθητής',
        ημ_μύησης           TEXT,
        ημ_εταίρου          TEXT,
        ημ_διδασκάλου       TEXT,
        στοά_μύησης         TEXT,
        κατάσταση           TEXT DEFAULT 'Ενεργός',
        παρατηρήσεις        TEXT,
        ημ_εγγραφής         TEXT DEFAULT CURRENT_TIMESTAMP
    )""")

    c.execute("""
    CREATE TABLE IF NOT EXISTS συνεδριάσεις (
        id                  INTEGER PRIMARY KEY AUTOINCREMENT,
        ημερομηνία          TEXT NOT NULL,
        ώρα                 TEXT,
        βαθμός              TEXT NOT NULL,
        τόπος               TEXT,
        πλήθος_παρόντων     INTEGER DEFAULT 0,
        αλληλογραφία        TEXT,
        ομιλίες             TEXT,
        αποφάσεις           TEXT,
        κορμός_αγαθοεργίας  REAL DEFAULT 0,
        κορμός_ολογράφως    TEXT,
        παρατηρήσεις        TEXT,
        ημ_εγγραφής         TEXT DEFAULT CURRENT_TIMESTAMP
    )""")

    c.execute("""
    CREATE TABLE IF NOT EXISTS παρουσίες (
        id                  INTEGER PRIMARY KEY AUTOINCREMENT,
        συνεδρίαση_id       INTEGER NOT NULL REFERENCES συνεδριάσεις(id) ON DELETE CASCADE,
        μέλος_id            INTEGER NOT NULL REFERENCES μέλη(id) ON DELETE CASCADE,
        παρών               INTEGER DEFAULT 1,
        δικαιολογήθηκε      INTEGER DEFAULT 0,
        αναπλήρωσε_θέση     TEXT,
        παρατηρήσεις        TEXT,
        UNIQUE(συνεδρίαση_id, μέλος_id)
    )""")

    c.execute("""
    CREATE TABLE IF NOT EXISTS πρωτόκολλο (
        id                  INTEGER PRIMARY KEY AUTOINCREMENT,
        αρ_πρωτ             TEXT NOT NULL,
        ημερομηνία          TEXT NOT NULL,
        κατεύθυνση          TEXT NOT NULL,
        αποστολέας          TEXT,
        παραλήπτης          TEXT,
        θέμα                TEXT NOT NULL,
        περιγραφή           TEXT,
        αρ_σχετικού         TEXT,
        κατάσταση           TEXT DEFAULT 'Εκκρεμές',
        ημ_απάντησης        TEXT,
        παρατηρήσεις        TEXT,
        αρχείο_bytes        BLOB,
        αρχείο_όνομα        TEXT,
        αρχείο_τύπος        TEXT,
        ημ_εγγραφής         TEXT DEFAULT CURRENT_TIMESTAMP
    )""")

    c.execute("""
    CREATE TABLE IF NOT EXISTS εντάλματα (
        id                  INTEGER PRIMARY KEY AUTOINCREMENT,
        αρ_εντάλματος       TEXT NOT NULL,
        ημερομηνία          TEXT NOT NULL,
        βιβλίο              TEXT NOT NULL,
        ποσό                REAL NOT NULL,
        αιτιολογία          TEXT NOT NULL,
        δικαιολογητικά      TEXT,
        αρ_απόφασης         TEXT,
        κατάσταση           TEXT DEFAULT 'Εκκρεμές',
        ημ_πληρωμής         TEXT,
        παρατηρήσεις        TEXT,
        ημ_εγγραφής         TEXT DEFAULT CURRENT_TIMESTAMP
    )""")

    c.execute("""
    CREATE TABLE IF NOT EXISTS μεταβολές (
        id                  INTEGER PRIMARY KEY AUTOINCREMENT,
        μέλος_id            INTEGER NOT NULL REFERENCES μέλη(id),
        ημερομηνία          TEXT NOT NULL,
        τύπος               TEXT NOT NULL,
        περιγραφή           TEXT,
        αναγγελία_μσ        TEXT,
        αρ_πρωτ_μσ          TEXT,
        παρατηρήσεις        TEXT,
        ημ_εγγραφής         TEXT DEFAULT CURRENT_TIMESTAMP
    )""")

    c.execute("""
    CREATE TABLE IF NOT EXISTS διαβεβαιώσεις_αξιωματικών (
        id                  INTEGER PRIMARY KEY AUTOINCREMENT,
        μέλος_id            INTEGER NOT NULL REFERENCES μέλη(id),
        αξίωμα              TEXT NOT NULL,
        ημ_εκλογής          TEXT NOT NULL,
        ημ_διαβεβαίωσης     TEXT,
        υπέγραψε            INTEGER DEFAULT 0,
        κείμενο_διαβεβαίωσης TEXT,
        παρατηρήσεις        TEXT
    )""")

    c.execute("""
    CREATE TABLE IF NOT EXISTS διαβεβαιώσεις_μυουμένων (
        id                  INTEGER PRIMARY KEY AUTOINCREMENT,
        μέλος_id            INTEGER NOT NULL REFERENCES μέλη(id),
        βαθμός              TEXT NOT NULL,
        ημ_μύησης           TEXT NOT NULL,
        υπέγραψε            INTEGER DEFAULT 0,
        παρατηρήσεις        TEXT
    )""")

    c.execute("""
    CREATE TABLE IF NOT EXISTS απορριφθέντες (
        id                  INTEGER PRIMARY KEY AUTOINCREMENT,
        επώνυμο             TEXT NOT NULL,
        όνομα               TEXT,
        ημ_απόρριψης        TEXT NOT NULL,
        απορρίπτουσα_στοά   TEXT,
        αιτία               TEXT,
        αρ_πρωτ_μσ          TEXT,
        παρατηρήσεις        TEXT
    )""")

    c.execute("""
    CREATE TABLE IF NOT EXISTS χρυσή_βίβλος (
        id                  INTEGER PRIMARY KEY AUTOINCREMENT,
        ημερομηνία          TEXT NOT NULL,
        τίτλος              TEXT NOT NULL,
        κείμενο             TEXT,
        είδος               TEXT DEFAULT 'Απόφαση',
        συνεδρίαση_id       INTEGER REFERENCES συνεδριάσεις(id),
        καταχωρήθηκε_από    TEXT DEFAULT 'Γραμματεύς-Σφραγιδοφύλαξ'
    )""")

    c.execute("""
    CREATE TABLE IF NOT EXISTS δελτία_διπλώματα (
        id                  INTEGER PRIMARY KEY AUTOINCREMENT,
        μέλος_id            INTEGER NOT NULL REFERENCES μέλη(id),
        τύπος               TEXT NOT NULL,
        βαθμός              TEXT,
        ημ_αίτησης          TEXT,
        ημ_έκδοσης          TEXT,
        ημ_παράδοσης        TEXT,
        κατάσταση           TEXT DEFAULT 'Εκκρεμής',
        τέλη                REAL DEFAULT 0,
        παρατηρήσεις        TEXT
    )""")

    c.execute("""
    CREATE TABLE IF NOT EXISTS πρακτικά_συμβουλίου (
        id                  INTEGER PRIMARY KEY AUTOINCREMENT,
        ημερομηνία          TEXT NOT NULL,
        ώρα                 TEXT,
        παρόντες            TEXT,
        θέματα              TEXT,
        αποφάσεις           TEXT,
        παρατηρήσεις        TEXT
    )""")

    c.execute("""
    CREATE TABLE IF NOT EXISTS εργασίες (
        id                  INTEGER PRIMARY KEY AUTOINCREMENT,
        τίτλος              TEXT NOT NULL,
        περιγραφή           TEXT,
        κατηγορία           TEXT DEFAULT 'Γενικά',
        προτεραιότητα       TEXT DEFAULT 'Μεσαία',
        κατάσταση           TEXT DEFAULT 'Εκκρεμής',
        ημ_λήξης            TEXT,
        ημ_ολοκλήρωσης      TEXT,
        ημ_εγγραφής         TEXT DEFAULT CURRENT_TIMESTAMP
    )""")

    conn.commit()
    conn.close()


# ═══════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════

def _get_cols(conn, table):
    return [d[0] for d in conn.execute(f"SELECT * FROM {table} LIMIT 0").description]


def _save(conn, table, data, id_col="id"):
    data = data.copy()
    rid = data.pop(id_col, None)
    if rid:
        fields = ", ".join(f"{k}=?" for k in data)
        conn.execute(f"UPDATE {table} SET {fields} WHERE {id_col}=?", (*data.values(), rid))
    else:
        cols = ", ".join(data.keys())
        phs  = ", ".join("?" * len(data))
        cur  = conn.execute(f"INSERT INTO {table} ({cols}) VALUES ({phs})", list(data.values()))
        rid  = cur.lastrowid
    conn.commit()
    return rid


# ═══════════════════════════════════════════════════════════════
# ΜΕΛΗ
# ═══════════════════════════════════════════════════════════════

def get_all_members(status: str = "all") -> pd.DataFrame:
    conn = get_conn()
    q = "SELECT * FROM μέλη"
    if status != "all":
        q += f" WHERE κατάσταση='{status}'"
    q += " ORDER BY επώνυμο, όνομα"
    df = pd.read_sql_query(q, conn)
    conn.close()
    return df


def get_member(mid: int) -> Optional[Dict]:
    conn = get_conn()
    row = conn.execute("SELECT * FROM μέλη WHERE id=?", (mid,)).fetchone()
    cols = _get_cols(conn, "μέλη")
    conn.close()
    return dict(zip(cols, row)) if row else None


def save_member(data: Dict) -> int:
    conn = get_conn()
    rid = _save(conn, "μέλη", data)
    conn.close()
    return rid


def delete_member(mid: int):
    conn = get_conn()
    conn.execute("DELETE FROM μέλη WHERE id=?", (mid,))
    conn.commit()
    conn.close()


def get_members_dropdown(active_only: bool = True) -> pd.DataFrame:
    conn = get_conn()
    q = "SELECT id, επώνυμο || ' ' || όνομα AS fullname FROM μέλη"
    if active_only:
        q += " WHERE κατάσταση='Ενεργός'"
    q += " ORDER BY επώνυμο"
    df = pd.read_sql_query(q, conn)
    conn.close()
    return df


def get_member_stats() -> Dict:
    conn = get_conn()
    c = conn.cursor()
    stats = {}
    stats["σύνολο"]  = c.execute("SELECT COUNT(*) FROM μέλη").fetchone()[0]
    stats["ενεργοί"] = c.execute("SELECT COUNT(*) FROM μέλη WHERE κατάσταση='Ενεργός'").fetchone()[0]
    for β in ΒΑΘΜΟΙ:
        stats[β] = c.execute(
            "SELECT COUNT(*) FROM μέλη WHERE τεκτονικός_βαθμός=? AND κατάσταση='Ενεργός'", (β,)
        ).fetchone()[0]
    conn.close()
    return stats


# ═══════════════════════════════════════════════════════════════
# ΣΥΝΕΔΡΙΑΣΕΙΣ
# ═══════════════════════════════════════════════════════════════

def get_sessions(βαθμός: str = "all") -> pd.DataFrame:
    conn = get_conn()
    q = "SELECT * FROM συνεδριάσεις"
    if βαθμός != "all":
        q += f" WHERE βαθμός='{βαθμός}'"
    q += " ORDER BY ημερομηνία DESC"
    df = pd.read_sql_query(q, conn)
    conn.close()
    return df


def get_session(sid: int) -> Optional[Dict]:
    conn = get_conn()
    row = conn.execute("SELECT * FROM συνεδριάσεις WHERE id=?", (sid,)).fetchone()
    if not row:
        conn.close()
        return None
    cols = _get_cols(conn, "συνεδριάσεις")
    conn.close()
    d = dict(zip(cols, row))
    for f in ("αλληλογραφία", "ομιλίες", "αποφάσεις"):
        try:
            d[f] = json.loads(d[f]) if d[f] else []
        except Exception:
            d[f] = []
    return d


def save_session(data: Dict) -> int:
    data = data.copy()
    for f in ("αλληλογραφία", "ομιλίες", "αποφάσεις"):
        if isinstance(data.get(f), list):
            data[f] = json.dumps(data[f], ensure_ascii=False)
    conn = get_conn()
    rid = _save(conn, "συνεδριάσεις", data)
    conn.close()
    return rid


# ═══════════════════════════════════════════════════════════════
# ΠΑΡΟΥΣΙΕΣ
# ═══════════════════════════════════════════════════════════════

def get_attendance(sid: int) -> pd.DataFrame:
    conn = get_conn()
    df = pd.read_sql_query("""
        SELECT π.*, μ.επώνυμο || ' ' || μ.όνομα AS fullname, μ.τεκτονικός_βαθμός
        FROM παρουσίες π
        JOIN μέλη μ ON μ.id = π.μέλος_id
        WHERE π.συνεδρίαση_id=?
        ORDER BY μ.επώνυμο
    """, conn, params=(sid,))
    conn.close()
    return df


def save_attendance_bulk(sid: int, rows: List[Dict]):
    conn = get_conn()
    for r in rows:
        conn.execute("""
            INSERT INTO παρουσίες
              (συνεδρίαση_id, μέλος_id, παρών, δικαιολογήθηκε, αναπλήρωσε_θέση, παρατηρήσεις)
            VALUES (?,?,?,?,?,?)
            ON CONFLICT(συνεδρίαση_id, μέλος_id) DO UPDATE SET
              παρών=excluded.παρών,
              δικαιολογήθηκε=excluded.δικαιολογήθηκε,
              αναπλήρωσε_θέση=excluded.αναπλήρωσε_θέση,
              παρατηρήσεις=excluded.παρατηρήσεις
        """, (sid, r["μέλος_id"], r["παρών"], r["δικαιολογήθηκε"],
              r.get("αναπλήρωσε_θέση", ""), r.get("παρατηρήσεις", "")))
    total = sum(1 for r in rows if r["παρών"])
    conn.execute("UPDATE συνεδριάσεις SET πλήθος_παρόντων=? WHERE id=?", (total, sid))
    conn.commit()
    conn.close()


def get_attendance_stats() -> pd.DataFrame:
    conn = get_conn()
    df = pd.read_sql_query("""
        SELECT μ.επώνυμο || ' ' || μ.όνομα AS μέλος,
               μ.τεκτονικός_βαθμός AS βαθμός,
               COUNT(*) AS συνολικές,
               SUM(π.παρών) AS παρουσίες,
               ROUND(SUM(π.παρών)*100.0/COUNT(*),1) AS ποσοστό
        FROM παρουσίες π
        JOIN μέλη μ ON μ.id = π.μέλος_id
        GROUP BY π.μέλος_id
        ORDER BY ποσοστό DESC
    """, conn)
    conn.close()
    return df


# ═══════════════════════════════════════════════════════════════
# ΠΡΩΤΟΚΟΛΛΟ
# ═══════════════════════════════════════════════════════════════

def get_protokollon(year: int = None, direction: str = "all") -> pd.DataFrame:
    conn = get_conn()
    q = "SELECT * FROM πρωτόκολλο WHERE 1=1"
    params = []
    if year:
        q += " AND ημερομηνία LIKE ?"
        params.append(f"{year}%")
    if direction != "all":
        q += " AND κατεύθυνση=?"
        params.append(direction)
    q += " ORDER BY αρ_πρωτ DESC"
    df = pd.read_sql_query(q, conn, params=params)
    conn.close()
    return df


def next_proto_number(year: int) -> str:
    conn = get_conn()
    cnt = conn.execute(
        "SELECT COUNT(*) FROM πρωτόκολλο WHERE ημερομηνία LIKE ?", (f"{year}%",)
    ).fetchone()[0]
    conn.close()
    return f"{cnt+1}/{year}"


def save_proto(data: Dict) -> int:
    conn = get_conn()
    rid = _save(conn, "πρωτόκολλο", data)
    conn.close()
    return rid


# ═══════════════════════════════════════════════════════════════
# ΕΝΤΟΛΕΣ ΠΛΗΡΩΜΗΣ
# ═══════════════════════════════════════════════════════════════

def get_entalmata(βιβλίο: str = "all") -> pd.DataFrame:
    conn = get_conn()
    q = "SELECT * FROM εντάλματα"
    if βιβλίο != "all":
        q += f" WHERE βιβλίο='{βιβλίο}'"
    q += " ORDER BY ημερομηνία DESC"
    df = pd.read_sql_query(q, conn)
    conn.close()
    return df


def next_entalma_number(βιβλίο: str, year: int) -> str:
    conn = get_conn()
    cnt = conn.execute(
        "SELECT COUNT(*) FROM εντάλματα WHERE βιβλίο=? AND ημερομηνία LIKE ?",
        (βιβλίο, f"{year}%")
    ).fetchone()[0]
    prefix = "Γ" if βιβλίο == "Γενικό" else "Ε"
    conn.close()
    return f"{prefix}{cnt+1}/{year}"


def save_entalma(data: Dict) -> int:
    data = data.copy()
    if isinstance(data.get("δικαιολογητικά"), list):
        data["δικαιολογητικά"] = json.dumps(data["δικαιολογητικά"], ensure_ascii=False)
    conn = get_conn()
    rid = _save(conn, "εντάλματα", data)
    conn.close()
    return rid


def get_entalma_stats() -> Dict:
    conn = get_conn()
    stats = {}
    for b in ("Γενικό", "Ελεονομείο"):
        res  = conn.execute(
            "SELECT COALESCE(SUM(ποσό),0), COUNT(*) FROM εντάλματα WHERE βιβλίο=?", (b,)
        ).fetchone()
        res2 = conn.execute(
            "SELECT COALESCE(SUM(ποσό),0) FROM εντάλματα WHERE βιβλίο=? AND κατάσταση='Εκκρεμές'", (b,)
        ).fetchone()
        stats[b] = {"σύνολο": res[0], "πλήθος": res[1], "εκκρεμή": res2[0]}
    conn.close()
    return stats


# ═══════════════════════════════════════════════════════════════
# ΜΕΤΑΒΟΛΕΣ
# ═══════════════════════════════════════════════════════════════

def get_metavoles(mid: int = None) -> pd.DataFrame:
    conn = get_conn()
    q = """
        SELECT mv.*, μ.επώνυμο || ' ' || μ.όνομα AS μέλος
        FROM μεταβολές mv
        JOIN μέλη μ ON μ.id = mv.μέλος_id
    """
    if mid:
        q += f" WHERE mv.μέλος_id={mid}"
    q += " ORDER BY mv.ημερομηνία DESC"
    df = pd.read_sql_query(q, conn)
    conn.close()
    return df


def save_metavoli(data: Dict, auto_update_member: bool = True) -> int:
    conn = get_conn()
    data = data.copy()
    did = _save(conn, "μεταβολές", data)
    if auto_update_member:
        status_map = {
            "Θέση σε Ανενεργό": "Ανενεργός",
            "Επιστροφή σε Ενεργό": "Ενεργός",
            "Διαγραφή": "Διαγραφείς",
            "Αποχώρηση": "Αποχωρήσας",
            "Αποβίωση": "Αποβιώσας",
        }
        τύπος = data.get("τύπος", "")
        new_status = status_map.get(τύπος)
        if new_status:
            conn.execute("UPDATE μέλη SET κατάσταση=? WHERE id=?",
                         (new_status, data["μέλος_id"]))
        elif τύπος == "Ανύψωση σε Εταίρο":
            conn.execute("UPDATE μέλη SET τεκτονικός_βαθμός='Εταίρος', ημ_εταίρου=? WHERE id=?",
                         (data.get("ημερομηνία"), data["μέλος_id"]))
        elif τύπος == "Ανύψωση σε Διδάσκαλο":
            conn.execute("UPDATE μέλη SET τεκτονικός_βαθμός='Διδάσκαλος', ημ_διδασκάλου=? WHERE id=?",
                         (data.get("ημερομηνία"), data["μέλος_id"]))
        conn.commit()
    conn.close()
    return did


def get_pending_announcements() -> pd.DataFrame:
    conn = get_conn()
    df = pd.read_sql_query("""
        SELECT mv.id, μ.επώνυμο || ' ' || μ.όνομα AS μέλος,
               mv.ημερομηνία, mv.τύπος, mv.περιγραφή
        FROM μεταβολές mv
        JOIN μέλη μ ON μ.id = mv.μέλος_id
        WHERE (mv.αναγγελία_μσ IS NULL OR mv.αναγγελία_μσ = '')
        ORDER BY mv.ημερομηνία
    """, conn)
    conn.close()
    return df


# ═══════════════════════════════════════════════════════════════
# ΔΙΑΒΕΒΑΙΩΣΕΙΣ
# ═══════════════════════════════════════════════════════════════

def get_diabevaiosis_axiomatikon() -> pd.DataFrame:
    conn = get_conn()
    df = pd.read_sql_query("""
        SELECT δα.*, μ.επώνυμο || ' ' || μ.όνομα AS μέλος
        FROM διαβεβαιώσεις_αξιωματικών δα
        JOIN μέλη μ ON μ.id = δα.μέλος_id
        ORDER BY δα.ημ_εκλογής DESC
    """, conn)
    conn.close()
    return df


def save_diabevaiosi_axiomatikou(data: Dict) -> int:
    conn = get_conn()
    rid = _save(conn, "διαβεβαιώσεις_αξιωματικών", data)
    conn.close()
    return rid


def get_diabevaiosis_myoumenon(βαθμός: str = "all") -> pd.DataFrame:
    conn = get_conn()
    q = """
        SELECT δμ.*, μ.επώνυμο || ' ' || μ.όνομα AS μέλος
        FROM διαβεβαιώσεις_μυουμένων δμ
        JOIN μέλη μ ON μ.id = δμ.μέλος_id
    """
    if βαθμός != "all":
        q += f" WHERE δμ.βαθμός='{βαθμός}'"
    q += " ORDER BY δμ.ημ_μύησης DESC"
    df = pd.read_sql_query(q, conn)
    conn.close()
    return df


def save_diabevaiosi_myoumenou(data: Dict) -> int:
    conn = get_conn()
    rid = _save(conn, "διαβεβαιώσεις_μυουμένων", data)
    conn.close()
    return rid


# ═══════════════════════════════════════════════════════════════
# ΑΠΟΡΡΙΦΘΕΝΤΕΣ
# ═══════════════════════════════════════════════════════════════

def get_aporriphthentes(search: str = "") -> pd.DataFrame:
    conn = get_conn()
    q = "SELECT * FROM απορριφθέντες"
    if search:
        q += f" WHERE επώνυμο LIKE '%{search}%' OR όνομα LIKE '%{search}%'"
    q += " ORDER BY επώνυμο"
    df = pd.read_sql_query(q, conn)
    conn.close()
    return df


def save_aporriphtheis(data: Dict) -> int:
    conn = get_conn()
    rid = _save(conn, "απορριφθέντες", data)
    conn.close()
    return rid


# ═══════════════════════════════════════════════════════════════
# ΧΡΥΣΗ ΒΙΒΛΟΣ
# ═══════════════════════════════════════════════════════════════

def get_chrysi_vivlos() -> pd.DataFrame:
    conn = get_conn()
    df = pd.read_sql_query(
        "SELECT * FROM χρυσή_βίβλος ORDER BY ημερομηνία DESC", conn)
    conn.close()
    return df


def save_chrysi_vivlos_entry(data: Dict) -> int:
    conn = get_conn()
    rid = _save(conn, "χρυσή_βίβλος", data)
    conn.close()
    return rid


# ═══════════════════════════════════════════════════════════════
# ΔΕΛΤΙΑ & ΔΙΠΛΩΜΑΤΑ
# ═══════════════════════════════════════════════════════════════

def get_deltia(status: str = "all") -> pd.DataFrame:
    conn = get_conn()
    q = """
        SELECT δδ.*, μ.επώνυμο || ' ' || μ.όνομα AS μέλος
        FROM δελτία_διπλώματα δδ
        JOIN μέλη μ ON μ.id = δδ.μέλος_id
    """
    if status != "all":
        q += f" WHERE δδ.κατάσταση='{status}'"
    q += " ORDER BY δδ.ημ_αίτησης DESC"
    df = pd.read_sql_query(q, conn)
    conn.close()
    return df


def save_deltio(data: Dict) -> int:
    conn = get_conn()
    rid = _save(conn, "δελτία_διπλώματα", data)
    conn.close()
    return rid


# ═══════════════════════════════════════════════════════════════
# ΠΡΑΚΤΙΚΑ ΣΥΜΒΟΥΛΙΟΥ
# ═══════════════════════════════════════════════════════════════

def get_symvoulio_minutes() -> pd.DataFrame:
    conn = get_conn()
    df = pd.read_sql_query(
        "SELECT id, ημερομηνία, ώρα FROM πρακτικά_συμβουλίου ORDER BY ημερομηνία DESC", conn)
    conn.close()
    return df


def get_symvoulio_minute(sid: int) -> Optional[Dict]:
    conn = get_conn()
    row = conn.execute("SELECT * FROM πρακτικά_συμβουλίου WHERE id=?", (sid,)).fetchone()
    if not row:
        conn.close()
        return None
    cols = _get_cols(conn, "πρακτικά_συμβουλίου")
    conn.close()
    d = dict(zip(cols, row))
    for f in ("παρόντες", "θέματα", "αποφάσεις"):
        try:
            d[f] = json.loads(d[f]) if d[f] else []
        except Exception:
            d[f] = []
    return d


def save_symvoulio_minute(data: Dict) -> int:
    data = data.copy()
    for f in ("παρόντες", "θέματα", "αποφάσεις"):
        if isinstance(data.get(f), list):
            data[f] = json.dumps(data[f], ensure_ascii=False)
    conn = get_conn()
    rid = _save(conn, "πρακτικά_συμβουλίου", data)
    conn.close()
    return rid


# ═══════════════════════════════════════════════════════════════
# ΕΡΓΑΣΙΕΣ
# ═══════════════════════════════════════════════════════════════

def get_ergasies(status: str = "all") -> pd.DataFrame:
    conn = get_conn()
    q = "SELECT * FROM εργασίες"
    if status != "all":
        q += f" WHERE κατάσταση='{status}'"
    q += " ORDER BY ημ_λήξης ASC NULLS LAST, προτεραιότητα DESC"
    df = pd.read_sql_query(q, conn)
    conn.close()
    return df


def save_ergasia(data: Dict) -> int:
    conn = get_conn()
    rid = _save(conn, "εργασίες", data)
    conn.close()
    return rid


def get_overdue_ergasies() -> pd.DataFrame:
    conn = get_conn()
    today = str(date.today())
    df = pd.read_sql_query("""
        SELECT * FROM εργασίες
        WHERE κατάσταση != 'Ολοκληρώθηκε'
        AND ημ_λήξης IS NOT NULL
        AND ημ_λήξης < ?
        ORDER BY ημ_λήξης
    """, conn, params=(today,))
    conn.close()
    return df

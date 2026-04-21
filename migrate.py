#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
migrate.py — Μεταφορά δεδομένων από παλιά βάση (lodge_members.db) στη νέα (grammateas.db)

Εκτέλεση (ΜIIA ΦΟΡΑ, ΠΡΙΝ ξεκινήσετε την εφαρμογή):
    python migrate.py
ή
    python migrate.py --old lodge_members.db --new grammateas.db
"""
import sys
import sqlite3
import argparse
from pathlib import Path
from datetime import datetime

OLD_DEFAULT = "lodge_members.db"
NEW_DEFAULT = "grammateas.db"

# Χαρτογράφηση παλαιών → νέων πεδίων μελών
FIELD_MAP = {
    "last_name":            "επώνυμο",
    "first_name":           "όνομα",
    "fathers_name":         "πατρώνυμο",
    "birth_date":           "ημ_γέννησης",
    "birth_place":          "τόπος_γέννησης",
    "profession":           "επάγγελμα",
    "address":              "διεύθυνση",
    "city":                 "πόλη",
    "postal_code":          "τκ",
    "home_phone":           "τηλέφωνο",
    "mobile_phone":         "κινητό",
    "email":                "email",
    "initiation_date":      "ημ_μύησης",
    "second_degree_date":   "ημ_εταίρου",
    "third_degree_date":    "ημ_διδασκάλου",
    "initiation_lodge":     "στοά_μύησης",
    "notes":                "παρατηρήσεις",
}

STATUS_MAP = {
    "Ενεργό":       "Ενεργός",
    "Ανενεργό":     "Ανενεργός",
    "Αποχωρήσαν":   "Αποχωρήσας",
    "Ενεργός":      "Ενεργός",
    "Ανενεργός":    "Ανενεργός",
}

DEGREE_MAP = {
    "Μαθητής":   "Μαθητής",
    "Εταίρος":   "Εταίρος",
    "Δάσκαλος":  "Διδάσκαλος",
    "Διδάσκαλος":"Διδάσκαλος",
}


def migrate(old_path: str, new_path: str):
    if not Path(old_path).exists():
        print(f"❌ Δεν βρέθηκε η παλιά βάση: {old_path}")
        sys.exit(1)

    # Φόρτωση νέας βάσης (δημιουργία αν δεν υπάρχει)
    sys.path.insert(0, str(Path(__file__).parent))
    from modules.database import init_db, DB_PATH
    import modules.database as db_mod
    db_mod.DB_PATH = new_path
    init_db()

    old_conn = sqlite3.connect(old_path)
    new_conn = sqlite3.connect(new_path)
    new_conn.execute("PRAGMA foreign_keys = ON")

    old_cols_raw = old_conn.execute("PRAGMA table_info(members)").fetchall()
    old_cols = [c[1] for c in old_cols_raw]
    rows = old_conn.execute("SELECT * FROM members").fetchall()

    migrated = 0
    skipped  = 0

    for row in rows:
        old = dict(zip(old_cols, row))

        # Έλεγχος αν υπάρχει ήδη (βάσει επωνύμου + ονόματος)
        exists = new_conn.execute(
            "SELECT id FROM μέλη WHERE επώνυμο=? AND όνομα=?",
            (old.get("last_name",""), old.get("first_name",""))
        ).fetchone()

        if exists:
            print(f"  ⏭  Υπάρχει ήδη: {old.get('last_name')} {old.get('first_name')}")
            skipped += 1
            continue

        # Χαρτογράφηση πεδίων
        new_data = {}
        for old_f, new_f in FIELD_MAP.items():
            val = old.get(old_f)
            if val is not None and str(val).strip() not in ("", "None", "nan"):
                # Καθαρισμός τηλεφώνου (αφαιρεί .0 από float)
                if old_f in ("home_phone", "mobile_phone"):
                    val = str(val).replace(".0","").strip()
                new_data[new_f] = str(val).strip()

        # Κατάσταση
        raw_status = old.get("member_status", "Ενεργό")
        new_data["κατάσταση"] = STATUS_MAP.get(str(raw_status).strip(), "Ενεργός")

        # Βαθμός
        raw_deg = old.get("current_degree", "Μαθητής")
        new_data["τεκτονικός_βαθμός"] = DEGREE_MAP.get(str(raw_deg).strip(), "Μαθητής")

        # Εισαγωγή
        if new_data:
            cols_str = ", ".join(new_data.keys())
            phs_str  = ", ".join("?" * len(new_data))
            new_conn.execute(
                f"INSERT INTO μέλη ({cols_str}) VALUES ({phs_str})",
                list(new_data.values())
            )
            print(f"  ✅ Μεταφέρθηκε: {new_data.get('επώνυμο','')} {new_data.get('όνομα','')}")
            migrated += 1

    new_conn.commit()
    old_conn.close()
    new_conn.close()

    print(f"\n{'='*50}")
    print(f"Μεταφέρθηκαν: {migrated} μέλη")
    print(f"Παρέλειπαν:   {skipped} (υπήρχαν ήδη)")
    print(f"{'='*50}")
    print(f"✅ Η βάση '{new_path}' είναι έτοιμη!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Μεταφορά δεδομένων στη νέα βάση")
    parser.add_argument("--old", default=OLD_DEFAULT, help=f"Παλιά βάση (default: {OLD_DEFAULT})")
    parser.add_argument("--new", default=NEW_DEFAULT, help=f"Νέα βάση (default: {NEW_DEFAULT})")
    args = parser.parse_args()
    print(f"🔄 Μεταφορά από '{args.old}' → '{args.new}'")
    migrate(args.old, args.new)

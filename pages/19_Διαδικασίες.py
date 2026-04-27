# -*- coding: utf-8 -*-
"""
Σελίδα 19 — Διαδικασίες & Έντυπα ΜΣΤΕ

Βοηθός συμπλήρωσης εντύπων βάσει:
  • Οδηγού Διαδικασιών & Απαιτούμενων Ενεργειών (Δεκ. 2017)
  • Γενικού Κανονισμού & Καταστατικού Χάρτη ΜΣΤΕ
  • Δεδομένων Μητρώου Στοάς

Υποστηριζόμενες διαδικασίες:
  1. Εισδοχή Υποψηφίου
  2. Αύξηση Μισθοδοσίας (Εταίρου / Διδασκάλου)
  3. Εκλογές Αξιωματικών & Εγκατάσταση
  4. Αναγγελία Μεταβολών
  5. Έγκριση Κοινής Συνεδρίας
  6. Έγκριση Λευκής Εορτής / Ανοικτής Εκδήλωσης
"""

import sys
sys.path.append("..")

import io
import json
import os
import re
import zipfile
from copy import deepcopy
from datetime import date
from typing import Any, Dict, List, Optional, Tuple

import streamlit as st

from modules.database import (
    init_db, get_all_members, get_member, get_members_dropdown,
)

# ══════════════════════════════════════════════════════════════
# APP SETUP
# ══════════════════════════════════════════════════════════════
init_db()

st.set_page_config(
    page_title="Διαδικασίες & Έντυπα",
    page_icon="📋",
    layout="wide",
)

st.markdown("# 📋 Διαδικασίες & Έντυπα ΜΣΤΕ")
st.caption(
    "Επιλέξτε διαδικασία → δείτε τα βήματα → συμπληρώστε στοιχεία → "
    "λάβετε έτοιμα έντυπα για αποστολή στη Μεγ. Γεν. Γραμματεία"
)

# ══════════════════════════════════════════════════════════════
# ΣΤΑΘΕΡΕΣ — ΔΙΑΔΙΚΑΣΙΕΣ
# ══════════════════════════════════════════════════════════════
FORMS_ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "forms")

DIKADIKASIEES: Dict[str, Dict] = {

    "📥 Εισδοχή Υποψηφίου": {
        "code": "eisodoxh",
        "subtitle": "Άρθρα 95–105 Γ.Κ.",
        "description": (
            "Πλήρης διαδικασία αποδοχής νέου μέλους: από την υποβολή "
            "της Συστατικής Δήλωσης ως την έγκριση της Μεγ. Στοάς."
        ),
        "deadline_note": "⏱️ Εντός 8 μηνών από έγκριση ΜΣΤ πρέπει να γίνει η μύηση (άρ. 105).",
        "steps": [
            ("1", "Απαιτούμενα έντυπα", [
                "Βιογραφικό Σημείωμα υποψηφίου",
                "Συστατική Δήλωση προτείνοντος Διδασκάλου (Αναδόχου)",
                "Αίτηση Εισδοχής υποψηφίου",
                "Υπεύθυνη Δήλωση υποψηφίου",
                "Εμπιστευτική Έκθεση εντεταλμένου Διδ (×3)",
                "2+2 φωτογραφίες (έγχρωμες, σακάκι & γραβάτα)",
            ]),
            ("2", "Υποβολή Συστατικής Δήλωσης & Βιογραφικού στη Στοά", ["Άρ. 95§1"]),
            ("3", "Ερώτηση στη Μεγ. Γεν. Γραμματεία για ιδιαίτερη κατάσταση", ["Άρ. 95§3"]),
            ("4", "Απόφαση Συμβουλίου Αξιωμ. εντός 1 μηνός", ["Άρ. 95§2 · Κ.Χ. 13"]),
            ("5", "Υποβολή Αίτησης Εισδοχής + Υπεύθυνης Δήλωσης (Σάκος Προτάσεων)", ["Άρ. 95§4 & 96"]),
            ("6", "Ανάγνωση Αίτησης & κατ' αρχήν φανερή ψηφοφορία", ["Άρ. 97§1 & 2"]),
            ("7α", "Ανάθεση σε 3 Διδ. για εμπιστ. πληρ. (εντός 7 ημ.) — έκθεση εντός 20 ημ.", ["Άρ. 97§2-4"]),
            ("7β", "Αίτηση προς λοιπές Στοές για πληροφορίες (εντός 1 μηνός)", ["Άρ. 97§4"]),
            ("7γ", "Ανάρτηση πίνακα με φωτογραφία στον Πρόναο (επί 1 μήνα)", ["Άρ. 98§1 & 2"]),
            ("8", "1 μήνα μετά: ανάγνωση 3 εκθέσεων & μυστική ψηφοφορία (σφαιρίδια)", ["Άρ. 100§1-4"]),
            ("9", "Αν αρνητικό: αποστολή ανακοίνωσης στη Μεγ. Γεν. Γραμματεία", ["Άρ. 100§3-4"]),
            ("10", "Αν θετικό: υποβολή πλήρους φακέλου στη Μεγ. Γεν. Γραμματεία", ["Άρ. 104§1"]),
            ("11", "Μεγ. Γεν. Γραμμ. εκδίδει Εγκριτικό Πίνακα Εισδοχής", []),
            ("12", "Μετά τη Μύηση: αποστολή αποκόμματος Αναγγελίας Εισδοχής", []),
        ],
        "forms": [
            {"name": "1. Βιογραφικό Σημείωμα Υποψηφίου",
             "file": "eisodoxh/1_-_ΒΙΟΓΡΑΦΙΚΟ_ΣΗΜΕΙΩΜΑ_ΥΠΟΨΗΦΙΟΥ.docx",
             "description": "Προσωπικά στοιχεία υποψηφίου"},
            {"name": "2. Συστατική Δήλωση Προτείνοντος Διδ.",
             "file": "eisodoxh/2_-_ΣΥΣΤΑΤΙΚΗ_ΔΗΛΩΣΗ_ΠΡΟΤΕΙΝΟΝΤΟΣ_ΔΙΔΑΣΚΑΛΟΥ.docx",
             "description": "Δήλωση Αναδόχου Διδασκάλου"},
            {"name": "3. Αίτηση Εισδοχής",
             "file": "eisodoxh/3_-_ΑΙΤΗΣΗ_ΕΙΣΔΟΧΗΣ__2024_05__2_.docx",
             "description": "Επίσημη αίτηση εισδοχής"},
            {"name": "4. Υπεύθυνη Δήλωση Υποψηφίου",
             "file": "eisodoxh/4_-_ΥΠΕΥΘΥΝΗ__ΔΗΛΩΣΗ__ΥΠΟΨΗΦΙΟΥ.docx",
             "description": "GDPR & δεδομένα"},
            {"name": "5. Εμπιστευτική Έκθεση Διδασκάλου",
             "file": "eisodoxh/5_-_ΕΜΠΙΣΤΕΥΤΙΚΗ_ΕΚΘΕΣΗ_ΔΙΔΑΣΚΑΛΟΥ.docx",
             "description": "Έκθεση εντεταλμένου (×3 αντίγραφα)"},
        ],
        "input_groups": [
            {
                "title": "👤 Στοιχεία Υποψηφίου",
                "fields": [
                    ("yp_eponimo",   "Επώνυμο",             "text",   ""),
                    ("yp_onoma",     "Όνομα",               "text",   ""),
                    ("yp_patronimo", "Πατρώνυμο",           "text",   ""),
                    ("yp_mitronimo", "Μητρώνυμο",           "text",   ""),
                    ("yp_gennisi",   "Ημ/νία Γέννησης",     "date",   ""),
                    ("yp_topos",     "Τόπος Γέννησης",      "text",   ""),
                    ("yp_epaggelma", "Επάγγελμα",           "text",   ""),
                    ("yp_diefthinsi","Διεύθυνση Κατοικίας", "text",   ""),
                    ("yp_poli",      "Πόλη",                "text",   "Αθήνα"),
                    ("yp_tilefono",  "Τηλέφωνο",            "text",   ""),
                    ("yp_kinito",    "Κινητό",              "text",   ""),
                    ("yp_email",     "Email",               "text",   ""),
                    ("yp_adt",       "Α.Δ.Τ. / Διαβατήριο","text",   ""),
                    ("yp_afm",       "Α.Φ.Μ.",              "text",   ""),
                    ("yp_oikogeneiaki","Οικογενειακή Κατάσταση","text",""),
                ],
            },
            {
                "title": "🤝 Στοιχεία Αναδόχου Διδασκάλου",
                "fields": [
                    ("an_eponimo",   "Επώνυμο Αναδόχου",   "member", ""),
                    ("an_onoma",     "Όνομα",               "auto",   ""),
                    ("an_arith",     "Αρ. Μητρώου Στοάς",  "auto",   ""),
                ],
            },
            {
                "title": "📋 Στοιχεία Στοάς & Διαδικασίας",
                "fields": [
                    ("st_sev",       "Σεβάσμιος",          "member", ""),
                    ("st_gramm",     "Γραμματεύς",         "member", ""),
                    ("st_imerominia_synedrias", "Ημ/νία Συνεδρίας", "date", ""),
                    ("st_arithos_protokollou",  "Αρ. Πρωτοκόλλου", "text",  ""),
                ],
            },
        ],
        "claude_hint": (
            "Πρόκειται για εισδοχή νέου μέλους σε Τεκτονική Στοά. "
            "Συμπλήρωσε τα έντυπα με επίσημη γλώσσα. "
            "Χρησιμοποίησε τεκτονικές συντομογραφίες (Σεβ∴ Διδ∴, Αδ∴ κλπ). "
            "Βάσει άρθρων 95-105 Γεν. Κανονισμού ΜΣΤΕ."
        ),
    },

    "📈 Αύξηση Μισθοδοσίας (Εταίρος)": {
        "code": "auxisi_etairos",
        "subtitle": "Άρθρο 116 Γ.Κ.",
        "description": (
            "Διαδικασία προαγωγής Μαθητή σε Εταίρο. "
            "Απαιτείται παρέλευση 1 έτους από τη μύηση και παρουσία στα 2/3 των συνεδριών."
        ),
        "deadline_note": "⏱️ Παρέλευση 1 έτους από μύηση (άρ. 113). Παρουσία σε 2/3 συνεδριών.",
        "steps": [
            ("1", "Πάροδος 1 έτους από μύηση στον βαθμό Μαθητού", ["Άρ. 113"]),
            ("2", "Παρουσία σε 2/3 συνεδριών ως Μαθητής (Βιβλίο Παρουσίας)", ["Άρ. 113"]),
            ("3", "Υποβολή Πρότασης Αύξησης Μισθοδοσίας (Σάκος Προτάσεων) — 2 Διδ. υπογράφουν", ["Άρ. 116§1"]),
            ("4", "Ανάγνωση & κατ' αρχήν φανερή ψηφοφορία", ["Άρ. 116§2"]),
            ("5", "Επόμενη συνεδρία Εταίρου: μυστική ψηφοφορία (3/4 πλειοψηφία)", ["Άρ. 116§3"]),
            ("6", "Αν αρνητικό: ανακοίνωση στη Μεγ. Γεν. Γραμματεία", []),
            ("7", "Αν θετικό: υποβολή εντύπου στη Μεγ. Γεν. Γραμματεία (πρωτότυπο + e-mail)", ["Άρ. 116§4"]),
            ("8", "Μεγ. Γεν. Γραμμ. εκδίδει Εγκριτικό Πίνακα — καταβολή μύετρων", []),
            ("9", "Μετά τη Μύηση: αποστολή αποκόμματος Αναγγελίας Αύξησης", []),
        ],
        "forms": [
            {"name": "1. Αύξηση Μισθοδοσίας Εταίρου",
             "file": "auxisi/1_-_ΑΥΞΗΣΗ_ΜΙΣΘΟΔΟΣΙΑΣ_ΕΤΑΙΡΟΥ.docx",
             "description": "Δίφυλλο έντυπο: Πρόταση + Αίτηση Έγκρισης"},
        ],
        "input_groups": [
            {
                "title": "👤 Στοιχεία Υποψηφίου",
                "fields": [
                    ("yp_melos",     "Μέλος (Υποψήφιος)",  "member", ""),
                    ("yp_eponimo",   "Επώνυμο",             "auto",   ""),
                    ("yp_onoma",     "Όνομα",               "auto",   ""),
                    ("yp_arith",     "Αρ. Μητρώου Στοάς",  "auto",   ""),
                    ("yp_arith_ms",  "Αρ. Μητρώου ΜΣ",     "auto",   ""),
                    ("yp_im_mithsis","Ημ/νία Μύησης (Μαθ.)","auto",  ""),
                    ("yp_par_synedrion","Αριθμός παρουσιών","number", ""),
                    ("yp_synolikoi","Συν. συνεδρίες Μαθητού","number",""),
                ],
            },
            {
                "title": "✍️ Προτείνοντες Διδάσκαλοι",
                "fields": [
                    ("pr1_melos",    "1ος Προτείνων",       "member", ""),
                    ("pr2_melos",    "2ος Προτείνων",       "member", ""),
                ],
            },
            {
                "title": "📋 Στοιχεία Στοάς",
                "fields": [
                    ("st_sev",       "Σεβάσμιος",          "member", ""),
                    ("st_gramm",     "Γραμματεύς",         "member", ""),
                    ("st_imerominia","Ημ/νία Συνεδρίας",   "date",   ""),
                    ("st_psifoi_yper","Ψήφοι υπέρ",        "number", ""),
                    ("st_psifoi_kata","Ψήφοι κατά",        "number", ""),
                    ("st_paronton",  "Παρόντες (αριθμός)", "number", ""),
                ],
            },
        ],
        "claude_hint": (
            "Πρόκειται για αύξηση μισθοδοσίας Μαθητή σε Εταίρο (βαθμός Εταίρου). "
            "Βάσει άρθρου 116 Γεν. Κανονισμού. Απαιτείται 1 έτος από μύηση και 2/3 παρουσίες. "
            "Συμπλήρωσε με επίσημη τεκτονική γλώσσα."
        ),
    },

    "🗳️ Εκλογές Αξιωματικών & Εγκατάσταση": {
        "code": "ekloges",
        "subtitle": "Άρθρα 73–86 Γ.Κ.",
        "description": (
            "Εκλογή Σεβασμίου, Συμβουλίου Αξιωματικών & Αντιπροσώπων. "
            "Υποβολή εντύπων στη Μεγ. Γεν. Γραμματεία εντός 10 ημερών."
        ),
        "deadline_note": "⏱️ Εντός 10 ημερών από αρχαιρεσίες υποβολή (άρ. 85§2). Εντός Οκτωβρίου.",
        "steps": [
            ("1", "Ελέγχος εκλογέων (1/3 παρουσιών τελευταίας διετίας)", ["Άρ. 73§2 & 128"]),
            ("2", "Ελέγχος εκλεξίμων (αρ. 73, 74 — ειδικές προϋποθέσεις για Σεβάσμιο)", ["Άρ. 73, 74"]),
            ("3", "Συνεδρία Μέσου Δώματος — παρουσία ≥ 1/2+1 Διδ. με δικ. ψήφου", ["Άρ. 73§3 & 138"]),
            ("4", "Εκλογή Σεβασμίου (1η ψηφοφορία)", ["Άρ. 77-83"]),
            ("5", "Εκλογή Α' & Β' Εποπτών", ["Άρ. 77"]),
            ("6", "Εκλογή λοιπών Αξιωματικών & Εξελεγκτικής Επιτροπής", ["Άρ. 77"]),
            ("7", "Τυχόν εκλογή Αντιπροσώπων (συμπίπτει ή χωριστά)", ["Άρ. 80 & 81§5"]),
            ("8", "Ανακοίνωση αποτελεσμάτων — επευφημία Στοάς", ["Άρ. 82"]),
            ("9", "Εντός 10 ημ.: υποβολή εντύπων α–ε στη Μεγ. Γεν. Γραμμ.", ["Άρ. 85§2"]),
            ("10","Εντός 15 Οκτωβρίου: Διοικητικός & Οικον. Απολογισμός", []),
            ("11","Μεγ. Στοά εγκρίνει — έκδοση Εγκριτικών Πινάκων", ["Άρ. 86"]),
            ("12","Αίτηση ημερομηνίας εγκατάστασης (εντός 30 ημ. από έγκριση)", ["Άρ. 88"]),
            ("13","Εγκατάσταση νέων Αρχών — αναγγελία στη Μεγ. Γεν. Γραμμ.", []),
        ],
        "forms": [
            {"name": "1. Αναγγελία Εκλογής Σεβασμίου & Συμβουλίου",
             "file": "ekloges/1_-_ΑΝΑΓΓΕΛΙΑ_ΕΚΛΟΓΗΣ_ΣΕΒΑΣΜΙΟΥ___ΣΥΜΒΟΥΛΙΟΥ.docx",
             "description": "Κύρια αναγγελία αποτελεσμάτων"},
            {"name": "2Α. Απόσπασμα Εκλογής Αξιωματικών",
             "file": "ekloges/2Α_-_ΑΠΟΣΠΑΣΜΑ_ΕΚΛΟΓΗΣ_ΑΞΙΩΜΑΤΙΚΩΝ.docx",
             "description": "Απόσπασμα πρακτικών συνεδρίας εκλογής"},
            {"name": "3. Αναλυτικός Πίνακας Εκλεγέντων",
             "file": "ekloges/3_-_ΑΝΑΛΥΤΙΚΟΣ_ΠΙΝΑΚΑΣ__ΕΚΛΕΓΕΝΤΩΝ_ΑΞΙΩΜΑΤΙΚΩΝ.docx",
             "description": "Πίνακας με ψήφους ανά αξίωμα"},
            {"name": "4. Κατάσταση Εκλεγέντων Αξιωματικών",
             "file": "ekloges/4_-_ΚΑΤΑΣΤΑΣΗ_ΕΚΛΕΓΕΝΤΩΝ_ΑΞΙΩΜΑΤΙΚΩΝ.docx",
             "description": "Σύνοψη εκλεγέντων"},
            {"name": "5. Ονομαστική Κατάσταση Ψηφισάντων",
             "file": "ekloges/5_-_ΟΝΟΜΑΣΤΙΚΗ_ΚΑΤΑΣΤΑΣΗ_ΨΗΦΙΣΑΝΤΩΝ.docx",
             "description": "Κατάλογος Διδ. που ψήφισαν"},
        ],
        "input_groups": [
            {
                "title": "🏛️ Νέο Συμβούλιο Αξιωματικών",
                "fields": [
                    ("ax_sev",    "Σεβάσμιος",             "member", ""),
                    ("ax_a_ep",   "Α' Επόπτης",            "member", ""),
                    ("ax_b_ep",   "Β' Επόπτης",            "member", ""),
                    ("ax_rhtor",  "Ρήτωρ",                 "member", ""),
                    ("ax_gramm",  "Γραμματεύς-Σφραγιδοφύλαξ","member",""),
                    ("ax_tamias", "Ταμίας",                "member", ""),
                    ("ax_eleon",  "Ελεονόμος",             "member", ""),
                    ("ax_tel",    "Τελετάρχης",            "member", ""),
                    ("ax_steg",   "Στεγαστής",             "member", ""),
                    ("ax_a_dok",  "Α' Δοκιμαστής",         "member", ""),
                    ("ax_b_dok",  "Β' Δοκιμαστής",         "member", ""),
                    ("ax_arxitekt","Αρχιτέκτων-Αρχιτρίκλινος","member",""),
                    ("ax_arxif",  "Αρχειοφύλαξ-Βιβλιοφύλαξ","member",""),
                    ("ax_xifok",  "Ξιφοφόρος-Σηματοφόρος",  "member", ""),
                ],
            },
            {
                "title": "➕ Πρόσθετοι Αξιωματικοί (αν υπάρχουν)",
                "fields": [
                    ("pr_rhtor",  "Πρόσθ. Ρήτωρ",          "member", ""),
                    ("pr_gramm",  "Πρόσθ. Γραμματεύς",     "member", ""),
                    ("pr_tamias", "Πρόσθ. Ταμίας",          "member", ""),
                    ("pr_eleon",  "Πρόσθ. Ελεονόμος",       "member", ""),
                    ("pr_tel",    "Πρόσθ. Τελετάρχης",      "member", ""),
                ],
            },
            {
                "title": "🗓️ Στοιχεία Αρχαιρεσιών",
                "fields": [
                    ("ekl_imerominia", "Ημ/νία Αρχαιρεσιών",   "date",   ""),
                    ("ekl_dikaiom",    "Εκλογείς (αριθμός)",    "number", ""),
                    ("ekl_paronton",   "Παρόντες κατά εκλογή",  "number", ""),
                    ("ekl_psifisantes","Ψηφίσαντες",            "number", ""),
                    ("ekl_diettia",    "Τεκτονική Διετία",      "text",   "2024-2026"),
                ],
            },
            {
                "title": "📊 Εξελεγκτική Επιτροπή",
                "fields": [
                    ("ex_1", "1ο Μέλος",  "member", ""),
                    ("ex_2", "2ο Μέλος",  "member", ""),
                    ("ex_3", "3ο Μέλος",  "member", ""),
                ],
            },
        ],
        "claude_hint": (
            "Εκλογές Αξιωματικών Τεκτονικής Στοάς. Βάσει άρθρων 73-86 Γεν. Κανονισμού ΜΣΤΕ. "
            "Η εκλογή γίνεται ανά διετία με μυστική δια ψηφοδελτίων ψηφοφορία. "
            "Χρησιμοποίησε επίσημη τεκτονική γλώσσα και συντομογραφίες."
        ),
    },

    "📣 Αναγγελία Μεταβολών": {
        "code": "metavoles",
        "subtitle": "Άρθρα 159–175 Γ.Κ.",
        "description": (
            "Αναγγελία μεταβολών μελών (θάνατος, αποχώρηση, διαγραφή, "
            "οικονομική ταξινόμηση, αναστολή κλπ.)."
        ),
        "deadline_note": "⏱️ Άμεση αναγγελία στη Μεγ. Γεν. Γραμματεία.",
        "steps": [
            ("1", "Καταγραφή μεταβολής στα πρακτικά Στοάς", []),
            ("2", "Συμπλήρωση εντύπου Αναγγελίας Μεταβολών", []),
            ("3", "Υπογραφή από Σεβ. & Γραμματεύς + Σφραγίδα Στοάς", []),
            ("4", "Αποστολή στη Μεγ. Γεν. Γραμματεία (αυτοπροσώπως ή e-mail)", []),
        ],
        "forms": [
            {"name": "1. Αναγγελία Μεταβολών",
             "file": "metavoles/1_-_ΑΝΑΓΓΕΛΙΑ_ΜΕΤΑΒΟΛΩΝ.docx",
             "description": "Έντυπο αναγγελίας μεταβολής μέλους"},
        ],
        "input_groups": [
            {
                "title": "👤 Στοιχεία Μέλους",
                "fields": [
                    ("melos",        "Μέλος",               "member", ""),
                    ("eponimo",      "Επώνυμο",             "auto",   ""),
                    ("onoma",        "Όνομα",               "auto",   ""),
                    ("arith_stoias", "Αρ. Μητρώου Στοάς",  "auto",   ""),
                    ("arith_ms",     "Αρ. Μητρώου ΜΣ",     "auto",   ""),
                    ("vathmος",      "Τεκτονικός Βαθμός",  "auto",   ""),
                ],
            },
            {
                "title": "📝 Τύπος Μεταβολής",
                "fields": [
                    ("typos_metavolis", "Τύπος Μεταβολής", "select",
                     ["Θάνατος", "Εκούσια Αποχώρηση", "Διαγραφή λόγω οφειλών",
                      "Αναστολή Δικαιωμάτων", "Επαναφορά σε Ενεργό",
                      "Αλλαγή Στοιχείων", "Άλλη μεταβολή"]),
                    ("imerominia_metavolis", "Ημ/νία Μεταβολής", "date", ""),
                    ("perigrafh",    "Περιγραφή / Παρατηρήσεις", "textarea", ""),
                ],
            },
            {
                "title": "📋 Στοιχεία Στοάς",
                "fields": [
                    ("st_sev",   "Σεβάσμιος",  "member", ""),
                    ("st_gramm", "Γραμματεύς", "member", ""),
                    ("st_date",  "Ημ/νία",     "date",   ""),
                ],
            },
        ],
        "claude_hint": (
            "Αναγγελία μεταβολής μέλους Τεκτονικής Στοάς. "
            "Συμπλήρωσε με επίσημη γλώσσα. Τεκτονικές συντομογραφίες όπου αρμόζει."
        ),
    },

    "🤝 Κοινή Συνεδρία Στοών": {
        "code": "koinh_synedria",
        "subtitle": "Εγκύκλιος ΜΣΤΕ",
        "description": (
            "Αίτηση έγκρισης κοινής συνεδρίας μεταξύ 2 ή περισσότερων Στοών "
            "υπό την Αιγίδα της ΜΣΤΕ. Υποβολή τουλάχιστον 15 ημέρες πριν."
        ),
        "deadline_note": "⏱️ Υποβολή ≥ 15 ημέρες πριν τη συνεδρία.",
        "steps": [
            ("1", "Επικοινωνία & συμφωνία με τη συνεργαζόμενη Στοά", []),
            ("2", "Συμπλήρωση Αίτησης Έγκρισης (τουλ. 15 ημ. πριν)", []),
            ("3", "Κοινοποίηση στις συνεργαζόμενες Στοές", []),
            ("4", "Αποστολή στη Μεγ. Γεν. Γραμματεία", []),
            ("5", "Μεγ. Γεν. Γραμμ. εκδίδει Εγκριτικό Πίνακα", []),
        ],
        "forms": [
            {"name": "2. Έγκριση Κοινής Συνεδρίας",
             "file": "loipa/2_-_ΕΓΚΡΙΣΗ_ΚΟΙΝΗΣ_ΣΥΝΕΔΡΙΑΣ.docx",
             "description": "Αίτηση έγκρισης κοινής συνεδρίας"},
        ],
        "input_groups": [
            {
                "title": "🏛️ Συνεργαζόμενες Στοές",
                "fields": [
                    ("stoaa_name",  "Στοά Α (η αιτούσα)",    "text", "ΑΚΡΟΠΟΛΙΣ 84"),
                    ("stoab_name",  "Στοά Β",                "text", ""),
                    ("stoac_name",  "Στοά Γ (αν υπάρχει)",   "text", ""),
                ],
            },
            {
                "title": "📅 Στοιχεία Συνεδρίας",
                "fields": [
                    ("syn_imerominia",  "Ημ/νία Κοινής Συνεδρίας", "date",   ""),
                    ("syn_ora",         "Ώρα",                     "text",   "20:00"),
                    ("syn_topos",       "Τόπος",                   "text",   "Τεκτ. Ναός"),
                    ("syn_vathmος",     "Βαθμός Εργασιών",         "select", ["Μαθητού", "Εταίρου", "Διδασκάλου"]),
                    ("syn_omilitis",    "Ομιλητής",                "member", ""),
                    ("syn_thema",       "Θέμα Ομιλίας",            "textarea",""),
                ],
            },
            {
                "title": "📋 Στοιχεία Αιτούσας Στοάς",
                "fields": [
                    ("st_sev",   "Σεβάσμιος",  "member", ""),
                    ("st_gramm", "Γραμματεύς", "member", ""),
                    ("st_date",  "Ημ/νία",     "date",   ""),
                ],
            },
        ],
        "claude_hint": (
            "Αίτηση έγκρισης κοινής συνεδρίας Τεκτονικών Στοών. "
            "Επίσημη γλώσσα, τεκτονικές συντομογραφίες. "
            "Ο ομιλητής πρέπει να αναφέρεται με αξίωμα."
        ),
    },

    "🌟 Λευκή Εορτή / Ανοικτή Εκδήλωση": {
        "code": "lefkh_eorth",
        "subtitle": "Εγκύκλιοι 89(Ο)/1999 & 24(Κ)/2002",
        "description": (
            "Αίτηση έγκρισης Λευκής Εορτής (Υιοθεσία Λυκιδέων, Μνημόσυνο, "
            "Αναγνώριση Συζυγικού Δεσμού) ή Ανοικτής Εκδήλωσης. "
            "Υποβολή ≥ 2 μήνες πριν."
        ),
        "deadline_note": "⏱️ Υποβολή ≥ 2 εργάσιμοι μήνες πριν την εκδήλωση.",
        "steps": [
            ("1", "Επιλογή τύπου εκδήλωσης (Λευκή Εορτή ή Ανοικτή Εκδήλωση)", []),
            ("2", "Τακτοποίηση οικονομικών υποχρεώσεων προς Μεγ. Θησαυροφυλάκιο", ["Εγκ. 11/1995"]),
            ("3", "Υποβολή Αίτησης Έγκρισης ≥ 2 μήνες πριν", ["Εγκ. 89(Ο)/1999"]),
            ("4", "Αν ομιλητής δεν είναι Ένδ. Αδ: υποβολή κειμένου ομιλίας για έγκριση", []),
            ("5", "Μεγ. Γεν. Γραμμ. εγκρίνει — αποστολή προσκλήσεων μόνο σε Στοές ΜΣΤΕ", ["Άρ. 189"]),
        ],
        "forms": [
            {"name": "4. Έγκριση Λευκής Εορτής / Ανοικτής Εκδήλωσης",
             "file": "loipa/4_-_ΕΓΚΡΙΣΗ_ΛΕΥΚΗΣ_ΕΟΡΤΗΣ_-_ΑΝΟΙΚ__ΕΚΔΗΛΩΣΕΩΣ.docx",
             "description": "Αίτηση έγκρισης"},
        ],
        "input_groups": [
            {
                "title": "🎉 Στοιχεία Εκδήλωσης",
                "fields": [
                    ("typos",         "Τύπος",              "select",
                     ["Υιοθεσία Λυκιδέων", "Τεκτονικό Μνημόσυνο",
                      "Τεκτ. Αναγνώριση Συζυγικού Δεσμού", "Ανοικτή Εκδήλωση"]),
                    ("imerominia",    "Ημ/νία Εκδήλωσης",  "date",   ""),
                    ("ora",           "Ώρα",                "text",   "19:30"),
                    ("topos",         "Τόπος",              "text",   ""),
                    ("omilitis",      "Ομιλητής",           "member", ""),
                    ("thema_omilias", "Θέμα Ομιλίας",      "textarea",""),
                    ("ypeuthinos",    "Υπεύθυνος Οργ.",     "member", ""),
                ],
            },
            {
                "title": "📋 Στοιχεία Στοάς",
                "fields": [
                    ("st_sev",   "Σεβάσμιος",  "member", ""),
                    ("st_gramm", "Γραμματεύς", "member", ""),
                    ("st_date",  "Ημ/νία",     "date",   ""),
                ],
            },
        ],
        "claude_hint": (
            "Αίτηση έγκρισης Λευκής Εορτής ή Ανοικτής Εκδήλωσης Τεκτονικής Στοάς. "
            "Βάσει εγκυκλίων 89(Ο)/1999 και 24(Κ)/2002 ΜΣΤΕ. "
            "Επίσημη γλώσσα και τεκτονικές συντομογραφίες."
        ),
    },
}

STOAA_NAME = "ΑΚΡΟΠΟΛΙΣ"
STOAA_NUMBER = "84"
STOAA_ANATOLI = "Αθηνών"

# ══════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════
def get_anthropic_key() -> str:
    try:
        return (
            st.secrets.get("AI", {}).get("ANTHROPIC_API_KEY")
            or st.secrets.get("ANTHROPIC_API_KEY", "")
        )
    except Exception:
        return ""


def load_members_dict() -> Dict[int, Dict]:
    """Returns {id: member_dict}"""
    try:
        df = get_all_members()
        result = {}
        for _, row in df.iterrows():
            result[int(row["id"])] = row.to_dict()
        return result
    except Exception:
        return {}


def member_display_name(m: Dict) -> str:
    vatm = m.get("τεκτονικός_βαθμός", "")
    prefix = {"Μαθητής": "Αδ∴", "Εταίρος": "Αδ∴", "Διδάσκαλος": "Αδ∴"}.get(vatm, "Αδ∴")
    return f"{prefix} {m.get('επώνυμο','')} {m.get('όνομα','')}".strip()


def read_docx_text(path: str) -> str:
    """Extract raw text from docx for passing to Claude."""
    try:
        from docx import Document
        doc = Document(path)
        lines = []
        for p in doc.paragraphs:
            if p.text.strip():
                lines.append(p.text.strip())
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    if cell.text.strip():
                        lines.append(cell.text.strip())
        return "\n".join(lines)
    except Exception as e:
        return f"[Σφάλμα ανάγνωσης: {e}]"


def fill_docx_with_replacements(template_path: str, replacements: Dict[str, str]) -> bytes:
    """
    Fill a docx template by replacing placeholder strings.
    Replacements format: {"PLACEHOLDER": "value"}
    """
    from docx import Document
    from docx.oxml.ns import qn
    import copy

    doc = Document(template_path)

    def replace_in_paragraph(para):
        full_text = "".join(r.text for r in para.runs)
        replaced = full_text
        for placeholder, value in replacements.items():
            replaced = replaced.replace(placeholder, value)
        if replaced != full_text and para.runs:
            # Put all text in first run, clear rest
            para.runs[0].text = replaced
            for r in para.runs[1:]:
                r.text = ""

    for para in doc.paragraphs:
        replace_in_paragraph(para)

    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for para in cell.paragraphs:
                    replace_in_paragraph(para)

    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf.read()


def claude_fill_form(
    form_template_text: str,
    user_data: Dict[str, str],
    procedure_hint: str,
    stoaa_info: str,
) -> Dict[str, str]:
    """
    Asks Claude to return a JSON dict of {field_description: filled_value}
    that can be used to fill the docx template.
    """
    key = get_anthropic_key()
    if not key:
        return {}
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=key)

        system = """
Είσαι βοηθός Γραμματέως-Σφραγιδοφύλακα Τεκτονικής Στοάς.
Σου δίνεται ένα πρότυπο εντύπου ΜΣΤΕ (κείμενο από docx) και τα στοιχεία που συμπλήρωσε ο χρήστης.

Στόχος: Επέστρεψε JSON object με {"παλιό_κείμενο": "νέο_κείμενο"} για text-replacement στο docx.

ΣΗΜΑΝΤΙΚΟΙ ΚΑΝΟΝΕΣ:
1. Τα κλειδιά πρέπει να είναι ΑΚΡΙΒΕΣ κείμενο που υπάρχει στο έντυπο (κενές γραμμές, ..., tabs)
2. Για εντυπά με πίνακες αξιωματικών: αντιστοίχισε ΑΞΙΩΜΑ → ΟΝΟΜΑΤΕΠΩΝΥΜΟ
3. Για ημερομηνίες χρησιμοποίησε μορφή ΗΗ/ΜΜ/ΕΕΕΕ
4. Χρησιμοποίησε επίσημη τεκτονική γλώσσα και συντομογραφίες (Αδ∴, Σεβ∴ Διδ∴ κλπ)
5. Χρησιμοποίησε ΜΟΝΟ string τιμές, ΟΧΙ tab (\t) ή άλλους special characters στις τιμές
6. Επέστρεψε ΜΟΝΟ valid JSON χωρίς markdown και χωρίς backticks
7. Αν πεδίο δεν έχει τιμή, παράλειψέ το (μην βάζεις κενή τιμή)

Για την Κατάσταση Εκλεγέντων (έντυπο 4) και Αναλυτικό Πίνακα (έντυπο 3):
- Κάθε γραμμή πίνακα έχει αξίωμα στην αριστερή στήλη
- Βάλε το ονοματεπώνυμο στη δεξιά στήλη χρησιμοποιώντας ακριβές κείμενο ως key
""".strip()

        user_msg = f"""
Τύπος διαδικασίας: {procedure_hint}
Στοιχεία Στοάς: {stoaa_info}

Δεδομένα αξιωματικών από τον χρήστη:
{json.dumps(user_data, ensure_ascii=False, indent=2)}

Κείμενο εντύπου (από docx):
{form_template_text[:4000]}

Επέστρεψε JSON replacements {{"κείμενο_στο_έντυπο": "συμπλήρωση"}}.
ΣΗΜΑΝΤΙΚΟ: Μόνο απλά strings στις τιμές, χωρίς \t ή control characters.
""".strip()

        msg = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2000,
            system=system,
            messages=[{"role": "user", "content": user_msg}],
        )
        raw = msg.content[0].text if msg.content else "{}"
        raw = re.sub(r"^```(?:json)?\s*", "", raw.strip(), flags=re.MULTILINE)
        raw = re.sub(r"\s*```\s*$", "", raw, flags=re.MULTILINE).strip()
        # Αφαίρεση control characters που σπάνε το json.loads
        raw = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", raw)
        # Αντικατάσταση tabs εντός strings με κενό
        raw = re.sub(r"\t", " ", raw)
        return json.loads(raw)
    except Exception as e:
        st.warning(f"⚠️ Claude error: {e}")
        return {}


def create_zip(files: List[Tuple[str, bytes]]) -> bytes:
    """Create a zip with multiple docx files."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, data in files:
            zf.writestr(name, data)
    buf.seek(0)
    return buf.read()


# ══════════════════════════════════════════════════════════════
# UI — ΕΠΙΛΟΓΗ ΔΙΑΔΙΚΑΣΙΑΣ
# ══════════════════════════════════════════════════════════════
col_left, col_right = st.columns([1, 2])

with col_left:
    st.markdown("### 📌 Επιλογή Διαδικασίας")
    selected = st.selectbox(
        "Διαδικασία",
        list(DIKADIKASIEES.keys()),
        label_visibility="collapsed",
    )

proc = DIKADIKASIEES[selected]

with col_right:
    st.info(f"**{selected}** — {proc['subtitle']}\n\n{proc['description']}")
    if proc.get("deadline_note"):
        st.warning(proc["deadline_note"])

st.markdown("---")

# ══════════════════════════════════════════════════════════════
# ΚΑΡΤΕΛΕΣ: Βήματα | Έντυπα | Συμπλήρωση
# ══════════════════════════════════════════════════════════════
tab_steps, tab_forms, tab_fill = st.tabs([
    "📋 Βήματα Διαδικασίας",
    "📁 Απαιτούμενα Έντυπα",
    "✍️ Συμπλήρωση & Λήψη",
])

# ──────────────────────────────────────────────────────────────
# TAB 1: ΒΗΜΑΤΑ
# ──────────────────────────────────────────────────────────────
with tab_steps:
    st.markdown(f"### Βήματα Διαδικασίας: {selected}")
    st.caption(
        "Βάσει Οδηγού Διαδικασιών & Απαιτούμενων Ενεργειών (Δεκ. 2017) "
        "και Γεν. Κανονισμού ΜΣΤΕ"
    )

    for step_num, step_title, refs in proc["steps"]:
        ref_str = " · ".join(refs) if refs else ""
        with st.expander(f"**Βήμα {step_num}** — {step_title}", expanded=False):
            if isinstance(refs, list) and refs and refs[0].startswith("•"):
                for r in refs:
                    st.markdown(r)
            elif ref_str:
                st.caption(f"📖 {ref_str}")
            else:
                st.caption("Εσωτερική διαδικασία Στοάς")

    # Απαιτούμενα έντυπα summary
    st.markdown("---")
    st.markdown("#### 📎 Απαιτούμενα Έντυπα")
    for f in proc["forms"]:
        path = os.path.join(FORMS_ROOT, f["file"])
        exists = os.path.exists(path)
        icon = "✅" if exists else "❌"
        st.markdown(f"{icon} **{f['name']}** — {f['description']}")

# ──────────────────────────────────────────────────────────────
# TAB 2: ΕΝΤΥΠΑ (preview + download blank)
# ──────────────────────────────────────────────────────────────
with tab_forms:
    st.markdown(f"### Έντυπα: {selected}")
    st.caption("Κατεβάστε τα κενά πρότυπα ή δείτε το περιεχόμενό τους.")

    all_blank = []
    for f in proc["forms"]:
        path = os.path.join(FORMS_ROOT, f["file"])
        st.markdown(f"#### {f['name']}")
        st.caption(f['description'])

        if os.path.exists(path):
            with open(path, "rb") as fh:
                data = fh.read()

            col1, col2 = st.columns([1, 3])
            with col1:
                fname = os.path.basename(f["file"])
                st.download_button(
                    f"⬇️ Κενό έντυπο",
                    data=data,
                    file_name=fname,
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    key=f"blank_{f['file']}",
                    use_container_width=True,
                )
                all_blank.append((fname, data))
            with col2:
                with st.expander("👁️ Προβολή κειμένου εντύπου"):
                    text = read_docx_text(path)
                    st.text(text[:1500] + ("…" if len(text) > 1500 else ""))
        else:
            st.error(f"❌ Δεν βρέθηκε: {path}")

        st.markdown("---")

    if len(all_blank) > 1:
        zip_data = create_zip(all_blank)
        st.download_button(
            f"📦 Λήψη όλων των κενών εντύπων (.zip)",
            data=zip_data,
            file_name=f"εντυπα_{proc['code']}.zip",
            mime="application/zip",
            use_container_width=True,
        )

# ──────────────────────────────────────────────────────────────
# TAB 3: ΣΥΜΠΛΗΡΩΣΗ
# ──────────────────────────────────────────────────────────────
with tab_fill:
    st.markdown(f"### ✍️ Συμπλήρωση Εντύπων: {selected}")
    st.caption(
        "Εισάγετε τα στοιχεία παρακάτω. Το σύστημα θα προσυμπληρώσει από "
        "το Μητρώο όπου είναι δυνατό και θα χρησιμοποιήσει Claude για "
        "αυτόματη συμπλήρωση των εντύπων."
    )

    # Φόρτωση μελών
    members_dict = load_members_dict()

    def member_selectbox(label: str, key: str) -> Optional[Dict]:
        """Selectbox επιλογής μέλους."""
        options = {0: "— Επιλογή μέλους —"}
        for mid, m in members_dict.items():
            options[mid] = f"{m.get('επώνυμο','')} {m.get('όνομα','')} ({m.get('τεκτονικός_βαθμός','')})"
        sel = st.selectbox(label, list(options.keys()),
                           format_func=lambda x: options[x], key=key)
        return members_dict.get(sel) if sel else None

    # Συλλογή δεδομένων ανά group
    collected: Dict[str, Any] = {}
    member_refs: Dict[str, Optional[Dict]] = {}  # field_id → member dict

    for group in proc["input_groups"]:
        st.markdown(f"#### {group['title']}")
        cols = st.columns(2)
        col_idx = 0

        for field_id, field_label, field_type, default in group["fields"]:
            if field_type == "auto":
                continue  # will be filled from member_refs

            with cols[col_idx % 2]:
                if field_type == "text":
                    collected[field_id] = st.text_input(
                        field_label, value=str(default), key=f"inp_{field_id}")
                elif field_type == "textarea":
                    collected[field_id] = st.text_area(
                        field_label, value=str(default), height=80, key=f"inp_{field_id}")
                elif field_type == "date":
                    try:
                        d = date.fromisoformat(default) if default else date.today()
                    except Exception:
                        d = date.today()
                    collected[field_id] = st.date_input(
                        field_label, value=d, key=f"inp_{field_id}"
                    ).strftime("%d/%m/%Y")
                elif field_type == "number":
                    collected[field_id] = st.number_input(
                        field_label, min_value=0, value=int(default) if default else 0,
                        key=f"inp_{field_id}")
                elif field_type == "select":
                    opts = default if isinstance(default, list) else [default]
                    collected[field_id] = st.selectbox(
                        field_label, opts, key=f"inp_{field_id}")
                elif field_type == "member":
                    sel_member = member_selectbox(field_label, key=f"inp_{field_id}")
                    member_refs[field_id] = sel_member
                    if sel_member:
                        collected[field_id] = member_display_name(sel_member)
                    else:
                        collected[field_id] = ""

            col_idx += 1

        # Auto-fill από member_refs
        for field_id, field_label, field_type, default in group["fields"]:
            if field_type != "auto":
                continue
            # Find the "member" field in same group
            base_id = field_id.rsplit("_", 1)[0]  # e.g. "yp_eponimo" → look for "yp_melos"
            # Try to find a member ref with matching prefix
            ref_member = None
            for mid_key, mref in member_refs.items():
                if mid_key.startswith(base_id.rsplit("_", 1)[0]) or base_id.startswith(mid_key.rsplit("_", 1)[0]):
                    ref_member = mref
                    break
                # Simple fallback: first member ref in group
                if not ref_member and mref:
                    ref_member = mref

            if ref_member:
                suffix = field_id.split("_")[-1]
                mapping = {
                    "eponimo":   ref_member.get("επώνυμο", ""),
                    "onoma":     ref_member.get("όνομα", ""),
                    "patronimo": ref_member.get("πατρώνυμο", ""),
                    "arith":     ref_member.get("αρ_μητρώου_στοάς", ""),
                    "arith_ms":  ref_member.get("αρ_μητρώου_μσ", ""),
                    "vathmος":   ref_member.get("τεκτονικός_βαθμός", ""),
                    "im_mithsis":ref_member.get("ημ_μύησης", ""),
                    "email":     ref_member.get("email", ""),
                }
                collected[field_id] = mapping.get(suffix, "")

        st.markdown("---")

    # Επιπλέον σχόλια
    extra_notes = st.text_area(
        "📝 Επιπλέον σχόλια / οδηγίες για τη συμπλήρωση",
        height=70,
        placeholder="π.χ. ειδικές παρατηρήσεις, σημειώσεις για Claude…",
        key="extra_notes",
    )

    # ── ΚΟΥΜΠΙ ΔΗΜΙΟΥΡΓΙΑΣ ────────────────────────────────────
    st.markdown("---")
    can_run = bool(get_anthropic_key())
    if not can_run:
        st.error("❌ Δεν βρέθηκε ANTHROPIC_API_KEY. Προσθέστε το στα Streamlit Secrets.")

    if st.button(
        "🤖 Συμπλήρωση Εντύπων με Claude",
        type="primary",
        use_container_width=True,
        disabled=not can_run,
        key="run_fill",
    ):
        stoaa_info = (
            f"Σ∴ Στ∴ {STOAA_NAME} υπ' αρ. {STOAA_NUMBER} εν Αν∴ {STOAA_ANATOLI}∴"
        )

        # Convert dates to string
        data_for_claude = {}
        for k, v in collected.items():
            data_for_claude[k] = str(v) if v is not None else ""
        if extra_notes:
            data_for_claude["extra_notes"] = extra_notes

        filled_files: List[Tuple[str, bytes]] = []
        progress = st.progress(0)
        n_forms = len(proc["forms"])

        for i, form_info in enumerate(proc["forms"]):
            path = os.path.join(FORMS_ROOT, form_info["file"])
            st.markdown(f"**⚙️ Επεξεργασία: {form_info['name']}…**")
            progress.progress(int((i / n_forms) * 80))

            if not os.path.exists(path):
                st.warning(f"⚠️ Δεν βρέθηκε: {path}")
                continue

            # 1. Ανάγνωση template
            template_text = read_docx_text(path)

            # 2. Claude → replacements
            with st.spinner(f"Claude συμπληρώνει «{form_info['name']}»…"):
                replacements = claude_fill_form(
                    template_text,
                    data_for_claude,
                    proc["claude_hint"],
                    stoaa_info,
                )

            # 3. Δημιουργία docx με replacements
            try:
                filled_bytes = fill_docx_with_replacements(path, replacements)
                fname = os.path.basename(form_info["file"])
                filled_files.append((fname, filled_bytes))

                st.download_button(
                    f"⬇️ {form_info['name']}",
                    data=filled_bytes,
                    file_name=fname,
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    key=f"dl_filled_{i}",
                    use_container_width=True,
                )

                if replacements:
                    with st.expander(f"🔍 Συμπλήρωση Claude για «{form_info['name']}»"):
                        for k, v in replacements.items():
                            if v:
                                st.markdown(f"- **{k[:60]}** → {v}")
            except Exception as e:
                st.error(f"❌ Σφάλμα δημιουργίας εντύπου: {e}")

        progress.progress(100)

        # ZIP όλων
        if len(filled_files) > 1:
            zip_data = create_zip(filled_files)
            st.markdown("---")
            st.download_button(
                f"📦 Λήψη όλων των συμπληρωμένων εντύπων (.zip)",
                data=zip_data,
                file_name=f"εντυπα_{proc['code']}_{date.today().strftime('%Y%m%d')}.zip",
                mime="application/zip",
                use_container_width=True,
                key="dl_all_zip",
            )
            st.success(
                f"✅ Δημιουργήθηκαν {len(filled_files)} έντυπα. "
                "Ελέγξτε και υπογράψτε πριν την αποστολή στη Μεγ. Γεν. Γραμματεία."
            )

    # ── ΟΔΗΓΙΕΣ ΑΠΟΣΤΟΛΗΣ ─────────────────────────────────────
    with st.expander("📬 Οδηγίες Αποστολής στη Μεγ. Γεν. Γραμματεία"):
        st.markdown("""
**Αποστολή εντύπων:**
- **Πρωτότυπα**: αυτοπροσώπως (Σεβ. ή Γραμμ.) ή courier ή ταχυδρομείο
- **Αντίγραφα**: e-mail μέσω **επίσημης** ηλεκτρονικής διεύθυνσης Στοάς
- **Διεύθυνση**: Αχαρνών 19, 10438 Αθήναι
- **Email**: megaligrammatia.gl@grandlodge.gr
- **Τηλ.**: 210 8229950

⚠️ **Χωρίς πρωτότυπα δεν εκδίδεται έγκριση από τη Μεγ. Στοά.**
        """)

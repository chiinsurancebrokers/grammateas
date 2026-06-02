# -*- coding: utf-8 -*-
"""
Σελίδα 14 — Πρακτικό Παραδοσης-Παραλαβής Γραμματείας
Επίσημο έγγραφο παραλαβής αρχείου, βιβλίων, σφραγίδας κλπ.
"""
import sys; sys.path.append("..")
import streamlit as st
import io
from datetime import date
from modules.database import init_db

init_db()
st.set_page_config(page_title="Παράδοση-Παραλαβή", page_icon="📋", layout="wide")

st.markdown("# 📋 Πρακτικό Παραδοσης-Παραλαβής Γραμματείας")
st.caption("Επίσημο πρακτικό παραλαβής αρχείου, βιβλίων, σφραγίδας — Βάσει Άρθρων 35-41 & 136 ΓΚ ΜΣΤΕ")

# ── PDF GENERATOR ─────────────────────────────────────────────

def generate_paradosi_pdf(data: dict) -> io.BytesIO:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
    from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                     Table, TableStyle, HRFlowable, KeepTogether)
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    import os

    # ── Καταχώρηση DejaVu γραμματοσειρών (πλήρης υποστήριξη ελληνικών) ──
    _fonts_base = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "fonts")
    for alias, fn in {
        "DSR":  "DejaVuSerif.ttf",
        "DSB":  "DejaVuSerif-Bold.ttf",
        "DSI":  "DejaVuSerif-Italic.ttf",
        "DSBI": "DejaVuSerif-BoldItalic.ttf",
        "DSS":  "DejaVuSans.ttf",
        "DSSB": "DejaVuSans-Bold.ttf",
    }.items():
        if alias not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont(alias, os.path.join(_fonts_base, fn)))

    NAVY = colors.HexColor("#1a2a4a"); GOLD = colors.HexColor("#b8960c")
    LIGHT = colors.HexColor("#f5f5f0"); WHITE = colors.white; BLACK = colors.black

    def S(**kw):
        defaults = dict(fontName="DSS", fontSize=10, spaceAfter=5, leading=14)
        defaults.update(kw)
        return ParagraphStyle(str(hash(str(kw))), **defaults)

    CB  = S(fontName="DSSB",  fontSize=10,  alignment=TA_CENTER, spaceAfter=3)
    CC  = S(fontName="DSS",  fontSize=10,  alignment=TA_CENTER, spaceAfter=3)
    TIT = S(fontName="DSSB",  fontSize=13,  alignment=TA_CENTER, spaceAfter=8, spaceBefore=6)
    BOD = S(fontName="DSS",  fontSize=10,  alignment=TA_JUSTIFY, spaceAfter=8, leading=15)
    BLD = S(fontName="DSSB",  fontSize=10,  spaceAfter=4)
    IND = S(fontName="DSS",  fontSize=10,  leftIndent=25, spaceAfter=5, leading=14, alignment=TA_JUSTIFY)
    SML = S(fontName="DSS",  fontSize=8,   textColor=colors.grey, spaceAfter=3)
    ART = S(fontName="DSS",  fontSize=9,   textColor=colors.HexColor("#444444"),
            leftIndent=15, spaceAfter=4, leading=13)
    # Styles για κελιά πινάκων (ώστε το κείμενο να αναδιπλώνεται)
    TH  = S(fontName="DSSB", fontSize=7,  textColor=colors.white, alignment=TA_CENTER, leading=9, spaceAfter=0)
    TD  = S(fontName="DSS",  fontSize=7,  leading=9, spaceAfter=0)
    TDC = S(fontName="DSS",  fontSize=7,  alignment=TA_CENTER, leading=9, spaceAfter=0)

    def hr(): return HRFlowable(width="100%", thickness=.5, color=GOLD, spaceBefore=5, spaceAfter=5)

    story = []

    # Κεφαλίδα
    story += [
        Paragraph("Ε∴Δ∴Τ∴Μ∴Α∴Τ∴Σ∴", CB),
        Paragraph("Εν Ονόματι και Υπό την Αιγίδα", CC),
        Paragraph("της Μεγάλης Στοάς της Ελλάδος", CC),
        Paragraph("των Αρχαίων Ελευθέρων και Αποδεδεγμένων Τεκτόνων", CC),
        Spacer(1, .2*cm),
        Paragraph(f"<b>Σ∴ Στ∴ ΑΚΡΟΠΟΛΙΣ υπ' αρ. 84    εν Αν∴ Αθ∴</b>", CB),
        Spacer(1, .2*cm),
        HRFlowable(width="100%", thickness=2, color=NAVY, spaceAfter=8),
    ]

    # Τίτλος
    story.append(Paragraph(
        "ΠΡΑΚΤΙΚΟΝ ΠΑΡΑΔΟΣΕΩΣ – ΠΑΡΑΛΑΒΗΣ ΓΡΑΜΜΑΤΕΙΑΣ", TIT))
    story.append(Paragraph(
        f"(Βάσει Άρθρων 35, 36, 37, 38, 39, 40, 41 & 136 Γενικού Κανονισμού ΜΣΤΕ)", SML))
    story.append(Spacer(1, .3*cm))

    # Εισαγωγική παράγραφος
    ΜΗΝΕΣ = ["","Ιανουαρίου","Φεβρουαρίου","Μαρτίου","Απριλίου","Μαΐου","Ιουνίου",
              "Ιουλίου","Αυγούστου","Σεπτεμβρίου","Οκτωβρίου","Νοεμβρίου","Δεκεμβρίου"]
    d = data["ημερομηνία"]
    if hasattr(d, 'strftime'):
        ημερ_str  = f"{d.day}ης/{d.month:02d}/{d.year}"
        ημερ_full = f"{d.day}η {ΜΗΝΕΣ[d.month]} {d.year}"
    else:
        ημερ_str = ημερ_full = str(d)
    ημερα = data.get("ημέρα","")
    story.append(Paragraph(
        f"Σήμερον {ημερα} {ημερ_full}, εις {data.get('τόπος','τα γραφεία της Σ∴ Στ∴, Αχαρνών 19, Αθήνα')}, "
        f"ο Απερχόμενος Γραμματεύς-Σφραγιδοφύλαξ <b>Αδ∴ {data['απερχόμενος']}</b>, "
        f"ο οποίος ασκούσε τα καθήκοντά του κατά την περίοδον {data.get('περίοδος_από','')} – {data.get('περίοδος_έως','')}, "
        f"παρέδωσε εις τον εκλεγέντα νέον Γραμματέα-Σφραγιδοφύλακα "
        f"<b>Αδ∴ {data['παραλαμβάνων']}</b> τα κατωτέρω καταγεγραμμένα βιβλία, έγγραφα, "
        f"αντικείμενα και λοιπό υλικό της Σ∴ Στ∴ μας, όπως αυτά ευρέθησαν, επιδείχθηκαν "
        f"και καταγράφηκαν κατά την παρούσα διαδικασία παραδόσεως – παραλαβής.", BOD))

    story.append(hr())

    # ── ΒΙΒΛΙΑ ────────────────────────────────────────────────
    story.append(Paragraph("Α. ΒΙΒΛΙΑ ΓΡΑΜΜΑΤΕΙΑΣ (Άρθρον 36 Γ.Κ. ΜΣΤΕ)", BLD))
    story.append(Paragraph(
        "Συμφώνως πρός το Άρθρον 36 του Γ.Κ. ΜΣΤΕ, ο Γραμματεύς-Σφραγιδοφύλαξ υποχρεούται "
        "εις την τήρησιν των κατωτέρω βιβλίων, η παράδοσις των οποίων γίνεται ως ακολούθως:", BOD))

    books = data.get("βιβλία", {})
    book_defs = [
        ("36§1",  "Χρυσή Βίβλος της Στοάς"),
        ("36§2a", "Βιβλίον Πρακτικών Α' Βαθμού (Μαθητών)"),
        ("36§2b", "Βιβλίον Πρακτικών Β' Βαθμού (Εταίρων)"),
        ("36§2c", "Βιβλίον Πρακτικών Γ' Βαθμού (Διδασκάλων)"),
        ("36§3",  "Βιβλίον Επισήμου Διαβεβαιώσεως Αξιωματικών"),
        ("36§4a", "Βιβλίον Επισήμου Διαβεβαιώσεως Μυουμένων (Α' Βαθμός)"),
        ("36§4b", "Βιβλίον Επισήμου Διαβεβαιώσεως Μυουμένων (Β' Βαθμός)"),
        ("36§4c", "Βιβλίον Επισήμου Διαβεβαιώσεως Μυουμένων (Γ' Βαθμός)"),
        ("36§5",  "Μητρώον της Στοάς"),
        ("36§6",  "Διπλότυπον Βιβλίον Ενταλμάτων Πληρωμών (Γενικόν)"),
        ("36§7",  "Διπλότυπον Βιβλίον Ενταλμάτων Πληρωμών Ελεονομείου"),
        ("36§8",  "Πρωτόκολλον Εισερχομένων-Εξερχομένων Εγγράφων"),
        ("36§9",  "Βιβλίον Απορριφθέντων"),
        ("36§10", "Βιβλίον Παρουσιών"),
        ("36§11", "Βιβλίον Πρακτικών Συμβουλίου Αξιωματικών"),
    ]

    tdata = [[Paragraph("Α/Α",TH), Paragraph("Άρθρο",TH), Paragraph("Βιβλίον",TH),
               Paragraph("Κατάσταση",TH), Paragraph("Παρατηρήσεις",TH)]]
    for i, (art, name) in enumerate(book_defs, 1):
        key = art
        bk = books.get(key, {})
        status = bk.get("κατάσταση", "Παραδόθηκε")
        notes  = bk.get("παρατηρήσεις", "")
        tdata.append([Paragraph(str(i),TDC), Paragraph(art,TDC),
                      Paragraph(name,TD), Paragraph(status,TD), Paragraph(notes,TD)])

    t = Table(tdata, colWidths=[.8*cm, 1.5*cm, 6.5*cm, 2.5*cm, 4.5*cm])
    t.setStyle(TableStyle([
        ("BACKGROUND",   (0,0),(-1,0), NAVY),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[WHITE, LIGHT]),
        ("GRID",(0,0),(-1,-1),.25,colors.lightgrey), ("BOX",(0,0),(-1,-1),1,NAVY),
        ("BOTTOMPADDING",(0,0),(-1,-1),3), ("TOPPADDING",(0,0),(-1,-1),3),
        ("VALIGN",(0,0),(-1,-1),"TOP"),
    ]))
    story.append(t)
    story.append(Spacer(1,.4*cm))

    # ── ΣΦΡΑΓΙΔΑ ──────────────────────────────────────────────
    story.append(hr())
    story.append(Paragraph("Β. ΣΦΡΑΓΙΣ ΓΡΑΜΜΑΤΕΙΑΣ (Άρθρον 35 & 136 Γ.Κ. ΜΣΤΕ)", BLD))
    story.append(Paragraph(
        "Ο Γραμματεύς-Σφραγιδοφύλαξ, συμφώνως πρός τον τίτλον του αξιώματός του "
        "και τα Άρθρα 35 και 136 του Γ.Κ. ΜΣΤΕ, τυγχάνει φύλαξ της Σφραγίδος της Στοάς. "
        "Κατωτέρω καταγράφεται η κατάστασις παραδόσεως:", BOD))

    sfragida = data.get("σφραγίδα", {})
    sf_status = sfragida.get("κατάσταση", "Παραδόθηκε")
    sf_notes  = sfragida.get("παρατηρήσεις", "")
    sf_desc   = sfragida.get("περιγραφή", "Σφραγίς Σ∴ Στ∴ ΑΚΡΟΠΟΛΙΣ υπ' αρ. 84 — Ελληνική")

    sf_data = [
        [Paragraph("Αντικείμενον",TH), Paragraph("Κατάστασις",TH), Paragraph("Παρατηρήσεις",TH)],
        [Paragraph(sf_desc,TD), Paragraph(sf_status,TD), Paragraph(sf_notes,TD)],
    ]
    ts = Table(sf_data, colWidths=[7*cm, 3*cm, 6.5*cm])
    ts.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),NAVY),
        ("BACKGROUND",(0,1),(-1,-1),LIGHT),
        ("GRID",(0,0),(-1,-1),.25,colors.lightgrey),("BOX",(0,0),(-1,-1),1,NAVY),
        ("BOTTOMPADDING",(0,0),(-1,-1),5),("TOPPADDING",(0,0),(-1,-1),5),
        ("VALIGN",(0,0),(-1,-1),"TOP"),
    ]))
    story.append(ts)
    story.append(Spacer(1,.3*cm))

    # ── ΓΡΑΦΙΚΗ ΥΛΗ ──────────────────────────────────────────
    story.append(hr())
    story.append(Paragraph("Γ. ΓΡΑΦΙΚΗ ΥΛΗ & ΛΟΙΠΑ ΑΝΤΙΚΕΙΜΕΝΑ", BLD))

    grafikia = data.get("γραφική_ύλη", [])
    if grafikia:
        gy_data = [[Paragraph("Α/Α",TH), Paragraph("Αντικείμενον",TH),
                     Paragraph("Ποσότης/Κατάστασις",TH), Paragraph("Παρατηρήσεις",TH)]]
        for i, item in enumerate(grafikia, 1):
            gy_data.append([Paragraph(str(i),TDC), Paragraph(item.get("είδος",""),TD),
                            Paragraph(item.get("κατάσταση",""),TD), Paragraph(item.get("παρατηρήσεις",""),TD)])
        tgy = Table(gy_data, colWidths=[.8*cm, 7*cm, 4*cm, 4.5*cm])
        tgy.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,0),NAVY),
            ("ROWBACKGROUNDS",(0,1),(-1,-1),[WHITE,LIGHT]),
            ("GRID",(0,0),(-1,-1),.25,colors.lightgrey),("BOX",(0,0),(-1,-1),1,NAVY),
            ("BOTTOMPADDING",(0,0),(-1,-1),4),("TOPPADDING",(0,0),(-1,-1),4),
            ("VALIGN",(0,0),(-1,-1),"TOP"),
        ]))
        story.append(tgy)
    else:
        story.append(Paragraph("Δεν παραδόθηκε γραφική ύλη ή αντικείμενα.", BOD))
    story.append(Spacer(1,.3*cm))

    # ── ΑΡΧΕΙΟ ΑΛΛΗΛΟΓΡΑΦΙΑΣ ─────────────────────────────────
    story.append(hr())
    story.append(Paragraph("Δ. ΑΡΧΕΙΟΝ ΑΛΛΗΛΟΓΡΑΦΙΑΣ (Άρθρον 37 Γ.Κ. ΜΣΤΕ)", BLD))
    allilogr = data.get("αλληλογραφία_κατάσταση","")
    story.append(Paragraph(
        f"Συμφώνως πρός το Άρθρον 37 Γ.Κ. ΜΣΤΕ, ο Γραμματεύς-Σφραγιδοφύλαξ διεξάγει "
        f"την αλληλογραφίαν και τηρεί το Πρωτόκολλον. "
        f"Κατάστασις αρχείου αλληλογραφίας: <b>{allilogr if allilogr else 'Βλέπε ανωτέρω Βιβλίον Πρωτοκόλλου'}</b>.", BOD))

    # ── ΠΑΡΑΤΗΡΗΣΕΙΣ ─────────────────────────────────────────
    notes_general = data.get("γενικές_παρατηρήσεις","")
    if notes_general:
        story.append(hr())
        story.append(Paragraph("Ε. ΓΕΝΙΚΕΣ ΠΑΡΑΤΗΡΗΣΕΙΣ & ΕΠΙΣΗΜΑΝΣΕΙΣ", BLD))
        story.append(Paragraph(notes_general, BOD))

    # ── ΒΕΒΑΙΩΣΕΙΣ ΠΑΡΑΔΟΣΕΩΣ - ΠΑΡΑΛΑΒΗΣ ────────────────────
    story.append(hr())
    story.append(Paragraph("ΣΤ. ΒΕΒΑΙΩΣΕΙΣ ΠΑΡΑΔΟΣΕΩΣ – ΠΑΡΑΛΑΒΗΣ", BLD))
    story.append(Paragraph(
        f"Ο Απερχόμενος Γραμματεύς-Σφραγιδοφύλαξ <b>Αδ∴ {data['απερχόμενος']}</b> "
        f"βεβαιοί δι' υπογραφής του ότι παρέδωσε τα ανωτέρω αντικείμενα, βιβλία, έγγραφα "
        f"και λοιπό υλικό που ευρίσκοντο υπό την ευθύνη και κατοχή του κατά τον χρόνο της παραδόσεως, "
        f"εν πλήρει γνώσει των υποχρεώσεών του εκ των Άρθρων 35-41 του Γ.Κ. ΜΣΤΕ.", BOD))
    story.append(Paragraph(
        f"Ο Νέος Γραμματεύς-Σφραγιδοφύλαξ <b>Αδ∴ {data['παραλαμβάνων']}</b> "
        f"βεβαιοί δι' υπογραφής του ότι παρέλαβε τα ανωτέρω αντικείμενα, βιβλία, έγγραφα "
        f"και λοιπό υλικό που του επιδείχθηκαν και του παραδόθηκαν κατά την παρούσα "
        f"διαδικασία παραδόσεως – παραλαβής.", BOD))
    story.append(Paragraph(
        "Η υπογραφή του παραλαμβάνοντος δεν συνιστά βεβαίωση περί της πληρότητας του ιστορικού "
        "αρχείου, των βιβλίων, των εγγράφων, των περιουσιακών στοιχείων ή εν γένει του υλικού "
        "της Στοάς, ούτε αποκλείει την ύπαρξη πρόσθετου υλικού, βιβλίων, εγγράφων ή αρχείων "
        "τα οποία δεν τέθηκαν υπόψη του ή δεν κατέστη δυνατόν να εντοπισθούν κατά τον χρόνο "
        "συντάξεως του παρόντος.", BOD))
    story.append(Paragraph(
        "Τυχόν συμπληρωματικά στοιχεία, βιβλία, έγγραφα ή αρχεία που ενδέχεται να ανευρεθούν "
        "μεταγενεστέρως θα καταγραφούν και θα ενσωματωθούν στο αρχείο της Στοάς με σχετική "
        "πράξη ή πρωτόκολλο.", BOD))

    story.append(Paragraph(
        "Πρός πίστωσιν των ανωτέρω, συνετάγη εις πενταπλούν το παρόν Πρακτικόν, "
        "εκ των πρωτοτύπων αντιτύπων, εν τίθεται εις το Αρχείον της Στ∴ και πρωτοκολλείται, "
        "ανά εν δε λαμβάνει έκαστος των υπογραφομένων.", BOD))

    # ── ΥΠΟΓΡΑΦΕΣ ────────────────────────────────────────────
    story.append(Spacer(1, 1*cm))
    story.append(Paragraph(f"Εν Αν∴ Αθηνών, {ημερ_full}", CC))
    story.append(Spacer(1, .8*cm))

    sig_data = [[
        Paragraph(f"Ο Απερχόμενος<br/>Γραμματεύς-Σφραγιδοφύλαξ<br/><br/><br/><br/>{data['απερχόμενος']}", CC),
        Paragraph(f"Ο Νέος<br/>Γραμματεύς-Σφραγιδοφύλαξ<br/><br/><br/><br/>{data['παραλαμβάνων']}", CC),
        Paragraph(f"Ο Σεβ∴ Διδ∴<br/>της Σ∴ Στ∴<br/><br/><br/><br/>{data.get('σεβάσμιος','')}", CC),
    ]]
    sig_t = Table(sig_data, colWidths=[5.5*cm, 5.5*cm, 5.5*cm])
    sig_t.setStyle(TableStyle([
        ("FONTSIZE",    (0,0),(-1,-1), 9),
        ("TOPPADDING",  (0,0),(-1,-1), 5),
        ("BOX",         (0,0),(0,-1), .5, BLACK),
        ("BOX",         (1,0),(1,-1), .5, BLACK),
        ("BOX",         (2,0),(2,-1), .5, BLACK),
        ("ALIGN",       (0,0),(-1,-1), "CENTER"),
        ("VALIGN",      (0,0),(-1,-1), "TOP"),
    ]))
    story.append(sig_t)

    # Επιπλέον υπογραφείς (Σεβάσμιος, τ.Σεβάσμιος)
    if data.get("επιπλέον_υπογράφοντες"):
        story.append(Spacer(1,.5*cm))
        extra = data["επιπλέον_υπογράφοντες"]
        ex_data = [[Paragraph(f"{p.get('τίτλος','')}<br/><br/><br/><br/>{p.get('όνομα','')}", CC)
                    for p in extra]]
        w = 16.5 / len(extra)
        ex_t = Table(ex_data, colWidths=[w*cm]*len(extra))
        box_styles = [("BOX",(i,0),(i,-1),.5,BLACK) for i in range(len(extra))]
        ex_t.setStyle(TableStyle(
            [("FONTSIZE",(0,0),(-1,-1),9),("TOPPADDING",(0,0),(-1,-1),5),
             ("ALIGN",(0,0),(-1,-1),"CENTER")] + box_styles
        ))
        story.append(ex_t)

    # Footer
    story.append(Spacer(1,.5*cm))
    story.append(HRFlowable(width="100%",thickness=.5,color=colors.lightgrey))
    story.append(Paragraph(
        f"Αρ. Πρωτ.: {data.get('αρ_πρωτ','')}  |  Ημερομηνία: {ημερ_full}  |  "
        f"Αντίτυπα: 5 (πενταπλούν)", SML))

    buf = io.BytesIO()
    SimpleDocTemplate(buf, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm,
                      topMargin=2*cm, bottomMargin=2*cm).build(story)
    buf.seek(0)
    return buf


# ── UI ────────────────────────────────────────────────────────

tab_form, tab_guide = st.tabs(["📋 Δημιουργία Πρακτικού", "📖 Οδηγός Παραλαβής"])

with tab_guide:
    st.markdown("""
    ## Οδηγός Παραλαβής Γραμματείας

    ### Τι υποχρεούστε να παραλάβετε (Άρθρο 36 ΓΚ ΜΣΤΕ):

    | Άρθρο | Στοιχείο | Σημείωση |
    |-------|----------|----------|
    | 36§1  | Χρυσή Βίβλος | Να ελέγξετε αν υπάρχει |
    | 36§2  | 3 Βιβλία Πρακτικών | Ένα ανά βαθμό |
    | 36§3  | Βιβλίο Διαβεβ. Αξ/κών | Να ελέγξετε αν έχουν υπογράψει |
    | 36§4  | 3 Βιβλία Διαβεβ. Μυουμένων | Ένα ανά βαθμό |
    | 36§5  | Μητρώο Στοάς | Να ελέγξετε ενημέρωση |
    | 36§6  | Ενταλμάτων Γενικό | Να ελέγξετε διπλότυπο |
    | 36§7  | Ενταλμάτων Ελεονομείου | Να ελέγξετε διπλότυπο |
    | 36§8  | Πρωτόκολλο | Να ελέγξετε ενημέρωση |
    | 36§9  | Βιβλίο Απορριφθέντων | Να ελέγξετε αλφαβητική τάξη |
    | 36§10 | Βιβλίο Παρουσιών | Να ελέγξετε ανά συνεδρίαση |
    | 36§11 | Πρακτικά Συμβουλίου | Να ελέγξετε ενημέρωση |

    ### Σφραγίς (Άρθρα 35 & 136):
    - Ο Γραμματεύς φέρει τον τίτλο **Σφραγιδοφύλαξ** — η παράδοση της σφραγίδας είναι **υποχρεωτική**
    - Βεβαιωθείτε για την κατάσταση και τη λειτουργικότητά της

    ### Συμβουλές:
    - ✅ Καταγράψτε **κάθε ελλιπές** βιβλίο με παρατηρήσεις
    - ✅ Ο προηγούμενος **υπογράφει** για όσα δεν παρέδωσε
    - ✅ Το πρακτικό συντάσσεται σε **πενταπλούν**
    - ✅ Πρωτοκολλείται και αρχειοθετείται
    """)

with tab_form:
    st.subheader("📋 Στοιχεία Πρακτικού")

    col1, col2 = st.columns(2)
    with col1:
        ημερ = st.date_input("Ημερομηνία", value=date.today())
        ημερα_opts = ["Δευτέρα","Τρίτη","Τετάρτη","Πέμπτη","Παρασκευή","Σάββατο","Κυριακή"]
        ημερα = st.selectbox("Ημέρα", ημερα_opts,
                              index=date.today().weekday() if date.today().weekday()<7 else 0)
        αρ_πρωτ = st.text_input("Αριθμός Πρωτοκόλλου", placeholder="π.χ. 1/2026")
    with col2:
        τόπος = st.text_input("Τόπος", value="τα γραφεία της Σ∴ Στ∴, Αχαρνών 19, Αθήνα")
        περίοδος_από = st.text_input("Περίοδος (από)", placeholder="π.χ. 1/10/2022")
        περίοδος_έως = st.text_input("Περίοδος (έως)", value=str(date.today()))

    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col1: απερχόμενος = st.text_input("Απερχόμενος Γραμματεύς *")
    with col2: παραλαμβάνων = st.text_input("Νέος Γραμματεύς (εγώ) *", value="")
    with col3: σεβάσμιος = st.text_input("Σεβάσμιος Διδάσκαλος *")

    # Επιπλέον υπογράφοντες
    with st.expander("➕ Επιπλέον Υπογράφοντες (π.χ. τ.Σεβάσμιος)"):
        n_extra = st.number_input("Αριθμός", 0, 4, 1)
        extra_sigs = []
        for i in range(int(n_extra)):
            c1,c2 = st.columns(2)
            with c1: τίτλ = st.text_input(f"Τίτλος {i+1}", value="ο τ.Σεβ∴ Διδ∴", key=f"et{i}")
            with c2: ον = st.text_input(f"Όνομα {i+1}", key=f"en{i}")
            if ον: extra_sigs.append({"τίτλος": τίτλ, "όνομα": ον})

    st.markdown("---")
    st.subheader("📚 Κατάσταση Βιβλίων")
    st.info("Συμπληρώστε για κάθε βιβλίο την κατάσταση παράδοσης.")

    STATUS_OPTS = ["Παραδόθηκε πλήρες", "Παραδόθηκε ελλιπές", "Δεν παραδόθηκε", "Δεν υπήρχε"]

    book_defs_ui = [
        ("36§1",  "Χρυσή Βίβλος"),
        ("36§2a", "Βιβλίο Πρακτικών Α' Βαθμού"),
        ("36§2b", "Βιβλίο Πρακτικών Β' Βαθμού"),
        ("36§2c", "Βιβλίο Πρακτικών Γ' Βαθμού"),
        ("36§3",  "Βιβλίο Διαβεβ. Αξιωματικών"),
        ("36§4a", "Βιβλίο Διαβεβ. Μυουμένων Α'"),
        ("36§4b", "Βιβλίο Διαβεβ. Μυουμένων Β'"),
        ("36§4c", "Βιβλίο Διαβεβ. Μυουμένων Γ'"),
        ("36§5",  "Μητρώον Στοάς"),
        ("36§6",  "Εντάλματα Γενικό (Διπλότυπο)"),
        ("36§7",  "Εντάλματα Ελεονομείου (Διπλότυπο)"),
        ("36§8",  "Πρωτόκολλο Εγγράφων"),
        ("36§9",  "Βιβλίο Απορριφθέντων"),
        ("36§10", "Βιβλίο Παρουσιών"),
        ("36§11", "Πρακτικά Συμβουλίου Αξ/κών"),
    ]

    βιβλία = {}
    for art, name in book_defs_ui:
        cols = st.columns([1, 3, 2, 3])
        with cols[0]: st.markdown(f"`{art}`")
        with cols[1]: st.markdown(f"**{name}**")
        with cols[2]:
            status = st.selectbox("", STATUS_OPTS, key=f"bk_{art}",
                                  label_visibility="collapsed")
        with cols[3]:
            notes = st.text_input("", placeholder="Παρατηρήσεις...", key=f"bn_{art}",
                                  label_visibility="collapsed")
        βιβλία[art] = {"κατάσταση": status, "παρατηρήσεις": notes}

    st.markdown("---")
    st.subheader("🔏 Σφραγίς")
    col1, col2, col3 = st.columns(3)
    with col1: sf_desc = st.text_input("Περιγραφή", value="Σφραγίς Σ∴ Στ∴ ΑΚΡΟΠΟΛΙΣ υπ' αρ. 84")
    with col2: sf_status = st.selectbox("Κατάσταση", STATUS_OPTS, key="sf_st")
    with col3: sf_notes = st.text_input("Παρατηρήσεις", key="sf_n")

    st.markdown("---")
    st.subheader("✏️ Γραφική Ύλη & Λοιπά")

    default_items = [
        "Μπλόκ αλληλογραφίας / επιστολόχαρτα Στοάς",
        "Φάκελοι αλληλογραφίας με λογότυπο",
        "Αρχείο (ντοσιέ) εγγράφων",
        "Λοιπή γραφική ύλη",
    ]
    n_items = st.number_input("Αριθμός αντικειμένων", 1, 15, len(default_items))
    γραφική_ύλη = []
    for i in range(int(n_items)):
        c1,c2,c3 = st.columns([3,2,3])
        with c1: eid = st.text_input("Είδος", value=default_items[i] if i<len(default_items) else "", key=f"gy_{i}")
        with c2: ekst = st.selectbox("Κατάσταση", STATUS_OPTS, key=f"gys_{i}")
        with c3: enotes = st.text_input("Παρατηρήσεις", key=f"gyn_{i}")
        if eid: γραφική_ύλη.append({"είδος":eid,"κατάσταση":ekst,"παρατηρήσεις":enotes})

    st.markdown("---")
    general_notes = st.text_area(
        "Γενικές Παρατηρήσεις & Επισημάνσεις",
        height=120,
        placeholder="π.χ. Διαπιστώθηκε ότι το Μητρώο δεν ήτο ενημερωμένο από ... "
                    "Το Πρωτόκολλο δεν τηρήθηκε κατά το χρονικό διάστημα ... "
                    "Ελλείπουν πρακτικά της συνεδρίασης της ..."
    )

    col1, col2 = st.columns(2)
    with col1:
        generate = st.button("📄 Δημιουργία & Λήψη PDF", type="primary",
                             use_container_width=True,
                             disabled=not (απερχόμενος and παραλαμβάνων and σεβάσμιος))
    with col2:
        if not (απερχόμενος and παραλαμβάνων and σεβάσμιος):
            st.warning("⚠️ Συμπληρώστε τα υποχρεωτικά πεδία (*)")

    if generate:
        data = {
            "ημερομηνία": ημερ, "ημέρα": ημερα, "τόπος": τόπος,
            "αρ_πρωτ": αρ_πρωτ, "περίοδος_από": περίοδος_από, "περίοδος_έως": περίοδος_έως,
            "απερχόμενος": απερχόμενος, "παραλαμβάνων": παραλαμβάνων, "σεβάσμιος": σεβάσμιος,
            "επιπλέον_υπογράφοντες": extra_sigs if extra_sigs else None,
            "βιβλία": βιβλία,
            "σφραγίδα": {"περιγραφή": sf_desc, "κατάσταση": sf_status, "παρατηρήσεις": sf_notes},
            "γραφική_ύλη": γραφική_ύλη,
            "γενικές_παρατηρήσεις": general_notes,
        }
        with st.spinner("Δημιουργία PDF..."):
            pdf_buf = generate_paradosi_pdf(data)
        st.success("✅ Το πρακτικό δημιουργήθηκε!")
        st.download_button(
            "⬇️ Λήψη PDF — Πρακτικό Παραδοσης-Παραλαβής",
            data=pdf_buf,
            file_name=f"πρακτικό_παράδοσης_παραλαβής_{ημερ}.pdf",
            mime="application/pdf",
            use_container_width=True
        )

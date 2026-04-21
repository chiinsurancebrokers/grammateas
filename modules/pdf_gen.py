# -*- coding: utf-8 -*-
"""PDF Generator v2 — μορφή βασισμένη στο επίσημο Τυπικό ΜΣΤΕ"""
import io, json
from datetime import date
from typing import Dict, List
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                 TableStyle, HRFlowable, KeepTogether)

LODGE_NAME = "Σ∴ Στ∴ ΑΚΡΟΠΟΛΙΣ υπ' αρ. 84     εν Αν∴ Αθ∴"
NAVY  = colors.HexColor("#1a2a4a")
GOLD  = colors.HexColor("#b8960c")
LIGHT = colors.HexColor("#f5f5f0")
WHITE = colors.white; BLACK = colors.black
ΒΑΘΜΟΙ_ABBR = {"Μαθητής":"Μαθ∴","Εταίρος":"Ετ∴","Διδάσκαλος":"Διδ∴"}

def _s():
    return {
        "cb":  ParagraphStyle("cb",  fontName="Helvetica-Bold", fontSize=10, alignment=TA_CENTER, spaceAfter=3),
        "cc":  ParagraphStyle("cc",  fontName="Helvetica",      fontSize=10, alignment=TA_CENTER, spaceAfter=3),
        "tit": ParagraphStyle("tit", fontName="Helvetica-Bold", fontSize=12, alignment=TA_CENTER, spaceAfter=6, spaceBefore=6),
        "bod": ParagraphStyle("bod", fontName="Helvetica",      fontSize=10, alignment=TA_JUSTIFY, spaceAfter=8, leading=15),
        "ind": ParagraphStyle("ind", fontName="Helvetica",      fontSize=10, alignment=TA_JUSTIFY, leftIndent=20, spaceAfter=5, leading=14),
        "bul": ParagraphStyle("bul", fontName="Helvetica",      fontSize=10, leftIndent=30, spaceAfter=4, leading=14),
        "bld": ParagraphStyle("bld", fontName="Helvetica-Bold", fontSize=10, spaceAfter=4),
        "sm":  ParagraphStyle("sm",  fontName="Helvetica",      fontSize=8,  textColor=colors.grey, spaceAfter=3),
    }

def _hdr(s):
    return [
        Paragraph("Ε∴Δ∴Τ∴Μ∴Α∴Τ∴Σ∴", s["cb"]),
        Paragraph("Εν Ονόματι και Υπό την Αιγίδα", s["cc"]),
        Paragraph("της Μεγάλης Στοάς της Ελλάδος", s["cc"]),
        Paragraph("των Αρχαίων Ελευθέρων και Αποδεδεγμένων Τεκτόνων", s["cc"]),
        Spacer(1,.2*cm),
        Paragraph(f"<b>{LODGE_NAME}</b>", s["cb"]),
        Spacer(1,.2*cm),
        HRFlowable(width="100%",thickness=1.5,color=NAVY,spaceAfter=6),
    ]

def _build(story):
    buf=io.BytesIO()
    SimpleDocTemplate(buf,pagesize=A4,rightMargin=2.5*cm,leftMargin=2.5*cm,
                      topMargin=2*cm,bottomMargin=2.5*cm).build(story)
    buf.seek(0); return buf

def _hr(s,space=4): return HRFlowable(width="100%",thickness=.5,color=GOLD,spaceBefore=space,spaceAfter=space)

# ── 1. ΠΡΑΚΤΙΚΑ ───────────────────────────────────────────────
def generate_minutes_pdf(session:Dict, attendance_list:List[str]=None,
                         dikaiologithentes:List[str]=None,
                         anaplirotai:Dict[str,str]=None) -> io.BytesIO:
    s=_s(); story=[]
    story.extend(_hdr(s))
    ημερ=session.get("ημερομηνία",""); βαθμ=session.get("βαθμός","Μαθητής")
    βα=ΒΑΘΜΟΙ_ABBR.get(βαθμ,βαθμ[:4]+"∴")
    story.append(Paragraph(f"<b>Πρακτικόν Συνεδρίας της {ημερ} εις Βαθμ∴ {βα}</b>",s["tit"]))
    story.append(Spacer(1,.2*cm))
    # Ημερ. Διάταξη
    agenda=session.get("αλληλογραφία") or []
    if agenda:
        story.append(Paragraph("<b>Ημερησία Διάταξις:</b>",s["bld"]))
        for it in agenda: story.append(Paragraph(f"- {it}",s["bul"]))
        story.append(Spacer(1,.3*cm))
    # Έναρξη
    topos=session.get("τόπος") or "τον Τεκτ∴ Ναόν"; ora=session.get("ώρα") or ""
    plithos=(len(attendance_list) if attendance_list else session.get("πλήθος_παρόντων") or 0)
    story.append(Paragraph(
        f"Σήμερον {ημερ}{', ώρα '+ora if ora else ''}, εις {topos}, "
        f"υπό την Σφύραν του Σεβ∴ Διδ∴ της Σ∴ Στ∴ μας, "
        f"ανοίγουν αι Εργασίαι εις Βαθμόν {βαθμ}.",s["bod"]))
    if plithos:
        story.append(Paragraph(
            f"Παρόντες είναι <b>{plithos}</b> Αδδ∴, ενεργά μέλη του πληρώματός της Στ∴ μας.",s["bod"]))
    if anaplirotai:
        anap=", ".join([f"η θέσις του {α} από τον Αδ∴ {ο}" for α,ο in anaplirotai.items()])
        story.append(Paragraph(f"Αι θέσεις των τακτικών Αξ/κών καταλαμβάνονται κανονικώς, ενώ {anap}.",s["bod"]))
    story.append(_hr(s))
    # Αλληλογραφία
    allilogr=session.get("αλληλογραφία") or []
    if allilogr:
        story.append(Paragraph("Ακολούθως, ο Σεβ∴ Διδ∴ εκάλεσε τον Αδ∴ Ρήτορα όπως αναγνώσει την αλληλογραφίαν.",s["bod"]))
        story.append(Paragraph("Ο Αδ∴ Ρήτωρ ανέγνωσεν των Αδδ∴ καθημένων:",s["bod"]))
        for it in allilogr: story.append(Paragraph(f"* {it}",s["ind"]))
        story.append(Spacer(1,.2*cm))
    # Ομιλίες
    omilies=session.get("ομιλίες") or []
    if omilies:
        story.append(_hr(s))
        story.append(Paragraph("<b>Ομιλίαι — Εργασίαι — Συζητήσεις</b>",s["bld"]))
        for it in omilies: story.append(Paragraph(it,s["bod"]))
    # Αποφάσεις
    apof=session.get("αποφάσεις") or []
    if apof:
        story.append(_hr(s))
        story.append(Paragraph("<b>Αποφάσεις</b>",s["bld"]))
        for i,it in enumerate(apof,1): story.append(Paragraph(f"{i}. {it}",s["ind"]))
    # Κορμός (Άρθρο 39 — ολογράφως ΚΑΙ αριθμητικώς)
    kormos=float(session.get("κορμός_αγαθοεργίας") or 0)
    olog=session.get("κορμός_ολογράφως") or ""
    story.append(_hr(s))
    story.append(Paragraph(
        f"Εκ του Κορμού της Αγαθοεργίας εβλάστησαν "
        f"<b>{olog+' ' if olog else ''}({kormos:.2f})</b> όστρακα.",s["bod"]))
    # Δικαιολογηθέντες (Άρθρο 40)
    if dikaiologithentes:
        story.append(Paragraph("Δικαιολογηθέντες: "+" · ".join(dikaiologithentes),s["bod"]))
    if session.get("παρατηρήσεις"):
        story.append(Paragraph(session["παρατηρήσεις"],s["bod"]))
    story.append(Spacer(1,.3*cm))
    story.append(Paragraph(
        "Τέλος, αι Εργασίαι έκλεισαν κανονικώς υπό την Σφύραν του Σεβ∴ Διδ∴ "
        "της Σ∴ Στ∴ μας, των Αδδ∴ ευχαριστημένων και ικανοποιημένων.",s["bod"]))
    story.append(Spacer(1,1.2*cm))
    sig=Table([[Paragraph("Ο Σεβ∴ Διδ∴",s["cc"]),
                Paragraph("Ο Ρήτωρ",s["cc"]),
                Paragraph("Ο Γραμματεύς",s["cc"])]],
              colWidths=[5*cm,5*cm,6*cm])
    sig.setStyle(TableStyle([("TOPPADDING",(0,0),(-1,-1),35),
                              ("LINEABOVE",(0,0),(-1,-1),.5,BLACK),
                              ("ALIGN",(0,0),(-1,-1),"CENTER")]))
    story.append(sig)
    return _build(story)

# ── 2. ΕΝΤΑΛΜΑ ────────────────────────────────────────────────
def generate_entalma_pdf(entalma:Dict) -> io.BytesIO:
    s=_s(); story=[]
    story.extend(_hdr(s))
    βιβλ=entalma.get("βιβλίο","Γενικό")
    story.append(Paragraph(f"<b>ΕΝΤΑΛΜΑ ΠΛΗΡΩΜΗΣ — {βιβλ.upper()}</b>",s["tit"]))
    story.append(Spacer(1,.4*cm))
    info=[["Αριθμός:","",entalma.get("αρ_εντάλματος",""),"","Ημερομηνία:","",entalma.get("ημερομηνία","")],
          ["Ποσό:","",f"{float(entalma.get('ποσό',0)):.2f} €","","Κατάσταση:","",entalma.get("κατάσταση","")],
          ["Αρ. Απόφ.:","",entalma.get("αρ_απόφασης","—"),"","","",""]]
    t=Table(info,colWidths=[2.5*cm,.3*cm,4*cm,.5*cm,3*cm,.3*cm,5.4*cm])
    t.setStyle(TableStyle([("FONTNAME",(0,0),(-1,-1),"Helvetica"),
                            ("FONTNAME",(0,0),(0,-1),"Helvetica-Bold"),
                            ("FONTNAME",(4,0),(4,-1),"Helvetica-Bold"),
                            ("FONTSIZE",(0,0),(-1,-1),10),
                            ("BACKGROUND",(0,0),(-1,-1),LIGHT),
                            ("BOX",(0,0),(-1,-1),1,NAVY),
                            ("GRID",(0,0),(-1,-1),.25,colors.lightgrey),
                            ("BOTTOMPADDING",(0,0),(-1,-1),5)]))
    story.append(t); story.append(Spacer(1,.5*cm))
    story.append(Paragraph("<b>Αιτιολογία Πληρωμής</b>",s["bld"]))
    story.append(_hr(s,2))
    story.append(Paragraph(entalma.get("αιτιολογία",""),s["bod"]))
    δικ=entalma.get("δικαιολογητικά")
    if δικ:
        try: items=json.loads(δικ) if isinstance(δικ,str) else δικ
        except: items=[]
        if items:
            story.append(Spacer(1,.3*cm))
            story.append(Paragraph("<b>Δικαιολογητικά (Άρθρο 36§7)</b>",s["bld"]))
            story.append(_hr(s,2))
            for i,d in enumerate(items,1): story.append(Paragraph(f"{i}. {d}",s["ind"]))
    story.append(Spacer(1,1.2*cm))
    sig=Table([["Ο Σεβ∴ Διδ∴","","Ο Γραμματεύς-Σφραγιδοφύλαξ"]],colWidths=[6*cm,4*cm,6*cm])
    sig.setStyle(TableStyle([("TOPPADDING",(0,0),(-1,-1),35),
                              ("LINEABOVE",(0,0),(0,-1),.5,BLACK),
                              ("LINEABOVE",(2,0),(2,-1),.5,BLACK),
                              ("ALIGN",(0,0),(-1,-1),"CENTER")]))
    story.append(sig)
    return _build(story)

# ── 3. ΚΑΡΤΕΛΑ ΜΕΛΟΥΣ ────────────────────────────────────────
def generate_member_card_pdf(member:Dict) -> io.BytesIO:
    s=_s(); story=[]; sv=lambda k:str(member.get(k) or "—")
    story.extend(_hdr(s))
    story.append(Paragraph("ΚΑΡΤΕΛΑ ΜΕΛΟΥΣ — ΜΗΤΡΩΟ ΣΤΟΑΣ",s["tit"]))
    story.append(Spacer(1,.3*cm))
    reg=Table([[Paragraph(f"<b>ΑΜ Στοάς: {sv('αρ_μητρώου_στοάς')}</b>",s["cb"]),
                Paragraph(f"<b>ΑΜ ΜΣ: {sv('αρ_μητρώου_μσ')}</b>",s["cb"])]],
              colWidths=[8*cm,8*cm])
    reg.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),NAVY),("TEXTCOLOR",(0,0),(-1,-1),WHITE),
                              ("FONTSIZE",(0,0),(-1,-1),11),("BOTTOMPADDING",(0,0),(-1,-1),8),
                              ("TOPPADDING",(0,0),(-1,-1),8)]))
    story.append(reg); story.append(Spacer(1,.4*cm))
    for title,fields in [
        ("ΠΡΟΣΩΠΙΚΑ ΣΤΟΙΧΕΙΑ",[("Επώνυμο",sv("επώνυμο")),("Όνομα",sv("όνομα")),
          ("Πατρώνυμο",sv("πατρώνυμο")),("Ημ. Γέννησης",sv("ημ_γέννησης")),
          ("Τόπος Γέννησης",sv("τόπος_γέννησης")),("Επάγγελμα",sv("επάγγελμα"))]),
        ("ΕΠΙΚΟΙΝΩΝΙΑ",[("Διεύθυνση",sv("διεύθυνση")),
          ("Πόλη/ΤΚ",f"{sv('πόλη')} {sv('τκ')}"),("Τηλέφωνο",sv("τηλέφωνο")),
          ("Κινητό",sv("κινητό")),("Email",sv("email"))]),
        ("ΤΕΚΤΟΝΙΚΑ ΣΤΟΙΧΕΙΑ",[("Βαθμός",sv("τεκτονικός_βαθμός")),
          ("Κατάσταση",sv("κατάσταση")),("Ημ. Μύησης (Α')",sv("ημ_μύησης")),
          ("Ημ. Εταίρου (Β')",sv("ημ_εταίρου")),("Ημ. Διδασκάλου (Γ')",sv("ημ_διδασκάλου")),
          ("Στοά Μύησης",sv("στοά_μύησης"))])]:
        story.append(KeepTogether([Paragraph(title,s["bld"]),
                                    HRFlowable(width="100%",thickness=1,color=GOLD,spaceAfter=4)]))
        td=[[Paragraph(f"<b>{l}:</b>",s["bod"]),Paragraph(v,s["bod"])] for l,v in fields]
        t=Table(td,colWidths=[5*cm,11*cm])
        t.setStyle(TableStyle([("FONTSIZE",(0,0),(-1,-1),10),("BOTTOMPADDING",(0,0),(-1,-1),4),
                                ("ROWBACKGROUNDS",(0,0),(-1,-1),[WHITE,LIGHT])]))
        story.append(t); story.append(Spacer(1,.3*cm))
    story.append(Paragraph(f"Εκτυπώθηκε: {date.today().strftime('%d/%m/%Y')}",s["sm"]))
    return _build(story)

# ── 4. ΜΗΤΡΩΟ ΛΙΣΤΑ ──────────────────────────────────────────
def generate_members_list_pdf(members_df) -> io.BytesIO:
    s=_s(); story=[]
    story.extend(_hdr(s))
    story.append(Paragraph("ΜΗΤΡΩΟ ΜΕΛΩΝ ΣΤΟΑΣ",s["tit"]))
    story.append(Paragraph(f"Ημερομηνία: {date.today().strftime('%d/%m/%Y')}",s["sm"]))
    story.append(Spacer(1,.4*cm))
    headers=["ΑΜ\nΣτοάς","ΑΜ ΜΣ","Επώνυμο","Όνομα","Βαθμός","Ημ. Μύησης","Κατάσταση"]
    data=[headers]+[[str(r.get("αρ_μητρώου_στοάς","") or ""),str(r.get("αρ_μητρώου_μσ","") or ""),
           str(r.get("επώνυμο","") or ""),str(r.get("όνομα","") or ""),
           str(r.get("τεκτονικός_βαθμός","") or ""),str(r.get("ημ_μύησης","") or ""),
           str(r.get("κατάσταση","") or "")] for _,r in members_df.iterrows()]
    t=Table(data,colWidths=[1.5*cm,1.8*cm,4*cm,3*cm,2.5*cm,2.8*cm,2.4*cm])
    t.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),NAVY),("TEXTCOLOR",(0,0),(-1,0),WHITE),
                            ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),("FONTSIZE",(0,0),(-1,-1),8),
                            ("FONTNAME",(0,1),(-1,-1),"Helvetica"),
                            ("ROWBACKGROUNDS",(0,1),(-1,-1),[WHITE,LIGHT]),
                            ("GRID",(0,0),(-1,-1),.25,colors.lightgrey),
                            ("BOX",(0,0),(-1,-1),1,NAVY),("BOTTOMPADDING",(0,0),(-1,-1),4),
                            ("TOPPADDING",(0,0),(-1,-1),4),("VALIGN",(0,0),(-1,-1),"MIDDLE")]))
    story.append(t)
    story.append(Spacer(1,.3*cm))
    story.append(Paragraph(f"Σύνολο: {len(members_df)} μέλη",s["sm"]))
    return _build(story)

# ── 5. ΠΡΩΤΟΚΟΛΛΟ ────────────────────────────────────────────
def generate_protokollon_pdf(rows, year:int) -> io.BytesIO:
    s=_s(); story=[]
    story.extend(_hdr(s))
    story.append(Paragraph(f"ΠΡΩΤΟΚΟΛΛΟ ΕΓΓΡΑΦΩΝ — ΕΤΟΣ {year}",s["tit"]))
    story.append(Spacer(1,.4*cm))
    headers=["ΑΠ","Ημερ.","Κατεύθ.","Αποστ./Παραλ.","Θέμα","Κατάσταση"]
    data=[headers]
    for r in rows.to_dict("records"):
        recv=r.get("αποστολέας","") or r.get("παραλήπτης","") or ""
        data.append([str(r.get("αρ_πρωτ","")),str(r.get("ημερομηνία","")),
                     str(r.get("κατεύθυνση","")),str(recv)[:25],
                     str(r.get("θέμα",""))[:45],str(r.get("κατάσταση",""))])
    t=Table(data,colWidths=[1.8*cm,2.2*cm,2.2*cm,3.5*cm,5.8*cm,2*cm])
    t.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),NAVY),("TEXTCOLOR",(0,0),(-1,0),WHITE),
                            ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),("FONTSIZE",(0,0),(-1,-1),8),
                            ("FONTNAME",(0,1),(-1,-1),"Helvetica"),
                            ("ROWBACKGROUNDS",(0,1),(-1,-1),[WHITE,LIGHT]),
                            ("GRID",(0,0),(-1,-1),.25,colors.lightgrey),
                            ("BOX",(0,0),(-1,-1),1,NAVY),("BOTTOMPADDING",(0,0),(-1,-1),4),
                            ("TOPPADDING",(0,0),(-1,-1),4)]))
    story.append(t)
    story.append(Spacer(1,.3*cm))
    story.append(Paragraph(f"Σύνολο: {len(rows)} εγγραφές",s["sm"]))
    return _build(story)


# ═══════════════════════════════════════════════════════════════
# 6. ΔΙΠΛΩΜΑ ΔΙΔΑΣΚΑΛΟΥ / ΕΤΑΙΡΟΥ / ΜΑΘΗΤΟΥ
#    Αντίγραφο αρχείου Στοάς (το επίσημο εκδίδεται από ΜΣ)
# ═══════════════════════════════════════════════════════════════

def generate_diploma_pdf(member: Dict, βαθμός: str, ημ_βαθμού: str,
                         watermark: bool = True) -> io.BytesIO:
    """
    Δημιουργεί αντίγραφο διπλώματος για το αρχείο της Στοάς.
    Το επίσημο εκδίδεται από τη Μεγάλη Στοά.

    member:     dict από get_member()
    βαθμός:     'Μαθητής' | 'Εταίρος' | 'Διδάσκαλος'
    ημ_βαθμού: ημερομηνία ανάδειξης
    watermark:  αν True, προσθέτει "ΑΝΤΙΓΡΑΦΟ ΑΡΧΕΙΟΥ ΣΤΟΑΣ"
    """
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
    from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                     Table, TableStyle, HRFlowable, KeepTogether)
    from reportlab.pdfgen import canvas as pdfcanvas
    from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate

    # ── Χρώματα & styles ──────────────────────────────────────
    GOLD_D  = colors.HexColor("#8B6914")
    NAVY_D  = colors.HexColor("#1a2a4a")
    CREAM   = colors.HexColor("#FAF7F0")
    BLACK   = colors.black

    def ST(name, **kw):
        d = dict(fontName="Helvetica", fontSize=11, spaceAfter=6,
                 leading=16, textColor=BLACK, backColor=None)
        d.update(kw)
        return ParagraphStyle(name, **d)

    # Styles που μιμούνται το επίσημο δίπλωμα
    HDR1 = ST("hdr1", fontName="Helvetica-Bold", fontSize=18, alignment=TA_CENTER,
              textColor=NAVY_D, spaceAfter=4, spaceBefore=4)
    HDR2 = ST("hdr2", fontName="Helvetica-Oblique", fontSize=12, alignment=TA_CENTER,
              textColor=NAVY_D, spaceAfter=12)
    INTRO = ST("intro", fontName="Helvetica-Oblique", fontSize=11, alignment=TA_CENTER,
               textColor=NAVY_D, spaceAfter=4, leading=18)
    NAME  = ST("name", fontName="Helvetica-Bold", fontSize=20, alignment=TA_CENTER,
               textColor=NAVY_D, spaceAfter=6, spaceBefore=6)
    BODY  = ST("body", fontName="Helvetica", fontSize=11, alignment=TA_CENTER,
               textColor=BLACK, spaceAfter=4, leading=18)
    DEG   = ST("deg",  fontName="Helvetica-Bold", fontSize=24, alignment=TA_CENTER,
               textColor=NAVY_D, spaceAfter=6, spaceBefore=4)
    DATE  = ST("date", fontName="Helvetica-Oblique", fontSize=11, alignment=TA_CENTER,
               textColor=NAVY_D, spaceAfter=16)
    SML   = ST("sml",  fontName="Helvetica", fontSize=8, alignment=TA_CENTER,
               textColor=colors.grey, spaceAfter=3)
    SIG   = ST("sig",  fontName="Helvetica", fontSize=10, alignment=TA_CENTER,
               textColor=BLACK, spaceAfter=2)

    # ── Κείμενο ανά βαθμό ─────────────────────────────────────
    ΒΑΘΜΟΣ_ΚΕΙΜ = {
        "Μαθητής":    ("τον του <b>Μαθητού</b>", "Μαθητού"),
        "Εταίρος":    ("τον του <b>Εταίρου</b>", "Εταίρου"),
        "Διδάσκαλος": ("τον του <b>Εταίρου</b> βαθμόν<br/>καί είτα εις τον του", "Διδασκάλου"),
    }
    βαθμ_text, βαθμ_title = ΒΑΘΜΟΣ_ΚΕΙΜ.get(βαθμός, ("τον του <b>Μαθητού</b>", "Μαθητού"))

    ονομα = f"{member.get('επώνυμο','')} {member.get('όνομα','')}".strip()

    # Μορφοποίηση ημερομηνίας
    try:
        import pandas as pd
        ημ = pd.to_datetime(ημ_βαθμού)
        ΜΗΝΕΣ = ["","Ιανουαρίου","Φεβρουαρίου","Μαρτίου","Απριλίου","Μαΐου","Ιουνίου",
                  "Ιουλίου","Αυγούστου","Σεπτεμβρίου","Οκτωβρίου","Νοεμβρίου","Δεκεμβρίου"]
        ημ_str = f"{ημ.day}η μηνός {ΜΗΝΕΣ[ημ.month]} δε του έτους {ημ.year}"
    except Exception:
        ημ_str = ημ_βαθμού

    # ── Δημιουργία PDF ─────────────────────────────────────────
    buf = io.BytesIO()

    def draw_border(c, doc):
        """Ζωγραφίζει το μαίανδρο περίγραμμα."""
        w, h = A4
        margin = 1.2*cm

        # Εξωτερικό πλαίσιο
        c.setStrokeColor(GOLD_D)
        c.setLineWidth(3)
        c.rect(margin, margin, w - 2*margin, h - 2*margin)

        # Εσωτερικό πλαίσιο
        c.setLineWidth(1)
        inner = margin + 0.3*cm
        c.rect(inner, inner, w - 2*inner, h - 2*inner)

        # Μαίανδρος — μικρά τετράγωνα κατά μήκος του περιγράμματος
        c.setFillColor(GOLD_D)
        c.setStrokeColor(GOLD_D)
        c.setLineWidth(0.5)
        sq = 0.28*cm; gap = 0.32*cm
        border_m = margin + 0.05*cm

        # Πάνω & κάτω
        x = border_m + sq
        while x < w - border_m - sq*2:
            c.rect(x, h - border_m - sq, sq, sq, fill=1)
            c.rect(x, border_m, sq, sq, fill=1)
            x += gap + sq

        # Αριστερά & δεξιά
        y = border_m + sq
        while y < h - border_m - sq*2:
            c.rect(border_m, y, sq, sq, fill=1)
            c.rect(w - border_m - sq, y, sq, sq, fill=1)
            y += gap + sq

        # Watermark
        if watermark:
            c.saveState()
            c.setFillColor(colors.Color(0.8, 0.8, 0.8, alpha=0.25))
            c.setFont("Helvetica-Bold", 36)
            c.translate(w/2, h/2)
            c.rotate(40)
            c.drawCentredString(0, 0, "ΑΝΤΙΓΡΑΦΟ ΑΡΧΕΙΟΥ ΣΤΟΑΣ")
            c.restoreState()

        # Κυκλική διακόσμηση κέντρου κεφαλής
        c.setStrokeColor(GOLD_D)
        c.setFillColor(colors.white)
        c.setLineWidth(1.5)
        c.circle(w/2, h - 3.2*cm, 0.9*cm, fill=1, stroke=1)
        c.setFillColor(NAVY_D)
        c.setFont("Helvetica-Bold", 6)
        c.drawCentredString(w/2, h - 3.15*cm, "Μ.Σ.Τ.Ε.")

    frame = Frame(2*cm, 2*cm, A4[0]-4*cm, A4[1]-4*cm,
                  leftPadding=0.5*cm, rightPadding=0.5*cm,
                  topPadding=0.3*cm, bottomPadding=0.3*cm)
    template = PageTemplate(id="diploma", frames=[frame], onPage=draw_border)
    doc = BaseDocTemplate(buf, pagesize=A4,
                          rightMargin=2*cm, leftMargin=2*cm,
                          topMargin=2*cm, bottomMargin=2*cm)
    doc.addPageTemplates([template])

    # ── Περιεχόμενο ───────────────────────────────────────────
    story = []

    # Κεφαλίδα
    story.append(Spacer(1, 0.8*cm))
    story.append(Paragraph("Ε.Λ.Τ.Μ.Α.Τ.Σ.", HDR2))
    story.append(Spacer(1, 0.5*cm))
    story.append(HRFlowable(width="80%", thickness=1.5, color=GOLD_D,
                             hAlign="CENTER", spaceAfter=6))
    story.append(Paragraph("ΜΕΓΑΛΗ ΣΤΟΑ ΤΗΣ ΕΛΛΑΔΟΣ", HDR1))
    story.append(Paragraph("Ἀρχαίου Ἐλευθέρου καὶ Ἀποδεδεγμένου Τεκτονισμοῦ", HDR2))
    story.append(HRFlowable(width="80%", thickness=1.5, color=GOLD_D,
                             hAlign="CENTER", spaceAfter=10))
    story.append(Spacer(1, 0.4*cm))

    # Κύριο κείμενο
    story.append(Paragraph("Γνωτοί πάντες", INTRO))
    story.append(Paragraph("οἱ τά γράμματα τάδε ἀναγνωσόμενοι,", INTRO))
    story.append(Paragraph("ὅτι ὁ ἀδελφός", INTRO))
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph(ονομα, NAME))
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph(
        "ὁ τὸ ἑαυτοῦ ὄνομα ἐν τῷ περιζώματι τῇ ἑαυτοῦ χειρί γεγραφώς",
        BODY))
    story.append(Paragraph(
        "εἰς τήν τῶν Λατόμων ἤ Τεκτονικῶν Τεχνῶν μεμύηται",
        BODY))
    story.append(Paragraph(
        "καί εἰσεληλύθεν εἰς τήν ὑπό τήν Ἡμετέραν Αἰγίδα Στοάν",
        BODY))
    story.append(Paragraph(
        "τῷ ὀνόματι μέν <b>Ἀκρόπολις</b> ὑπό ἀριθμόν 84 δέ.",
        BODY))
    story.append(Paragraph(
        "Οὗτος τόν νενομισμένον χρόνον ἀνύσας καί δοκιμασθείς",
        BODY))
    story.append(Paragraph(
        f"καί ἐξετασθείς, εἰς {βαθμ_text}",
        BODY))
    story.append(Spacer(1, 0.2*cm))

    story.append(Paragraph(βαθμ_title, DEG))

    story.append(Paragraph(
        "ἀναδέδεκται ἐν τῇ τῆς Στοᾶς συνεδρίᾳ τῇ γενομένῃ",
        BODY))
    story.append(Paragraph(f"ἐν ἡμέρᾳ μέν {ημ_str}.", BODY))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph(
        "Τό ὄνομα αὐτοῦ ἐν ταῖς Ἐπισήμοις Πράξεσι",
        BODY))
    story.append(Paragraph(
        "τῆς Μεγάλης Στοᾶς τῆς Ἑλλάδος",
        BODY))
    story.append(Paragraph(
        "ἀναγέγραπται καί τοῦτο, οὕτω δή γενόμενον,",
        BODY))
    story.append(Paragraph(
        "δηλοῦται τῷ Διπλώματι τῷδε",
        BODY))
    story.append(Paragraph(
        "οὐ μόνον τοῖς Ἡμετέροις αὐτογράφοις,",
        BODY))
    story.append(Paragraph(
        "ἀλλά καί τῇ Σφραγῖδι τῆς Μεγάλης Στοᾶς κεκυρωμένον.",
        BODY))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph(
        "Πίστευε δ' ὅτι, οὐδείς, εἰ μή πρότερον δοκιμασθείς",
        BODY))
    story.append(Paragraph(
        "καί ἐξετασθείς, ἔξεστιν εἰσελθεῖν",
        BODY))
    story.append(Paragraph(
        "εἰς Λατόμον ἤ Τεκτονικήν Στοάν",
        BODY))
    story.append(Spacer(1, 0.4*cm))

    # Ημερομηνία
    story.append(Paragraph(
        f"Ἐν Ἀνατολῇ Ἀθηνῶν τῇ {ημ_str.replace('μηνός','μηνός').split('δε')[0].strip()} {ημ_βαθμού[-4:] if len(ημ_βαθμού)>=4 else ''}",
        DATE))

    story.append(Spacer(1, 0.2*cm))

    # Υπογραφές
    sig_data = [[
        Paragraph("ο Μέγας Διδάσκαλος<br/><br/><br/><br/>Γεώργιος Μπινιάρης", SIG),
        Paragraph("", SIG),
        Paragraph("ο Μέγας Γραμματεύς<br/><br/><br/><br/>Ανδρέας Αρχουζής", SIG),
    ]]
    sig_t = Table(sig_data, colWidths=[5.5*cm, 3.5*cm, 5.5*cm])
    sig_t.setStyle(TableStyle([
        ("FONTSIZE",    (0,0),(-1,-1), 10),
        ("ALIGN",       (0,0),(-1,-1), "CENTER"),
        ("VALIGN",      (0,0),(-1,-1), "TOP"),
        ("TOPPADDING",  (0,0),(-1,-1), 5),
        ("LINEABOVE",   (0,0),(0,-1), 0.5, GOLD_D),
        ("LINEABOVE",   (2,0),(2,-1), 0.5, GOLD_D),
    ]))
    story.append(sig_t)

    if watermark:
        story.append(Spacer(1, 0.2*cm))
        story.append(Paragraph(
            "⚠ ΑΝΤΙΓΡΑΦΟ ΑΡΧΕΙΟΥ ΣΤΟΑΣ — Το επίσημο εκδίδεται από τη Μεγάλη Στοά",
            SML))

    doc.build(story)
    buf.seek(0)
    return buf

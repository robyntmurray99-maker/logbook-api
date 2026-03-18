from flask import Flask, request, send_file, jsonify
from flask_cors import CORS
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
import io, os

app = Flask(__name__)
CORS(app)

BLUE         = colors.HexColor('#2563eb')
BLUE_DARK    = colors.HexColor('#1d4ed8')
LIGHT_BLUE   = colors.HexColor('#eff6ff')
BORDER_COLOR = colors.HexColor('#dbe4f8')
MUTED        = colors.HexColor('#6b7a9e')
TEXT         = colors.HexColor('#1a2340')
GREEN        = colors.HexColor('#16a34a')
GREEN_LIGHT  = colors.HexColor('#f0fdf4')
WHITE        = colors.white
LIGHT_GREY   = colors.HexColor('#f8faff')

def S(name, **kw):
    return ParagraphStyle(name, **kw)

def build_styles():
    return {
        'cover_label':   S('cl', fontSize=10, fontName='Helvetica', textColor=MUTED, alignment=TA_CENTER, spaceAfter=2, leading=14),
        'cover_value':   S('cv', fontSize=15, fontName='Helvetica-Bold', textColor=TEXT, alignment=TA_CENTER, spaceAfter=10, leading=20),
        'cover_title1':  S('ct1', fontSize=32, fontName='Helvetica-Bold', textColor=BLUE, alignment=TA_CENTER, spaceAfter=0, leading=40),
        'cover_title2':  S('ct2', fontSize=32, fontName='Helvetica-Bold', textColor=TEXT, alignment=TA_CENTER, spaceAfter=0, leading=40),
        'cover_sub':     S('cs', fontSize=12, fontName='Helvetica-Oblique', textColor=MUTED, alignment=TA_CENTER, spaceAfter=0),
        'cover_period':  S('cp', fontSize=11, fontName='Helvetica', textColor=MUTED, alignment=TA_CENTER, spaceAfter=4),
        'section_hdr':   S('sh', fontSize=9, fontName='Helvetica-Bold', textColor=BLUE, spaceBefore=10, spaceAfter=5, letterSpacing=1.5),
        'entry_type':    S('et', fontSize=8, fontName='Helvetica-Bold', textColor=BLUE, spaceAfter=2, letterSpacing=1),
        'entry_title':   S('etl', fontSize=13, fontName='Helvetica-Bold', textColor=TEXT, spaceAfter=3),
        'entry_meta':    S('em', fontSize=9, fontName='Helvetica', textColor=MUTED, spaceAfter=5),
        'label':         S('lb', fontSize=8, fontName='Helvetica-Bold', textColor=MUTED, spaceAfter=2),
        'body':          S('bd', fontSize=9, fontName='Helvetica', textColor=TEXT, spaceAfter=3, leading=13),
        'nature_item':   S('ni', fontSize=9, fontName='Helvetica', textColor=TEXT, leftIndent=8, spaceAfter=2, leading=13),
        'degree':        S('dg', fontSize=9, fontName='Helvetica-Bold', textColor=BLUE, spaceAfter=3),
        'principal_txt': S('pt', fontSize=9, fontName='Helvetica-Oblique', textColor=TEXT, spaceAfter=3, leading=13),
        'pr_heading':    S('prh', fontSize=13, fontName='Helvetica-Bold', textColor=WHITE, spaceAfter=0),
        'pr_label':      S('prl', fontSize=8, fontName='Helvetica-Bold', textColor=MUTED, spaceAfter=3),
        'pr_body':       S('prb', fontSize=10, fontName='Helvetica', textColor=TEXT, spaceAfter=4, leading=15),
        'sig_line':      S('sl', fontSize=9, fontName='Helvetica', textColor=MUTED, spaceAfter=2),
        'decl_text':     S('dt', fontSize=10, fontName='Helvetica-Oblique', textColor=TEXT, leading=16, spaceAfter=6),
    }

def fmt_date(d):
    if not d: return '—'
    try:
        parts = d.split('-')
        months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
        return f"{int(parts[2])} {months[int(parts[1])-1]} {parts[0]}"
    except:
        return d

def make_cover(styles, student_name, principal_name, office, period, num_entries, total_hours):
    story = []
    story.append(Spacer(1, 22*mm))

    # Top decorative rule
    story.append(HRFlowable(width="100%", thickness=3, color=BLUE, hAlign='CENTER'))
    story.append(Spacer(1, 10*mm))

    # Title - two lines with breathing room
    story.append(Paragraph("Student Surveyor's", styles['cover_title1']))
    story.append(Spacer(1, 4*mm))
    story.append(Paragraph("Diary and Log Book", styles['cover_title2']))
    story.append(Spacer(1, 6*mm))
    story.append(Paragraph("Attachment (Practical)", styles['cover_sub']))
    story.append(Spacer(1, 10*mm))

    # Thin divider
    story.append(HRFlowable(width="50%", thickness=1, color=BORDER_COLOR, hAlign='CENTER'))
    story.append(Spacer(1, 10*mm))

    # Info block as a centered table
    info = [
        ["Student Surveyor's Name:", student_name],
        ["Principal's Name:", principal_name],
        ["Principal's Office:", office],
        ["Period:", period],
        ["Total Entries:", str(num_entries)],
        ["Total Hours:", str(total_hours)],
    ]
    label_style = S('il', fontSize=10, fontName='Helvetica', textColor=MUTED, alignment=TA_RIGHT, leading=18)
    value_style = S('iv', fontSize=10, fontName='Helvetica-Bold', textColor=TEXT, alignment=TA_LEFT, leading=18)

    table_data = [[Paragraph(r[0], label_style), Paragraph(r[1], value_style)] for r in info]
    info_table = Table(table_data, colWidths=[68*mm, 90*mm])
    info_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ('LINEBELOW', (0,0), (-1,-2), 0.3, BORDER_COLOR),
        ('BACKGROUND', (0,0), (-1,-1), LIGHT_GREY),
        ('ROUNDEDCORNERS', [8]),
    ]))
    # Center the table on the page
    wrapper = Table([[info_table]], colWidths=[170*mm])
    wrapper.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(wrapper)
    story.append(Spacer(1, 12*mm))

    # Principal's Declaration box
    decl_data = [
        [Paragraph("Principal's Declaration", S('pdh', fontSize=10, fontName='Helvetica-Bold', textColor=BLUE, spaceAfter=6))],
        [Paragraph("I confirm that the entries in this Diary and Logbook are an accurate record of the candidate's work.", styles['decl_text'])],
        [Spacer(1, 4*mm)],
        [Table([
            [
                Paragraph("Interim Assessment", S('slt', fontSize=9, fontName='Helvetica-Bold', textColor=MUTED)),
                Paragraph("Signature: _________________________", S('sls', fontSize=9, fontName='Helvetica', textColor=TEXT)),
                Paragraph("Date: ________________", S('sls2', fontSize=9, fontName='Helvetica', textColor=TEXT)),
            ],
            [
                Paragraph("Final Assessment", S('slt2', fontSize=9, fontName='Helvetica-Bold', textColor=MUTED)),
                Paragraph("Signature: _________________________", S('sls3', fontSize=9, fontName='Helvetica', textColor=TEXT)),
                Paragraph("Date: ________________", S('sls4', fontSize=9, fontName='Helvetica', textColor=TEXT)),
            ],
        ], colWidths=[40*mm, 85*mm, 45*mm])],
    ]
    decl_table = Table([[cell] for cell in [
        Paragraph("Principal's Declaration", S('pdh2', fontSize=10, fontName='Helvetica-Bold', textColor=BLUE, spaceAfter=4)),
        Paragraph("I confirm that the entries in this Diary and Logbook are an accurate record of the candidate's work.", styles['decl_text']),
        Spacer(1, 3*mm),
        Table([
            [
                Paragraph("Interim Assessment", S('slt', fontSize=9, fontName='Helvetica-Bold', textColor=MUTED)),
                Paragraph("Signature: _______________________", S('sls', fontSize=9, fontName='Helvetica', textColor=TEXT)),
                Paragraph("Date: _____________", S('slsd', fontSize=9, fontName='Helvetica', textColor=TEXT)),
            ],
            [
                Paragraph("Final Assessment", S('slt2', fontSize=9, fontName='Helvetica-Bold', textColor=MUTED)),
                Paragraph("Signature: _______________________", S('sls2', fontSize=9, fontName='Helvetica', textColor=TEXT)),
                Paragraph("Date: _____________", S('slsd2', fontSize=9, fontName='Helvetica', textColor=TEXT)),
            ],
        ], colWidths=[42*mm, 82*mm, 42*mm], style=TableStyle([
            ('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5),
            ('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),4),
            ('LINEBELOW',(0,0),(-1,-2),0.4,BORDER_COLOR),
        ])),
    ]], colWidths=[166*mm])
    decl_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), LIGHT_BLUE),
        ('LEFTPADDING', (0,0), (-1,-1), 14),
        ('RIGHTPADDING', (0,0), (-1,-1), 14),
        ('TOPPADDING', (0,0), (0,0), 12),
        ('TOPPADDING', (0,1), (-1,-1), 4),
        ('BOTTOMPADDING', (0,-1), (-1,-1), 12),
        ('ROUNDEDCORNERS', [8]),
        ('BOX', (0,0), (-1,-1), 1, BLUE),
    ]))
    story.append(decl_table)
    story.append(Spacer(1, 8*mm))
    story.append(HRFlowable(width="100%", thickness=3, color=BLUE, hAlign='CENTER'))
    story.append(PageBreak())
    return story

def make_tally(styles, entries):
    story = []
    story.append(Paragraph("TALLY OF HOURS", styles['section_hdr']))
    story.append(HRFlowable(width="100%", thickness=1, color=BORDER_COLOR))
    story.append(Spacer(1, 4*mm))

    cat_map = {
        "Cadastral Survey (Boundary Reopening)": "Cadastral",
        "Cadastral Survey (Boundary Survey)": "Cadastral",
        "Cadastral Survey (Surveyor's Identification Report)": "Cadastral",
        "Engineering Survey": "Engineering",
        "Topographical Survey": "Topographic",
        "Subdivision": "Subdivision",
        "Strata (Plan Preparation)": "Strata",
        "Plan Preparation": "Cadastral",
    }
    cat_totals = {}
    for e in entries:
        cat = cat_map.get(e.get('job_type',''), e.get('job_type',''))
        hrs = float(e.get('total_hours',0) or 0)
        cat_totals[cat] = cat_totals.get(cat,0) + hrs
    grand = sum(float(e.get('total_hours',0) or 0) for e in entries)

    def fmth(n): return int(n) if n==int(n) else round(n,1)

    data = [['Nature of Work', 'Total Hours']]
    for cat, hrs in cat_totals.items():
        data.append([cat, str(fmth(hrs))])
    data.append(['TOTAL', str(fmth(grand))])

    t = Table(data, colWidths=[120*mm, 46*mm])
    t.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),BLUE),('TEXTCOLOR',(0,0),(-1,0),WHITE),
        ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),('FONTSIZE',(0,0),(-1,-1),9),
        ('FONTNAME',(0,1),(-1,-2),'Helvetica'),('FONTNAME',(0,-1),(-1,-1),'Helvetica-Bold'),
        ('BACKGROUND',(0,-1),(-1,-1),LIGHT_BLUE),('TEXTCOLOR',(0,-1),(-1,-1),BLUE),
        ('ALIGN',(1,0),(1,-1),'CENTER'),('GRID',(0,0),(-1,-1),0.5,BORDER_COLOR),
        ('ROWBACKGROUNDS',(0,1),(-1,-2),[WHITE,LIGHT_GREY]),
        ('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7),
        ('LEFTPADDING',(0,0),(-1,-1),10),
    ]))
    story.append(t)
    story.append(PageBreak())
    return story

def make_progress_report(styles, report):
    items = []
    label = report.get('period_label','')
    obs = report.get('principal_observations','')
    cand = report.get('candidate_comments','')
    psig = report.get('principal_signature_date','')
    csig = report.get('candidate_signature_date','')

    # Header
    head = Table([[Paragraph(f"PRINCIPAL'S PROGRESS REPORT", S('prht', fontSize=9, fontName='Helvetica-Bold', textColor=WHITE, letterSpacing=1)),
                   Paragraph(label, S('prhs', fontSize=10, fontName='Helvetica-Bold', textColor=WHITE, alignment=TA_RIGHT))]],
                 colWidths=[90*mm, 76*mm])
    head.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,-1),BLUE),
        ('LEFTPADDING',(0,0),(-1,-1),12),('RIGHTPADDING',(0,0),(-1,-1),12),
        ('TOPPADDING',(0,0),(-1,-1),10),('BOTTOMPADDING',(0,0),(-1,-1),10),
    ]))
    items.append(head)
    items.append(Spacer(1, 3*mm))
    items.append(Paragraph("To be completed every six (6) months.", S('note', fontSize=8, fontName='Helvetica-Oblique', textColor=MUTED, spaceAfter=6)))

    # Principal observations
    items.append(Paragraph("Observations on training to date, experience gained and ability of Trainee:", styles['pr_label']))
    obs_box = Table([[Paragraph(obs if obs else '[Pending]', styles['pr_body'])]], colWidths=[166*mm])
    obs_box.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,-1),LIGHT_BLUE if obs else LIGHT_GREY),
        ('BOX',(0,0),(-1,-1),0.5,BORDER_COLOR),
        ('LEFTPADDING',(0,0),(-1,-1),10),('RIGHTPADDING',(0,0),(-1,-1),10),
        ('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),8),
    ]))
    items.append(obs_box)

    # Principal signature
    sig_data = [[
        Paragraph("Signature:", S('sl1', fontSize=9, fontName='Helvetica-Bold', textColor=MUTED)),
        Paragraph("_______________________________", S('sl2', fontSize=9, fontName='Helvetica', textColor=TEXT)),
        Paragraph("Date:", S('sl3', fontSize=9, fontName='Helvetica-Bold', textColor=MUTED)),
        Paragraph(fmt_date(psig) if psig else '________________', S('sl4', fontSize=9, fontName='Helvetica', textColor=TEXT)),
    ]]
    sig_table = Table(sig_data, colWidths=[22*mm, 70*mm, 16*mm, 58*mm])
    sig_table.setStyle(TableStyle([
        ('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),
        ('LEFTPADDING',(0,0),(-1,-1),0),
    ]))
    items.append(sig_table)
    items.append(Spacer(1, 4*mm))

    # Candidate comments
    items.append(Paragraph("Candidate's Comments:", styles['pr_label']))
    cand_box = Table([[Paragraph(cand if cand else '[To be completed by candidate]', styles['pr_body'])]], colWidths=[166*mm])
    cand_box.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,-1),GREEN_LIGHT if cand else LIGHT_GREY),
        ('BOX',(0,0),(-1,-1),0.5,BORDER_COLOR),
        ('LEFTPADDING',(0,0),(-1,-1),10),('RIGHTPADDING',(0,0),(-1,-1),10),
        ('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),8),
    ]))
    items.append(cand_box)

    # Candidate signature
    csig_data = [[
        Paragraph("Signature:", S('csl1', fontSize=9, fontName='Helvetica-Bold', textColor=MUTED)),
        Paragraph("_______________________________", S('csl2', fontSize=9, fontName='Helvetica', textColor=TEXT)),
        Paragraph("Date:", S('csl3', fontSize=9, fontName='Helvetica-Bold', textColor=MUTED)),
        Paragraph(fmt_date(csig) if csig else '________________', S('csl4', fontSize=9, fontName='Helvetica', textColor=TEXT)),
    ]]
    csig_table = Table(csig_data, colWidths=[22*mm, 70*mm, 16*mm, 58*mm])
    csig_table.setStyle(TableStyle([
        ('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),
        ('LEFTPADDING',(0,0),(-1,-1),0),
    ]))
    items.append(csig_table)
    items.append(Spacer(1, 6*mm))
    items.append(HRFlowable(width="100%", thickness=0.5, color=BORDER_COLOR))
    items.append(Spacer(1, 6*mm))

    return KeepTogether(items)

def make_entry(styles, entry, num, total):
    job_type  = entry.get('job_type','')
    date      = entry.get('date','')
    title_ref = entry.get('title_ref','—')
    parish    = entry.get('parish','')
    prop_desc = entry.get('property_desc','—')
    nature    = entry.get('selected_nature',[]) or []
    notes     = entry.get('student_notes','') or ''
    hour_rows = entry.get('hour_rows',[]) or []
    total_hrs = entry.get('total_hours','0')
    parcel    = entry.get('parcel_size','N/A') or 'N/A'
    degree    = entry.get('degree','—') or '—'
    principal = entry.get('principal_comments','') or '[Pending]'

    items = []

    header = Table([[
        Paragraph(job_type.upper(), styles['entry_type']),
        Paragraph(f"Entry {num} of {total}", S('er', fontSize=8, fontName='Helvetica', textColor=MUTED, alignment=TA_RIGHT))
    ]], colWidths=[120*mm, 46*mm])
    header.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,-1),LIGHT_BLUE),
        ('LEFTPADDING',(0,0),(-1,-1),10),('RIGHTPADDING',(0,0),(-1,-1),10),
        ('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),4),
        ('LINEBELOW',(0,0),(-1,-1),1.5,BLUE),
    ]))
    items.append(header)
    items.append(Paragraph(prop_desc, styles['entry_title']))

    meta = f"{parish}  ·  {fmt_date(date)}  ·  {title_ref}  ·  Parcel: {parcel}"
    items.append(Paragraph(meta, styles['entry_meta']))
    items.append(HRFlowable(width="100%", thickness=0.5, color=BORDER_COLOR))
    items.append(Spacer(1, 3*mm))

    left = []
    left.append(Paragraph("NATURE OF PROFESSIONAL WORK", styles['label']))
    for n in nature:
        left.append(Paragraph(f"– {n}", styles['nature_item']))
    left.append(Spacer(1, 3*mm))
    left.append(Paragraph("STUDENT SURVEYOR'S NOTES", styles['label']))
    left.append(Paragraph(notes if notes else '—', styles['body']))

    right = []
    right.append(Paragraph("WORK HOURS", styles['label']))
    for row in hour_rows:
        if row.get('hours'):
            right.append(Paragraph(f"{row.get('type','')}: <b>{row.get('hours','')} hrs</b>", styles['body']))
    right.append(Paragraph(f"<b>Total: {total_hrs} hrs</b>", styles['degree']))
    right.append(Spacer(1, 3*mm))
    right.append(Paragraph("STUDENT SURVEYOR DEGREE", styles['label']))
    right.append(Paragraph(degree, styles['degree']))
    right.append(Spacer(1, 3*mm))
    right.append(Paragraph("PRINCIPAL'S COMMENTS", styles['label']))
    right.append(Paragraph(principal, styles['principal_txt']))

    lt = Table([[c] for c in left], colWidths=[100*mm])
    lt.setStyle(TableStyle([('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),4),('TOPPADDING',(0,0),(-1,-1),1),('BOTTOMPADDING',(0,0),(-1,-1),1)]))
    rt = Table([[c] for c in right], colWidths=[66*mm])
    rt.setStyle(TableStyle([('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),0),('TOPPADDING',(0,0),(-1,-1),1),('BOTTOMPADDING',(0,0),(-1,-1),1),('LINEBEFORE',(0,0),(0,-1),0.5,BORDER_COLOR)]))

    two = Table([[lt,rt]], colWidths=[100*mm,68*mm])
    two.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),0),('TOPPADDING',(0,0),(-1,-1),0),('BOTTOMPADDING',(0,0),(-1,-1),0)]))
    items.append(two)
    items.append(Spacer(1, 4*mm))
    items.append(HRFlowable(width="100%", thickness=0.5, color=BORDER_COLOR))
    items.append(Spacer(1, 5*mm))

    return KeepTogether(items)

def get_period_for_entry(date_str):
    """Return the 6-month period label for a given date string."""
    try:
        parts = date_str.split('-')
        year, month = int(parts[0]), int(parts[1])
        if month <= 6:
            return f"January – June {year}"
        else:
            return f"July – December {year}"
    except:
        return None

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'})

@app.route('/generate-pdf', methods=['POST'])
def generate_pdf():
    try:
        data = request.get_json()
        entries          = data.get('entries', [])
        student_name     = data.get('student_name', 'Student Surveyor')
        principal_name   = data.get('principal_name', 'Timothy A. Thwaites, BA(Hons) MSc., CLS')
        office           = data.get('office', 'Thwaites Surveying Limited')
        period           = data.get('period', '2025 – 2026')
        progress_reports = data.get('progress_reports', [])

        total_hours = sum(float(e.get('total_hours',0) or 0) for e in entries)
        th_fmt = int(total_hours) if total_hours == int(total_hours) else round(total_hours,1)

        styles = build_styles()

        # Build a dict of progress reports keyed by period label
        pr_by_label = {r.get('period_label',''): r for r in progress_reports}

        # Determine all 6-month periods covered by entries
        period_labels_seen = []
        for e in entries:
            lbl = get_period_for_entry(e.get('date',''))
            if lbl and lbl not in period_labels_seen:
                period_labels_seen.append(lbl)

        def add_page_number(canvas, doc):
            canvas.saveState()
            canvas.setFont('Helvetica', 8)
            canvas.setFillColor(MUTED)
            canvas.drawString(20*mm, 12*mm, f"{student_name}  ·  Surveyor's Logbook  ·  {period}")
            canvas.drawRightString(190*mm, 12*mm, f"Page {doc.page}")
            canvas.setStrokeColor(BORDER_COLOR)
            canvas.setLineWidth(0.5)
            canvas.line(20*mm, 15*mm, 190*mm, 15*mm)
            canvas.restoreState()

        story = []
        story += make_cover(styles, f"{student_name}, BSc.(Hons.)", principal_name, office, period, len(entries), th_fmt)
        story += make_tally(styles, entries)

        # Group entries by period and insert progress reports between groups
        story.append(Paragraph("LOGBOOK ENTRIES", styles['section_hdr']))
        story.append(HRFlowable(width="100%", thickness=2, color=BLUE))
        story.append(Spacer(1, 4*mm))

        current_period = None
        entry_num = 0
        for e in entries:
            lbl = get_period_for_entry(e.get('date',''))
            # If we've moved into a new period, insert progress report first
            if lbl and lbl != current_period:
                if current_period is not None:
                    # Insert progress report for the period we just finished
                    story.append(PageBreak())
                    pr = pr_by_label.get(current_period, {'period_label': current_period})
                    story.append(make_progress_report(styles, pr))
                    story.append(Paragraph("LOGBOOK ENTRIES (CONTINUED)", styles['section_hdr']))
                    story.append(HRFlowable(width="100%", thickness=2, color=BLUE))
                    story.append(Spacer(1, 4*mm))
                current_period = lbl

            entry_num += 1
            story.append(make_entry(styles, e, entry_num, len(entries)))

        # Insert final progress report at end
        if current_period:
            story.append(PageBreak())
            pr = pr_by_label.get(current_period, {'period_label': current_period})
            story.append(make_progress_report(styles, pr))

        buf = io.BytesIO()
        doc = SimpleDocTemplate(
            buf, pagesize=A4,
            leftMargin=20*mm, rightMargin=20*mm,
            topMargin=20*mm, bottomMargin=22*mm,
            title="Student Surveyor's Diary and Log Book",
            author=student_name,
        )
        doc.build(story, onFirstPage=add_page_number, onLaterPages=add_page_number)
        buf.seek(0)

        filename = f"Logbook_{student_name.replace(' ','_')}.pdf"
        return send_file(buf, mimetype='application/pdf', as_attachment=True, download_name=filename)

    except Exception as e:
        import traceback
        return jsonify({'error': str(e), 'trace': traceback.format_exc()}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

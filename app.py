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
import io
import json

app = Flask(__name__)
CORS(app)

# ── COLORS ──
BLUE        = colors.HexColor('#2563eb')
LIGHT_BLUE  = colors.HexColor('#eff6ff')
BORDER_COLOR= colors.HexColor('#dbe4f8')
MUTED       = colors.HexColor('#6b7a9e')
TEXT        = colors.HexColor('#1a2340')
GREEN       = colors.HexColor('#16a34a')
WHITE       = colors.white

def build_styles():
    styles = getSampleStyleSheet()
    return {
        'cover_title': ParagraphStyle('cover_title', fontSize=26, fontName='Helvetica-Bold', textColor=BLUE, alignment=TA_CENTER, spaceAfter=6),
        'cover_sub':   ParagraphStyle('cover_sub', fontSize=12, fontName='Helvetica', textColor=MUTED, alignment=TA_CENTER, spaceAfter=4),
        'cover_name':  ParagraphStyle('cover_name', fontSize=15, fontName='Helvetica-Bold', textColor=TEXT, alignment=TA_CENTER, spaceAfter=6),
        'section_header': ParagraphStyle('section_header', fontSize=9, fontName='Helvetica-Bold', textColor=BLUE, spaceBefore=10, spaceAfter=5, letterSpacing=1.5),
        'entry_type':  ParagraphStyle('entry_type', fontSize=8, fontName='Helvetica-Bold', textColor=BLUE, spaceAfter=2, letterSpacing=1),
        'entry_title': ParagraphStyle('entry_title', fontSize=13, fontName='Helvetica-Bold', textColor=TEXT, spaceAfter=3),
        'entry_meta':  ParagraphStyle('entry_meta', fontSize=9, fontName='Helvetica', textColor=MUTED, spaceAfter=5),
        'label':       ParagraphStyle('label', fontSize=8, fontName='Helvetica-Bold', textColor=MUTED, spaceAfter=2),
        'body':        ParagraphStyle('body', fontSize=9, fontName='Helvetica', textColor=TEXT, spaceAfter=3, leading=13),
        'nature_item': ParagraphStyle('nature_item', fontSize=9, fontName='Helvetica', textColor=TEXT, leftIndent=8, spaceAfter=2, leading=13),
        'degree':      ParagraphStyle('degree', fontSize=9, fontName='Helvetica-Bold', textColor=BLUE, spaceAfter=3),
        'principal':   ParagraphStyle('principal', fontSize=9, fontName='Helvetica-Oblique', textColor=TEXT, spaceAfter=3, leading=13),
    }

def make_cover(styles, student_name, principal_name, office, period, num_entries, total_hours):
    story = []
    story.append(Spacer(1, 35*mm))
    story.append(Paragraph("STUDENT SURVEYOR'S", styles['cover_title']))
    story.append(Paragraph("DIARY AND LOG BOOK", styles['cover_title']))
    story.append(Spacer(1, 6*mm))
    story.append(HRFlowable(width="55%", thickness=2, color=BLUE, hAlign='CENTER'))
    story.append(Spacer(1, 6*mm))
    story.append(Paragraph("Attachment (Practical)", styles['cover_sub']))
    story.append(Spacer(1, 5*mm))
    story.append(Paragraph("Student Surveyor's Name:", styles['cover_sub']))
    story.append(Paragraph(student_name, styles['cover_name']))
    story.append(Paragraph("Principal's Name:", styles['cover_sub']))
    story.append(Paragraph(principal_name, styles['cover_name']))
    story.append(Paragraph("Principal's Office:", styles['cover_sub']))
    story.append(Paragraph(office, styles['cover_name']))
    story.append(Spacer(1, 6*mm))
    story.append(HRFlowable(width="55%", thickness=1, color=BORDER_COLOR, hAlign='CENTER'))
    story.append(Spacer(1, 5*mm))
    story.append(Paragraph(f"Period: {period}", styles['cover_sub']))
    story.append(Paragraph(f"Total Entries: {num_entries}   ·   Total Hours: {total_hours}", styles['cover_sub']))
    story.append(PageBreak())
    return story

def make_tally(styles, entries):
    story = []
    story.append(Paragraph("TALLY OF HOURS", styles['section_header']))
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
        jt = e.get('job_type', '')
        hrs = float(e.get('total_hours', 0) or 0)
        cat = cat_map.get(jt, jt)
        cat_totals[cat] = cat_totals.get(cat, 0) + hrs

    grand = sum(float(e.get('total_hours', 0) or 0) for e in entries)
    grand_fmt = int(grand) if grand == int(grand) else round(grand, 1)

    data = [['Nature of Work', 'Total Hours']]
    for cat, hrs in cat_totals.items():
        hrs_fmt = int(hrs) if hrs == int(hrs) else round(hrs, 1)
        data.append([cat, str(hrs_fmt)])
    data.append(['TOTAL', str(grand_fmt)])

    t = Table(data, colWidths=[120*mm, 40*mm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), BLUE),
        ('TEXTCOLOR', (0,0), (-1,0), WHITE),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('FONTNAME', (0,1), (-1,-2), 'Helvetica'),
        ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'),
        ('BACKGROUND', (0,-1), (-1,-1), LIGHT_BLUE),
        ('TEXTCOLOR', (0,-1), (-1,-1), BLUE),
        ('ALIGN', (1,0), (1,-1), 'CENTER'),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('ROWBACKGROUNDS', (0,1), (-1,-2), [WHITE, colors.HexColor('#f8faff')]),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(t)
    story.append(PageBreak())
    return story

def make_entry(styles, entry, num, total):
    job_type    = entry.get('job_type', '')
    date        = entry.get('date', '')
    title_ref   = entry.get('title_ref', '—')
    parish      = entry.get('parish', '')
    prop_desc   = entry.get('property_desc', '—')
    nature      = entry.get('selected_nature', []) or []
    notes       = entry.get('student_notes', '') or ''
    hour_rows   = entry.get('hour_rows', []) or []
    total_hrs   = entry.get('total_hours', '0')
    parcel      = entry.get('parcel_size', 'N/A') or 'N/A'
    degree      = entry.get('degree', '—') or '—'
    principal   = entry.get('principal_comments', '') or '[Pending]'

    items = []

    # Header bar
    header_data = [[
        Paragraph(job_type.upper(), styles['entry_type']),
        Paragraph(f"Entry {num} of {total}", ParagraphStyle('right9', fontSize=8, fontName='Helvetica', textColor=MUTED, alignment=TA_RIGHT))
    ]]
    header_table = Table(header_data, colWidths=[120*mm, 50*mm])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), LIGHT_BLUE),
        ('LEFTPADDING', (0,0), (-1,-1), 10),
        ('RIGHTPADDING', (0,0), (-1,-1), 10),
        ('TOPPADDING', (0,0), (-1,-1), 7),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LINEBELOW', (0,0), (-1,-1), 1.5, BLUE),
    ]))
    items.append(header_table)
    items.append(Paragraph(prop_desc, styles['entry_title']))

    # Format date nicely
    try:
        parts = date.split('-')
        months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
        date_fmt = f"{int(parts[2])} {months[int(parts[1])-1]} {parts[0]}"
    except:
        date_fmt = date

    meta = f"{parish}  ·  {date_fmt}  ·  {title_ref}  ·  Parcel: {parcel}"
    items.append(Paragraph(meta, styles['entry_meta']))
    items.append(HRFlowable(width="100%", thickness=0.5, color=BORDER_COLOR))
    items.append(Spacer(1, 3*mm))

    # Left column
    left = []
    left.append(Paragraph("NATURE OF PROFESSIONAL WORK", styles['label']))
    for n in nature:
        left.append(Paragraph(f"– {n}", styles['nature_item']))
    left.append(Spacer(1, 3*mm))
    left.append(Paragraph("STUDENT SURVEYOR'S NOTES", styles['label']))
    left.append(Paragraph(notes if notes else '—', styles['body']))

    # Right column
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
    right.append(Paragraph(principal, styles['principal']))

    left_table = Table([[cell] for cell in left], colWidths=[100*mm])
    left_table.setStyle(TableStyle([
        ('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),4),
        ('TOPPADDING',(0,0),(-1,-1),1),('BOTTOMPADDING',(0,0),(-1,-1),1),
    ]))
    right_table = Table([[cell] for cell in right], colWidths=[68*mm])
    right_table.setStyle(TableStyle([
        ('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),0),
        ('TOPPADDING',(0,0),(-1,-1),1),('BOTTOMPADDING',(0,0),(-1,-1),1),
        ('LINEBEFORE',(0,0),(0,-1),0.5,BORDER_COLOR),
    ]))

    two_col = Table([[left_table, right_table]], colWidths=[100*mm, 70*mm])
    two_col.setStyle(TableStyle([
        ('VALIGN',(0,0),(-1,-1),'TOP'),
        ('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),0),
        ('TOPPADDING',(0,0),(-1,-1),0),('BOTTOMPADDING',(0,0),(-1,-1),0),
    ]))
    items.append(two_col)
    items.append(Spacer(1, 4*mm))
    items.append(HRFlowable(width="100%", thickness=0.5, color=BORDER_COLOR))
    items.append(Spacer(1, 5*mm))

    return KeepTogether(items)

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'})

@app.route('/generate-pdf', methods=['POST'])
def generate_pdf():
    try:
        data = request.get_json()
        entries       = data.get('entries', [])
        student_name  = data.get('student_name', 'Student Surveyor')
        principal_name= data.get('principal_name', 'Timothy A. Thwaites, BA(Hons) MSc., CLS')
        office        = data.get('office', 'Thwaites Surveying Ltd.')
        period        = data.get('period', '2025 – 2026')

        total_hours = sum(float(e.get('total_hours', 0) or 0) for e in entries)
        total_fmt = int(total_hours) if total_hours == int(total_hours) else round(total_hours, 1)

        styles = build_styles()
        story = []

        # Page number footer
        student_name_ref = student_name
        period_ref = period

        def add_page_number(canvas, doc):
            canvas.saveState()
            canvas.setFont('Helvetica', 8)
            canvas.setFillColor(MUTED)
            canvas.drawString(20*mm, 12*mm, f"{student_name_ref}  ·  Surveyor's Logbook  ·  {period_ref}")
            canvas.drawRightString(190*mm, 12*mm, f"Page {doc.page}")
            canvas.setStrokeColor(BORDER_COLOR)
            canvas.setLineWidth(0.5)
            canvas.line(20*mm, 15*mm, 190*mm, 15*mm)
            canvas.restoreState()

        # Build story
        story += make_cover(styles, student_name, principal_name, office, period, len(entries), total_fmt)
        story += make_tally(styles, entries)

        story.append(Paragraph("LOGBOOK ENTRIES", styles['section_header']))
        story.append(HRFlowable(width="100%", thickness=2, color=BLUE))
        story.append(Spacer(1, 4*mm))

        for i, entry in enumerate(entries):
            story.append(make_entry(styles, entry, i+1, len(entries)))

        # Generate PDF to buffer
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
        return send_file(buf, mimetype='application/pdf',
                         as_attachment=True, download_name=filename)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

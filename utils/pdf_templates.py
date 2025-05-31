import io
import re # Ensure re is imported for html_to_reportlab_paragraph
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, KeepInFrame, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import Color, black, HexColor, lightgrey, dimgrey, grey
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY

# --- Base Styles ---
BASE_STYLES = getSampleStyleSheet()
BASE_STYLES.add(ParagraphStyle(name='NameTitle', fontName='Helvetica-Bold', fontSize=22, leading=26, alignment=TA_CENTER, spaceBottom=10))
BASE_STYLES.add(ParagraphStyle(name='ContactInfo', fontName='Helvetica', fontSize=9.5, alignment=TA_CENTER, spaceBottom=8, textColor=dimgrey))
BASE_STYLES.add(ParagraphStyle(name='SectionTitle', fontName='Helvetica-Bold', fontSize=13, leading=16, spaceBefore=10, spaceAfter=5, textColor=HexColor("#333333"))) # Darker Green/Teal could be an option
BASE_STYLES.add(ParagraphStyle(name='BodyText', fontName='Helvetica', fontSize=10, leading=12, alignment=TA_LEFT, spaceBottom=5))
BASE_STYLES.add(ParagraphStyle(name='JobTitle', fontName='Helvetica-Bold', fontSize=10.5, leading=13, spaceBottom=1))
BASE_STYLES.add(ParagraphStyle(name='CompanyName', fontName='Helvetica', fontSize=10, leading=12, spaceBottom=1, textColor=grey))
BASE_STYLES.add(ParagraphStyle(name='Dates', fontName='Helvetica-Oblique', fontSize=9, leading=11, spaceBottom=3, textColor=grey))
BASE_STYLES.add(ParagraphStyle(name='BulletPoint', parent=BASE_STYLES['BodyText'], leftIndent=0.2*inch, bulletIndent=0.05*inch, spaceBefore=0, spaceAfter=1, firstLineIndent=-0.15*inch))
BASE_STYLES.add(ParagraphStyle(name='LinkStyle', parent=BASE_STYLES['BodyText'], textColor=HexColor("#0066CC"))) # Blue for links


def _clean_field(data, key, default="N/A"):
    """Helper to get data and replace None or empty string with default."""
    val = data.get(key, "")
    return val if val and str(val).strip() else default

def _format_description(description_text: str, style: ParagraphStyle) -> list[Paragraph]:
    """Formats a description string (potentially with newlines/bullets) into Paragraphs."""
    output_story = []
    if not description_text or description_text == "N/A":
        return [Paragraph("No description provided.", style)] # Or empty list: []

    lines = description_text.split('\n')
    for line in lines:
        line_stripped = line.strip()
        if not line_stripped:
            continue
        # Check for common bullet point markers
        if line_stripped.startswith(('-', '*', '•', '‣')):
            # Strip the bullet marker and leading space for the Paragraph content
            bullet_content = re.sub(r'^[\s*-•‣]+\s*', '', line_stripped)
            output_story.append(Paragraph(f"• {bullet_content}", style)) # Add bullet back for consistency
        else:
            output_story.append(Paragraph(line_stripped, style)) # Treat as a normal paragraph
    return output_story if output_story else [Paragraph("No description provided.", style)]


# --- Template 1: Simple Text-Based ---
def create_simple_text_resume(resume_data: dict) -> io.BytesIO:
    """
    Generates a PDF for the 'Simple Text-Based' resume template.
    Args:
        resume_data: Dictionary containing resume data from st.session_state.
    Returns:
        A BytesIO buffer containing the PDF.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                            leftMargin=0.75*inch, rightMargin=0.75*inch,
                            topMargin=0.75*inch, bottomMargin=0.75*inch,
                            title=_clean_field(resume_data, 'rb_name', 'Resume') + " Simple")
    story = []
    styles = BASE_STYLES # Use a copy or directly use BASE_STYLES

    # Name & Contact
    story.append(Paragraph(_clean_field(resume_data, 'rb_name'), styles['NameTitle']))
    contact_parts = [
        _clean_field(resume_data, 'rb_email'),
        _clean_field(resume_data, 'rb_phone')
    ]
    if resume_data.get('rb_linkedin'): contact_parts.append(f"<link href='{_clean_field(resume_data, 'rb_linkedin')}' color='blue'>{_clean_field(resume_data, 'rb_linkedin')}</link>")
    if resume_data.get('rb_portfolio'): contact_parts.append(f"<link href='{_clean_field(resume_data, 'rb_portfolio')}' color='blue'>{_clean_field(resume_data, 'rb_portfolio')}</link>")
    story.append(Paragraph(" | ".join(filter(lambda x: x!="N/A", contact_parts)), styles['ContactInfo']))
    story.append(HRFlowable(width="90%", thickness=0.5, color=HexColor("#4CAF50"), spaceBefore=2, spaceAfter=10, hAlign='CENTER'))

    # Summary
    if _clean_field(resume_data, 'rb_summary') != "N/A":
        story.append(Paragraph("Summary", styles['SectionTitle']))
        story.extend(_format_description(_clean_field(resume_data, 'rb_summary'), styles['BodyText']))
        story.append(Spacer(1, 0.1*inch))

    # Experience
    if resume_data.get('rb_experience') and any(_clean_field(exp, 'job_title') != "N/A" for exp in resume_data['rb_experience']):
        story.append(Paragraph("Work Experience", styles['SectionTitle']))
        for exp in resume_data['rb_experience']:
            if _clean_field(exp, 'job_title') == "N/A" and _clean_field(exp, 'company') == "N/A": continue
            story.append(Paragraph(_clean_field(exp, 'job_title'), styles['JobTitle']))
            story.append(Paragraph(_clean_field(exp, 'company'), styles['CompanyName']))
            story.append(Paragraph(f"{_clean_field(exp, 'start_date')} - {_clean_field(exp, 'end_date')}", styles['Dates']))
            story.extend(_format_description(_clean_field(exp, 'description'), styles['BulletPoint'])) # Use BulletPoint style
            story.append(Spacer(1, 0.05*inch))

    # Education
    if resume_data.get('rb_education') and any(_clean_field(edu, 'institution') != "N/A" for edu in resume_data['rb_education']):
        story.append(Paragraph("Education", styles['SectionTitle']))
        for edu in resume_data['rb_education']:
            if _clean_field(edu, 'institution') == "N/A" and _clean_field(edu, 'degree') == "N/A": continue
            story.append(Paragraph(_clean_field(edu, 'degree'), styles['JobTitle']))
            story.append(Paragraph(_clean_field(edu, 'institution'), styles['CompanyName']))
            if _clean_field(edu, 'grad_year') != "N/A": story.append(Paragraph(f"Graduation: {_clean_field(edu, 'grad_year')}", styles['Dates']))
            if _clean_field(edu, 'details') != "N/A": story.append(Paragraph(_clean_field(edu, 'details'), styles['BodyText']))
            story.append(Spacer(1, 0.05*inch))

    # Skills
    skills_list = [s for s in resume_data.get('rb_skills', []) if s != "N/A"]
    if skills_list:
        story.append(Paragraph("Skills", styles['SectionTitle']))
        story.append(Paragraph(" • ".join(skills_list), styles['BodyText']))
        story.append(Spacer(1, 0.1*inch))

    # Projects
    if resume_data.get('rb_projects') and any(_clean_field(proj, 'name') != "N/A" for proj in resume_data['rb_projects']):
        story.append(Paragraph("Projects", styles['SectionTitle']))
        for proj in resume_data['rb_projects']:
            if _clean_field(proj, 'name') == "N/A": continue
            story.append(Paragraph(_clean_field(proj, 'name'), styles['JobTitle']))
            if _clean_field(proj, 'technologies') != "N/A": story.append(Paragraph(f"<i>Technologies:</i> {_clean_field(proj, 'technologies')}", styles['Dates']))
            if _clean_field(proj, 'link') != "N/A": story.append(Paragraph(f"<link href='{_clean_field(proj, 'link')}' color='blue'>{_clean_field(proj, 'link')}</link>", styles['LinkStyle']))
            story.extend(_format_description(_clean_field(proj, 'description'), styles['BulletPoint']))
            story.append(Spacer(1, 0.05*inch))

    # Awards
    if resume_data.get('rb_awards') and any(_clean_field(award, 'name') != "N/A" for award in resume_data['rb_awards']):
        story.append(Paragraph("Awards and Recognition", styles['SectionTitle']))
        for award in resume_data['rb_awards']:
            if _clean_field(award, 'name') == "N/A": continue
            story.append(Paragraph(_clean_field(award, 'name'), styles['JobTitle']))
            if _clean_field(award, 'organization') != "N/A": story.append(Paragraph(_clean_field(award, 'organization'), styles['CompanyName']))
            if _clean_field(award, 'year') != "N/A": story.append(Paragraph(f"Year: {_clean_field(award, 'year')}", styles['Dates']))
            if _clean_field(award, 'description') != "N/A": story.append(Paragraph(_clean_field(award, 'description'), styles['BodyText']))
            story.append(Spacer(1, 0.05*inch))

    try:
        doc.build(story)
    except Exception as e:
        print(f"Error building PDF (Simple Text): {e}") # Log specific error
        buffer.seek(0); buffer.truncate() # Clear buffer for error message
        SimpleDocTemplate(buffer, pagesize=letter).build([Paragraph(f"Error generating PDF: {e}", styles['BodyText'])])

    buffer.seek(0)
    return buffer


# --- Template 2: Modern Professional ---
# This version introduces slightly different styling and structure.
# True two-column layouts would require Frames and PageTemplates, which is more complex.
def create_modern_professional_resume(resume_data: dict) -> io.BytesIO:
    """
    Generates a PDF for a 'Modern Professional' resume template with some enhanced styling.
    Args:
        resume_data: Dictionary containing resume data.
    Returns:
        A BytesIO buffer containing the PDF.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                            leftMargin=0.7*inch, rightMargin=0.7*inch,
                            topMargin=0.6*inch, bottomMargin=0.6*inch,
                            title=_clean_field(resume_data, 'rb_name', 'Resume') + " Modern")
    story = []

    # Define modern styles, possibly inheriting or modifying BASE_STYLES
    modern_name_style = ParagraphStyle('ModernName', parent=BASE_STYLES['NameTitle'], fontSize=24, alignment=TA_LEFT, textColor=HexColor("#111111"), spaceBottom=2)
    modern_contact_style = ParagraphStyle('ModernContact', parent=BASE_STYLES['ContactInfo'], alignment=TA_LEFT, fontSize=9, spaceBottom=12, textColor=HexColor("#444444"))
    modern_section_title_style = ParagraphStyle('ModernSectionTitle', fontName='Helvetica-Bold', fontSize=11,textColor=black, spaceBefore=8, spaceAfter=3, leading=14,
                                                borderColor=lightgrey, borderPadding=(2,0,2,0), leftIndent=0) # No border on top/bottom
    modern_body_style = ParagraphStyle('ModernBody', parent=BASE_STYLES['BodyText'], fontSize=9.5, leading=11.5)
    modern_job_title_style = ParagraphStyle('ModernJobTitle', parent=BASE_STYLES['JobTitle'], fontSize=10, textColor=HexColor("#222222"))
    modern_company_style = ParagraphStyle('ModernCompany', parent=BASE_STYLES['CompanyName'], fontSize=9.5)
    modern_dates_style = ParagraphStyle('ModernDates', parent=BASE_STYLES['Dates'], fontSize=8.5)
    modern_bullet_style = ParagraphStyle('ModernBullet', parent=modern_body_style, leftIndent=0.15*inch, bulletIndent=0, spaceBefore=0, spaceAfter=1, firstLineIndent=-0.1*inch)


    # Name & Contact (Left Aligned)
    story.append(Paragraph(_clean_field(resume_data, 'rb_name'), modern_name_style))
    contact_parts = [
        f"✉️ {_clean_field(resume_data, 'rb_email')}",
        f"📞 {_clean_field(resume_data, 'rb_phone')}"
    ]
    if resume_data.get('rb_linkedin'): contact_parts.append(f"🔗 <link href='{_clean_field(resume_data, 'rb_linkedin')}' color='blue'>{_clean_field(resume_data, 'rb_linkedin').split('//')[-1]}</link>")
    if resume_data.get('rb_portfolio'): contact_parts.append(f"🌐 <link href='{_clean_field(resume_data, 'rb_portfolio')}' color='blue'>{_clean_field(resume_data, 'rb_portfolio').split('//')[-1]}</link>")
    story.append(Paragraph("  |  ".join(filter(lambda x: "N/A" not in x, contact_parts)), modern_contact_style))
    story.append(HRFlowable(width="100%", thickness=0.8, color=HexColor("#4CAF50"), spaceBefore=0, spaceAfter=10))

    # Summary
    if _clean_field(resume_data, 'rb_summary') != "N/A":
        story.append(Paragraph("PROFESSIONAL SUMMARY", modern_section_title_style))
        story.extend(_format_description(_clean_field(resume_data, 'rb_summary'), modern_body_style))
        story.append(Spacer(1, 0.1*inch))

    # Experience
    if resume_data.get('rb_experience') and any(_clean_field(exp, 'job_title') != "N/A" for exp in resume_data['rb_experience']):
        story.append(Paragraph("WORK EXPERIENCE", modern_section_title_style))
        for exp in resume_data['rb_experience']:
            if _clean_field(exp, 'job_title') == "N/A" and _clean_field(exp, 'company') == "N/A": continue
            story.append(Paragraph(_clean_field(exp, 'job_title'), modern_job_title_style))
            story.append(Paragraph(f"{_clean_field(exp, 'company')} | {_clean_field(exp, 'start_date')} - {_clean_field(exp, 'end_date')}", modern_company_style)) # Company and Dates on one line
            story.extend(_format_description(_clean_field(exp, 'description'), modern_bullet_style))
            story.append(Spacer(1, 0.08*inch))

    # Education
    if resume_data.get('rb_education') and any(_clean_field(edu, 'institution') != "N/A" for edu in resume_data['rb_education']):
        story.append(Paragraph("EDUCATION", modern_section_title_style))
        for edu in resume_data['rb_education']:
            if _clean_field(edu, 'institution') == "N/A" and _clean_field(edu, 'degree') == "N/A": continue
            story.append(Paragraph(f"{_clean_field(edu, 'degree')} - {_clean_field(edu, 'institution')}", modern_job_title_style)) # Degree and Institution on one line
            date_info = []
            if _clean_field(edu, 'grad_year') != "N/A": date_info.append(f"Graduation: {_clean_field(edu, 'grad_year')}")
            if _clean_field(edu, 'details') != "N/A": date_info.append(_clean_field(edu, 'details'))
            if date_info: story.append(Paragraph(", ".join(date_info), modern_dates_style))
            story.append(Spacer(1, 0.08*inch))

    # Skills - could be presented in columns using Tables for a more modern feel
    skills_list = [s for s in resume_data.get('rb_skills', []) if s != "N/A"]
    if skills_list:
        story.append(Paragraph("SKILLS", modern_section_title_style))
        # Simple comma list for now, but could be a Table for multi-column
        story.append(Paragraph(", ".join(skills_list), modern_body_style))
        story.append(Spacer(1, 0.1*inch))

    # Projects
    if resume_data.get('rb_projects') and any(_clean_field(proj, 'name') != "N/A" for proj in resume_data['rb_projects']):
        story.append(Paragraph("PROJECTS", modern_section_title_style))
        for proj in resume_data['rb_projects']:
            if _clean_field(proj, 'name') == "N/A": continue
            story.append(Paragraph(_clean_field(proj, 'name'), modern_job_title_style))
            tech_and_link = []
            if _clean_field(proj, 'technologies') != "N/A": tech_and_link.append(f"<i>Tech:</i> {_clean_field(proj, 'technologies')}")
            if _clean_field(proj, 'link') != "N/A": tech_and_link.append(f"<link href='{_clean_field(proj, 'link')}' color='blue'>{_clean_field(proj, 'link')}</link>")
            if tech_and_link: story.append(Paragraph(" | ".join(tech_and_link), modern_dates_style)) # Using dates style for this line
            story.extend(_format_description(_clean_field(proj, 'description'), modern_bullet_style))
            story.append(Spacer(1, 0.08*inch))

    # Awards
    if resume_data.get('rb_awards') and any(_clean_field(award, 'name') != "N/A" for award in resume_data['rb_awards']):
        story.append(Paragraph("AWARDS & RECOGNITION", modern_section_title_style))
        for award in resume_data['rb_awards']:
            if _clean_field(award, 'name') == "N/A": continue
            story.append(Paragraph(f"{_clean_field(award, 'name')} - {_clean_field(award, 'organization')} ({_clean_field(award, 'year')})", modern_job_title_style))
            if _clean_field(award, 'description') != "N/A": story.append(Paragraph(_clean_field(award, 'description'), modern_body_style))
            story.append(Spacer(1, 0.08*inch))

    try:
        doc.build(story)
    except Exception as e:
        print(f"Error building PDF (Modern Professional): {e}")
        buffer.seek(0); buffer.truncate()
        SimpleDocTemplate(buffer, pagesize=letter).build([Paragraph(f"Error generating PDF: {e}", BASE_STYLES['BodyText'])])

    buffer.seek(0)
    return buffer


# --- Template Function Mapping ---
TEMPLATE_FUNCTIONS = {
    "Simple Text-Based": create_simple_text_resume,
    "Modern Professional": create_modern_professional_resume,
}

# Note: The html_to_reportlab_paragraph function was removed as it was unused and basic.
# Direct Paragraph creation with ReportLab's XML tags (<br/>, <i>, <b>, <link>) is more robust.
# If more complex HTML parsing is needed, a dedicated library like `xhtml2pdf` or `WeasyPrint`
# might be considered, but they have heavier dependencies. ReportLab offers precision for direct drawing.

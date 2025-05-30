import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import Color, black, HexColor
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY

# Define some base styles - can be expanded
styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name='NameTitle',
                          fontName='Helvetica-Bold',
                          fontSize=20,
                          leading=24,
                          alignment=TA_CENTER,
                          spaceBottom=12))
styles.add(ParagraphStyle(name='ContactInfo',
                          fontName='Helvetica',
                          fontSize=10,
                          alignment=TA_CENTER,
                          spaceBottom=10))
styles.add(ParagraphStyle(name='SectionTitle',
                          fontName='Helvetica-Bold',
                          fontSize=14,
                          leading=18,
                          spaceBefore=12,
                          spaceAfter=6,
                          textColor=HexColor("#4CAF50"))) # Green accent
styles.add(ParagraphStyle(name='BodyText',
                          fontName='Helvetica',
                          fontSize=10,
                          leading=12,
                          alignment=TA_LEFT,
                          spaceBottom=6))
styles.add(ParagraphStyle(name='JobTitle',
                          fontName='Helvetica-Bold',
                          fontSize=11,
                          leading=14,
                          spaceBottom=2))
styles.add(ParagraphStyle(name='CompanyName',
                          fontName='Helvetica',
                          fontSize=10,
                          leading=12,
                          spaceBottom=2,
                          textColor=HexColor("#555555")))
styles.add(ParagraphStyle(name='Dates',
                          fontName='Helvetica-Oblique',
                          fontSize=9,
                          leading=11,
                          spaceBottom=4,
                          textColor=HexColor("#777777")))
styles.add(ParagraphStyle(name='BulletPoint',
                          parent=styles['BodyText'],
                          leftIndent=0.25*inch,
                          bulletIndent=0.1*inch,
                          firstLineIndent=-0.15*inch, # Negative to bring bullet out
                          spaceBefore=0,
                          spaceAfter=2))


def html_to_reportlab_paragraph(html_text, style):
    """
    Basic HTML to ReportLab Paragraph conversion.
    Handles <ul>, <li>, <b>/<strong>, <i>/<em>.
    More complex HTML would need a more robust parser.
    """
    if not html_text:
        return Paragraph("", style)

    # Replace <ul> and <li> with bullet points and newlines
    # This is a very simplified conversion.
    text = html_text.replace("<ul>", "").replace("</ul>", "")
    text = re.sub(r"<li>\s*(.*?)\s*</li>", r"• \1<br/>", text) # Basic list item to bullet

    # Convert bold and italic
    text = re.sub(r"<b>(.*?)</b>", r"<para fontName='Helvetica-Bold'>\1</para>", text, flags=re.IGNORECASE)
    text = re.sub(r"<strong>(.*?)</strong>", r"<para fontName='Helvetica-Bold'>\1</para>", text, flags=re.IGNORECASE)
    text = re.sub(r"<i>(.*?)</i>", r"<para fontName='Helvetica-Oblique'>\1</para>", text, flags=re.IGNORECASE)
    text = re.sub(r"<em>(.*?)</em>", r"<para fontName='Helvetica-Oblique'>\1</para>", text, flags=re.IGNORECASE)

    return Paragraph(text, style)


def create_simple_text_resume(resume_data: dict):
    """
    Generates a PDF for the 'Simple Text-Based' resume template.
    Returns a BytesIO buffer containing the PDF.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                            leftMargin=0.75*inch, rightMargin=0.75*inch,
                            topMargin=0.75*inch, bottomMargin=0.75*inch)
    story = []

    # 1. Name
    if resume_data.get('rb_name'):
        story.append(Paragraph(resume_data['rb_name'], styles['NameTitle']))

    # 2. Contact Information
    contact_parts = []
    if resume_data.get('rb_email'):
        contact_parts.append(resume_data['rb_email'])
    if resume_data.get('rb_phone'):
        contact_parts.append(resume_data['rb_phone'])
    if resume_data.get('rb_linkedin'):
        contact_parts.append(f"<link href='{resume_data['rb_linkedin']}'>{resume_data['rb_linkedin']}</link>")
    if resume_data.get('rb_portfolio'):
        contact_parts.append(f"<link href='{resume_data['rb_portfolio']}'>{resume_data['rb_portfolio']}</link>")
    if contact_parts:
        story.append(Paragraph(" | ".join(contact_parts), styles['ContactInfo']))

    story.append(HRFlowable(width="100%", thickness=0.5, color=HexColor("#4CAF50"), spaceBefore=2, spaceAfter=10))


    # 3. Summary
    if resume_data.get('rb_summary'):
        story.append(Paragraph("Summary", styles['SectionTitle']))
        story.append(Paragraph(resume_data['rb_summary'].replace('\n', '<br/>'), styles['BodyText']))
        story.append(Spacer(1, 0.1*inch))

    # 4. Experience
    if resume_data.get('rb_experience') and any(exp.get('job_title') for exp in resume_data['rb_experience']):
        story.append(Paragraph("Work Experience", styles['SectionTitle']))
        for exp in resume_data['rb_experience']:
            if not exp.get('job_title'): continue # Skip if no job title
            story.append(Paragraph(exp.get('job_title', 'N/A'), styles['JobTitle']))
            story.append(Paragraph(exp.get('company', 'N/A'), styles['CompanyName']))
            story.append(Paragraph(f"{exp.get('start_date', 'N/A')} - {exp.get('end_date', 'N/A')}", styles['Dates']))

            desc = exp.get('description', '')
            if desc:
                # Basic handling for bullet points if they start with common markers
                desc_lines = desc.split('\n')
                for line in desc_lines:
                    line = line.strip()
                    if line.startswith(('-', '*', '•')):
                        story.append(Paragraph(line, styles['BulletPoint']))
                    elif line: # Non-empty line without bullet
                        story.append(Paragraph(line, styles['BodyText']))
            story.append(Spacer(1, 0.1*inch))

    # 5. Education
    if resume_data.get('rb_education') and any(edu.get('institution') for edu in resume_data['rb_education']):
        story.append(Paragraph("Education", styles['SectionTitle']))
        for edu in resume_data['rb_education']:
            if not edu.get('institution'): continue
            story.append(Paragraph(edu.get('degree', 'N/A'), styles['JobTitle'])) # Using JobTitle style for degree
            story.append(Paragraph(edu.get('institution', 'N/A'), styles['CompanyName'])) # Using CompanyName for institution
            if edu.get('grad_year'):
                 story.append(Paragraph(f"Graduation: {edu.get('grad_year', '')}", styles['Dates']))
            if edu.get('details'):
                story.append(Paragraph(edu.get('details', ''), styles['BodyText']))
            story.append(Spacer(1, 0.1*inch))

    # 6. Skills
    if resume_data.get('rb_skills') and resume_data['rb_skills'] != ["N/A"]:
        story.append(Paragraph("Skills", styles['SectionTitle']))
        # Join skills with a bullet point character for display, or simply comma-separated
        skills_text = " • ".join(resume_data['rb_skills'])
        story.append(Paragraph(skills_text, styles['BodyText']))
        story.append(Spacer(1, 0.1*inch))

    # 7. Projects (Optional)
    if resume_data.get('rb_projects') and any(proj.get('name') for proj in resume_data['rb_projects']):
        story.append(Paragraph("Projects", styles['SectionTitle']))
        for proj in resume_data['rb_projects']:
            if not proj.get('name'): continue
            story.append(Paragraph(proj.get('name', 'N/A'), styles['JobTitle']))
            if proj.get('technologies'):
                story.append(Paragraph(f"<i>Technologies:</i> {proj.get('technologies', '')}", styles['Dates'])) # Using Dates style for tech
            if proj.get('link'):
                 story.append(Paragraph(f"<link href='{proj['link']}'>{proj['link']}</link>", styles['BodyText']))
            if proj.get('description'):
                desc_lines = proj.get('description', '').split('\n')
                for line in desc_lines:
                    line = line.strip()
                    if line.startswith(('-', '*', '•')):
                        story.append(Paragraph(line, styles['BulletPoint']))
                    elif line:
                        story.append(Paragraph(line, styles['BodyText']))
            story.append(Spacer(1, 0.1*inch))

    # 8. Awards (Optional)
    if resume_data.get('rb_awards') and any(award.get('name') for award in resume_data['rb_awards']):
        story.append(Paragraph("Awards and Recognition", styles['SectionTitle']))
        for award in resume_data['rb_awards']:
            if not award.get('name'): continue
            story.append(Paragraph(award.get('name', 'N/A'), styles['JobTitle']))
            if award.get('organization'):
                story.append(Paragraph(award.get('organization', ''), styles['CompanyName']))
            if award.get('year'):
                story.append(Paragraph(f"Year: {award.get('year', '')}", styles['Dates']))
            if award.get('description'):
                story.append(Paragraph(award.get('description', ''), styles['BodyText']))
            story.append(Spacer(1, 0.1*inch))

    try:
        doc.build(story)
    except Exception as e:
        print(f"Error building PDF: {e}")
        # Fallback: write a simple error message to the PDF
        buffer.seek(0)
        buffer.truncate()
        doc_error = SimpleDocTemplate(buffer, pagesize=letter)
        story_error = [Paragraph("Error generating PDF. Please check data.", styles['BodyText']),
                       Paragraph(str(e), styles['BodyText'])]
        doc_error.build(story_error)

    buffer.seek(0)
    return buffer

# --- Template 2: Modern Professional (Basic) ---
# This will be more complex and might use Frames or Tables for layout.
# For now, let's define its structure and a placeholder function.

def create_modern_professional_resume(resume_data: dict):
    """
    Generates a PDF for the 'Modern Professional' resume template.
    (Placeholder - more complex layout to be implemented)
    """
    # For now, it can just call the simple template as a fallback
    # Or implement a slightly different styling approach
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                            leftMargin=0.6*inch, rightMargin=0.6*inch,
                            topMargin=0.5*inch, bottomMargin=0.5*inch)
    story = []

    # Styles specific to this template (can inherit or override)
    modern_styles = {
        'NameTitle': ParagraphStyle(name='ModernName', parent=styles['NameTitle'], fontSize=24, spaceBottom=6, alignment=TA_LEFT, textColor=HexColor("#333333")),
        'ContactInfo': ParagraphStyle(name='ModernContact', parent=styles['ContactInfo'], alignment=TA_LEFT, fontSize=9, spaceBottom=15, textColor=HexColor("#555555")),
        'SectionTitle': ParagraphStyle(name='ModernSectionTitle', parent=styles['SectionTitle'], fontSize=12, spaceAfter=4, textColor=black, borderPadding=2, leading=14, spaceBefore=10,
                                      leftIndent=-2), # Negative indent for effect with a border
        'BodyText': ParagraphStyle(name='ModernBody', parent=styles['BodyText'], fontSize=9.5, leading=11.5),
        'JobTitle': ParagraphStyle(name='ModernJobTitle', parent=styles['JobTitle'], fontSize=10.5,textColor=HexColor("#222222")),
        'CompanyName': ParagraphStyle(name='ModernCompany', parent=styles['CompanyName'], fontSize=9.5),
        'Dates': ParagraphStyle(name='ModernDates', parent=styles['Dates'], fontSize=8.5),
        'BulletPoint': ParagraphStyle(name='ModernBullet', parent=styles['BulletPoint'], fontSize=9.5, leading=11.5, spaceAfter=1, bulletIndent=0.05*inch, leftIndent=0.2*inch),
    }

    # 1. Name & Contact
    if resume_data.get('rb_name'):
        story.append(Paragraph(resume_data['rb_name'], modern_styles['NameTitle']))
    contact_parts = []
    if resume_data.get('rb_email'): contact_parts.append(f"✉️ {resume_data['rb_email']}")
    if resume_data.get('rb_phone'): contact_parts.append(f"📞 {resume_data['rb_phone']}")
    if resume_data.get('rb_linkedin'): contact_parts.append(f"🔗 <link href='{resume_data['rb_linkedin']}'>{resume_data['rb_linkedin'].split('//')[-1]}</link>") # Shorter link
    if resume_data.get('rb_portfolio'): contact_parts.append(f"🌐 <link href='{resume_data['rb_portfolio']}'>{resume_data['rb_portfolio'].split('//')[-1]}</link>")
    if contact_parts:
        story.append(Paragraph(" &nbsp;|&nbsp; ".join(contact_parts), modern_styles['ContactInfo']))

    # Horizontal Line - Thicker for modern look
    story.append(HRFlowable(width="100%", thickness=1, color=HexColor("#4CAF50"), spaceBefore=0, spaceAfter=8))


    # 3. Summary
    if resume_data.get('rb_summary'):
        story.append(Paragraph("PROFESSIONAL SUMMARY", modern_styles['SectionTitle']))
        story.append(Paragraph(resume_data['rb_summary'].replace('\n', '<br/>'), modern_styles['BodyText']))
        story.append(Spacer(1, 0.1*inch))

    # 4. Experience
    if resume_data.get('rb_experience') and any(exp.get('job_title') for exp in resume_data['rb_experience']):
        story.append(Paragraph("WORK EXPERIENCE", modern_styles['SectionTitle']))
        for exp in resume_data['rb_experience']:
            if not exp.get('job_title'): continue
            story.append(Paragraph(exp.get('job_title', 'N/A'), modern_styles['JobTitle']))
            story.append(Paragraph(exp.get('company', 'N/A'), modern_styles['CompanyName']))
            story.append(Paragraph(f"{exp.get('start_date', 'N/A')} - {exp.get('end_date', 'N/A')}", modern_styles['Dates']))
            desc = exp.get('description', '')
            if desc:
                desc_lines = desc.split('\n')
                for line in desc_lines:
                    line = line.strip()
                    if line.startswith(('-', '*', '•')):
                        story.append(Paragraph(line, modern_styles['BulletPoint']))
                    elif line:
                        story.append(Paragraph(line, modern_styles['BodyText'])) # Fallback for non-bullet lines
            story.append(Spacer(1, 0.05*inch)) # Smaller spacer

    # 5. Education
    if resume_data.get('rb_education') and any(edu.get('institution') for edu in resume_data['rb_education']):
        story.append(Paragraph("EDUCATION", modern_styles['SectionTitle']))
        for edu in resume_data['rb_education']:
            if not edu.get('institution'): continue
            story.append(Paragraph(edu.get('degree', 'N/A'), modern_styles['JobTitle']))
            story.append(Paragraph(edu.get('institution', 'N/A'), modern_styles['CompanyName']))
            if edu.get('grad_year'): story.append(Paragraph(f"Graduation: {edu.get('grad_year', '')}", modern_styles['Dates']))
            if edu.get('details'): story.append(Paragraph(edu.get('details', ''), modern_styles['BodyText']))
            story.append(Spacer(1, 0.05*inch))

    # 6. Skills
    if resume_data.get('rb_skills') and resume_data['rb_skills'] != ["N/A"]:
        story.append(Paragraph("SKILLS", modern_styles['SectionTitle']))
        # For a modern look, skills could be in a multi-column table or flowable, but simple for now.
        # Using a slightly smaller body text for skills list.
        skills_style = ParagraphStyle('ModernSkills', parent=modern_styles['BodyText'], fontSize=9)
        skills_text = ", ".join(resume_data['rb_skills']) # Comma separated for a denser look
        story.append(Paragraph(skills_text, skills_style))
        story.append(Spacer(1, 0.1*inch))

    # Projects and Awards would follow similar structure as Experience/Education, using modern_styles
    # (Skipping full re-implementation here for brevity, but structure would be analogous)
    if resume_data.get('rb_projects') and any(proj.get('name') for proj in resume_data['rb_projects']):
        story.append(Paragraph("PROJECTS", modern_styles['SectionTitle']))
        # ... (similar loop and Paragraph calls as Experience, using modern_styles) ...
        for proj in resume_data['rb_projects']: # Example
            if not proj.get('name'): continue
            story.append(Paragraph(proj.get('name', 'N/A'), modern_styles['JobTitle']))
            if proj.get('technologies'): story.append(Paragraph(f"<i>Tech:</i> {proj.get('technologies')}", modern_styles['Dates']))
            if proj.get('description'): story.append(Paragraph(proj.get('description'), modern_styles['BodyText'])) # Simplified
            story.append(Spacer(1, 0.05*inch))


    doc.build(story)
    buffer.seek(0)
    return buffer

# Helper for HTML list conversion (very basic)
import re
# (html_to_reportlab_paragraph was moved up for clarity as it's a general utility)

# Mapping template names to functions
TEMPLATE_FUNCTIONS = {
    "Simple Text-Based": create_simple_text_resume,
    "Modern Professional": create_modern_professional_resume,
}

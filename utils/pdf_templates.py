import io
import re
from typing import List, Dict, Any, Callable # For type hinting

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, KeepInFrame, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, black, dimgrey, grey, lightgrey
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY

# --- Base Styles Definition ---
def get_base_styles() -> getSampleStyleSheet:
    """Creates and returns a base stylesheet with custom styles."""
    stylesheet = getSampleStyleSheet()
    stylesheet.add(ParagraphStyle(name='NameTitle', fontName='Helvetica-Bold', fontSize=22, leading=26, alignment=TA_CENTER, spaceBottom=10))
    stylesheet.add(ParagraphStyle(name='ContactInfo', fontName='Helvetica', fontSize=9.5, alignment=TA_CENTER, spaceBottom=8, textColor=dimgrey))
    stylesheet.add(ParagraphStyle(name='SectionTitle', fontName='Helvetica-Bold', fontSize=13, leading=16, spaceBefore=10, spaceAfter=5, textColor=HexColor("#333333")))
    stylesheet.add(ParagraphStyle(name='BodyText', fontName='Helvetica', fontSize=10, leading=12, alignment=TA_LEFT, spaceBottom=5))
    stylesheet.add(ParagraphStyle(name='JobTitle', fontName='Helvetica-Bold', fontSize=10.5, leading=13, spaceBottom=1))
    stylesheet.add(ParagraphStyle(name='CompanyName', fontName='Helvetica', fontSize=10, leading=12, spaceBottom=1, textColor=grey))
    stylesheet.add(ParagraphStyle(name='Dates', fontName='Helvetica-Oblique', fontSize=9, leading=11, spaceBottom=3, textColor=grey))
    stylesheet.add(ParagraphStyle(name='BulletPoint', parent=stylesheet['BodyText'], leftIndent=0.2*inch, bulletIndent=0.05*inch, spaceBefore=0, spaceAfter=1, firstLineIndent=-0.15*inch, allowOrphans=1, allowWidows=1))
    stylesheet.add(ParagraphStyle(name='LinkStyle', parent=stylesheet['BodyText'], textColor=HexColor("#0066CC")))
    return stylesheet

BASE_STYLES = get_base_styles() # Initialize once

# --- Helper Functions ---
def _clean_field(data: Dict[str, Any], key: str, default: str = "N/A") -> str:
    """
    Safely retrieves and cleans a field from the resume data.
    Args:
        data: The dictionary (usually an entry from a list in resume_data).
        key: The key to retrieve.
        default: The default value if key is not found or value is empty.
    Returns:
        The cleaned string value.
    """
    val = data.get(key, "")
    return str(val).strip() if val and str(val).strip() else default

def _format_description_to_paragraphs(description_text: str, style: ParagraphStyle) -> List[Paragraph]:
    """
    Formats a multi-line description string (potentially with bullet points)
    into a list of ReportLab Paragraph objects.
    Args:
        description_text: The raw description string.
        style: The ParagraphStyle to apply to each line/bullet.
    Returns:
        A list of Paragraph objects.
    """
    story_elements = []
    if not description_text or description_text == "N/A":
        return [] # Return empty list if no description, let caller decide on placeholder

    lines = description_text.split('\n')
    for line in lines:
        line_stripped = line.strip()
        if not line_stripped: continue

        # Check for common bullet point markers and format accordingly
        if line_stripped.startswith(('-', '*', '•', '‣')):
            # Strip the marker, add a standard bullet, and apply style
            bullet_content = re.sub(r'^[\s*-•‣]+\s*', '', line_stripped)
            story_elements.append(Paragraph(f"•&nbsp;&nbsp;{bullet_content}", style)) # Non-breaking space for indent
        else:
            story_elements.append(Paragraph(line_stripped, style)) # Treat as a normal paragraph
    return story_elements


# --- PDF Document Building Blocks ---
def _add_header(story: List[Any], resume_data: Dict[str, Any], styles: getSampleStyleSheet):
    """Adds name and contact information to the story."""
    story.append(Paragraph(_clean_field(resume_data, 'rb_name'), styles['NameTitle']))
    contact_parts = [
        _clean_field(resume_data, 'rb_email'),
        _clean_field(resume_data, 'rb_phone')
    ]
    # Add links if present, ensuring they are not "N/A"
    linkedin_url = _clean_field(resume_data, 'rb_linkedin')
    if linkedin_url != "N/A": contact_parts.append(f"<link href='{linkedin_url}' color='blue'>{linkedin_url}</link>")
    portfolio_url = _clean_field(resume_data, 'rb_portfolio')
    if portfolio_url != "N/A": contact_parts.append(f"<link href='{portfolio_url}' color='blue'>{portfolio_url}</link>")

    story.append(Paragraph(" | ".join(filter(lambda x: x and x!="N/A", contact_parts)), styles['ContactInfo']))
    story.append(HRFlowable(width="90%", thickness=0.5, color=HexColor("#4CAF50"), spaceBefore=2, spaceAfter=10, hAlign='CENTER'))

def _add_section(story: List[Any], title: str, content_data: Any,
                 item_style: ParagraphStyle, content_style: ParagraphStyle,
                 styles: getSampleStyleSheet, is_list_of_dicts: bool = False,
                 dict_format_func: Optional[Callable[[Dict[str,Any], getSampleStyleSheet], List[Any]]] = None):
    """Adds a generic section to the story."""
    if not content_data or content_data == "N/A" or (isinstance(content_data, list) and not any(content_data)):
        return # Skip empty or N/A sections

    story.append(Paragraph(title, styles['SectionTitle']))
    if is_list_of_dicts:
        if dict_format_func:
            for item in content_data:
                # Check if item itself is meaningful (not just full of "N/A")
                if any(v != "N/A" for k, v in item.items() if k != 'description'): # Heuristic: check non-description fields
                    story.extend(dict_format_func(item, styles))
                    story.append(Spacer(1, 0.05*inch))
    elif isinstance(content_data, list): # List of strings (e.g., skills)
         story.append(Paragraph(" • ".join(s for s in content_data if s != "N/A"), content_style))
    else: # Single string content (e.g., summary)
        story.extend(_format_description_to_paragraphs(str(content_data), content_style))
    story.append(Spacer(1, 0.1*inch))

def _format_experience_entry(exp: Dict[str, Any], styles: getSampleStyleSheet) -> List[Any]:
    """Formats a single experience entry into a list of Flowables."""
    entry_story = []
    entry_story.append(Paragraph(_clean_field(exp, 'job_title'), styles['JobTitle']))
    entry_story.append(Paragraph(_clean_field(exp, 'company'), styles['CompanyName']))
    entry_story.append(Paragraph(f"{_clean_field(exp, 'start_date')} - {_clean_field(exp, 'end_date')}", styles['Dates']))
    entry_story.extend(_format_description_to_paragraphs(_clean_field(exp, 'description'), styles['BulletPoint']))
    return entry_story

def _format_education_entry(edu: Dict[str, Any], styles: getSampleStyleSheet) -> List[Any]:
    """Formats a single education entry."""
    entry_story = []
    entry_story.append(Paragraph(_clean_field(edu, 'degree'), styles['JobTitle'])) # Using JobTitle for degree too
    entry_story.append(Paragraph(_clean_field(edu, 'institution'), styles['CompanyName']))
    if _clean_field(edu, 'grad_year') != "N/A": entry_story.append(Paragraph(f"Graduation: {_clean_field(edu, 'grad_year')}", styles['Dates']))
    if _clean_field(edu, 'details') != "N/A": entry_story.append(Paragraph(_clean_field(edu, 'details'), styles['BodyText']))
    return entry_story

def _format_project_entry(proj: Dict[str, Any], styles: getSampleStyleSheet) -> List[Any]:
    """Formats a single project entry."""
    entry_story = []
    entry_story.append(Paragraph(_clean_field(proj, 'name'), styles['JobTitle']))
    tech = _clean_field(proj, 'technologies')
    link = _clean_field(proj, 'link')
    if tech != "N/A": entry_story.append(Paragraph(f"<i>Technologies:</i> {tech}", styles['Dates']))
    if link != "N/A": entry_story.append(Paragraph(f"<link href='{link}' color='blue'>{link}</link>", styles['LinkStyle']))
    entry_story.extend(_format_description_to_paragraphs(_clean_field(proj, 'description'), styles['BulletPoint']))
    return entry_story

def _format_award_entry(award: Dict[str, Any], styles: getSampleStyleSheet) -> List[Any]:
    """Formats a single award entry."""
    entry_story = []
    entry_story.append(Paragraph(_clean_field(award, 'name'), styles['JobTitle']))
    if _clean_field(award, 'organization') != "N/A": entry_story.append(Paragraph(_clean_field(award, 'organization'), styles['CompanyName']))
    if _clean_field(award, 'year') != "N/A": entry_story.append(Paragraph(f"Year: {_clean_field(award, 'year')}", styles['Dates']))
    if _clean_field(award, 'description') != "N/A": entry_story.append(Paragraph(_clean_field(award, 'description'), styles['BodyText']))
    return entry_story


# --- Template 1: Simple Text-Based ---
def create_simple_text_resume(resume_data: Dict[str, Any]) -> io.BytesIO:
    """Generates a PDF for the 'Simple Text-Based' resume template."""
    buffer = io.BytesIO()
    doc_title = _clean_field(resume_data, 'rb_name', 'Resume') + "_Simple_Text"
    doc = SimpleDocTemplate(buffer, pagesize=letter, title=doc_title,
                            leftMargin=0.75*inch, rightMargin=0.75*inch,
                            topMargin=0.75*inch, bottomMargin=0.75*inch)
    story: List[Any] = []
    styles = BASE_STYLES

    _add_header(story, resume_data, styles)
    _add_section(story, "Summary", _clean_field(resume_data, 'rb_summary'), styles['BodyText'], styles['BodyText'], styles)
    _add_section(story, "Work Experience", resume_data.get('rb_experience', []), styles['JobTitle'], styles['BulletPoint'], styles, is_list_of_dicts=True, dict_format_func=_format_experience_entry)
    _add_section(story, "Education", resume_data.get('rb_education', []), styles['JobTitle'], styles['BodyText'], styles, is_list_of_dicts=True, dict_format_func=_format_education_entry)
    _add_section(story, "Skills", [s for s in resume_data.get('rb_skills', []) if s != "N/A"], styles['BodyText'], styles['BodyText'], styles, is_list_of_dicts=False) # Pass as list of strings
    _add_section(story, "Projects", resume_data.get('rb_projects', []), styles['JobTitle'], styles['BulletPoint'], styles, is_list_of_dicts=True, dict_format_func=_format_project_entry)
    _add_section(story, "Awards and Recognition", resume_data.get('rb_awards', []), styles['JobTitle'], styles['BodyText'], styles, is_list_of_dicts=True, dict_format_func=_format_award_entry)

    try:
        doc.build(story)
    except Exception as e:
        print(f"Error building PDF (Simple Text): {e}")
        buffer.seek(0); buffer.truncate()
        SimpleDocTemplate(buffer, pagesize=letter).build([Paragraph(f"Error generating PDF: {e}", styles['BodyText'])])

    buffer.seek(0)
    return buffer

# --- Template 2: Modern Professional ---
def create_modern_professional_resume(resume_data: Dict[str, Any]) -> io.BytesIO:
    """Generates a PDF for a 'Modern Professional' resume template."""
    buffer = io.BytesIO()
    doc_title = _clean_field(resume_data, 'rb_name', 'Resume') + "_Modern_Professional"
    doc = SimpleDocTemplate(buffer, pagesize=letter, title=doc_title,
                            leftMargin=0.6*inch, rightMargin=0.6*inch,
                            topMargin=0.5*inch, bottomMargin=0.5*inch)
    story: List[Any] = []

    # Define styles specific to this template, possibly overriding or extending BASE_STYLES
    modern_styles = get_base_styles() # Start with a copy of base styles
    modern_styles['NameTitle'].alignment = TA_LEFT
    modern_styles['NameTitle'].fontSize = 24
    modern_styles['NameTitle'].textColor = HexColor("#222222") # Darker name
    modern_styles['NameTitle'].spaceBottom = 2

    modern_styles['ContactInfo'].alignment = TA_LEFT
    modern_styles['ContactInfo'].fontSize = 9
    modern_styles['ContactInfo'].spaceBottom = 12
    modern_styles['ContactInfo'].textColor = HexColor("#444444")

    modern_styles['SectionTitle'].fontSize = 11
    modern_styles['SectionTitle'].textColor = black
    modern_styles['SectionTitle'].spaceBefore = 10
    modern_styles['SectionTitle'].spaceAfter = 3
    modern_styles['SectionTitle'].leftIndent = -0.1*inch # Slight outdent for visual effect with HR

    modern_styles['BodyText'].fontSize = 9.5
    modern_styles['BodyText'].leading = 11.5

    modern_styles['JobTitle'].fontSize = 10
    modern_styles['JobTitle'].textColor = HexColor("#333333")

    modern_styles['CompanyName'].fontSize = 9.5 # Company and dates on one line often
    modern_styles['CompanyName'].textColor = dimgrey

    modern_styles['Dates'].fontSize = 9
    modern_styles['Dates'].textColor = dimgrey

    modern_styles['BulletPoint'].fontSize = 9.5
    modern_styles['BulletPoint'].leading = 11.5
    modern_styles['BulletPoint'].spaceAfter = 1
    modern_styles['BulletPoint'].bulletIndent = -0.05*inch # Adjust bullet indent if needed
    modern_styles['BulletPoint'].leftIndent = 0.15*inch


    # Header: Name and Contact (Left Aligned)
    story.append(Paragraph(_clean_field(resume_data, 'rb_name'), modern_styles['NameTitle']))
    contact_parts = []
    email = _clean_field(resume_data, 'rb_email'); phone = _clean_field(resume_data, 'rb_phone')
    linkedin = _clean_field(resume_data, 'rb_linkedin'); portfolio = _clean_field(resume_data, 'rb_portfolio')
    if email != "N/A": contact_parts.append(f"✉️ {email}")
    if phone != "N/A": contact_parts.append(f"📞 {phone}")
    if linkedin != "N/A": contact_parts.append(f"🔗 <link href='{linkedin}' color='blue'>{linkedin.split('//')[-1]}</link>")
    if portfolio != "N/A": contact_parts.append(f"🌐 <link href='{portfolio}' color='blue'>{portfolio.split('//')[-1]}</link>")
    story.append(Paragraph("  |  ".join(filter(None, contact_parts)), modern_styles['ContactInfo']))
    story.append(HRFlowable(width="100%", thickness=0.7, color=HexColor("#4CAF50"), spaceBefore=0, spaceAfter=8))

    # Sections
    _add_section(story, "PROFESSIONAL SUMMARY", _clean_field(resume_data, 'rb_summary'), modern_styles['BodyText'], modern_styles['BodyText'], modern_styles)
    _add_section(story, "WORK EXPERIENCE", resume_data.get('rb_experience', []), modern_styles['JobTitle'], modern_styles['BulletPoint'], modern_styles, is_list_of_dicts=True, dict_format_func=_format_experience_entry_modern)
    _add_section(story, "EDUCATION", resume_data.get('rb_education', []), modern_styles['JobTitle'], modern_styles['BodyText'], modern_styles, is_list_of_dicts=True, dict_format_func=_format_education_entry_modern)

    skills_list = [s for s in resume_data.get('rb_skills', []) if s != "N/A"]
    if skills_list:
        story.append(Paragraph("SKILLS", modern_styles['SectionTitle']))
        # For a modern look, skills could be presented in columns or as denser text
        story.append(Paragraph(", ".join(skills_list), ParagraphStyle('ModernSkills', parent=modern_styles['BodyText'], fontSize=9)))
        story.append(Spacer(1, 0.1*inch))

    _add_section(story, "PROJECTS", resume_data.get('rb_projects', []), modern_styles['JobTitle'], modern_styles['BulletPoint'], modern_styles, is_list_of_dicts=True, dict_format_func=_format_project_entry_modern)
    _add_section(story, "AWARDS & RECOGNITION", resume_data.get('rb_awards', []), modern_styles['JobTitle'], modern_styles['BodyText'], modern_styles, is_list_of_dicts=True, dict_format_func=_format_award_entry_modern)

    try:
        doc.build(story)
    except Exception as e:
        print(f"Error building PDF (Modern Professional): {e}")
        buffer.seek(0); buffer.truncate()
        SimpleDocTemplate(buffer, pagesize=letter).build([Paragraph(f"Error generating PDF: {e}", BASE_STYLES['BodyText'])])

    buffer.seek(0)
    return buffer

# --- Modern Template Specific Formatters (Example of adapting for different layouts) ---
def _format_experience_entry_modern(exp: Dict[str, Any], styles: getSampleStyleSheet) -> List[Any]:
    entry_story = []
    entry_story.append(Paragraph(_clean_field(exp, 'job_title'), styles['JobTitle']))
    # Company and Dates on one line for modern look
    company_line = f"{_clean_field(exp, 'company')} | {_clean_field(exp, 'start_date')} - {_clean_field(exp, 'end_date')}"
    entry_story.append(Paragraph(company_line, styles['CompanyName'])) # Use CompanyName style, which is smaller
    entry_story.extend(_format_description_to_paragraphs(_clean_field(exp, 'description'), styles['BulletPoint']))
    return entry_story

def _format_education_entry_modern(edu: Dict[str, Any], styles: getSampleStyleSheet) -> List[Any]:
    entry_story = []
    degree_inst = f"{_clean_field(edu, 'degree')} - {_clean_field(edu, 'institution')}"
    entry_story.append(Paragraph(degree_inst, styles['JobTitle']))

    details_parts = []
    if _clean_field(edu, 'grad_year') != "N/A": details_parts.append(f"Graduation: {_clean_field(edu, 'grad_year')}")
    if _clean_field(edu, 'details') != "N/A": details_parts.append(_clean_field(edu, 'details'))
    if details_parts: entry_story.append(Paragraph(", ".join(details_parts), styles['Dates']))
    return entry_story

def _format_project_entry_modern(proj: Dict[str, Any], styles: getSampleStyleSheet) -> List[Any]:
    entry_story = []
    entry_story.append(Paragraph(_clean_field(proj, 'name'), styles['JobTitle']))
    tech_and_link = []
    tech = _clean_field(proj, 'technologies')
    link = _clean_field(proj, 'link')
    if tech != "N/A": tech_and_link.append(f"<i>Technologies:</i> {tech}")
    if link != "N/A": tech_and_link.append(f"<link href='{link}' color='blue'>{link}</link>")
    if tech_and_link: entry_story.append(Paragraph(" | ".join(tech_and_link), styles['Dates']))
    entry_story.extend(_format_description_to_paragraphs(_clean_field(proj, 'description'), styles['BulletPoint']))
    return entry_story

def _format_award_entry_modern(award: Dict[str, Any], styles: getSampleStyleSheet) -> List[Any]:
    entry_story = []
    award_line = f"{_clean_field(award, 'name')} - {_clean_field(award, 'organization')}"
    if _clean_field(award, 'year') != "N/A": award_line += f" ({_clean_field(award, 'year')})"
    entry_story.append(Paragraph(award_line, styles['JobTitle']))
    if _clean_field(award, 'description') != "N/A":
        entry_story.extend(_format_description_to_paragraphs(_clean_field(award, 'description'), styles['BodyText']))
    return entry_story

# --- Template Function Mapping ---
TEMPLATE_FUNCTIONS: Dict[str, Callable[[Dict[str, Any]], io.BytesIO]] = {
    "Simple Text-Based": create_simple_text_resume,
    "Modern Professional": create_modern_professional_resume,
}

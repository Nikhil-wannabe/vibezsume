"""
This module provides functionality to build a resume in PDF format
from structured resume data. It uses the ReportLab library to generate the PDF.

The `DEFAULT_RESUME_STRUCTURE` dictionary defines the expected schema for the input data,
including sections like contact information, summary, skills, experience, education, and projects.
Each key in this structure corresponds to a section or piece of information in the resume.
"""
import json
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import Color, black, darkblue, gray # Color is not explicitly used but good to have for potential custom colors.
from typing import Dict, List, Any, Optional
import io

# --- Resume Data Structures (aligned with slm_module.parser.EXPECTED_FIELDS) ---

# Define a default structure, similar to EXPECTED_FIELDS in the SLM parser.
# This ensures consistency and provides a template for new resumes.
# It also serves as a reference for the expected data schema when generating PDFs.
DEFAULT_RESUME_STRUCTURE = {
    "name": "Your Name",  # (str) Full name of the individual.
    "contact_info": {      # (Dict[str, str]) Dictionary for contact details.
        "email": "your.email@example.com",    # (str) Email address.
        "phone": "(123) 456-7890",            # (str) Phone number.
        "linkedin": "linkedin.com/in/yourprofile", # (str) LinkedIn profile URL (e.g., "linkedin.com/in/yourprofile", protocol (http/https) will be added automatically).
        "github": "github.com/yourusername",       # (str) GitHub profile URL (e.g., "github.com/yourusername", protocol will be added automatically).
        "address": "123 Main St, Anytown, USA" # (str) Physical address (optional).
    },
    "summary": "A brief professional summary about yourself.", # (str) A short paragraph summarizing skills and career goals.
    "skills": ["Skill 1", "Skill 2", "Skill 3"], # (List[str]) List of key skills.
    "experience": [        # (List[Dict[str, str]]) List of professional experiences.
        {
            "job_title": "Your Job Title",       # (str) Title held at the job.
            "company": "Company Name",           # (str) Name of the company.
            "location": "City, State",           # (str) Location of the company (e.g., "San Francisco, CA").
            "dates": "Month Year - Month Year",  # (str) Employment dates (e.g., "Jan 2020 - Present").
            "description": "- Responsibility or achievement 1.\n- Responsibility or achievement 2." # (str) Bullet points or paragraph. Newlines `\n` are respected for multiple points.
        }
    ],
    "education": [         # (List[Dict[str, str]]) List of educational qualifications.
        {
            "institution": "University Name",    # (str) Name of the institution.
            "location": "City, State",           # (str) Location of the institution (e.g., "Stanford, CA").
            "degree": "Your Degree (e.g., B.S. in Computer Science)", # (str) Degree obtained.
            "dates": "Month Year - Month Year",  # (str) Dates of attendance or graduation (e.g., "Aug 2016 - May 2020").
            "details": "Relevant coursework, honors, or GPA (optional)." # (str) Additional details like GPA, honors, relevant coursework.
        }
    ],
    "projects": [          # (List[Dict[str, str]]) List of personal or academic projects (optional section).
        {
            "name": "Project Name",             # (str) Name of the project.
            "technologies": "Tech 1, Tech 2",   # (str) Comma-separated list of technologies used.
            "description": "A brief description of your project and your role.", # (str) Description of the project.
            "link": "github.com/yourproject"    # (str) Optional link to the project (e.g., "github.com/username/project", protocol will be added automatically).
        }
    ]
}

def get_new_resume_data() -> Dict[str, Any]:
    """
    Returns a deep copy of the `DEFAULT_RESUME_STRUCTURE`.

    This function is useful for initializing a new resume data object with a predefined
    template, ensuring all expected keys are present.

    Returns:
        Dict[str, Any]: A new dictionary object representing a blank resume structure.
    """
    # Using json.loads(json.dumps(...)) is a common way to perform a deep copy of simple data structures.
    return json.loads(json.dumps(DEFAULT_RESUME_STRUCTURE))

# --- PDF Generation Logic ---

def create_resume_pdf_bytes(resume_data: Dict[str, Any]) -> Optional[bytes]:
    """
    Generates a PDF resume from the given structured data using ReportLab.

    The function takes a dictionary conforming to `DEFAULT_RESUME_STRUCTURE` (or similar)
    and builds a PDF document. It defines styles for various text elements (name, titles,
    body text, etc.) and constructs the PDF story by adding paragraphs and spacers for each
    section of the resume.

    Args:
        resume_data (Dict[str, Any]): A dictionary containing the resume information.
                                      It's expected to generally follow the structure of
                                      `DEFAULT_RESUME_STRUCTURE`. Providing severely malformed
                                      data might lead to errors or an incorrectly formatted PDF.

    Returns:
        Optional[bytes]: The generated PDF content as a byte string.
                         Returns None if `resume_data` is empty or if an error occurs
                         during PDF generation.
    """
    if not resume_data:
        print("Error: No resume data provided for PDF generation.")
        return None

    # This function expects input data to generally conform to DEFAULT_RESUME_STRUCTURE.
    # Providing severely malformed data might lead to errors or an incorrectly formatted PDF.
    # More robust validation could be added here if needed.

    try:
        # Create a BytesIO buffer to hold the PDF data in memory.
        buffer = io.BytesIO()
        # Create a SimpleDocTemplate for the PDF, defining page size and margins.
        doc = SimpleDocTemplate(buffer, pagesize=letter,
                                leftMargin=0.75*inch, rightMargin=0.75*inch,
                                topMargin=0.75*inch, bottomMargin=0.75*inch)

        # Get default ReportLab stylesheet.
        styles = getSampleStyleSheet()

        # Define custom paragraph styles for different parts of the resume.
        # These styles control font, size, color, alignment, and spacing.
        styles.add(ParagraphStyle(name='NameStyle', fontName='Helvetica-Bold', fontSize=24, textColor=darkblue, alignment=1, spaceBottom=2)) # Centered name
        styles.add(ParagraphStyle(name='ContactStyle', fontName='Helvetica', fontSize=9, textColor=gray, alignment=1, spaceBottom=12)) # Centered contact info
        styles.add(ParagraphStyle(name='SectionTitleStyle', fontName='Helvetica-Bold', fontSize=14, textColor=darkblue, spaceBefore=12, spaceBottom=6))
        
        # Modify existing 'Normal' style or 'BodyText' if it exists, otherwise add a new one.
        # ReportLab's default stylesheet might already have 'BodyText'.
        # If 'BodyText' is not a standard key, this would fail. 'Normal' is standard.
        # Let's try to modify 'Normal' and use it as our body text, or create a new unique style.
        # For safety and clarity, creating a new custom style if BodyText is the issue:
        styles.add(ParagraphStyle(name='CustomBodyText', parent=styles['Normal'], spaceBottom=6, leading=14))
        
        styles.add(ParagraphStyle(name='JobTitleStyle', fontName='Helvetica-Bold', fontSize=11, spaceBottom=2))
        styles.add(ParagraphStyle(name='CompanyDateStyle', fontName='Helvetica', fontSize=10, textColor=gray, spaceBottom=4)) # For company, location, dates line
        styles.add(ParagraphStyle(name='InstitutionStyle', fontName='Helvetica-Bold', fontSize=11, spaceBottom=2))
        styles.add(ParagraphStyle(name='DegreeDateStyle', fontName='Helvetica', fontSize=10, textColor=gray, spaceBottom=4)) # For degree, location, dates line
        styles.add(ParagraphStyle(name='ProjectNameStyle', fontName='Helvetica-Bold', fontSize=11, spaceBottom=2))
        styles.add(ParagraphStyle(name='ProjectTechStyle', fontName='Helvetica-Oblique', fontSize=9, textColor=gray, spaceBottom=4)) # For project technologies and link

        # `story` is a list of ReportLab Flowables that will be rendered in the PDF.
        story: List[Any] = [] # Initialize the list of ReportLab Flowables.

        # Helper function to safely get and convert data to string for Paragraphs
        # This prevents errors if a field is None or not a string.
        def to_para_str(data_value: Any, default_str: str = "") -> str:
            """Converts any value to string, defaulting to empty string if None."""
            return str(data_value) if data_value is not None else default_str

        # 1. Name Section
        name_str = to_para_str(resume_data.get("name"))
        if name_str.strip(): # Check if name exists and is not just whitespace
            story.append(Paragraph(name_str, styles['NameStyle']))

        # 2. Contact Information Section
        contact_parts = []
        contact_info = resume_data.get("contact_info") # Get the contact_info dictionary
        if isinstance(contact_info, dict): # Ensure contact_info is a dictionary before processing
            email_str = to_para_str(contact_info.get("email"))
            if email_str.strip(): contact_parts.append(email_str)
            
            phone_str = to_para_str(contact_info.get("phone"))
            if phone_str.strip(): contact_parts.append(phone_str)
            
            linkedin_raw = contact_info.get("linkedin")
            if linkedin_raw and str(linkedin_raw).strip(): # Check if not None and not empty/whitespace string
                linkedin_url = str(linkedin_raw).strip()
                # Ensure links use https for consistency and security.
                if not linkedin_url.startswith(('http://', 'https://')):
                    linkedin_url = 'https://' + linkedin_url
                # Use the raw value for display text to keep it clean (e.g., "linkedin.com/in/profile")
                contact_parts.append(f"<link href='{linkedin_url}'>{str(linkedin_raw)}</link>")

            github_raw = contact_info.get("github")
            if github_raw and str(github_raw).strip(): # Check if not None and not empty/whitespace string
                github_url = str(github_raw).strip()
                if not github_url.startswith(('http://', 'https://')):
                    github_url = 'https://' + github_url
                contact_parts.append(f"<link href='{github_url}'>{str(github_raw)}</link>")
            
            address_str = to_para_str(contact_info.get("address"))
            if address_str.strip(): contact_parts.append(address_str)
        
        if contact_parts: # If any contact information was actually added
            # Join contact parts with a separator for a single line display.
            story.append(Paragraph(" | ".join(contact_parts), styles['ContactStyle']))

        # Add a horizontal line separator only if name or contact info was present.
        if name_str.strip() or contact_parts: 
            story.append(HRFlowable(width="100%", thickness=0.5, color=gray, spaceBefore=6, spaceAfter=6))

        # 3. Summary Section
        summary_str = to_para_str(resume_data.get("summary"))
        if summary_str.strip(): # Check if summary exists and is not just whitespace
            story.append(Paragraph("Summary", styles['SectionTitleStyle']))
            story.append(Paragraph(summary_str, styles['CustomBodyText']))

        # 4. Skills Section
        skills_list = resume_data.get("skills")
        # Check if skills_list is a list and contains at least one non-empty, stripped skill string.
        if isinstance(skills_list, list):
            valid_skills = [to_para_str(skill) for skill in skills_list if skill and str(skill).strip()]
            if valid_skills: # Only add section if there are valid skills to show
                story.append(Paragraph("Skills", styles['SectionTitleStyle']))
                story.append(Paragraph(", ".join(valid_skills), styles['CustomBodyText']))

        # 5. Experience Section
        experience_list = resume_data.get("experience")
        if isinstance(experience_list, list) and experience_list: # Check if it's a non-empty list
            story.append(Paragraph("Experience", styles['SectionTitleStyle']))
            for entry in experience_list:
                if not isinstance(entry, dict): continue # Skip if an entry is not a dictionary
                
                job_title_str = to_para_str(entry.get("job_title"))
                if job_title_str.strip(): # Check if job_title exists and is not whitespace
                    story.append(Paragraph(job_title_str, styles['JobTitleStyle']))

                company_line_parts = []
                if entry.get("company"): company_line_parts.append(to_para_str(entry.get("company")))
                if entry.get("location"): company_line_parts.append(to_para_str(entry.get("location")))
                if entry.get("dates"): company_line_parts.append(to_para_str(entry.get("dates")))
                if company_line_parts: # If any part of this line exists (after stripping, they might be empty)
                    actual_parts = [part for part in company_line_parts if part.strip()]
                    if actual_parts:
                        story.append(Paragraph(" | ".join(actual_parts), styles['CompanyDateStyle']))
                
                description_str = to_para_str(entry.get("description"))
                if description_str.strip(): # Check if description exists and is not whitespace
                    desc_lines = description_str.split('\n')
                    for line in desc_lines:
                        line_stripped = line.strip()
                        if line_stripped: # Process only non-empty lines
                            prefix = ""
                            # Check for common bullet point markers.
                            if line_stripped.startswith(("-", "*", "•")):
                                prefix = "• " # Use a standard bullet character.
                                line_stripped = line_stripped[1:].lstrip() # Remove marker and leading spaces after it.
                            # No special indentation for non-bulleted lines in this version, keeps it clean.
                            story.append(Paragraph(prefix + line_stripped, styles['CustomBodyText']))
                story.append(Spacer(1, 0.1*inch)) # Add a small vertical space after each experience entry.

        # 6. Education Section
        education_list = resume_data.get("education")
        if isinstance(education_list, list) and education_list: # Check if it's a non-empty list
            story.append(Paragraph("Education", styles['SectionTitleStyle']))
            for entry in education_list:
                if not isinstance(entry, dict): continue # Skip if an entry is not a dictionary
                
                institution_str = to_para_str(entry.get("institution"))
                if institution_str.strip(): # Check if institution exists
                    story.append(Paragraph(institution_str, styles['InstitutionStyle']))

                degree_line_parts = []
                if entry.get("degree"): degree_line_parts.append(to_para_str(entry.get("degree")))
                if entry.get("location"): degree_line_parts.append(to_para_str(entry.get("location")))
                if entry.get("dates"): degree_line_parts.append(to_para_str(entry.get("dates")))
                if degree_line_parts: # If any part of this line exists
                    actual_parts = [part for part in degree_line_parts if part.strip()]
                    if actual_parts:
                        story.append(Paragraph(" | ".join(actual_parts), styles['DegreeDateStyle']))

                details_str = to_para_str(entry.get("details"))
                if details_str.strip(): # Check if details exist
                    story.append(Paragraph(details_str, styles['CustomBodyText']))
                story.append(Spacer(1, 0.1*inch)) # Space after each education entry.

        # 7. Projects Section (Optional)
        project_list = resume_data.get("projects")
        if isinstance(project_list, list) and project_list: # Check if it's a non-empty list
            story.append(Paragraph("Projects", styles['SectionTitleStyle']))
            for entry in project_list:
                if not isinstance(entry, dict): continue # Skip if an entry is not a dictionary
                
                project_name_str = to_para_str(entry.get("name"))
                if project_name_str.strip(): # Check if project_name exists
                    story.append(Paragraph(project_name_str, styles['ProjectNameStyle']))

                tech_line_parts = []
                technologies_str = to_para_str(entry.get("technologies"))
                if technologies_str.strip(): tech_line_parts.append(technologies_str)
                
                project_link_raw = entry.get("link")
                if project_link_raw and str(project_link_raw).strip(): # Check if not None and not empty/whitespace string
                    link_url = str(project_link_raw).strip()
                    if not link_url.startswith(('http://', 'https://')):
                        link_url = 'https://' + link_url
                    tech_line_parts.append(f"<link href='{link_url}'>{str(project_link_raw)}</link>")
                
                if tech_line_parts: # If technologies or link exist
                     story.append(Paragraph(" | ".join(tech_line_parts), styles['ProjectTechStyle']))

                description_proj_str = to_para_str(entry.get("description"))
                if description_proj_str.strip(): # Check if project description exists
                    story.append(Paragraph(description_proj_str, styles['CustomBodyText']))
                story.append(Spacer(1, 0.1*inch)) # Space after each project entry.

        # Build the PDF document from the story list of Flowables.
        doc.build(story)
        # Get the PDF content from the buffer.
        pdf_bytes = buffer.getvalue()
        buffer.close() # Close the buffer.
        return pdf_bytes

    except Exception as e:
        # Catch any other exceptions during PDF generation.
        print(f"Error generating PDF resume: {e}")
        return None

# --- Placeholder for data management functions (to be implemented later if needed by backend) ---
# def save_resume_data(user_id: str, resume_data: Dict[str, Any]): ...
# def load_resume_data(user_id: str) -> Optional[Dict[str, Any]]: ...


# --- Main for Testing PDF Generation ---
if __name__ == '__main__':
    print("--- Resume Builder Logic Test (PDF Generation) ---")

    # Use the default structure for a quick test
    test_resume_data = get_new_resume_data()

    # Customize a bit for a more realistic test
    test_resume_data["name"] = "Dr. Jane Doe"
    test_resume_data["contact_info"]["email"] = "jane.doe@example.com"
    test_resume_data["contact_info"]["linkedin"] = "linkedin.com/in/janedoetest"
    test_resume_data["summary"] = ("Highly skilled and motivated professional with experience in "
                                   "software development and project management. Proven ability to "
                                   "deliver high-quality results in fast-paced environments. "
                                   "Seeking challenging opportunities to leverage expertise in innovative projects.")
    test_resume_data["skills"] = ["Python", "JavaScript", "React", "Node.js", "AWS", "Docker", "Agile Methodologies", "Project Management"]
    test_resume_data["experience"] = [
        {
            "job_title": "Senior Software Engineer", "company": "Tech Solutions Inc.",
            "location": "San Francisco, CA", "dates": "Jan 2020 - Present",
            "description": ("- Led a team of 5 developers in designing and implementing a new cloud-based platform.\n"
                          "- Improved system performance by 25% through code optimization and architectural changes.\n"
                          "- Mentored junior engineers and conducted code reviews.")
        },
        {
            "job_title": "Software Developer", "company": "Innovate LLC",
            "location": "Austin, TX", "dates": "June 2017 - Dec 2019",
            "description": ("- Developed and maintained full-stack web applications using JavaScript, React, and Node.js.\n"
                          "- Collaborated with cross-functional teams to deliver new features and enhancements.")
        }
    ]
    test_resume_data["education"] = [
        {
            "institution": "State University", "degree": "M.S. in Computer Science",
            "location": "Anytown, USA", "dates": "2015 - 2017",
            "details": "Thesis on Advanced Algorithms. GPA: 3.9/4.0"
        },
        {
            "institution": "Tech College", "degree": "B.S. in Software Engineering",
            "location": "Techville, USA", "dates": "2011 - 2015",
            "details": "Graduated with Honors. Capstone project on mobile app development."
        }
    ]
    test_resume_data["projects"] = [
        {
            "name": "Personal Portfolio Website", "technologies": "React, Gatsby, Netlify",
            "description": "Developed and deployed a personal portfolio website to showcase projects and skills. Features a blog and responsive design.",
            "link": "github.com/janedoe/portfolio"
        },
        {
            "name": "AI Chatbot Assistant", "technologies": "Python, TensorFlow, NLTK",
            "description": "Created a conversational AI chatbot for customer service inquiries. Implemented intent recognition and dialogue management.",
            "link": "github.com/janedoe/chatbot"
        }
    ]

    pdf_output_filename = "test_resume_output.pdf"
    pdf_bytes = create_resume_pdf_bytes(test_resume_data)

    if pdf_bytes:
        try:
            with open(pdf_output_filename, "wb") as f:
                f.write(pdf_bytes)
            print(f"Successfully generated PDF: {pdf_output_filename}")
            print("Please open the file to review the layout and content.")
        except Exception as e:
            print(f"Error writing PDF to file: {e}")
    else:
        print("Failed to generate PDF bytes.")

    # Test with minimal data
    minimal_data = {"name": "John Minimal"}
    pdf_bytes_minimal = create_resume_pdf_bytes(minimal_data)
    if pdf_bytes_minimal:
         print(f"Successfully generated PDF for minimal data (length: {len(pdf_bytes_minimal)} bytes). First 100 bytes: {pdf_bytes_minimal[:100]}")
    else:
        print("Failed to generate PDF for minimal data.")

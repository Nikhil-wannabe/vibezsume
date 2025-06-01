import json
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import Color, black, darkblue, gray
from typing import Dict, List, Any, Optional
import io

# --- Resume Data Structures (aligned with slm_module.parser.EXPECTED_FIELDS) ---

# Define a default structure, similar to EXPECTED_FIELDS in the SLM parser
# This ensures consistency and provides a template for new resumes.
DEFAULT_RESUME_STRUCTURE = {
    "name": "Your Name",
    "contact_info": {
        "email": "your.email@example.com",
        "phone": "(123) 456-7890",
        "linkedin": "linkedin.com/in/yourprofile",
        "github": "github.com/yourusername",
        "address": "123 Main St, Anytown, USA" # Added address field
    },
    "summary": "A brief professional summary about yourself.",
    "skills": ["Skill 1", "Skill 2", "Skill 3"],
    "experience": [
        {
            "job_title": "Your Job Title",
            "company": "Company Name",
            "location": "City, State", # Added location for experience
            "dates": "Month Year - Month Year",
            "description": "- Responsibility or achievement 1.\n- Responsibility or achievement 2."
        }
    ],
    "education": [
        {
            "institution": "University Name",
            "location": "City, State", # Added location for education
            "degree": "Your Degree (e.g., B.S. in Computer Science)",
            "dates": "Month Year - Month Year", # Or "Graduation Month Year"
            "details": "Relevant coursework, honors, or GPA (optional)."
        }
    ],
    "projects": [ # Added a projects section
        {
            "name": "Project Name",
            "technologies": "Tech 1, Tech 2",
            "description": "A brief description of your project and your role.",
            "link": "github.com/yourproject" # Optional link
        }
    ]
}

def get_new_resume_data() -> Dict[str, Any]:
    """Returns a deep copy of the default resume structure."""
    return json.loads(json.dumps(DEFAULT_RESUME_STRUCTURE))

# --- PDF Generation Logic ---

def create_resume_pdf_bytes(resume_data: Dict[str, Any]) -> Optional[bytes]:
    """
    Generates a PDF resume from the given structured data using ReportLab.
    Returns the PDF content as bytes, or None if an error occurs.
    """
    if not resume_data:
        return None

    try:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter,
                                leftMargin=0.75*inch, rightMargin=0.75*inch,
                                topMargin=0.75*inch, bottomMargin=0.75*inch)

        styles = getSampleStyleSheet()

        # Custom Styles
        styles.add(ParagraphStyle(name='NameStyle', fontName='Helvetica-Bold', fontSize=24, textColor=darkblue, alignment=1, spaceBottom=2))
        styles.add(ParagraphStyle(name='ContactStyle', fontName='Helvetica', fontSize=9, textColor=gray, alignment=1, spaceBottom=12))
        styles.add(ParagraphStyle(name='SectionTitleStyle', fontName='Helvetica-Bold', fontSize=14, textColor=darkblue, spaceBefore=12, spaceBottom=6))
        styles.add(ParagraphStyle(name='BodyText', parent=styles['Normal'], spaceBottom=6, leading=14))
        styles.add(ParagraphStyle(name='JobTitleStyle', fontName='Helvetica-Bold', fontSize=11, spaceBottom=2))
        styles.add(ParagraphStyle(name='CompanyDateStyle', fontName='Helvetica', fontSize=10, textColor=gray, spaceBottom=4))
        styles.add(ParagraphStyle(name='InstitutionStyle', fontName='Helvetica-Bold', fontSize=11, spaceBottom=2))
        styles.add(ParagraphStyle(name='DegreeDateStyle', fontName='Helvetica', fontSize=10, textColor=gray, spaceBottom=4))
        styles.add(ParagraphStyle(name='ProjectNameStyle', fontName='Helvetica-Bold', fontSize=11, spaceBottom=2))
        styles.add(ParagraphStyle(name='ProjectTechStyle', fontName='Helvetica-Oblique', fontSize=9, textColor=gray, spaceBottom=4))


        story = []

        # 1. Name
        if resume_data.get("name"):
            story.append(Paragraph(resume_data["name"], styles['NameStyle']))

        # 2. Contact Info
        contact_parts = []
        ci = resume_data.get("contact_info", {})
        if ci.get("email"): contact_parts.append(ci["email"])
        if ci.get("phone"): contact_parts.append(ci["phone"])
        if ci.get("linkedin"): contact_parts.append(f"<link href='http://{ci['linkedin']}'>{ci['linkedin']}</link>") # Basic hyperlinking
        if ci.get("github"): contact_parts.append(f"<link href='http://{ci['github']}'>{ci['github']}</link>")
        if ci.get("address"): contact_parts.append(ci["address"])
        if contact_parts:
            story.append(Paragraph(" | ".join(contact_parts), styles['ContactStyle']))

        # Horizontal Line
        story.append(HRFlowable(width="100%", thickness=0.5, color=gray, spaceBefore=6, spaceAfter=6))

        # 3. Summary
        if resume_data.get("summary"):
            story.append(Paragraph("Summary", styles['SectionTitleStyle']))
            story.append(Paragraph(resume_data["summary"], styles['BodyText']))

        # 4. Skills
        skills = resume_data.get("skills")
        if skills and isinstance(skills, list) and any(s.strip() for s in skills):
            story.append(Paragraph("Skills", styles['SectionTitleStyle']))
            # Could be a comma-separated paragraph or bullet points
            story.append(Paragraph(", ".join(skill for skill in skills if skill.strip()), styles['BodyText']))

        # 5. Experience
        experience_entries = resume_data.get("experience")
        if experience_entries and isinstance(experience_entries, list):
            story.append(Paragraph("Experience", styles['SectionTitleStyle']))
            for entry in experience_entries:
                if not isinstance(entry, dict): continue
                if entry.get("job_title"):
                    story.append(Paragraph(entry["job_title"], styles['JobTitleStyle']))

                company_line_parts = []
                if entry.get("company"): company_line_parts.append(entry["company"])
                if entry.get("location"): company_line_parts.append(entry["location"])
                if entry.get("dates"): company_line_parts.append(entry["dates"])
                if company_line_parts:
                    story.append(Paragraph(" | ".join(company_line_parts), styles['CompanyDateStyle']))

                if entry.get("description"):
                    # Basic handling for newlines in description to create bullet points
                    desc_lines = entry["description"].split('\n')
                    for line in desc_lines:
                        if line.strip():
                             # Add bullet point if line starts with common markers or just indent
                            prefix = ""
                            if line.strip().startswith(("-", "*", "•")):
                                prefix = "• "
                                line = line.strip()[1:].strip()
                            else: # Indent non-bulleted lines slightly for readability
                                prefix = "&nbsp;&nbsp;&nbsp;&nbsp;" # HTML space for indentation
                            story.append(Paragraph(prefix + line.strip(), styles['BodyText']))
                story.append(Spacer(1, 0.1*inch)) # Space between entries

        # 6. Education
        education_entries = resume_data.get("education")
        if education_entries and isinstance(education_entries, list):
            story.append(Paragraph("Education", styles['SectionTitleStyle']))
            for entry in education_entries:
                if not isinstance(entry, dict): continue
                if entry.get("institution"):
                    story.append(Paragraph(entry["institution"], styles['InstitutionStyle']))

                degree_line_parts = []
                if entry.get("degree"): degree_line_parts.append(entry["degree"])
                if entry.get("location"): degree_line_parts.append(entry["location"])
                if entry.get("dates"): degree_line_parts.append(entry["dates"])
                if degree_line_parts:
                    story.append(Paragraph(" | ".join(degree_line_parts), styles['DegreeDateStyle']))

                if entry.get("details"):
                    story.append(Paragraph(entry["details"], styles['BodyText']))
                story.append(Spacer(1, 0.1*inch))

        # 7. Projects (Optional Section)
        project_entries = resume_data.get("projects")
        if project_entries and isinstance(project_entries, list):
            story.append(Paragraph("Projects", styles['SectionTitleStyle']))
            for entry in project_entries:
                if not isinstance(entry, dict): continue
                if entry.get("name"):
                    story.append(Paragraph(entry["name"], styles['ProjectNameStyle']))

                tech_line_parts = []
                if entry.get("technologies"): tech_line_parts.append(entry["technologies"])
                project_link = entry.get("link")
                if project_link:
                     tech_line_parts.append(f"<link href='http://{project_link}'>{project_link}</link>")
                if tech_line_parts:
                     story.append(Paragraph(" | ".join(tech_line_parts), styles['ProjectTechStyle']))

                if entry.get("description"):
                    story.append(Paragraph(entry["description"], styles['BodyText']))
                story.append(Spacer(1, 0.1*inch))

        doc.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes

    except Exception as e:
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

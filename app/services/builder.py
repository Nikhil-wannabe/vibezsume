from jinja2 import Environment, FileSystemLoader
import base64
import os
from app.models.resume_model import ResumeData, Resume
import uuid

# Set up Jinja2 environment
template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
env = Environment(loader=FileSystemLoader(template_dir))

def build_resume(resume_data: ResumeData) -> Resume:
    """Build a Resume object from submitted form data"""
    # Convert from ResumeData to Resume, potentially doing some processing
    resume = Resume(
        name=resume_data.name,
        email=resume_data.email,
        phone=resume_data.phone,
        summary=resume_data.summary,
        skills=resume_data.skills,
        education=resume_data.education,
        experience=resume_data.experience,
        generated_id=str(uuid.uuid4())
    )
    return resume

def render_resume(resume: Resume) -> str:
    """Render resume to HTML and convert to PDF (base64 encoded)"""
    # Get the resume template
    template = env.get_template("resume_template.html")
    
    # Render the template with resume data
    html_content = template.render(
        name=resume.name,
        email=resume.email,
        phone=resume.phone,
        skills=resume.skills,
        experience=resume.experience,
        education=resume.education
    )
    
    # In a real implementation, you would convert HTML to PDF here
    # For this example, we'll just return the HTML content encoded in base64
    encoded_content = base64.b64encode(html_content.encode()).decode()
    
    return encoded_content
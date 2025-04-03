import fitz  # PyMuPDF
import docx
import os
import re

def parse_resume(content: bytes, filename: str) -> dict:
    """Parse resume content from various file formats"""
    file_extension = os.path.splitext(filename)[1].lower()
    
    if file_extension == '.pdf':
        return parse_pdf(content)
    elif file_extension in ['.docx', '.doc']:
        return parse_docx(content)
    else:
        raise ValueError(f"Unsupported file format: {file_extension}")

def parse_pdf(content: bytes) -> dict:
    """Extract text from PDF and parse into resume sections"""
    try:
        document = fitz.open(stream=content, filetype="pdf")
        text = ""
        for page in document:
            text += page.get_text()
        
        # Parse the text into sections
        return extract_resume_sections(text)
    except Exception as e:
        raise Exception(f"Error parsing PDF: {str(e)}")

def parse_docx(content: bytes) -> dict:
    """Extract text from DOCX and parse into resume sections"""
    try:
        doc = docx.Document(content)
        text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
        
        # Parse the text into sections
        return extract_resume_sections(text)
    except Exception as e:
        raise Exception(f"Error parsing DOCX: {str(e)}")

def extract_resume_sections(text: str) -> dict:
    """Extract sections like education, experience, skills, etc."""
    # This is a simplified version - in practice, you'd need more sophisticated parsing
    resume_data = {
        "name": extract_name(text),
        "email": extract_email(text),
        "phone": extract_phone(text),
        "skills": extract_skills(text),
        "education": extract_education(text),
        "experience": extract_experience(text),
        "summary": extract_summary(text)
    }
    return resume_data

def extract_name(text: str) -> str:
    # Simplified name extraction
    lines = text.split('\n')
    if lines and lines[0].strip():
        return lines[0].strip()
    return ""

def extract_email(text: str) -> str:
    # Extract email using regex
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    match = re.search(email_pattern, text)
    if match:
        return match.group(0)
    return ""

def extract_phone(text: str) -> str:
    # Extract phone number using regex
    phone_pattern = r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
    match = re.search(phone_pattern, text)
    if match:
        return match.group(0)
    return ""

def extract_skills(text: str) -> list:
    # Simplified skill extraction - look for skills section
    skills_section = re.search(r'(?i)skills?:?(.*?)(?:\n\n|\Z)', text, re.DOTALL)
    if skills_section:
        skills_text = skills_section.group(1)
        # Split by commas or new lines and clean up
        skills = re.split(r'[,\n]', skills_text)
        return [skill.strip() for skill in skills if skill.strip()]
    return []

def extract_education(text: str) -> str:
    # Simplified education extraction
    education_section = re.search(r'(?i)education:?(.*?)(?:\n\n|\Z)', text, re.DOTALL)
    if education_section:
        return education_section.group(1).strip()
    return ""

def extract_experience(text: str) -> str:
    # Simplified experience extraction
    experience_section = re.search(r'(?i)(?:experience|work|employment):?(.*?)(?:\n\n|\Z)', text, re.DOTALL)
    if experience_section:
        return experience_section.group(1).strip()
    return ""

def extract_summary(text: str) -> str:
    # Simplified summary extraction
    summary_section = re.search(r'(?i)(?:summary|profile|objective):?(.*?)(?:\n\n|\Z)', text, re.DOTALL)
    if summary_section:
        return summary_section.group(1).strip()
    return ""
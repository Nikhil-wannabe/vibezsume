import os
from PyPDF2 import PdfReader
import docx2txt

def extract_text_from_pdf(file_path):
    """Extracts text from a PDF file."""
    text = ""
    with open(file_path, "rb") as file:
        reader = PdfReader(file)
        for page in reader.pages:
            text += page.extract_text() or ""
    return text

def extract_text_from_docx(file_path):
    """Extracts text from a DOCX file."""
    return docx2txt.process(file_path)

def extract_resume_data(file_path):
    """
    Determines the file format and extracts text accordingly.
    Supports PDF and DOCX formats.
    """
    _, file_extension = os.path.splitext(file_path)
    file_extension = file_extension.lower()
    
    if file_extension == '.pdf':
        return extract_text_from_pdf(file_path)
    elif file_extension == '.docx':
        return extract_text_from_docx(file_path)
    else:
        raise ValueError("Unsupported file format. Only PDF and DOCX are supported.")

if __name__ == '__main__':
    # Replace the below path with the actual file path of the uploaded resume document.
    file_path = "../docs/resume.pdf"  # or "path_to_resume.docx"
    
    try:
        resume_text = extract_resume_data(file_path)
        print("Extracted Resume Text:\n")
        print(resume_text)
    except Exception as e:
        print(f"Error: {e}")

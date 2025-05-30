import PyPDF2
import docx
import re

def extract_text_from_pdf(file_path):
    """Extracts text from a PDF file."""
    try:
        with open(file_path, 'rb') as pdf_file:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            text = ""
            for page_num in range(len(pdf_reader.pages)):
                text += pdf_reader.pages[page_num].extract_text()
        return text
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return None

def extract_text_from_docx(file_path):
    """Extracts text from a DOCX file."""
    try:
        doc = docx.Document(file_path)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text
    except Exception as e:
        print(f"Error extracting text from DOCX: {e}")
        return None

def parse_resume_text(text):
    """
    Parses extracted text to find structured data.
    This is a basic implementation and can be significantly improved.
    """
    if not text:
        return {}

    resume_data = {
        "name": None,
        "email": None,
        "phone": None,
        "skills": [],
        "experience": [],
        "education": [],
        "summary": None,
    }

    # Basic regex patterns (can be expanded and refined)
    email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    phone_pattern = r"\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}" # Basic US phone format

    # Extract email
    match = re.search(email_pattern, text)
    if match:
        resume_data["email"] = match.group(0)

    # Extract phone
    match = re.search(phone_pattern, text)
    if match:
        resume_data["phone"] = match.group(0)

    # Placeholder for name extraction (often the first few lines or largest font)
    # This is highly dependent on resume format.
    lines = text.split('\n')
    if lines:
        resume_data["name"] = lines[0].strip() # Simplistic assumption

    # Placeholder for skills, experience, education, summary
    # These would require more sophisticated NLP or rule-based parsing
    # For now, we'll just add some keywords as examples if found

    # Example for skills (very basic)
    if "python" in text.lower():
        resume_data["skills"].append("Python")
    if "java" in text.lower():
        resume_data["skills"].append("Java")
    if "machine learning" in text.lower():
        resume_data["skills"].append("Machine Learning")

    # Example for summary (look for a section header)
    summary_match = re.search(r"(summary|objective|profile)\s*?\n([\s\S]+?)(experience|skills|education)", text, re.IGNORECASE)
    if summary_match:
        resume_data["summary"] = summary_match.group(2).strip()


    # This function would be called from the Streamlit app
    # For example:
    # if uploaded_file.type == "application/pdf":
    #     text = extract_text_from_pdf(uploaded_file_path)
    # elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
    #     text = extract_text_from_docx(uploaded_file_path)
    # if text:
    #     parsed_data = parse_resume_text(text)
    #     # Display parsed_data in Streamlit

    return resume_data

if __name__ == '__main__':
    # Example Usage (for testing)
    # Create dummy files or use actual test files for this part

    # Test with a dummy PDF (requires a PDF file named 'dummy.pdf' in the same directory)
    # with open('dummy.pdf', 'w') as f: # This will not create a valid PDF
    #     f.write("This is a test PDF for John Doe. Email: john.doe@example.com. Skills: Python, SQL.")
    # pdf_text = extract_text_from_pdf('dummy.pdf')
    # if pdf_text:
    #     print("---- PDF Text ----")
    #     print(pdf_text)
    #     parsed_pdf_data = parse_resume_text(pdf_text)
    #     print("---- Parsed PDF Data ----")
    #     print(parsed_pdf_data)

    # Test with a dummy DOCX (requires a DOCX file named 'dummy.docx' in the same directory)
    # from docx import Document
    # doc = Document()
    # doc.add_paragraph("This is a test DOCX for Jane Smith. Email: jane.smith@example.com. Phone: (123) 456-7890")
    # doc.add_paragraph("Summary: Experienced professional.")
    # doc.save('dummy.docx')
    # docx_text = extract_text_from_docx('dummy.docx')
    # if docx_text:
    #     print("\n---- DOCX Text ----")
    #     print(docx_text)
    #     parsed_docx_data = parse_resume_text(docx_text)
    #     print("---- Parsed DOCX Data ----")
    #     print(parsed_docx_data)
    pass

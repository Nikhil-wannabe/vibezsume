import PyPDF2
import docx
from typing import Optional, Union
import io

def extract_text_from_pdf(file_content: bytes) -> Optional[str]:
    """Extracts text content from a PDF file's byte content."""
    try:
        pdf_file = io.BytesIO(file_content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text
        return text.strip() if text.strip() else None
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return None

def extract_text_from_docx(file_content: bytes) -> Optional[str]:
    """Extracts text content from a DOCX file's byte content."""
    try:
        doc_file = io.BytesIO(file_content)
        doc_obj = docx.Document(doc_file)
        text = "\n".join(paragraph.text for paragraph in doc_obj.paragraphs)
        return text.strip() if text.strip() else None
    except Exception as e:
        print(f"Error extracting text from DOCX: {e}")
        return None

def extract_text_from_file(file_name: str, file_content: bytes) -> Optional[str]:
    """
    Extracts text from a file based on its extension.
    Args:
        file_name (str): The name of the file (e.g., "resume.pdf").
        file_content (bytes): The byte content of the file.
    Returns:
        Optional[str]: The extracted text, or None if extraction fails or format is unsupported.
    """
    if not file_name or not file_content:
        return None

    file_extension = file_name.split('.')[-1].lower()

    if file_extension == 'pdf':
        return extract_text_from_pdf(file_content)
    elif file_extension == 'docx':
        return extract_text_from_docx(file_content)
    elif file_extension == 'txt':
        try:
            return file_content.decode('utf-8').strip()
        except UnicodeDecodeError:
            try:
                return file_content.decode('latin-1').strip() # Try another common encoding
            except Exception as e:
                print(f"Error decoding TXT file: {e}")
                return None
    else:
        print(f"Unsupported file format: {file_extension}")
        return None

if __name__ == '__main__':
    # Basic test logic (requires dummy files or mocking)
    # Create dummy PDF and DOCX for local testing if possible, or use mocks.
    # For now, just print a message.
    print("Text extraction module ready. Testing requires actual file content.")

    # Example of how it might be used (conceptual)
    # with open("dummy.pdf", "rb") as f:
    #     content = f.read()
    #     text = extract_text_from_file("dummy.pdf", content)
    #     if text:
    #         print("Successfully extracted text from PDF (dummy):", text[:100])
    #     else:
    #         print("Failed to extract text from PDF (dummy).")

    # try:
    #     # Create a dummy docx for testing
    #     from docx import Document
    #     doc = Document()
    #     doc.add_paragraph("This is a test document for DOCX extraction.")
    #     doc.add_paragraph("It contains multiple paragraphs.")
    #     dummy_docx_bytes_io = io.BytesIO()
    #     doc.save(dummy_docx_bytes_io)
    #     dummy_docx_bytes = dummy_docx_bytes_io.getvalue()

    #     text_docx = extract_text_from_file("test.docx", dummy_docx_bytes)
    #     if text_docx:
    #         print(f"Successfully extracted from dummy DOCX: '{text_docx}'")
    #     else:
    #         print("Failed to extract from dummy DOCX.")

    #     # Create dummy txt for testing
    #     dummy_txt_content = "This is a plain text file for testing. With UTF-8 characters: éàçüö".encode('utf-8')
    #     text_txt = extract_text_from_file("test.txt", dummy_txt_content)
    #     if text_txt:
    #         print(f"Successfully extracted from dummy TXT: '{text_txt}'")
    #     else:
    #         print("Failed to extract from dummy TXT.")

    # except ImportError:
    #     print("python-docx or PyPDF2 not installed, skipping some local tests.")
    # except Exception as e:
    #     print(f"Error during local test setup: {e}")

def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from a PDF file using PyPDF2 (simpler alternative)"""
    try:
        # Try using PyPDF2 which has fewer dependencies
        import PyPDF2
        
        text = ""
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page_num in range(len(reader.pages)):
                text += reader.pages[page_num].extract_text() or ""
        
        if text.strip():
            return text
        else:
            return "No text could be extracted from this PDF. It may be scanned or image-based."
            
    except ImportError:
        return "PDF parsing library not installed. Please run: pip install PyPDF2"
    except Exception as e:
        return f"Error extracting text from PDF: {str(e)}"
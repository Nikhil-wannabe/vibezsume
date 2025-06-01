from fastapi import FastAPI, File, UploadFile, HTTPException, Body
from fastapi.responses import JSONResponse, StreamingResponse
from typing import Dict, Optional, Any
import io

# Adjust import paths based on project structure
# These modules are in sibling directories to 'backend', so we need to adjust Python's path
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core_logic import text_extraction
from slm_module import parser as slm_parser
from core_logic import job_analyzer
from core_logic import resume_builder

app = FastAPI(
    title="AI Resume Toolkit Backend",
    description="API endpoints for resume analysis, job analysis, and resume building.",
    version="1.0.0"
)

# --- In-memory storage for simplicity (replace with database in a real app) ---
# For Resume Builder: stores the current working resume data
current_resume_data: Dict[str, Any] = resume_builder.get_new_resume_data()
# For Job Analyzer: stores the last analyzed resume and job description
last_analyzed_resume_slm: Optional[Dict[str, Any]] = None
last_job_description_text: Optional[str] = None


# --- Error Handling Helper ---
def http_exc(status_code: int, detail: str):
    return HTTPException(status_code=status_code, detail=detail)

# --- API Endpoints ---

# 1. Resume Analysis Endpoint
@app.post("/resume/analyze", tags=["Resume Analysis"])
async def analyze_resume_file(file: UploadFile = File(...)):
    """
    Accepts a resume file (PDF, DOCX, TXT), extracts text,
    parses it with the SLM, and returns the structured JSON data.
    """
    global last_analyzed_resume_slm
    if not file.filename:
        raise http_exc(400, "No file name provided.")

    file_content = await file.read()
    if not file_content:
        raise http_exc(400, "File content is empty.")

    try:
        extracted_text = text_extraction.extract_text_from_file(file.filename, file_content)
        if not extracted_text:
            raise http_exc(422, f"Could not extract text from file: {file.filename}. Unsupported format or corrupt file.")

        # Ensure SLM model is loaded (it loads on first call within the module)
        slm_parser.load_slm_model()
        if not slm_parser.ner_pipeline: # Check if model loaded successfully
             raise http_exc(503, "SLM model is not available. Please try again later.")

        parsed_data = slm_parser.parse_resume_text_with_slm(extracted_text)

        if parsed_data.get("name") == "ERROR: SLM Model Not Loaded": # Check for specific error from parser
            raise http_exc(503, "SLM model failed to load during parsing.")

        last_analyzed_resume_slm = parsed_data # Store for potential use by Job Analyzer
        return JSONResponse(content=parsed_data)

    except HTTPException as e: # Re-raise HTTPExceptions
        raise e
    except Exception as e:
        print(f"Error during resume analysis: {e}") # Log for server
        raise http_exc(500, f"An unexpected error occurred during resume analysis: {str(e)}")


# --- Job Analysis Endpoints ---

@app.post("/job/scrape-url", tags=["Job Analysis"])
async def scrape_job_url_endpoint(payload: Dict[str, str] = Body(..., example={"url": "https://example.com/job/123"})):
    """
    Accepts a URL, scrapes the job description, stores it, and returns the text.
    """
    global last_job_description_text
    url = payload.get("url")
    if not url:
        raise http_exc(400, "URL must be provided in the payload.")

    try:
        scraped_text = job_analyzer.scrape_job_description_from_url(url)
        if not scraped_text:
            raise http_exc(422, f"Could not scrape or find significant content at URL: {url}")

        last_job_description_text = scraped_text
        return JSONResponse(content={"url": url, "scraped_text": scraped_text})
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Error during job scraping for URL {url}: {e}")
        raise http_exc(500, f"An unexpected error occurred during job scraping: {str(e)}")

@app.post("/job/analyze-text", tags=["Job Analysis"])
async def analyze_job_text_endpoint(payload: Dict[str, str] = Body(..., example={"text": "Job description text here..."})):
    """
    Accepts raw job description text, stores it, and can return basic analysis (e.g., keywords).
    """
    global last_job_description_text
    text = payload.get("text")
    if not text or not text.strip():
        raise http_exc(400, "Job description text must be provided in the payload.")

    last_job_description_text = text.strip()
    # Optionally, perform some immediate analysis like keyword extraction
    # keywords = job_analyzer.extract_keywords_from_text(last_job_description_text)
    # return JSONResponse(content={"message": "Job text received and stored.", "keywords_preview": keywords[:20]})
    return JSONResponse(content={"message": "Job text received and stored.", "text_snippet": last_job_description_text[:200]})


@app.post("/job/compare-resume", tags=["Job Analysis"])
async def compare_resume_with_job_endpoint(payload: Optional[Dict[str, Any]] = Body(None, example={"job_description_text": "Optional job text...", "resume_data": {"name": "Jane", "skills": ["Python"]}})):
    """
    Compares resume data with job description text.
    Uses last stored resume analysis and job description if not provided in payload.
    Payload structure:
    {
        "job_description_text": "Optional text of the job description.",
        "resume_data": { Optional structured resume data from SLM }
    }
    """
    global last_analyzed_resume_slm, last_job_description_text

    current_job_text = None
    if payload and payload.get("job_description_text"):
        current_job_text = payload["job_description_text"]
    elif last_job_description_text:
        current_job_text = last_job_description_text
    else:
        raise http_exc(400, "No job description text available. Please provide it in the payload or use '/job/analyze-text' or '/job/scrape-url' first.")

    current_resume_data = None
    if payload and payload.get("resume_data"):
        current_resume_data = payload["resume_data"]
    elif last_analyzed_resume_slm:
        current_resume_data = last_analyzed_resume_slm
    else:
        raise http_exc(400, "No resume data available for comparison. Please provide it or analyze a resume first using '/resume/analyze'.")

    if not isinstance(current_resume_data, dict) or not isinstance(current_job_text, str):
         raise http_exc(400, "Invalid format for resume data or job text.")

    try:
        comparison_results = job_analyzer.compare_resume_to_job_description(current_resume_data, current_job_text)
        return JSONResponse(content=comparison_results)
    except Exception as e:
        print(f"Error during resume-job comparison: {e}")
        raise http_exc(500, f"An unexpected error occurred during comparison: {str(e)}")


# --- Resume Builder Endpoints ---

@app.get("/builder/resume", tags=["Resume Builder"])
async def get_resume_builder_data_endpoint():
    """
    Retrieves the current resume data being edited in the builder.
    """
    global current_resume_data
    if current_resume_data is None:
        # Initialize with default if it somehow became None, though it's initialized globally
        current_resume_data = resume_builder.get_new_resume_data()
    return JSONResponse(content=current_resume_data)

@app.put("/builder/resume", tags=["Resume Builder"])
async def update_resume_builder_data_endpoint(new_resume_data: Dict[str, Any] = Body(...)):
    """
    Updates the current resume data in the builder with the provided JSON payload.
    A basic validation could be to check for 'name' or other essential fields.
    """
    global current_resume_data
    if not new_resume_data or not isinstance(new_resume_data, dict): # Basic check
        raise http_exc(400, "Invalid resume data payload. Must be a JSON object.")

    # Optional: Add more specific validation against DEFAULT_RESUME_STRUCTURE keys/types
    # For example, ensure 'name' exists, 'skills' is a list, etc.
    # For now, we'll accept any valid JSON dictionary.

    current_resume_data = new_resume_data
    return JSONResponse(content={"message": "Resume data updated successfully.", "updated_data_preview": {"name": current_resume_data.get("name")}})

@app.post("/builder/resume/download-pdf", tags=["Resume Builder"]) # Changed to POST to optionally accept data
async def download_resume_as_pdf_endpoint(resume_data_payload: Optional[Dict[str, Any]] = Body(None, example={"resume_data": resume_builder.DEFAULT_RESUME_STRUCTURE})):
    """
    Generates a PDF version of the resume.
    It can use the globally stored `current_resume_data` if no data is provided in the payload,
    or it can generate a PDF from the `resume_data` provided in the request body.
    Payload structure: Optional { "resume_data": { ... full resume data ... } }
    """
    global current_resume_data

    data_to_use_for_pdf = None

    if resume_data_payload and resume_data_payload.get("resume_data") and isinstance(resume_data_payload.get("resume_data"), dict):
        data_to_use_for_pdf = resume_data_payload["resume_data"]
    elif current_resume_data:
        data_to_use_for_pdf = current_resume_data
    else:
        # If current_resume_data is also None (e.g. server just started and no PUT yet),
        # we could generate a PDF from the default template or raise an error.
        # For now, let's use the default template if nothing else is available.
        data_to_use_for_pdf = resume_builder.get_new_resume_data()
        # Or, alternatively, raise an error if no specific data is available:
        # raise http_exc(404, "No resume data available to generate PDF. Please update resume data first or provide it in the request.")

    if not data_to_use_for_pdf: # Should not happen if default is used above
        raise http_exc(404, "No resume data found to generate PDF.")

    try:
        pdf_bytes = resume_builder.create_resume_pdf_bytes(data_to_use_for_pdf)
        if not pdf_bytes:
            raise http_exc(500, "Failed to generate PDF bytes. Core logic might have encountered an issue.")

        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=resume.pdf"}
        )
    except Exception as e:
        print(f"Error during PDF generation endpoint: {e}")
        raise http_exc(500, f"An unexpected error occurred during PDF generation: {str(e)}")


# --- Main block for running with Uvicorn (optional, for local dev) ---
if __name__ == "__main__":
    import uvicorn
    # This allows running the app with `python backend/main.py`
    # Ensure SLM model is pre-loaded if desired, or it will load on first API call
    print("Attempting to pre-load SLM model...")
    slm_parser.load_slm_model()
    if slm_parser.ner_pipeline:
        print("SLM model loaded successfully for local development.")
    else:
        print("Failed to pre-load SLM model. It will attempt to load on the first API call.")

    uvicorn.run(app, host="0.0.0.0", port=8000)

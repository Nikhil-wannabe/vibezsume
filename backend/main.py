"""
FastAPI application server for the AI Resume Toolkit.

This module defines the main FastAPI application and its API endpoints for various functionalities,
including:
- Resume analysis (text extraction and SLM parsing).
- Job description scraping and analysis.
- Comparison between a resume and a job description.
- Resume building and PDF generation.

It uses in-memory storage for simplicity, suitable for demonstration or single-user scenarios.
For production use, a persistent database would be required for storing user data,
resume versions, and job analysis results.
"""
from fastapi import FastAPI, File, UploadFile, HTTPException, Body
from fastapi.responses import JSONResponse, StreamingResponse
from typing import Dict, Optional, Any
import io

# --- Path Adjustments for Module Imports ---
# This block adjusts the Python system path to allow importing modules
# (core_logic, slm_module) from sibling directories.
# This is common in project structures where the main script is in a subdirectory (e.g., 'backend').
import sys
import os
# Adds the parent directory of the current file's directory (i.e., the project root) to sys.path.
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# --- Core Logic Imports ---
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

# `current_resume_data`: Stores the resume data currently being edited or built.
# Initialized with a default template from resume_builder.
# This is in-memory and will reset if the server restarts.
current_resume_data: Dict[str, Any] = resume_builder.get_new_resume_data()

# `last_analyzed_resume_slm`: Stores the result of the last successful SLM parsing from /resume/analyze.
# Used as a default resume for comparison if not explicitly provided.
# This is in-memory and will reset if the server restarts.
last_analyzed_resume_slm: Optional[Dict[str, Any]] = None

# `last_job_description_text`: Stores the text from the last scraped or submitted job description.
# Used as a default job description for comparison if not explicitly provided.
# This is in-memory and will reset if the server restarts.
last_job_description_text: Optional[str] = None


# --- Error Handling Helper ---
def http_exc(status_code: int, detail: str) -> HTTPException:
    """Helper function to create and return an HTTPException."""
    return HTTPException(status_code=status_code, detail=detail)

# --- API Endpoints ---

# 1. Resume Analysis Endpoint
@app.post("/resume/analyze", tags=["Resume Analysis"])
async def analyze_resume_file(file: UploadFile = File(...)):
    """
    Analyzes a resume file (PDF, DOCX, TXT).

    The endpoint extracts text from the uploaded file, parses it using an SLM
    (Small Language Model) for Named Entity Recognition and structure, and then
    returns the structured data as JSON. The parsed resume is also stored in memory
    as `last_analyzed_resume_slm` for potential use in subsequent job comparison calls.

    - **Request File:**
        - `file`: An uploaded file (types: PDF, DOCX, TXT). The file should be sent
                  as part of a multipart/form-data request.

    - **Successful Response (200 OK):**
        - Returns a JSON object containing the structured resume data. The structure
          is based on `slm_module.parser.EXPECTED_FIELDS` (e.g., name, contact_info,
          skills, experience, education).
          Example:
          ```json
          {
            "name": "John Doe",
            "contact_info": {"email": "john.doe@email.com", ...},
            "skills": ["Python", "FastAPI"],
            ...
          }
          ```

    - **Possible Status Codes:**
        - `200 OK`: Resume analyzed successfully.
        - `400 Bad Request`: No file name provided or file content is empty.
        - `422 Unprocessable Entity`: Could not extract text from the file (e.g., unsupported
          format, corrupt file, encrypted PDF).
        - `500 Internal Server Error`: An unexpected error occurred during analysis (e.g.,
          SLM processing error not caught by specific checks).
        - `503 Service Unavailable`: The SLM model is not available or failed to load.
    """
    global last_analyzed_resume_slm # Allow modification of the global variable

    # Basic file validation
    if not file.filename:
        raise http_exc(400, "No file name provided with the upload.")

    file_content = await file.read() # Read file content into memory
    if not file_content:
        raise http_exc(400, "Uploaded file content is empty.")

    try:
        # Extract text from the file using the core logic module.
        extracted_text = text_extraction.extract_text_from_file(file.filename, file_content)
        if not extracted_text:
            # This can happen for unsupported formats or if the file is corrupt/empty after initial checks.
            raise http_exc(422, f"Could not extract text from file: '{file.filename}'. Unsupported format, corrupt file, or empty text content.")

        # Ensure SLM model is loaded (it loads on first call within the slm_parser module if not already loaded).
        slm_parser.load_slm_model()
        if not slm_parser.ner_pipeline: # Check if the NER pipeline (core of SLM) is available.
             raise http_exc(503, "The SLM model (NER pipeline) is not available. Please try again later or contact support.")

        # Parse the extracted text using the SLM.
        parsed_data = slm_parser.parse_resume_text_with_slm(extracted_text)

        # Check for a specific error message that parse_resume_text_with_slm might return.
        if parsed_data.get("name") == "ERROR: SLM Model Not Loaded":
            raise http_exc(503, "SLM model failed to load properly during the parsing process.")
        if not parsed_data.get("name") and not parsed_data.get("skills"): # Heuristic: if no key info, parsing might have issues
             print(f"Warning: Parsed data for {file.filename} lacks common fields like name or skills.")


        last_analyzed_resume_slm = parsed_data # Store for potential use by Job Analyzer
        return JSONResponse(content=parsed_data)

    except HTTPException as e: # Re-raise HTTPExceptions to ensure FastAPI handles them.
        raise e
    except Exception as e:
        # Log the full error for server-side debugging.
        print(f"Unexpected error during resume analysis for file '{file.filename}': {e}")
        # Return a generic 500 error to the client.
        raise http_exc(500, f"An unexpected error occurred during resume analysis. Details: {str(e)}")


# --- Job Analysis Endpoints ---

@app.post("/job/scrape-url", tags=["Job Analysis"])
async def scrape_job_url_endpoint(payload: Dict[str, str] = Body(..., example={"url": "https://example.com/job/123"})):
    """
    Scrapes a job description from a given URL.

    This endpoint accepts a URL in the request body, attempts to scrape the main textual
    content of the job description from that URL, stores it in memory as
    `last_job_description_text`, and returns the scraped text.

    - **Request Body:**
        - A JSON object with a "url" key.
          Example:
          ```json
          {
            "url": "https://www.linkedin.com/jobs/view/some-job-id/"
          }
          ```

    - **Successful Response (200 OK):**
        - Returns a JSON object containing the original URL and the scraped text.
          Example:
          ```json
          {
            "url": "https://www.linkedin.com/jobs/view/some-job-id/",
            "scraped_text": "Full job description text..."
          }
          ```

    - **Possible Status Codes:**
        - `200 OK`: Job description scraped successfully.
        - `400 Bad Request`: The "url" field is missing from the payload.
        - `422 Unprocessable Entity`: Could not scrape significant content from the URL
          (e.g., URL is invalid, site structure not recognized, or no text found).
        - `500 Internal Server Error`: An unexpected error occurred during scraping.
    """
    global last_job_description_text # Allow modification of the global variable
    url = payload.get("url")
    if not url or not url.strip(): # Also check if URL is just whitespace
        raise http_exc(400, "A non-empty URL must be provided in the request payload.")

    try:
        scraped_text = job_analyzer.scrape_job_description_from_url(url)
        if not scraped_text:
            # This could be due to network errors handled by the scraper, or no text found.
            raise http_exc(422, f"Could not scrape or find significant textual content at the provided URL: {url}. The site might be inaccessible, require JavaScript, or have an unsupported layout.")

        last_job_description_text = scraped_text # Store the successfully scraped text.
        return JSONResponse(content={"url": url, "scraped_text": scraped_text})
    except HTTPException as e: # Re-raise HTTPExceptions
        raise e
    except Exception as e:
        print(f"Unexpected error during job scraping for URL '{url}': {e}")
        raise http_exc(500, f"An unexpected error occurred during job scraping. Details: {str(e)}")

@app.post("/job/analyze-text", tags=["Job Analysis"])
async def analyze_job_text_endpoint(payload: Dict[str, str] = Body(..., example={"text": "Software Engineer job description text..."})):
    """
    Accepts and stores raw job description text provided in the request body.

    This endpoint is an alternative to scraping. It allows a user to directly submit
    job description text. The text is stored in memory as `last_job_description_text`.
    It can optionally return a preview or basic analysis (like keywords), but currently
    returns a snippet of the stored text.

    - **Request Body:**
        - A JSON object with a "text" key containing the job description.
          Example:
          ```json
          {
            "text": "We are looking for a skilled Software Engineer..."
          }
          ```

    - **Successful Response (200 OK):**
        - Returns a JSON confirmation message and a snippet of the received text.
          Example:
          ```json
          {
            "message": "Job text received and stored successfully.",
            "text_snippet": "We are looking for a skilled Software Engineer..."
          }
          ```

    - **Possible Status Codes:**
        - `200 OK`: Job description text received and stored.
        - `400 Bad Request`: The "text" field is missing or empty in the payload.
        - `500 Internal Server Error`: An unexpected error occurred. (Less likely for this simple endpoint)
    """
    global last_job_description_text # Allow modification of the global variable
    text = payload.get("text")
    if not text or not text.strip():
        raise http_exc(400, "Job description text must be provided and cannot be empty in the payload.")

    last_job_description_text = text.strip()
    # Optionally, perform some immediate analysis like keyword extraction for a richer response.
    # keywords = job_analyzer.extract_keywords_from_text(last_job_description_text)
    # return JSONResponse(content={"message": "Job text received and stored.", "keywords_preview": keywords[:20]})
    return JSONResponse(content={"message": "Job text received and stored successfully.", "text_snippet": last_job_description_text[:200] + "..." if len(last_job_description_text) > 200 else last_job_description_text})


@app.post("/job/compare-resume", tags=["Job Analysis"])
async def compare_resume_with_job_endpoint(payload: Optional[Dict[str, Any]] = Body(None, example={"job_description_text": "Optional job text...", "resume_data": {"name": "Jane", "skills": ["Python"]}})):
    """
    Compares resume data with job description text to find matches and gaps.

    This endpoint uses either previously analyzed/stored resume data and job description text
    or accepts them directly in the payload. It then performs a comparison, highlighting
    matching skills and suggesting keywords from the job description that might be missing
    from the resume.

    - **Request Body (Optional):**
        - A JSON object that can contain:
            - `job_description_text` (str, optional): Full text of the job description.
              If not provided, uses `last_job_description_text`.
            - `resume_data` (dict, optional): Structured resume data (e.g., from SLM parsing).
              If not provided, uses `last_analyzed_resume_slm`.
          Example:
          ```json
          {
            "job_description_text": "Looking for a Python developer with FastAPI experience...",
            "resume_data": {
              "name": "Jane Doe",
              "skills": ["Python", "SQL"],
              ...
            }
          }
          ```
          If the payload is `null` or an empty object, the endpoint relies on stored data.

    - **Successful Response (200 OK):**
        - Returns a JSON object with comparison results:
            - `matching_skills` (List[str]): Skills from the resume found in the job description.
            - `missing_skills_from_jd` (List[str]): Keywords from JD not obviously in resume skills.
            - `job_summary_keywords` (List[str]): Keywords extracted from the job description.
            - `match_score_heuristic` (float): A simple heuristic score of the match.
          Example:
          ```json
          {
            "matching_skills": ["Python"],
            "missing_skills_from_jd": ["fastapi", "api-design"],
            "job_summary_keywords": ["python", "fastapi", "developer", "api-design"],
            "match_score_heuristic": 65.7
          }
          ```

    - **Possible Status Codes:**
        - `200 OK`: Comparison performed successfully.
        - `400 Bad Request`: Necessary data (resume or job description) is missing and not
          available from previous steps, or provided data is in an invalid format.
        - `500 Internal Server Error`: An unexpected error occurred during the comparison logic.
    """
    global last_analyzed_resume_slm, last_job_description_text # Access global state

    current_job_text: Optional[str] = None
    # Prioritize job text from payload, then fall back to stored text.
    if payload and payload.get("job_description_text"):
        current_job_text = payload["job_description_text"]
        if not isinstance(current_job_text, str) or not current_job_text.strip(): # Validate if provided
             raise http_exc(400, "Provided 'job_description_text' must be a non-empty string.")
    elif last_job_description_text:
        current_job_text = last_job_description_text
    else:
        # If no job text is available at all.
        raise http_exc(400, "No job description text available. Please provide it in the payload or use '/job/analyze-text' or '/job/scrape-url' first.")

    current_resume_data: Optional[Dict[str, Any]] = None
    # Prioritize resume data from payload, then fall back to stored data.
    if payload and payload.get("resume_data"):
        current_resume_data = payload["resume_data"]
        if not isinstance(current_resume_data, dict) or not current_resume_data: # Validate if provided
            raise http_exc(400, "Provided 'resume_data' must be a non-empty JSON object.")
    elif last_analyzed_resume_slm:
        current_resume_data = last_analyzed_resume_slm
    else:
        # If no resume data is available at all.
        raise http_exc(400, "No resume data available for comparison. Please provide it or analyze a resume first using '/resume/analyze'.")

    # Final check on types after potential fallback
    if not isinstance(current_resume_data, dict) or not isinstance(current_job_text, str):
         raise http_exc(400, "Internal error: Invalid format for resume data or job text after processing.") # Should be caught by earlier checks

    try:
        # Perform the comparison using the core logic module.
        comparison_results = job_analyzer.compare_resume_to_job_description(current_resume_data, current_job_text)
        return JSONResponse(content=comparison_results)
    except Exception as e:
        print(f"Error during resume-job comparison: {e}")
        raise http_exc(500, f"An unexpected error occurred during comparison. Details: {str(e)}")


# --- Resume Builder Endpoints ---

@app.get("/builder/resume", tags=["Resume Builder"])
async def get_resume_builder_data_endpoint():
    """
    Retrieves the current resume data being edited in the resume builder.

    This endpoint returns the full JSON object representing the resume that is
    currently stored in memory for editing.

    - **Successful Response (200 OK):**
        - Returns the JSON object of the current resume data. The structure follows
          `resume_builder.DEFAULT_RESUME_STRUCTURE`.
          Example:
          ```json
          {
            "name": "Jane Doe",
            "contact_info": {...},
            "skills": [...],
            ...
          }
          ```

    - **Possible Status Codes:**
        - `200 OK`: Successfully retrieved current resume data.
        - `500 Internal Server Error`: If `current_resume_data` is unexpectedly unavailable (though unlikely as it's initialized).
    """
    global current_resume_data # Access global state
    if current_resume_data is None:
        # This case should ideally not be reached if current_resume_data is always initialized.
        # However, as a fallback, re-initialize.
        print("Warning: current_resume_data was None, re-initializing with default.")
        current_resume_data = resume_builder.get_new_resume_data()
    return JSONResponse(content=current_resume_data)

@app.put("/builder/resume", tags=["Resume Builder"])
async def update_resume_builder_data_endpoint(new_resume_data: Dict[str, Any] = Body(..., example=resume_builder.DEFAULT_RESUME_STRUCTURE)):
    """
    Updates the current resume data in the builder with the provided JSON payload.

    The entire resume data stored in memory is replaced by the payload.
    It's recommended that the payload structure matches `resume_builder.DEFAULT_RESUME_STRUCTURE`.

    - **Request Body:**
        - A JSON object representing the full resume data.
          Example:
          ```json
          {
            "name": "Jane Doe Updated",
            "contact_info": {"email": "jane.doe.new@example.com", ...},
            "skills": ["Python", "FastAPI", "SQL"],
            ...
          }
          ```

    - **Successful Response (200 OK):**
        - Returns a JSON confirmation message and a preview of the updated name.
          Example:
          ```json
          {
            "message": "Resume data updated successfully.",
            "updated_data_preview": {"name": "Jane Doe Updated"}
          }
          ```

    - **Possible Status Codes:**
        - `200 OK`: Resume data updated successfully.
        - `400 Bad Request`: Invalid resume data payload (e.g., not a JSON object or empty).
        - `422 Unprocessable Entity`: Payload is not a valid JSON object (though FastAPI usually handles this).
    """
    global current_resume_data # Allow modification of the global variable

    if not new_resume_data or not isinstance(new_resume_data, dict): # Basic validation
        raise http_exc(400, "Invalid resume data payload. Must be a non-empty JSON object.")

    # Optional: Add more specific validation against DEFAULT_RESUME_STRUCTURE keys/types.
    # This would involve checking for essential keys, correct data types for values, etc.
    # Example: if "name" not in new_resume_data or not isinstance(new_resume_data.get("skills"), list):
    # raise http_exc(422, "Resume data is missing required fields or has incorrect types.")

    current_resume_data = new_resume_data # Replace the in-memory data.
    return JSONResponse(content={"message": "Resume data updated successfully.", "updated_data_preview": {"name": current_resume_data.get("name", "N/A")}})

@app.post("/builder/resume/download-pdf", tags=["Resume Builder"])
async def download_resume_as_pdf_endpoint(resume_data_payload: Optional[Dict[str, Any]] = Body(None, description="Optional: Provide resume data to generate PDF from. If null, uses current server-side resume data.", example={"resume_data": resume_builder.DEFAULT_RESUME_STRUCTURE})):
    """
    Generates and returns a PDF version of the resume.

    This endpoint can either use the resume data currently stored in memory (if no payload is sent)
    or generate a PDF from `resume_data` provided directly in the request body.
    The generated PDF is returned as a file stream.

    - **Request Body (Optional):**
        - A JSON object that can contain:
            - `resume_data` (dict, optional): The full resume data to use for PDF generation.
              If this key is present and valid, it will be used. Otherwise, the endpoint
              falls back to `current_resume_data` on the server.
          Example:
          ```json
          {
            "resume_data": {
              "name": "PDF Specific Name",
              "skills": ["PDF Generation", "ReportLab"],
              ... // complete resume structure
            }
          }
          ```
          If body is `null` or `{}`, server-side `current_resume_data` is used.

    - **Successful Response (200 OK):**
        - Returns the generated PDF as an application/pdf stream.
        - The `Content-Disposition` header is set to "attachment; filename=resume.pdf",
          prompting a download in the browser.

    - **Possible Status Codes:**
        - `200 OK`: PDF generated and streamed successfully.
        - `404 Not Found`: No resume data available (neither in payload nor on server)
          and no default could be reasonably used.
        - `422 Unprocessable Entity`: If `resume_data` is provided in payload but is invalid.
        - `500 Internal Server Error`: Failed to generate PDF bytes due to an issue in the
          core PDF generation logic or other unexpected error.
    """
    global current_resume_data # Access global state

    data_to_use_for_pdf: Optional[Dict[str, Any]] = None

    # Determine which data source to use for PDF generation.
    if resume_data_payload and isinstance(resume_data_payload.get("resume_data"), dict):
        # Use data from payload if "resume_data" key exists and is a dictionary.
        data_to_use_for_pdf = resume_data_payload["resume_data"]
        if not data_to_use_for_pdf: # Check if the dict is empty
             raise http_exc(422, "Provided 'resume_data' in payload is empty.")
    elif current_resume_data:
        # Fallback to globally stored resume data if no valid payload data.
        data_to_use_for_pdf = current_resume_data
    else:
        # As a last resort, if no data is available at all (e.g., server just started, no updates yet).
        # Using a default template ensures the endpoint can always produce a PDF.
        print("Warning: No specific resume data available; generating PDF from default template.")
        data_to_use_for_pdf = resume_builder.get_new_resume_data()

    if not data_to_use_for_pdf: # Should not be reached if default is used, but as a safeguard.
        raise http_exc(404, "Critical error: No resume data available to generate PDF even after fallbacks.")

    try:
        # Generate PDF bytes using the core logic module.
        pdf_bytes = resume_builder.create_resume_pdf_bytes(data_to_use_for_pdf)
        if not pdf_bytes:
            # This indicates an error within the create_resume_pdf_bytes function.
            raise http_exc(500, "Failed to generate PDF bytes. The PDF generation logic might have encountered an issue or the data was unsuitable.")

        # Stream the PDF bytes as a response.
        return StreamingResponse(
            io.BytesIO(pdf_bytes), # Create a file-like object from bytes for streaming.
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=resume.pdf"} # Prompts download.
        )
    except Exception as e:
        print(f"Unexpected error during PDF generation endpoint: {e}")
        raise http_exc(500, f"An unexpected error occurred during PDF generation. Details: {str(e)}")


# --- Main block for running with Uvicorn (optional, for local development) ---
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

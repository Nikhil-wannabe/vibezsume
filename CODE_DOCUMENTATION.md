# Code Documentation

This document provides a summary of functions and their purposes based on docstrings from the key Python modules in the AI Resume Toolkit. For full details, please refer to the source code.

## Module: `slm_module.parser`

This module is responsible for parsing raw resume text into a structured format using an SLM (NER model).

### `load_slm_model(model_name="dbmdz/bert-large-cased-finetuned-conll03-english")`
- **Purpose**: Loads the Named Entity Recognition (NER) pipeline model from Hugging Face Transformers. Initializes `ner_pipeline` if not already loaded.
- **Args**: `model_name` (str): Name of the NER model.
- **Returns**: `transformers.pipelines.Pipeline` or `None`: The loaded NER pipeline or None on failure.

### `initialize_parsed_data()` -> `dict`
- **Purpose**: Creates and returns a deep copy of the `EXPECTED_FIELDS` dictionary, providing a fresh structure for parsing.
- **Returns**: `dict`: A new dictionary structured according to `EXPECTED_FIELDS`.

### `get_section_text(full_text: str, section_keywords: list)` -> `str | None`
- **Purpose**: Extracts text content of a specific section (e.g., "Experience") from the full resume text using regex to identify section boundaries.
- **Args**:
    - `full_text` (str): The entire resume text.
    - `section_keywords` (list): Keywords identifying the start of the desired section.
- **Returns**: `str` or `None`: Extracted section text or None if not found.

### `extract_entities_from_text(text: str, entity_labels: list)` -> `list`
- **Purpose**: Extracts entities (like Person, Organization) of specified types from text using the loaded NER model.
- **Args**:
    - `text` (str): Text to process.
    - `entity_labels` (list): Entity labels to extract (e.g., `['PER', 'ORG']`).
- **Returns**: `list`: List of extracted entity words (strings).

### `extract_dates(text: str, patterns: list)` -> `str | None`
- **Purpose**: Extracts date-like strings from text using a list of predefined regex patterns.
- **Args**:
    - `text` (str): Text to search for dates.
    - `patterns` (list): Compiled regex objects for date matching.
- **Returns**: `str` or `None`: The first or most relevant matched date string, or None.

### `parse_resume_text_with_slm(resume_text: str)` -> `dict`
- **Purpose**: Parses the entire resume text to extract structured information using regex and the SLM (NER model).
- **Args**: `resume_text` (str): Full text of the resume.
- **Returns**: `dict`: Dictionary with parsed information, structured by `EXPECTED_FIELDS`.

## Module: `core_logic.text_extraction`

This module provides utilities for extracting plain text from various file formats.

### `extract_text_from_pdf(file_content: bytes)` -> `Optional[str]`
- **Purpose**: Extracts text from PDF file byte content. Does not perform OCR. Handles encrypted PDFs by returning None.
- **Args**: `file_content` (bytes): Byte content of the PDF.
- **Returns**: `Optional[str]`: Extracted text or None on failure.

### `extract_text_from_docx(file_content: bytes)` -> `Optional[str]`
- **Purpose**: Extracts text from DOCX file byte content.
- **Args**: `file_content` (bytes): Byte content of the DOCX.
- **Returns**: `Optional[str]`: Extracted text or None on failure.

### `extract_text_from_file(file_name: str, file_content: bytes)` -> `Optional[str]`
- **Purpose**: Extracts text from a file (PDF, DOCX, TXT) based on its extension.
- **Args**:
    - `file_name` (str): Name of the file (to determine type).
    - `file_content` (bytes): Byte content of the file.
- **Returns**: `Optional[str]`: Extracted text or None on failure/unsupported format.

## Module: `core_logic.job_analyzer`

This module handles scraping, parsing, and analyzing job descriptions, and comparing them to resumes.

### `scrape_job_description_from_url(url: str)` -> `Optional[str]`
- **Purpose**: Scrapes main textual content from a job description URL. Basic scraper with limitations.
- **Args**: `url` (str): URL of the job description.
- **Returns**: `Optional[str]`: Scraped text or None on failure.

### `extract_keywords_from_text(text: str, min_keyword_length: int = 3, top_n: int = 50)` -> `List[str]`
- **Purpose**: Simple heuristic keyword extraction from text based on frequency, after removing stop words.
- **Args**:
    - `text` (str): Text to extract keywords from.
    - `min_keyword_length` (int): Minimum length of a keyword.
    - `top_n` (int): Number of most frequent keywords to return.
- **Returns**: `List[str]`: List of extracted keywords.

### `compare_resume_to_job_description(parsed_resume_data: Dict[str, Any], job_description_text: str)` -> `Dict[str, Any]`
- **Purpose**: Compares extracted resume data (skills) with job description text (keywords).
- **Args**:
    - `parsed_resume_data` (Dict): Structured resume data.
    - `job_description_text` (str): Text of the job description.
- **Returns**: `Dict`: Contains `matching_skills`, `missing_skills_from_jd`, `job_summary_keywords`, and `match_score_heuristic`.

## Module: `core_logic.resume_builder`

This module is responsible for generating PDF resumes from structured data.

### `get_new_resume_data()` -> `Dict[str, Any]`
- **Purpose**: Returns a deep copy of `DEFAULT_RESUME_STRUCTURE` for initializing new resume data.
- **Returns**: `Dict[str, Any]`: A blank resume structure.

### `create_resume_pdf_bytes(resume_data: Dict[str, Any])` -> `Optional[bytes]`
- **Purpose**: Generates a PDF resume from structured data using ReportLab.
- **Args**: `resume_data` (Dict): Resume information conforming to `DEFAULT_RESUME_STRUCTURE`.
- **Returns**: `Optional[bytes]`: Generated PDF content as bytes, or None on error.

## Module: `backend.main` (API Endpoints)

This module defines the FastAPI application and its API endpoints. Docstrings below summarize the primary function of each endpoint.

### `analyze_resume_file(file: UploadFile)`
- **Endpoint**: `POST /resume/analyze`
- **Purpose**: Analyzes an uploaded resume file (PDF, DOCX, TXT), extracts text, parses with SLM, and returns structured JSON.

### `scrape_job_url_endpoint(payload: Dict[str, str])`
- **Endpoint**: `POST /job/scrape-url`
- **Purpose**: Scrapes a job description from a URL provided in the payload.

### `analyze_job_text_endpoint(payload: Dict[str, str])`
- **Endpoint**: `POST /job/analyze-text`
- **Purpose**: Accepts and stores raw job description text from the payload.

### `compare_resume_with_job_endpoint(payload: Optional[Dict[str, Any]])`
- **Endpoint**: `POST /job/compare-resume`
- **Purpose**: Compares resume data (stored or from payload) with job description text (stored or from payload).

### `get_resume_builder_data_endpoint()`
- **Endpoint**: `GET /builder/resume`
- **Purpose**: Retrieves the current resume data being edited in the builder.

### `update_resume_builder_data_endpoint(new_resume_data: Dict[str, Any])`
- **Endpoint**: `PUT /builder/resume`
- **Purpose**: Updates the current resume data in the builder with the provided JSON payload.

### `download_resume_as_pdf_endpoint(resume_data_payload: Optional[Dict[str, Any]])`
- **Endpoint**: `POST /builder/resume/download-pdf`
- **Purpose**: Generates and returns a PDF version of the resume (using stored data or data from payload).
```

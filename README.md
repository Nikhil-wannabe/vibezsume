# AI Resume Toolkit

## Overview

The AI Resume Toolkit is a comprehensive application designed to assist users in managing and optimizing their resumes. It offers functionalities for parsing resume documents, analyzing job descriptions, comparing resumes against these descriptions to identify skill gaps and matches, and building/editing resumes with an option to download them as PDFs.

## Features

*   **Resume Parsing**: Extracts text and structure from uploaded resume files (PDF, DOCX, TXT) using an SLM (Small Language Model).
*   **Job Description Analysis**: Scrapes job descriptions from URLs or accepts raw text input.
*   **Resume-to-Job Comparison**: Highlights matching skills, identifies potential skill gaps, and provides a heuristic match score.
*   **Resume Building**: Allows users to create or modify resume data through an API.
*   **PDF Download**: Generates and downloads the resume in PDF format.

## Architecture

The toolkit is structured into a frontend application, a backend API, core processing logic modules, and an SLM module for parsing.

### Frontend (`frontend/`)

*   A React-based single-page application (SPA).
*   Provides the user interface for interacting with the toolkit's features.
*   Communicates with the backend via RESTful API calls using `axios`.
*   (Further details about specific UI components are in `frontend/src/components/`)

### Backend (`backend/`)

*   A FastAPI application (`backend/main.py`) serving RESTful APIs.
*   Handles business logic orchestration, data validation, and serves as the interface to the core logic modules.
*   Uses in-memory storage for simplicity (not suitable for production multi-user scenarios).

### Core Logic (`core_logic/`)

Contains Python modules responsible for specific processing tasks:

*   **`text_extraction.py`**: Utilities for extracting plain text from PDF, DOCX, and TXT files using libraries like PyPDF2 and python-docx.
*   **`job_analyzer.py`**: Logic for:
    *   Scraping job descriptions from URLs (using Requests and BeautifulSoup).
    *   Extracting keywords from text.
    *   Comparing resume skills with job description keywords.
*   **`resume_builder.py`**:
    *   Defines a standard structure for resume data.
    *   Generates PDF resumes from this structured data using the ReportLab library.

### SLM Module (`slm_module/`)

*   **`parser.py`**:
    *   Utilizes a pre-trained Named Entity Recognition (NER) model from the Hugging Face Transformers library (e.g., `dbmdz/bert-large-cased-finetuned-conll03-english`).
    *   Parses raw resume text into a structured dictionary format, identifying entities like name, contact information, skills, education sections, and experience sections.

## Modules & Functionality Details

### `slm_module/parser.py`
This module is central to understanding uploaded resumes. It takes raw text extracted from a resume document and attempts to identify and categorize different pieces of information into a predefined schema. This schema includes personal details, contact information, a summary, lists of skills, educational history, and work experience. The accuracy of this parsing depends on the clarity of the resume's formatting and the capabilities of the underlying NER model.

### `core_logic/text_extraction.py`
Provides the foundational step of getting usable text from various document formats. It supports PDF, DOCX, and TXT files. For PDFs, it relies on text embedded in the PDF and does not perform Optical Character Recognition (OCR) on scanned images.

### `core_logic/job_analyzer.py`
This module helps in understanding job requirements. It can fetch job descriptions from web pages (with limitations, as web scraping can be complex) or work with user-supplied text. It then extracts keywords to identify key requirements and skills. The comparison function provides a basic analysis of how well a resume's skills align with these keywords.

### `core_logic/resume_builder.py`
Facilitates the creation and formatting of resumes into a professional PDF document. It uses a predefined template structure (`DEFAULT_RESUME_STRUCTURE`) which the backend API uses to manage resume data. ReportLab is used for fine-grained control over the PDF layout.

### `backend/main.py`
The FastAPI application orchestrates all these functionalities through a set of API endpoints. It handles incoming requests, validates data, calls the appropriate core logic or SLM functions, and manages a simple in-memory store for data like the current resume being built or the last analyzed resume/job description.

## API Endpoints

The backend provides the following RESTful API endpoints:

### Resume Analysis

*   **`POST /resume/analyze`**
    *   **Description**: Uploads a resume file (PDF, DOCX, TXT), extracts text, parses it using the SLM, and returns structured JSON data.
    *   **Request**: `FormData` with `file` (the resume file).
    *   **Response**: JSON object of the parsed resume.
    *   **Example `curl`**:
        ```bash
        curl -X POST -F "file=@/path/to/your/resume.pdf" http://localhost:8000/resume/analyze
        ```

### Job Analysis

*   **`POST /job/scrape-url`**
    *   **Description**: Scrapes a job description from a given URL.
    *   **Request Body (JSON)**: `{"url": "https://example.com/job/123"}`
    *   **Response**: JSON with `url` and `scraped_text`.
    *   **Example `curl`**:
        ```bash
        curl -X POST -H "Content-Type: application/json" -d '{"url": "https://example.com/job/123"}' http://localhost:8000/job/scrape-url
        ```

*   **`POST /job/analyze-text`**
    *   **Description**: Accepts raw job description text.
    *   **Request Body (JSON)**: `{"text": "Job description content..."}`
    *   **Response**: JSON with a confirmation message and `text_snippet`.
    *   **Example `curl`**:
        ```bash
        curl -X POST -H "Content-Type: application/json" -d '{"text": "Detailed job description here..."}' http://localhost:8000/job/analyze-text
        ```

*   **`POST /job/compare-resume`**
    *   **Description**: Compares resume data (from previous analysis or payload) with job description text (from previous analysis or payload).
    *   **Request Body (JSON, optional)**:
        ```json
        {
          "job_description_text": "Optional job text...",
          "resume_data": {"name": "Jane", "skills": ["Python"]}
        }
        ```
    *   **Response**: JSON with `matching_skills`, `missing_skills_from_jd`, `job_summary_keywords`, `match_score_heuristic`.

### Resume Builder

*   **`GET /builder/resume`**
    *   **Description**: Retrieves the current resume data being edited.
    *   **Response**: JSON object of the current resume.

*   **`PUT /builder/resume`**
    *   **Description**: Updates the current resume data with the provided payload.
    *   **Request Body (JSON)**: Full resume data object.
    *   **Response**: JSON confirmation.

*   **`POST /builder/resume/download-pdf`**
    *   **Description**: Generates a PDF of the resume (from current data or payload).
    *   **Request Body (JSON, optional)**: `{"resume_data": {...}}`
    *   **Response**: PDF file stream (`application/pdf`).

## Setup and Installation

### Prerequisites

*   Python 3.8+ and `pip`
*   Node.js and `npm` (for frontend development)

### Backend Setup

1.  **Clone the repository** (if you haven't already):
    ```bash
    git clone <repository-url>
    cd <repository-root-directory>
    ```

2.  **Create and activate a virtual environment** (recommended):
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install Python dependencies**:
    The backend dependencies include `transformers` and `torch`. `torch` can be a large download. If you encounter issues or have a specific hardware setup (e.g., CUDA GPU), you might want to install PyTorch separately by following instructions on the [official PyTorch website](https://pytorch.org/get-started/locally/) before running the command below.
    ```bash
    pip install -r backend/requirements.txt
    ```
    (`backend/requirements.txt` includes: `fastapi`, `uvicorn[standard]`, `python-multipart`, `transformers`, `torch`, `PyPDF2`, `python-docx`, `requests`, `beautifulsoup4`, `reportlab`)

4.  **Run the backend server**:
    The SLM model will be downloaded on the first run if not already cached by Transformers. This can take some time.
    ```bash
    python backend/main.py
    ```
    Alternatively, using Uvicorn for development with auto-reload:
    ```bash
    uvicorn backend.main:app --reload --port 8000
    ```
    The API will typically be available at `http://localhost:8000`.

### Frontend Setup

1.  **Navigate to the frontend directory**:
    ```bash
    cd frontend
    ```

2.  **Install Node.js dependencies**:
    ```bash
    npm install
    ```
    (`frontend/package.json` includes: `react`, `react-dom`, `react-scripts`, `axios`)

3.  **Run the frontend development server**:
    ```bash
    npm start
    ```
    This will usually open the application in your default web browser at `http://localhost:3000`. The frontend is configured to proxy API requests to the backend (typically `http://localhost:8000` if that's where the backend is running).

## Basic Usage Example (API)

1.  **Analyze a Resume**:
    Send a POST request to `/resume/analyze` with your resume file.
    ```bash
    curl -X POST -F "file=@/path/to/your/resume.pdf" http://localhost:8000/resume/analyze > resume_output.json
    ```
    This saves the structured resume data to `resume_output.json`.

2.  **Provide Job Description**:
    Either scrape it via URL:
    ```bash
    curl -X POST -H "Content-Type: application/json" -d '{"url": "URL_OF_JOB_POSTING"}' http://localhost:8000/job/scrape-url > jd_output.json
    ```
    Or submit text directly:
    ```bash
    curl -X POST -H "Content-Type: application/json" -d '{"text": "Full job description text here..."}' http://localhost:8000/job/analyze-text
    ```

3.  **Compare Resume to Job**:
    This will use the resume and JD from the previous steps (stored in server memory).
    ```bash
    curl -X POST http://localhost:8000/job/compare-resume > comparison_results.json
    ```
    Alternatively, provide data directly in the payload.

4.  **Build/Edit Resume Data (using GET/PUT on `/builder/resume`) and Download PDF**:
    Use the GET endpoint to fetch current resume data, modify it, then PUT it back.
    Finally, download the PDF:
    ```bash
    curl -X POST http://localhost:8000/builder/resume/download-pdf -o my_resume.pdf
    ```
    (This downloads the PDF based on data stored on the server. You can also POST specific resume data to this endpoint for PDF generation).
```

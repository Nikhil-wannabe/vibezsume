# Vibezsume - Resume Analysis and Builder

A web application for analyzing resumes, matching them against job descriptions, and building professional resumes.

## Features

- **Resume Analysis**: Upload your resume (PDF, DOCX) and extract key information
- **Job Description Analysis**: Analyze job descriptions to identify required and preferred skills
- **Resume-Job Matching**: Compare your resume against job descriptions to see how well you match
- **Resume Builder**: Create a professional resume with a step-by-step form

## Setup and Installation

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Download spaCy model: `python -m spacy download en_core_web_sm`
4. Run the application: `uvicorn app.main:app --reload`
5. Open your browser at http://localhost:8000

## Tech Stack

- Backend: FastAPI, spaCy, PyMuPDF
- Frontend: HTML, CSS, JavaScript
- Text Processing: Regular expressions, NLP

## Project Structure

- `/app`: Backend code
  - `/models`: Data models
  - `/routers`: API endpoints
  - `/services`: Business logic and services
  - `/data`: Application data
- `/static`: Frontend assets (CSS, JavaScript)
- `index.html`: Main application page

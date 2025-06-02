# Frontend Notes

## Overview

The frontend is a React-based Single Page Application (SPA) designed to provide a user interface for the AI Resume Toolkit. It interacts with the backend FastAPI services to perform operations like resume analysis, job comparison, and resume building.

## Structure (`frontend/src/`)

*   **`App.js`**: The main application component. It handles basic page navigation (Resume Analyzer, Job Analyzer, Resume Builder, Settings) using internal state and renders the appropriate page component.
*   **`App.css`**: Global styles for the application.
*   **`components/`**: This directory houses the primary UI components for each feature page:
    *   `ResumeAnalyzerPage.js`: UI for uploading resumes and viewing analysis results.
    *   `JobAnalyzerPage.js`: UI for inputting job descriptions (URL or text) and viewing comparison results.
    *   `ResumeBuilderPage.js`: UI for creating and editing resume data.
    *   Each component typically has its own CSS file (e.g., `ResumeAnalyzerPage.css`).
*   **`services/`**: Contains modules for external communication.
    *   `api.js`: A dedicated module for all backend API interactions, using `axios`. It centralizes the API call logic.

## API Interaction (`services/api.js`)

The `api.js` module provides functions that map to the backend REST API endpoints. The `API_BASE_URL` is configurable via `process.env.REACT_APP_API_BASE_URL` and defaults to `http://localhost:8000`.

Key functions include:
*   `analyzeResume(formData)`: `POST /resume/analyze`
*   `scrapeJobUrl(url)`: `POST /job/scrape-url`
*   `analyzeJobText(text)`: `POST /job/analyze-text`
*   `compareResumeWithJob(jobDescriptionText?, resumeData?)`: `POST /job/compare-resume`
*   `getResumeData()`: `GET /builder/resume`
*   `updateResumeData(resumeData)`: `PUT /builder/resume`
*   `downloadResumePdf(resumeData?)`: `POST /builder/resume/download-pdf` (handles blob response for file download)

## State Management

Currently, `App.js` uses simple React state (`useState`) for page navigation. More complex state management (like Context API or Redux) might be needed for larger features or shared state between components, but is not explicitly present in the reviewed files.

## Running the Frontend

Refer to the main project `README.md` for instructions on installing dependencies (`npm install`) and running the development server (`npm start`).

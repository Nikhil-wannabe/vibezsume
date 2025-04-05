Vibezsume - Resume Analysis and Builder
A modern web application for analyzing resumes, matching them against job descriptions, and building professional resumes with AI-powered insights.

Overview
Vibezsume helps job seekers create optimized resumes by:

Analyzing existing resumes to extract key information
Matching skills against job descriptions
Providing recommendations to improve job match scores
Building professional resumes with a user-friendly interface
Features
Resume Analyzer: Upload and analyze existing resumes (PDF, DOCX)
Job Description Analysis: Extract key requirements from job postings
Resume-Job Matching: Calculate match scores and identify skill gaps
Resume Builder: Create professional resumes with an easy-to-use form
PDF Export: Generate polished resume documents
Getting Started
Prerequisites
Python 3.8+ (Python 3.13 compatible with Flask version)
Web browser (Chrome, Firefox, Edge recommended)
Installation
Clone the repository:

Install dependencies:

Run the application:

Open your browser and navigate to:

Usage
Resume Analysis
Click on "Resume Analyzer" in the navigation
Upload your existing resume (PDF or DOCX)
Review the extracted information and skills
Compare against job descriptions
Job Description Analysis
Click on "Job Analysis" in the navigation
Paste a job description or provide a URL
View required and preferred skills
Compare with your resume to see match score
Resume Building
Click on "Resume Builder" in the navigation
Fill out the multi-step form with your information
Review and edit the generated resume
Download as PDF
Technical Details
Architecture
Frontend: HTML, CSS, JavaScript
Backend:
FastAPI (standard version)
Flask (Python 3.13 compatible version)
PDF Processing: PyPDF2, python-docx
Data Models: Pydantic (FastAPI version)
Directory Structure
Development
Running in Development Mode
Use the Flask development server:

Adding New Features
Backend: Add new endpoints in flask_app.py
Frontend: Modify index.html, script.js, and styles.css
License
This project is licensed under the MIT License - see the LICENSE file for details.

Acknowledgments
Resume parsing inspired by modern NLP techniques
Design influenced by best practices in UX for form-heavy applications
Special thanks to the open-source libraries that made this project possible

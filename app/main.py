from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
import os
from pathlib import Path

# Import routers
from app.routers import resume

# Create FastAPI app
app = FastAPI(title="Vibezsume", description="Resume analysis and builder tool")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development - restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get the project root directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Mount the static files
app.mount("/static", StaticFiles(directory=BASE_DIR), name="static")

# Set up templates
templates = Jinja2Templates(directory=BASE_DIR)

# Include routers
app.include_router(resume.router)

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Serve the main application page"""
    html_path = BASE_DIR / "index.html"
    if html_path.exists():
        return FileResponse(html_path)
    else:
        return HTMLResponse("<h1>Vibezsume</h1><p>Welcome to Vibezsume. HTML file not found.</p>")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "message": "Vibezsume API is running"}

@app.get("/styles.css")
async def get_css():
    """Serve the CSS file"""
    css_path = BASE_DIR / "styles.css"
    if css_path.exists():
        return FileResponse(css_path)
    return {"error": "CSS file not found"}

@app.get("/script.js")
async def get_js():
    """Serve the JavaScript file"""
    js_path = BASE_DIR / "script.js"
    if js_path.exists():
        return FileResponse(js_path)
    return {"error": "JavaScript file not found"}

@app.post("/resume/upload")
async def upload_resume_mock():
    """Mock endpoint for resume upload"""
    return {
        "name": "John Doe",
        "email": "john@example.com",
        "phone": "555-123-4567",
        "skills": ["Python", "JavaScript", "React", "HTML", "CSS"],
        "education": "Bachelor's in Computer Science",
        "experience": "5 years software development experience",
        "summary": "Experienced software developer with strong web development skills"
    }

@app.post("/resume/job-description")
async def analyze_job_mock():
    """Mock endpoint for job description analysis"""
    return {
        "id": "job123",
        "job_title": "Frontend Developer",
        "required_skills": ["JavaScript", "HTML", "CSS", "React"],
        "nice_to_have": ["TypeScript", "Redux", "UI/UX"],
        "description_preview": "We are looking for a Frontend Developer with experience in React..."
    }

@app.post("/resume/match-jobs")
async def match_jobs_mock():
    """Mock endpoint for job matching"""
    return [{
        "job_title": "Frontend Developer",
        "match_score": 75.5,
        "match_strength": "Good match",
        "matched_required_skills": ["JavaScript", "HTML", "CSS"],
        "matched_nice_to_have": ["Redux"],
        "missing_required_skills": ["React"],
        "recommendations": ["Add React to your skills", "Include more frontend project examples"],
        "job_description": "We are looking for a Frontend Developer with experience in React..."
    }]
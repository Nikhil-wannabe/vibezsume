from fastapi import APIRouter, HTTPException, UploadFile, File
from typing import List
from app.models.resume_model import ResumeData, Resume
from app.services.parser import parse_resume
from app.services.matcher import match_roles
from app.services.builder import build_resume, render_resume

router = APIRouter(prefix="/resume", tags=["resume"])

@router.post("/upload")
async def upload_resume(file: UploadFile = File(...)):
    """Upload and parse a resume file"""
    try:
        content = await file.read()
        parsed_resume = parse_resume(content, file.filename)
        return parsed_resume
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/build")
async def create_resume(resume_data: ResumeData):
    """Create a resume from submitted data"""
    try:
        resume = build_resume(resume_data)
        return resume
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/generate-pdf")
async def generate_pdf(resume: Resume):
    """Generate a PDF from resume data"""
    try:
        pdf_bytes = render_resume(resume)
        return {"pdf_base64": pdf_bytes}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/match-jobs")
async def match_jobs(parsed_resume: dict, job_descriptions: List[str]):
    """Match resume against job descriptions"""
    try:
        matches = match_roles(parsed_resume, job_descriptions)
        return matches
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
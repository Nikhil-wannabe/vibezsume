from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Body
from fastapi.responses import JSONResponse, FileResponse
from typing import Dict, List, Optional
import os
import uuid
import json
from datetime import datetime
from pydantic import BaseModel

from app.services.pdf_parser import extract_text_from_pdf
from app.services.docx_parser import extract_text_from_docx
from app.services.text_extractor import extract_resume_data
from app.services.job_parser import parse_job_description, extract_skills_from_job
from app.models.resume_model import ResumeData

router = APIRouter(prefix="/resume", tags=["Resume"])

# In-memory storage for job descriptions and parsed resumes
JOB_DESCRIPTIONS = {}
PARSED_RESUMES = {}

class JobDescription(BaseModel):
    text: str
    url: Optional[str] = None
    
class JobMatchRequest(BaseModel):
    parsed_resume: Dict
    job_description_id: Optional[str] = None
    job_description_text: Optional[str] = None

@router.post("/upload")
async def upload_resume(file: UploadFile = File(...)):
    """Upload a resume file (PDF or DOCX) and parse it"""
    # Validate file type
    filename = file.filename.lower()
    if not (filename.endswith('.pdf') or filename.endswith('.docx') or filename.endswith('.doc')):
        raise HTTPException(status_code=400, detail="Only PDF and DOCX files are supported")
    
    # Create uploads directory if it doesn't exist
    os.makedirs("uploads", exist_ok=True)
    
    # Generate unique filename to prevent collisions
    unique_filename = f"uploads/{str(uuid.uuid4())}-{filename}"
    
    # Save uploaded file
    with open(unique_filename, "wb") as file_object:
        file_object.write(await file.read())
    
    try:
        # Extract text from file
        if filename.endswith('.pdf'):
            text = extract_text_from_pdf(unique_filename)
        else:  # DOCX
            text = extract_text_from_docx(unique_filename)
        
        # Extract data from text
        resume_data = extract_resume_data(text)
        
        # Store parsed resume with unique ID
        resume_id = str(uuid.uuid4())
        PARSED_RESUMES[resume_id] = {
            "data": resume_data,
            "raw_text": text,
            "uploaded_at": datetime.now().isoformat()
        }
        
        # Add ID to response
        resume_data["id"] = resume_id
        
        return resume_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing resume: {str(e)}")
    finally:
        # Clean up the file
        if os.path.exists(unique_filename):
            os.remove(unique_filename)

@router.post("/job-description")
async def add_job_description(job_description: JobDescription):
    """Add a job description for analysis"""
    # Generate unique ID for this job description
    job_id = str(uuid.uuid4())
    
    # Parse the job description
    parsed_job = parse_job_description(job_description.text)
    
    # Store the job description and parsed data
    JOB_DESCRIPTIONS[job_id] = {
        "original": job_description.dict(),
        "parsed": parsed_job,
        "created_at": datetime.now().isoformat()
    }
    
    # Return the parsed job with ID
    return {
        "id": job_id,
        "job_title": parsed_job["job_title"],
        "required_skills": parsed_job["required_skills"],
        "nice_to_have": parsed_job["nice_to_have"],
        "description_preview": parsed_job["description"]
    }

@router.get("/job-description/{job_id}")
async def get_job_description(job_id: str):
    """Get a stored job description by ID"""
    if job_id not in JOB_DESCRIPTIONS:
        raise HTTPException(status_code=404, detail="Job description not found")
    
    return {
        "id": job_id,
        **JOB_DESCRIPTIONS[job_id]["parsed"]
    }

@router.delete("/job-description/{job_id}")
async def delete_job_description(job_id: str):
    """Delete a stored job description"""
    if job_id not in JOB_DESCRIPTIONS:
        raise HTTPException(status_code=404, detail="Job description not found")
    
    del JOB_DESCRIPTIONS[job_id]
    return {"message": "Job description deleted"}

@router.post("/match-jobs")
async def match_resume_to_jobs(request: JobMatchRequest):
    """Match a parsed resume to job description(s)"""
    resume_data = request.parsed_resume
    
    # If a job description ID is provided, match against that specific job
    if request.job_description_id:
        if request.job_description_id not in JOB_DESCRIPTIONS:
            raise HTTPException(status_code=404, detail="Job description not found")
        
        job_data = JOB_DESCRIPTIONS[request.job_description_id]["parsed"]
        matches = match_resume_to_job(resume_data, job_data)
        return [matches]  # Return as a list with one item
    
    # If job description text is provided, parse and match
    elif request.job_description_text:
        job_data = parse_job_description(request.job_description_text)
        matches = match_resume_to_job(resume_data, job_data)
        return [matches]  # Return as a list with one item
    
    # If no specific job description, match against all stored job descriptions
    else:
        results = []
        for job_id, job_info in JOB_DESCRIPTIONS.items():
            job_data = job_info["parsed"]
            matches = match_resume_to_job(resume_data, job_data)
            matches["id"] = job_id  # Include the job ID
            results.append(matches)
        
        # Sort by match score (descending)
        results.sort(key=lambda x: x["match_score"], reverse=True)
        return results

def match_resume_to_job(resume_data: Dict, job_data: Dict) -> Dict:
    """Match a resume against a specific job description"""
    resume_skills = [skill.lower() for skill in resume_data.get("skills", [])]
    required_skills = [skill.lower() for skill in job_data.get("required_skills", [])]
    nice_to_have = [skill.lower() for skill in job_data.get("nice_to_have", [])]
    
    # Match required skills
    matched_required = [skill for skill in required_skills if skill in resume_skills]
    missing_required = [skill for skill in required_skills if skill not in resume_skills]
    
    # Match nice-to-have skills
    matched_nice = [skill for skill in nice_to_have if skill in resume_skills]
    
    # Calculate scores
    required_score = len(matched_required) / len(required_skills) if required_skills else 0
    nice_score = len(matched_nice) / len(nice_to_have) if nice_to_have else 0
    
    # Weighted score (required skills are more important)
    match_score = (required_score * 0.7 + nice_score * 0.3) * 100
    
    # Determine match strength description
    match_strength = "Weak match"
    if match_score >= 80:
        match_strength = "Excellent match"
    elif match_score >= 60:
        match_strength = "Good match"
    elif match_score >= 40:
        match_strength = "Moderate match"
    
    # Generate recommendations
    recommendations = []
    if missing_required:
        recommendations.append(f"Add these required skills: {', '.join(missing_required)}")
    
    # If score is low, suggest improvements
    if match_score < 60:
        recommendations.append("Consider adding more relevant experience to your resume")
    
    # If very low score, suggest exploring other roles
    if match_score < 30:
        recommendations.append("This job may not be the best match for your current skills")
    
    return {
        "job_title": job_data["job_title"],
        "match_score": round(match_score, 1),
        "match_strength": match_strength,
        "matched_required_skills": matched_required,
        "matched_nice_to_have": matched_nice,
        "missing_required_skills": missing_required,
        "recommendations": recommendations,
        "job_description": job_data.get("description", "")
    }

@router.post("/build", response_model=Dict)
async def build_resume(resume_data: ResumeData):
    """Build a resume from provided data"""
    # Generate a unique ID for this resume
    resume_id = str(uuid.uuid4())
    
    # Store the resume data
    resume_dict = resume_data.dict()
    resume_dict["generated_id"] = resume_id
    resume_dict["created_at"] = datetime.now().isoformat()
    
    # In a real app, you would store this in a database
    # For this example, we'll store it in memory
    with open(f"resume_{resume_id}.json", "w") as f:
        json.dump(resume_dict, f)
    
    return {"message": "Resume built successfully", "generated_id": resume_id}
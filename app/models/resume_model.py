from pydantic import BaseModel
from typing import List, Optional

class Education(BaseModel):
    institution: str
    degree: str
    field_of_study: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    description: Optional[str] = None

class Experience(BaseModel):
    company: str
    position: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    description: Optional[str] = None

class ResumeData(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    summary: Optional[str] = None
    skills: List[str] = []
    education: Optional[str] = None  # Simplified for initial version
    experience: Optional[str] = None  # Simplified for initial version

class Resume(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    summary: Optional[str] = None
    skills: List[str] = []
    education: Optional[str] = None
    experience: Optional[str] = None
    generated_id: Optional[str] = None
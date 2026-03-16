"""
Candidate Model for Recruitment AI System
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class CandidateStatus(str, Enum):
    """Candidate status enum"""
    NEW = "new"
    SCREENING = "screening"
    SCREENED = "screened"
    INTERVIEW_SCHEDULED = "interview_scheduled"
    INTERVIEWED = "interviewed"
    SELECTED = "selected"
    REJECTED = "rejected"
    OFFER_SENT = "offer_sent"
    JOINED = "joined"


class CandidateSkill(BaseModel):
    """Individual skill with proficiency level"""
    name: str
    proficiency: Optional[str] = Field(default="intermediate", description="beginner, intermediate, advanced, expert")
    years_of_experience: Optional[float] = Field(default=None, description="Years of experience with this skill")


class Candidate(BaseModel):
    """Candidate model with complete profile"""
    id: str = Field(..., description="Unique candidate ID (UUID)")
    name: str = Field(..., min_length=1, description="Full name")
    email: EmailStr = Field(..., description="Email address")
    phone: str = Field(..., description="Phone number")
    
    # Resume information
    resume_url: str = Field(..., description="URL to resume in Google Drive")
    resume_text: Optional[str] = Field(default=None, description="Extracted text from resume (PDF/DOC)")
    
    # Skills and experience
    skills: List[CandidateSkill] = Field(default_factory=list, description="List of candidate skills")
    total_experience: Optional[float] = Field(default=None, description="Total years of experience")
    relevant_experience: Optional[float] = Field(default=None, description="Years of relevant experience")
    
    # JD matching
    jd_id: str = Field(..., description="Job description ID")
    matching_score: Optional[float] = Field(default=None, ge=0, le=1, description="Matching score (0-1)")
    screening_notes: Optional[str] = Field(default=None, description="AI screening notes")
    
    # Career details
    current_company: Optional[str] = Field(default=None)
    current_role: Optional[str] = Field(default=None)
    current_location: Optional[str] = Field(default=None)
    current_salary: Optional[float] = Field(default=None, ge=0)
    expected_salary: Optional[float] = Field(default=None, ge=0)
    
    # Availability
    notice_period_days: Optional[int] = Field(default=0, description="Days notice period")
    availability_date: Optional[datetime] = Field(default=None)
    
    # Status
    status: CandidateStatus = Field(default=CandidateStatus.NEW)
    
    # Additional info
    marital_status: Optional[str] = Field(default=None)
    date_of_birth: Optional[datetime] = Field(default=None)
    nationality: Optional[str] = Field(default=None)
    passport_details: Optional[str] = Field(default=None)
    visa_status: Optional[str] = Field(default=None)
    noc_status: Optional[str] = Field(default=None, description="No Objection Certificate status")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = Field(default=None, description="Recruiter ID who created this candidate")
    
    class Config:
        use_enum_values = False
        json_schema_extra = {
            "example": {
                "id": "cand_12345",
                "name": "John Doe",
                "email": "john.doe@example.com",
                "phone": "+1-234-567-8900",
                "resume_url": "https://drive.google.com/...",
                "jd_id": "jd_12345",
                "status": "screening",
                "total_experience": 5.5,
                "matching_score": 0.85
            }
        }

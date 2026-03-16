"""
Requirement (Job Description) Model for Recruitment AI System
"""

from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, List
from datetime import datetime
from enum import Enum


class RecruitmentType(str, Enum):
    """Employment type"""
    PERMANENT = "permanent"
    CONTRACT = "contract"
    INTERNSHIP = "internship"
    FREELANCE = "freelance"


class JobLevel(str, Enum):
    """Job level"""
    ENTRY = "entry"
    JUNIOR = "junior"
    SENIOR = "senior"
    LEAD = "lead"
    MANAGER = "manager"
    DIRECTOR = "director"


class Requirement(BaseModel):
    """Job Description / Requirement Model"""
    
    id: str = Field(..., description="Unique requirement ID (UUID)")
    job_title: str = Field(..., min_length=1, description="Job title")
    client: str = Field(..., description="Client/Company name")
    jd_url: str = Field(..., description="URL to JD in Google Drive")
    jd_text: Optional[str] = Field(default=None, description="Extracted full JD text")
    
    # Job details
    recruitment_type: RecruitmentType = Field(default=RecruitmentType.PERMANENT)
    job_level: Optional[JobLevel] = Field(default=None)
    contract_duration_months: Optional[int] = Field(default=None, description="Duration for contract jobs")
    
    # Location
    location: str = Field(..., description="Job location (city/country)")
    work_type: Optional[str] = Field(default="onsite", description="onsite, remote, hybrid")
    
    # Experience requirements
    min_experience: float = Field(..., ge=0, description="Minimum years of experience required")
    max_experience: Optional[float] = Field(default=None, ge=0, description="Maximum years of experience")
    
    # Skills
    required_skills: List[str] = Field(default_factory=list, description="List of required skills")
    preferred_skills: List[str] = Field(default_factory=list, description="List of preferred skills")
    
    # Compensation
    budget_min: Optional[float] = Field(default=None, ge=0, description="Minimum salary/budget")
    budget_max: Optional[float] = Field(default=None, ge=0, description="Maximum salary/budget")
    currency: Optional[str] = Field(default="USD", description="Currency code")
    
    # Availability
    start_date: Optional[datetime] = Field(default=None)
    urgency: Optional[str] = Field(default="medium", description="low, medium, high, urgent")
    
    # Job description content
    company_description: Optional[str] = Field(default=None, description="Company overview")
    role_overview: Optional[str] = Field(default=None, description="Role description")
    key_responsibilities: List[str] = Field(default_factory=list, description="Main job responsibilities")
    education_requirements: List[str] = Field(default_factory=list, description="Education requirements")
    
    # Metadata
    status: str = Field(default="open", description="open, closed, on_hold")
    positions_count: int = Field(default=1, ge=1, description="Number of positions open")
    applications_count: int = Field(default=0, ge=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = Field(default=None, description="HR/Recruiter ID")
    
    class Config:
        use_enum_values = False
        json_schema_extra = {
            "example": {
                "id": "jd_12345",
                "job_title": "Senior Software Engineer",
                "client": "TechCorp Inc",
                "jd_url": "https://drive.google.com/...",
                "recruitment_type": "permanent",
                "location": "San Francisco, CA",
                "min_experience": 5,
                "required_skills": ["Python", "FastAPI", "PostgreSQL"],
                "status": "open"
            }
        }

"""
Interview Model for Recruitment AI System
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class InterviewStage(str, Enum):
    """Interview stage"""
    PHONE_SCREENING = "phone_screening"
    TECHNICAL_SCREENING = "technical_screening"
    FIRST_ROUND = "first_round"
    SECOND_ROUND = "second_round"
    FINAL_ROUND = "final_round"
    HR_ROUND = "hr_round"


class InterviewStatus(str, Enum):
    """Interview status"""
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    NO_SHOW = "no_show"
    RESCHEDULED = "rescheduled"
    CANCELLED = "cancelled"


class InterviewFeedback(BaseModel):
    """Interview feedback from interviewer"""
    rating: int = Field(..., ge=1, le=10, description="Rating 1-10")
    technical_score: Optional[int] = Field(default=None, ge=0, le=100)
    communication_score: Optional[int] = Field(default=None, ge=0, le=100)
    culture_fit_score: Optional[int] = Field(default=None, ge=0, le=100)
    comments: Optional[str] = Field(default=None)
    recommendation: Optional[str] = Field(default=None, description="hire, no_hire, maybe")
    interviewer_notes: Optional[str] = Field(default=None)


class Interview(BaseModel):
    """Interview scheduling and feedback model"""
    
    id: str = Field(..., description="Unique interview ID (UUID)")
    candidate_id: str = Field(..., description="Candidate ID")
    jd_id: str = Field(..., description="Job description ID")
    
    # Interview details
    stage: InterviewStage = Field(...)
    status: InterviewStatus = Field(default=InterviewStatus.SCHEDULED)
    
    # Scheduling
    scheduled_at: datetime = Field(..., description="Interview date and time")
    duration_minutes: int = Field(default=60, ge=15)
    interview_link: Optional[str] = Field(default=None, description="Video call link (Zoom, Teams, etc.)")
    location: Optional[str] = Field(default=None, description="Physical location if in-person")
    
    # Interviewer info
    interviewer_name: str = Field(..., description="Name of interviewer")
    interviewer_email: str = Field(...)
    interviewer_id: Optional[str] = Field(default=None)
    
    # Interview content
    custom_questions: Optional[List[str]] = Field(default=None, description="Custom screening questions")
    ai_generated_questions: Optional[List[str]] = Field(default=None)
    
    # Feedback
    feedback: Optional[InterviewFeedback] = Field(default=None, description="Interview feedback after completion")
    candidate_feedback: Optional[str] = Field(default=None, description="Candidate's feedback on interview")
    
    # Recording
    recording_url: Optional[str] = Field(default=None)
    transcript_url: Optional[str] = Field(default=None)
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        use_enum_values = False
        json_schema_extra = {
            "example": {
                "id": "int_12345",
                "candidate_id": "cand_12345",
                "jd_id": "jd_12345",
                "stage": "phone_screening",
                "status": "scheduled",
                "scheduled_at": "2026-02-15T14:00:00Z",
                "interviewer_name": "Jane Smith"
            }
        }

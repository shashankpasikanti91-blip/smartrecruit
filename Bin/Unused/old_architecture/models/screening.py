"""
Screening Result Model for Recruitment AI System
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class SkillMatch(BaseModel):
    """Individual skill match details"""
    skill: str
    required: bool = Field(default=False, description="Is this a required skill?")
    found: bool = Field(description="Was this skill found in resume?")
    proficiency_match: Optional[float] = Field(default=None, ge=0, le=1, description="0-1 proficiency match score")
    relevance_score: Optional[float] = Field(default=None, ge=0, le=1)


class ScreeningResult(BaseModel):
    """AI Screening result for candidate vs JD"""
    
    id: str = Field(..., description="Unique screening ID (UUID)")
    candidate_id: str = Field(..., description="Candidate ID")
    jd_id: str = Field(..., description="Job description ID")
    
    # Overall score
    overall_score: float = Field(..., ge=0, le=1, description="Overall match score 0-1")
    recommendation: str = Field(..., description="strong_match, good_match, fair_match, poor_match, not_match")
    
    # Skill matching
    skill_matches: List[SkillMatch] = Field(default_factory=list)
    required_skills_match: float = Field(default=0, ge=0, le=1, description="% of required skills matched")
    optional_skills_match: Optional[float] = Field(default=None, ge=0, le=1)
    
    # Experience matching
    experience_score: float = Field(default=0, ge=0, le=1, description="Experience match score")
    years_requirement_met: bool = Field(default=False)
    experience_details: Optional[str] = Field(default=None)
    
    # Qualifications
    education_match: Optional[float] = Field(default=None, ge=0, le=1)
    education_details: Optional[str] = Field(default=None)
    
    # Score breakdown
    score_breakdown: Dict[str, float] = Field(default_factory=dict, description="Detailed score components")
    
    # AI Analysis
    strengths: List[str] = Field(default_factory=list, description="Candidate strengths vs JD")
    weaknesses: List[str] = Field(default_factory=list, description="Candidate weaknesses vs JD")
    gaps: List[str] = Field(default_factory=list, description="Skill/experience gaps")
    ai_summary: Optional[str] = Field(default=None, description="AI-generated screening summary")
    
    # Recommended actions
    recommended_action: Optional[str] = Field(default=None, description="proceed, conditional, reject")
    reason_for_recommendation: Optional[str] = Field(default=None)
    questions_to_ask: Optional[List[str]] = Field(default=None, description="Screening questions to ask candidate")
    
    # Metadata
    screening_method: str = Field(default="ai", description="ai, manual, hybrid")
    screened_by: Optional[str] = Field(default=None, description="AI model name or HR ID")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    processing_time_seconds: Optional[float] = Field(default=None)
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "scr_12345",
                "candidate_id": "cand_12345",
                "jd_id": "jd_12345",
                "overall_score": 0.85,
                "recommendation": "strong_match",
                "required_skills_match": 0.9,
                "experience_score": 0.8,
                "strengths": ["Strong Python skills", "5+ years experience"],
                "gaps": ["No FastAPI experience"]
            }
        }

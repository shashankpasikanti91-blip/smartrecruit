"""
JD Intelligence Router — SRP SmartRecruit v4.0
Generate JDs, analyse existing JDs, download JD as plain text
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database.connection import get_db
from app.auth.dependencies import get_current_verified_user
from app.models.user import User
from app.services.jd_service import JDService
from app.services.audit_service import log_action

router = APIRouter(prefix="/api/v4/jd", tags=["JD Intelligence"])


# ─────────────────────────────────────────────────────────────────────────────
# Request / Response models
# ─────────────────────────────────────────────────────────────────────────────

class GenerateJDRequest(BaseModel):
    job_title:        str = Field(..., min_length=2, max_length=200)
    skills:           List[str] = Field(default_factory=list)
    experience:       Optional[str] = None
    education:        Optional[str] = None
    location:         Optional[str] = None
    employment_type:  Optional[str] = None
    salary:           Optional[str] = None
    industry:         Optional[str] = None
    company_name:     Optional[str] = None
    notice_period:    Optional[str] = None
    additional_notes: Optional[str] = None


class AnalyzeJDRequest(BaseModel):
    jd_text: str = Field(..., min_length=50, max_length=20000)


class JDResponse(BaseModel):
    id:             int
    title:          str
    full_jd_text:   str
    structured_data: dict
    version:        int
    is_final:       bool
    created_at:     str

    class Config:
        from_attributes = True


class JDAnalysisResponse(BaseModel):
    id:                  int
    must_have_skills:    List[str]
    nice_to_have_skills: List[str]
    alternate_titles:    List[str]
    skill_clusters:      dict
    suggested_questions: List[str]
    screening_criteria:  dict
    created_at:          str


# ─────────────────────────────────────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/generate", status_code=status.HTTP_201_CREATED)
async def generate_jd(
    request: GenerateJDRequest,
    req: Request,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db),
):
    """
    Generate a complete, professional Job Description from structured inputs.

    Returns:
    - Full formatted JD text
    - Structured breakdown (responsibilities, skills, etc.)
    """
    try:
        params = request.model_dump(exclude_none=True)
        record = JDService.generate_jd(db, current_user, params)
        log_action(
            db, action="jd.generated", resource_type="generated_jd",
            resource_id=record.id, user=current_user,
            ip_address=req.client.host if req.client else None,
        )
        return {
            "id":             record.id,
            "title":          record.title,
            "full_jd_text":   record.full_jd_text,
            "structured_data": record.structured_data,
            "version":        record.version,
            "is_final":       record.is_final,
            "created_at":     record.created_at.isoformat(),
        }
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"JD generation failed: {str(e)}")


@router.post("/analyze", status_code=status.HTTP_201_CREATED)
async def analyze_jd(
    request: AnalyzeJDRequest,
    req: Request,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db),
):
    """
    Analyse an existing JD to extract structured intelligence:
    - Must-have vs preferred skills
    - Alternate job titles
    - Skill clusters
    - Suggested screening questions
    """
    try:
        record = JDService.analyze_jd(db, current_user, request.jd_text)
        log_action(
            db, action="jd.analyzed", resource_type="jd_analysis",
            resource_id=record.id, user=current_user,
            ip_address=req.client.host if req.client else None,
        )
        return {
            "id":                  record.id,
            "must_have_skills":    record.must_have_skills,
            "nice_to_have_skills": record.nice_to_have_skills,
            "alternate_titles":    record.alternate_titles,
            "skill_clusters":      record.skill_clusters,
            "suggested_questions": record.suggested_questions,
            "screening_criteria":  record.screening_criteria,
            "created_at":          record.created_at.isoformat(),
        }
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"JD analysis failed: {str(e)}")


@router.get("/list")
async def list_generated_jds(
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db),
    limit: int = 20,
):
    """List all JDs generated by the current user."""
    records = JDService.list_jds(db, current_user, limit=min(limit, 50))
    return {
        "jds": [
            {
                "id":          r.id,
                "title":       r.title,
                "version":     r.version,
                "is_final":    r.is_final,
                "created_at":  r.created_at.isoformat(),
            }
            for r in records
        ]
    }


@router.get("/{jd_id}")
async def get_generated_jd(
    jd_id: int,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db),
):
    """Get a specific generated JD by ID."""
    record = JDService.get_jd(db, current_user, jd_id)
    if not record:
        raise HTTPException(status_code=404, detail="JD not found")
    return {
        "id":             record.id,
        "title":          record.title,
        "full_jd_text":   record.full_jd_text,
        "structured_data": record.structured_data,
        "input_params":   record.input_params,
        "version":        record.version,
        "is_final":       record.is_final,
        "created_at":     record.created_at.isoformat(),
    }


@router.get("/{jd_id}/download", response_class=PlainTextResponse)
async def download_jd(
    jd_id: int,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db),
):
    """Download JD as plain text."""
    record = JDService.get_jd(db, current_user, jd_id)
    if not record:
        raise HTTPException(status_code=404, detail="JD not found")
    filename = f"JD_{record.title.replace(' ', '_')}.txt"
    return PlainTextResponse(
        content=record.full_jd_text,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

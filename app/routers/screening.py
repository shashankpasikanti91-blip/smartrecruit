"""
Screening router for SRP SmartRecruit v3.2
Resume screening, job matching, interview invites
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
import shutil
from pathlib import Path

from app.database.connection import get_db
from app.schemas import ScreeningRequest, ScreeningResponse, InviteRequest, InviteResponse, MessageResponse
from app.services.screening_service import ScreeningService
from app.services.rate_limit_service import RateLimitService
from app.auth.dependencies import get_current_verified_user
from app.models.user import User
from app.models.resume import ResumeMetadata
from app.models.screening import ScreeningResult

router = APIRouter(prefix="/api/screening", tags=["Screening"])


@router.post("/screen", status_code=status.HTTP_200_OK)
async def screen_resume(
    request: ScreeningRequest,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """
    Screen resume against job description
    
    Features:
    - AI-powered matching using pydantic-ai
    - Score calculation (0-100)
    - Strengths and concerns analysis
    - Auto-eligibility for interview (score >= 75)
    
    Rate Limits:
    - Free users: 1 screening per day
    - Pro/Admin: Unlimited
    """
    screening = await ScreeningService.screen_resume(
        db,
        current_user,
        request.resume_id,
        request.job_description
    )
    
    return {
        "id": screening.id,
        "score": screening.score,
        "recommendation": screening.recommendation,
        "strengths": screening.strengths,
        "concerns": screening.concerns,
        "is_eligible_for_invite": screening.is_eligible_for_invite,
        "created_at": screening.created_at
    }


@router.get("/results/{screening_id}")
async def get_screening_result(
    screening_id: int,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Get screening result by ID"""
    screening = ScreeningService.get_screening_result(db, current_user, screening_id)
    
    return {
        "id": screening.id,
        "resume_id": screening.resume_id,
        "score": screening.score,
        "recommendation": screening.recommendation,
        "strengths": screening.strengths,
        "concerns": screening.concerns,
        "is_eligible_for_invite": screening.is_eligible_for_invite,
        "job_description": screening.job_description,
        "created_at": screening.created_at
    }


@router.get("/results")
async def list_screening_results(
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db),
    limit: int = 10
):
    """List all screening results for current user"""
    results = db.query(ScreeningResult).filter(
        ScreeningResult.user_id == current_user.id
    ).order_by(ScreeningResult.created_at.desc()).limit(limit).all()
    
    return {
        "results": [
            {
                "id": r.id,
                "resume_id": r.resume_id,
                "score": r.score,
                "recommendation": r.recommendation,
                "is_eligible_for_invite": r.is_eligible_for_invite,
                "created_at": r.created_at
            }
            for r in results
        ]
    }


@router.post("/invite", status_code=status.HTTP_201_CREATED)
async def create_interview_invite(
    request: InviteRequest,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """
    Create interview invitation
    
    Only allowed if screening score >= 75%
    Auto-generates professional invitation email
    """
    invite = ScreeningService.create_interview_invite(
        db,
        current_user,
        request.screening_id,
        request.candidate_name,
        request.candidate_email
    )
    
    return {
        "id": invite.id,
        "candidate_email": invite.candidate_email,
        "email_subject": invite.email_subject,
        "email_body": invite.email_body,
        "invite_status": invite.invite_status,
        "created_at": invite.created_at
    }


@router.post("/invite/{invite_id}/send")
async def send_interview_invite(
    invite_id: int,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """
    Send interview invitation email
    
    SMTP integration placeholder - configure in .env
    """
    return ScreeningService.send_interview_invite(db, current_user, invite_id)


@router.get("/usage")
async def get_usage_stats(
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """
    Get current usage statistics
    
    Shows screenings used today and limits based on role
    """
    return RateLimitService.get_usage_stats(db, current_user)

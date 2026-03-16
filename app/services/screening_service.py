"""
Screening service for SRP SmartRecruit v3.2
AI-powered resume screening and job matching
"""

from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from fastapi import HTTPException, status
from typing import Optional
import json

from app.models.user import User
from app.models.resume import ResumeMetadata
from app.models.screening import ScreeningResult, InterviewInvite
from app.services.pydantic_ai_agents import match_candidate_to_job
from app.services.rate_limit_service import RateLimitService


class ScreeningService:
    """Resume screening and interview invite service"""
    
    @staticmethod
    async def screen_resume(
        db: Session, 
        user: User, 
        resume_id: int, 
        job_description: str
    ) -> ScreeningResult:
        """
        Screen resume against job description using AI
        
        Steps:
        1. Check rate limit
        2. Get resume data
        3. Run AI matching
        4. Save screening result
        5. Check if eligible for interview (score >= 75)
        """
        # Check rate limit
        RateLimitService.check_screening_limit(db, user)
        
        # Get resume
        resume = db.query(ResumeMetadata).filter(
            ResumeMetadata.id == resume_id,
            ResumeMetadata.user_id == user.id
        ).first()
        
        if not resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resume not found"
            )
        
        if not resume.extracted_text:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Resume text not available. Please re-upload the resume."
            )
        
        try:
            # Run AI matching using pydantic-ai
            match_result = await match_candidate_to_job(
                resume.extracted_text,
                job_description
            )
            
            # Create screening result
            screening = ScreeningResult(
                user_id=user.id,
                resume_id=resume_id,
                job_description=job_description,
                score=match_result.score,
                status="completed",
                ai_analysis={"match_result": match_result.dict()},
                strengths=match_result.strengths,
                concerns=match_result.concerns,
                recommendation=match_result.recommendation,
                is_eligible_for_invite=(match_result.score >= 75.0)
            )
            
            db.add(screening)
            db.commit()
            db.refresh(screening)
            
            return screening
            
        except Exception as e:
            # Handle AI errors gracefully
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Screening failed: {str(e)}"
            )
    
    @staticmethod
    def get_screening_result(
        db: Session,
        user: User,
        screening_id: int
    ) -> ScreeningResult:
        """Get screening result by ID"""
        screening = db.query(ScreeningResult).filter(
            ScreeningResult.id == screening_id,
            ScreeningResult.user_id == user.id
        ).first()
        
        if not screening:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Screening result not found"
            )
        
        return screening
    
    @staticmethod
    def create_interview_invite(
        db: Session,
        user: User,
        screening_id: int,
        candidate_name: str,
        candidate_email: str
    ) -> InterviewInvite:
        """
        Create interview invitation
        
        Only allowed if screening score >= 75%
        Auto-generates professional email
        """
        # Get screening result
        screening = ScreeningService.get_screening_result(db, user, screening_id)
        
        # Check if eligible (score >= 75)
        if not screening.is_eligible_for_invite:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Candidate not eligible for interview. Score: {screening.score}/100 (minimum 75 required)"
            )
        
        # Check if invite already exists
        existing_invite = db.query(InterviewInvite).filter(
            InterviewInvite.screening_id == screening_id
        ).first()
        
        if existing_invite:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Interview invitation already created for this screening"
            )
        
        # Generate professional email
        email_subject = f"Interview Invitation - {user.email.split('@')[0].title()} Company"
        email_body = f"""Dear {candidate_name},

We are pleased to inform you that your application has been carefully reviewed by our recruitment team and AI-powered screening system.

Your profile scored {screening.score:.1f}/100, demonstrating strong alignment with our requirements.

Key Strengths Identified:
{chr(10).join(f"• {strength}" for strength in screening.strengths[:5])}

We would like to invite you for an interview to discuss this opportunity further.

Please reply to this email with your availability for the next week, and we will schedule a convenient time.

Best Regards,
{user.email.split('@')[0].title()} Recruitment Team

Powered by SRP SmartRecruit v3.2
"""
        
        # Create invite
        invite = InterviewInvite(
            user_id=user.id,
            screening_id=screening_id,
            candidate_name=candidate_name,
            candidate_email=candidate_email,
            email_subject=email_subject,
            email_body=email_body,
            invite_status="draft"
        )
        
        db.add(invite)
        db.commit()
        db.refresh(invite)
        
        return invite
    
    @staticmethod
    def send_interview_invite(
        db: Session,
        user: User,
        invite_id: int
    ) -> dict:
        """
        Send interview invitation email
        
        In production, this would integrate with SMTP
        For now, marks as sent
        """
        invite = db.query(InterviewInvite).filter(
            InterviewInvite.id == invite_id,
            InterviewInvite.user_id == user.id
        ).first()
        
        if not invite:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invitation not found"
            )
        
        if invite.invite_status != "draft":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invitation already {invite.invite_status}"
            )
        
        # TODO: Integrate with SMTP to send actual email
        # For now, just mark as sent
        invite.invite_status = "sent"
        invite.sent_at = db.query(func.now()).scalar()
        db.commit()
        
        return {
            "message": "Interview invitation sent successfully",
            "invite_id": invite.id,
            "candidate_email": invite.candidate_email
        }

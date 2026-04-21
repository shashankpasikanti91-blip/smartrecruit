"""
AI Writing Assistant router for SRP SmartRecruit v3.2
Powered by pydantic-ai for professional content generation
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.schemas import WritingAssistRequest, WritingAssistResponse
from app.auth.dependencies import get_current_verified_user
from app.models.user import User
from app.services.pydantic_ai_agents import improve_writing

router = APIRouter(prefix="/api/ai", tags=["AI Assistant"])


@router.post("/writing-assist", response_model=WritingAssistResponse)
async def ai_writing_assistant(
    request: WritingAssistRequest,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """
    AI Writing Assistant
    
    Helps improve:
    - Job descriptions
    - Interview invitation emails
    - Rejection emails
    - Internal communications
    
    Powered by pydantic-ai with structured output
    """
    try:
        result = await improve_writing(request.text, request.context)
        
        return {
            "improved_text": result.improved_text,
            "suggestions": result.suggestions,
            "tone": result.tone
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI writing assistant failed: {str(e)}"
        )


@router.post("/generate-job-description")
async def generate_job_description(
    job_title: str,
    requirements: str,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """
    Generate professional job description
    
    Input: Job title + basic requirements
    Output: Complete professional job description
    """
    prompt = f"Job Title: {job_title}\n\nRequirements:\n{requirements}"
    
    try:
        result = await improve_writing(prompt, "job description")
        return {
            "job_description": result.improved_text,
            "suggestions": result.suggestions
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate job description: {str(e)}"
        )


@router.post("/improve-email")
async def improve_email(
    email_body: str,
    email_type: str = "interview invitation",
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """
    Improve email content
    
    Types: interview invitation, rejection, follow-up, etc.
    """
    try:
        result = await improve_writing(email_body, f"{email_type} email")
        return {
            "improved_email": result.improved_text,
            "suggestions": result.suggestions,
            "tone": result.tone
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to improve email: {str(e)}"
        )


@router.post("/quick-suggestions")
async def quick_suggestions(
    text: str,
    current_user: User = Depends(get_current_verified_user)
):
    """
    Get quick writing suggestions without full rewrite
    
    Useful for real-time assistance as user types
    """
    try:
        result = await improve_writing(text, "quick suggestions")
        return {
            "suggestions": result.suggestions
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate suggestions: {str(e)}"
        )

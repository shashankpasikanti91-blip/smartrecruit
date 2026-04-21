"""
Pydantic Schemas for SRP SmartRecruit v3.2
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime


# ============================================
# AUTH SCHEMAS
# ============================================

class UserRegister(BaseModel):
    """User registration request"""
    email: EmailStr
    password: str = Field(min_length=8, max_length=100)


class UserLogin(BaseModel):
    """User login request"""
    email: EmailStr
    password: str


class OTPVerifyRequest(BaseModel):
    """OTP verification request"""
    email: EmailStr
    otp_code: str = Field(min_length=6, max_length=6)


class PasswordResetRequest(BaseModel):
    """Password reset request"""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation with OTP"""
    email: EmailStr
    otp_code: str = Field(min_length=6, max_length=6)
    new_password: str = Field(min_length=8, max_length=100)


class TokenResponse(BaseModel):
    """JWT token response"""
    access_token: str
    token_type: str = "bearer"
    user: dict


class UserResponse(BaseModel):
    """User data response"""
    id: int
    email: str
    role: str
    is_active: bool
    is_verified: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================
# RESUME SCHEMAS
# ============================================

class ResumeUpload(BaseModel):
    """Resume upload response"""
    id: int
    filename: str
    file_size: int
    uploaded_at: datetime


class ResumeAnalysisResponse(BaseModel):
    """Resume AI analysis result"""
    candidate_name: str
    email: Optional[str]
    years_experience: int
    key_skills: List[str]
    education: str
    summary: str
    match_score: float


# ============================================
# SCREENING SCHEMAS
# ============================================

class ScreeningRequest(BaseModel):
    """Screening request"""
    resume_id: int
    job_description: str


class ScreeningResponse(BaseModel):
    """Screening result"""
    id: int
    score: float
    recommendation: str
    strengths: List[str]
    concerns: List[str]
    is_eligible_for_invite: bool
    created_at: datetime


# ============================================
# INTERVIEW INVITE SCHEMAS
# ============================================

class InviteRequest(BaseModel):
    """Interview invitation request"""
    screening_id: int
    candidate_name: str
    candidate_email: EmailStr


class InviteResponse(BaseModel):
    """Interview invitation response"""
    id: int
    candidate_email: str
    email_subject: str
    email_body: str
    invite_status: str
    created_at: datetime


# ============================================
# SUPPORT SCHEMAS
# ============================================

class SupportTicketCreate(BaseModel):
    """Create support ticket"""
    message: str
    category: str = "general"  # technical, billing, general
    user_email: Optional[EmailStr] = None


class SupportTicketResponse(BaseModel):
    """Support ticket response"""
    id: int
    message: str
    category: str
    status: str
    created_at: datetime


# ============================================
# AI WRITING ASSISTANT SCHEMAS
# ============================================

class WritingAssistRequest(BaseModel):
    """AI writing assistant request"""
    text: str
    context: str = "job description"  # job description, email, etc.


class WritingAssistResponse(BaseModel):
    """AI writing assistant response"""
    improved_text: str
    suggestions: List[str]
    tone: str


# ============================================
# GENERAL SCHEMAS
# ============================================

class MessageResponse(BaseModel):
    """Generic message response"""
    message: str
    success: bool = True


class ErrorResponse(BaseModel):
    """Error response"""
    detail: str
    success: bool = False

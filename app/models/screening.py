"""Screening models for SRP SmartRecruit v3.2"""

from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.connection import Base


class ScreeningResult(Base):
    """AI screening results for candidates"""
    __tablename__ = "screening_results"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Allow NULL for anonymous screening
    resume_id = Column(Integer, ForeignKey("resume_metadata.id"), nullable=True)
    job_description = Column(Text)  # The job requirements used
    score = Column(Float, nullable=False)  # 0-100
    status = Column(String, default="completed")  # pending, completed, failed
    ai_analysis = Column(JSON)  # Detailed AI analysis
    strengths = Column(JSON)  # List of strengths
    concerns = Column(JSON)  # List of concerns
    recommendation = Column(String)  # hire, interview, reject
    is_eligible_for_invite = Column(Boolean, default=False)  # score >= 75
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships (using lazy loading to avoid circular imports)
    user = relationship("User", foreign_keys=[user_id], lazy="select")
    resume = relationship("ResumeMetadata", back_populates="screening_results", lazy="select")
    interview_invites = relationship("InterviewInvite", back_populates="screening", lazy="select")


class InterviewInvite(Base):
    """Interview invitation tracking"""
    __tablename__ = "interview_invites"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    screening_id = Column(Integer, ForeignKey("screening_results.id"), nullable=False)
    candidate_name = Column(String)
    candidate_email = Column(String, nullable=False)
    email_subject = Column(String)
    email_body = Column(Text)  # Auto-generated invitation email
    invite_status = Column(String, default="draft")  # draft, sent, accepted, rejected
    sent_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User")
    screening = relationship("ScreeningResult", back_populates="interview_invites")

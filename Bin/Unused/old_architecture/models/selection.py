"""
Selection Model for Recruitment AI System
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class SelectionStatus(str, Enum):
    """Selection status"""
    PENDING = "pending"
    SELECTED = "selected"
    OFFER_EXTENDED = "offer_extended"
    OFFER_ACCEPTED = "offer_accepted"
    OFFER_REJECTED = "offer_rejected"
    JOINED = "joined"
    NOT_SELECTED = "not_selected"


class OfferStatus(str, Enum):
    """Offer status"""
    DRAFT = "draft"
    SENT = "sent"
    VIEWED = "viewed"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    NEGOTIATING = "negotiating"
    WITHDRAWN = "withdrawn"


class OfferDetails(BaseModel):
    """Offer details"""
    salary: float = Field(..., ge=0)
    currency: str = Field(default="USD")
    bonus: Optional[float] = Field(default=None, ge=0)
    benefits: Optional[List[str]] = Field(default=None, description="List of benefits")
    start_date: datetime = Field(...)
    contract_terms: Optional[str] = Field(default=None)
    probation_period_days: Optional[int] = Field(default=90)


class Selection(BaseModel):
    """Selection decision and offer model"""
    
    id: str = Field(..., description="Unique selection ID (UUID)")
    candidate_id: str = Field(..., description="Candidate ID")
    jd_id: str = Field(..., description="Job description ID")
    
    # Selection
    status: SelectionStatus = Field(default=SelectionStatus.PENDING)
    decision_date: Optional[datetime] = Field(default=None)
    decision_reason: Optional[str] = Field(default=None)
    
    # Selection scores
    technical_fit_score: Optional[float] = Field(default=None, ge=0, le=100)
    cultural_fit_score: Optional[float] = Field(default=None, ge=0, le=100)
    overall_score: Optional[float] = Field(default=None, ge=0, le=100)
    
    # Offer
    offer: Optional[OfferDetails] = Field(default=None, description="Offer details if extended")
    offer_status: Optional[OfferStatus] = Field(default=None)
    offer_sent_at: Optional[datetime] = Field(default=None)
    offer_accepted_at: Optional[datetime] = Field(default=None)
    offer_rejected_at: Optional[datetime] = Field(default=None)
    
    # Joining details
    joining_date: Optional[datetime] = Field(default=None)
    joining_document_status: Optional[str] = Field(default=None, description="pending, submitted, verified")
    joining_documents: Optional[List[str]] = Field(default=None, description="URLs to joining documents")
    
    # Comments and notes
    selection_committee_notes: Optional[str] = Field(default=None)
    candidate_notes: Optional[str] = Field(default=None)
    
    # Metadata
    selected_by: Optional[str] = Field(default=None, description="HR/Manager ID who made selection")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        use_enum_values = False
        json_schema_extra = {
            "example": {
                "id": "sel_12345",
                "candidate_id": "cand_12345",
                "jd_id": "jd_12345",
                "status": "selected",
                "overall_score": 85,
                "offer": {
                    "salary": 120000,
                    "currency": "USD",
                    "start_date": "2026-03-15T00:00:00Z"
                }
            }
        }

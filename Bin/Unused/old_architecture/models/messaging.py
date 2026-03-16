"""
Messaging Model for Recruitment AI System
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime
from enum import Enum


class MessageTone(str, Enum):
    """Message tone/style"""
    FORMAL = "formal"
    PROFESSIONAL = "professional"
    SEMI_FORMAL = "semi_formal"
    FRIENDLY = "friendly"
    CASUAL = "casual"


class MessagePlatform(str, Enum):
    """Message platform"""
    EMAIL = "email"
    WHATSAPP = "whatsapp"
    LINKEDIN = "linkedin"
    TELEGRAM = "telegram"
    SMS = "sms"


class MessageType(str, Enum):
    """Message type"""
    JOB_POSTING = "job_posting"
    INTERVIEW_INVITE = "interview_invite"
    OFFER = "offer"
    REJECTION = "rejection"
    FOLLOW_UP = "follow_up"
    SCREENING = "screening"
    CUSTOM = "custom"


class MessageRequest(BaseModel):
    """Request to generate a message"""
    
    id: str = Field(..., description="Unique message request ID (UUID)")
    
    # Message parameters
    message_type: MessageType
    platform: MessagePlatform
    tone: MessageTone = Field(default=MessageTone.PROFESSIONAL)
    
    # Recipients
    recipient_name: str = Field(...)
    recipient_email: Optional[EmailStr] = Field(default=None)
    recipient_phone: Optional[str] = Field(default=None)
    
    # Content context
    subject: Optional[str] = Field(default=None, description="For email/LinkedIn")
    job_title: Optional[str] = Field(default=None)
    company_name: Optional[str] = Field(default=None)
    location: Optional[str] = Field(default=None)
    
    # Custom content
    custom_content: Optional[str] = Field(default=None, description="User-provided content to include")
    key_points: Optional[List[str]] = Field(default=None, description="Key points to highlight")
    
    # Interview details (if applicable)
    interview_date: Optional[datetime] = Field(default=None)
    interview_time: Optional[str] = Field(default=None)
    interview_link: Optional[str] = Field(default=None)
    
    # Offer details (if applicable)
    salary: Optional[float] = Field(default=None)
    currency: Optional[str] = Field(default="USD")
    start_date: Optional[datetime] = Field(default=None)
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        use_enum_values = False


class MessageResponse(BaseModel):
    """Generated message response"""
    
    id: str = Field(..., description="Message request ID")
    platform: MessagePlatform
    
    # Generated content
    subject: Optional[str] = Field(default=None, description="Email subject line")
    body: str = Field(..., description="Message body")
    
    # Pre-formatted versions
    body_plain_text: Optional[str] = Field(default=None)
    body_html: Optional[str] = Field(default=None)
    
    # Additional versions
    short_version: Optional[str] = Field(default=None, description="For short platforms like SMS")
    long_version: Optional[str] = Field(default=None, description="Detailed version")
    
    # Metadata
    estimated_read_time_seconds: Optional[int] = Field(default=None)
    tone_applied: MessageTone
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    ai_model: str = Field(default="gpt-4o-mini")
    
    class Config:
        use_enum_values = False
        json_schema_extra = {
            "example": {
                "id": "msg_12345",
                "platform": "email",
                "subject": "Interview Opportunity - Senior Software Engineer",
                "body": "Dear John,\n\nWe are excited to invite you...",
                "tone_applied": "professional"
            }
        }


class MessageHistory(BaseModel):
    """Message history record"""
    
    id: str = Field(..., description="Unique history ID")
    message_response_id: str = Field(..., description="Message response ID")
    candidate_id: str = Field(..., description="Candidate ID")
    
    # Delivery status
    status: str = Field(default="pending", description="pending, sent, delivered, read, failed")
    sent_at: Optional[datetime] = Field(default=None)
    delivered_at: Optional[datetime] = Field(default=None)
    read_at: Optional[datetime] = Field(default=None)
    
    # Platform specific
    platform: MessagePlatform
    platform_message_id: Optional[str] = Field(default=None, description="Provider's message ID")
    recipient_contact: str = Field(..., description="Email, phone, or username")
    
    # Response tracking
    has_response: bool = Field(default=False)
    response_received_at: Optional[datetime] = Field(default=None)
    response_content: Optional[str] = Field(default=None)
    
    # Error handling
    error_message: Optional[str] = Field(default=None)
    retry_count: int = Field(default=0, ge=0)
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        use_enum_values = False

"""Support models for SRP SmartRecruit v3.2"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.connection import Base


class SupportTicket(Base):
    """Chatbot support ticket tracking"""
    __tablename__ = "support_tickets"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Can be null for anonymous
    user_email = Column(String)  # For anonymous users
    message = Column(Text, nullable=False)
    category = Column(String)  # technical, billing, general
    priority = Column(String, default="normal")  # low, normal, high
    status = Column(String, default="open")  # open, in_progress, resolved, closed
    admin_reply = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User")

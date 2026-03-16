"""Resume models for SRP SmartRecruit v3.2"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.connection import Base


class ResumeMetadata(Base):
    """Resume upload and metadata tracking"""
    __tablename__ = "resume_metadata"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_size = Column(Integer)  # in bytes
    mime_type = Column(String)
    extracted_text = Column(Text)  # Full resume text
    parsed_data = Column(JSON)  # Structured data from AI
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User")
    screening_results = relationship("ScreeningResult", back_populates="resume")

"""
Enterprise models for SRP SmartRecruit v4.0
JD Intelligence, Boolean Search, Audit Logs
"""

from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Text,
    ForeignKey, JSON, Enum as SAEnum
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.database.connection import Base


# ────────────────────────────────────────────────────────────────────────────
# Audit Log
# ────────────────────────────────────────────────────────────────────────────

class AuditLog(Base):
    __tablename__ = "audit_logs_backend"    # separate from frontend's audit_logs

    id              = Column(Integer, primary_key=True, index=True)
    user_id         = Column(Integer, ForeignKey("users.id"), nullable=True)
    user_email      = Column(String(255), nullable=True)
    action          = Column(String(120), nullable=False, index=True)
    resource_type   = Column(String(80), nullable=False, index=True)
    resource_id     = Column(String(80), nullable=True)
    details         = Column(JSON, default=dict)
    ip_address      = Column(String(45), nullable=True)
    user_agent      = Column(String(512), nullable=True)
    result          = Column(String(30), nullable=False, default="success")
    created_at      = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    user = relationship("User", foreign_keys=[user_id], lazy="select")


# ────────────────────────────────────────────────────────────────────────────
# Generated JD
# ────────────────────────────────────────────────────────────────────────────

class GeneratedJD(Base):
    __tablename__ = "generated_jds_backend"

    id              = Column(Integer, primary_key=True, index=True)
    user_id         = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    title           = Column(String(255), nullable=False)
    input_params    = Column(JSON, default=dict)
    full_jd_text    = Column(Text, nullable=False)
    structured_data = Column(JSON, default=dict)
    version         = Column(Integer, nullable=False, default=1)
    is_final        = Column(Boolean, default=False)
    created_at      = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at      = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user            = relationship("User", foreign_keys=[user_id], lazy="select")
    boolean_searches = relationship("GeneratedBooleanSearch", back_populates="source_jd", lazy="select")


# ────────────────────────────────────────────────────────────────────────────
# Generated Boolean Search
# ────────────────────────────────────────────────────────────────────────────

class GeneratedBooleanSearch(Base):
    __tablename__ = "generated_boolean_searches_backend"

    id               = Column(Integer, primary_key=True, index=True)
    user_id          = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    source_jd_id     = Column(Integer, ForeignKey("generated_jds_backend.id"), nullable=True)
    job_title        = Column(String(255), nullable=False)
    input_text       = Column(Text, nullable=False)
    must_have        = Column(JSON, default=list)       # list[str]
    nice_to_have     = Column(JSON, default=list)
    exclude_keywords = Column(JSON, default=list)
    short_boolean    = Column(Text, nullable=True)
    advanced_boolean = Column(Text, nullable=True)
    alternate_boolean = Column(Text, nullable=True)
    linkedin_search  = Column(Text, nullable=True)
    naukri_search    = Column(Text, nullable=True)
    indeed_search    = Column(Text, nullable=True)
    structured_data  = Column(JSON, default=dict)
    created_at       = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    user        = relationship("User", foreign_keys=[user_id], lazy="select")
    source_jd   = relationship("GeneratedJD", back_populates="boolean_searches", lazy="select")


# ────────────────────────────────────────────────────────────────────────────
# JD Analysis Result
# ────────────────────────────────────────────────────────────────────────────

class JDAnalysisResult(Base):
    __tablename__ = "jd_analysis_results_backend"

    id                  = Column(Integer, primary_key=True, index=True)
    user_id             = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    source_jd_text      = Column(Text, nullable=False)
    must_have_skills    = Column(JSON, default=list)
    nice_to_have_skills = Column(JSON, default=list)
    alternate_titles    = Column(JSON, default=list)
    skill_clusters      = Column(JSON, default=dict)
    suggested_questions = Column(JSON, default=list)
    screening_criteria  = Column(JSON, default=dict)
    created_at          = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    user = relationship("User", foreign_keys=[user_id], lazy="select")

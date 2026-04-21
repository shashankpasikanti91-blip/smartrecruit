"""
Communication Hub models — SRP SmartRecruit v4.0
Providers, templates, logs for Email/WhatsApp/Telegram
"""

from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Text,
    ForeignKey, JSON
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.connection import Base


class CommunicationProvider(Base):
    __tablename__ = "communication_providers_backend"

    id              = Column(Integer, primary_key=True, index=True)
    user_id         = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    channel         = Column(String(30), nullable=False, index=True)
    provider_name   = Column(String(80), nullable=False)
    is_active       = Column(Boolean, default=False)
    is_default      = Column(Boolean, default=False)
    config          = Column(JSON, default=dict)
    test_passed     = Column(Boolean, nullable=True)
    last_tested_at  = Column(DateTime(timezone=True), nullable=True)
    created_at      = Column(DateTime(timezone=True), server_default=func.now())
    updated_at      = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user            = relationship("User", foreign_keys=[user_id], lazy="select")
    logs            = relationship("CommunicationLog", back_populates="provider",
                                   cascade="all, delete-orphan", lazy="select")


class CommunicationTemplate(Base):
    __tablename__ = "communication_templates_backend"

    id              = Column(Integer, primary_key=True, index=True)
    user_id         = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name            = Column(String(120), nullable=False)
    channel         = Column(String(30), nullable=False, index=True)
    purpose         = Column(String(60), nullable=False, index=True)
    subject         = Column(String(255), nullable=True)
    body_template   = Column(Text, nullable=False)
    variables       = Column(JSON, default=list)
    is_active       = Column(Boolean, default=True)
    created_at      = Column(DateTime(timezone=True), server_default=func.now())
    updated_at      = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user            = relationship("User", foreign_keys=[user_id], lazy="select")


class CommunicationLog(Base):
    __tablename__ = "communication_logs_backend"

    id              = Column(Integer, primary_key=True, index=True)
    user_id         = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    provider_id     = Column(Integer, ForeignKey("communication_providers_backend.id"), nullable=True)
    template_id     = Column(Integer, ForeignKey("communication_templates_backend.id"), nullable=True)
    channel         = Column(String(30), nullable=False, index=True)
    recipient       = Column(String(255), nullable=False)
    subject         = Column(String(255), nullable=True)
    body_preview    = Column(String(500), nullable=True)
    status          = Column(String(20), nullable=False, default="pending", index=True)
    error_message   = Column(Text, nullable=True)
    external_id     = Column(String(255), nullable=True)
    retry_count     = Column(Integer, default=0)
    resource_type   = Column(String(60), nullable=True)
    resource_id     = Column(String(80), nullable=True)
    metadata        = Column(JSON, default=dict)
    sent_at         = Column(DateTime(timezone=True), nullable=True)
    delivered_at    = Column(DateTime(timezone=True), nullable=True)
    created_at      = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    user            = relationship("User", foreign_keys=[user_id], lazy="select")
    provider        = relationship("CommunicationProvider", back_populates="logs")

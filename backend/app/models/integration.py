"""
Integration Hub models for SRP SmartRecruit v4.0
Connector registry, credentials, sync logs
"""

from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Text,
    ForeignKey, JSON
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.connection import Base


class Integration(Base):
    __tablename__ = "integrations_backend"

    id            = Column(Integer, primary_key=True, index=True)
    user_id       = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name          = Column(String(120), nullable=False)
    slug          = Column(String(80), nullable=False, index=True)
    category      = Column(String(60), nullable=False)
    status        = Column(String(30), nullable=False, default="inactive")
    auth_method   = Column(String(40), nullable=False, default="api_key")
    mode          = Column(String(30), nullable=False, default="manual")
    direction     = Column(String(20), nullable=False, default="outbound")
    webhook_url   = Column(Text, nullable=True)
    scopes        = Column(JSON, default=list)
    config        = Column(JSON, default=dict)
    last_sync_at  = Column(DateTime(timezone=True), nullable=True)
    last_error    = Column(Text, nullable=True)
    error_count   = Column(Integer, default=0)
    created_at    = Column(DateTime(timezone=True), server_default=func.now())
    updated_at    = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user          = relationship("User", foreign_keys=[user_id], lazy="select")
    credentials   = relationship("ConnectorCredential", back_populates="integration",
                                 cascade="all, delete-orphan", lazy="select")
    sync_logs     = relationship("ConnectorSyncLog", back_populates="integration",
                                 cascade="all, delete-orphan", lazy="select")


class ConnectorCredential(Base):
    __tablename__ = "connector_credentials_backend"

    id              = Column(Integer, primary_key=True, index=True)
    integration_id  = Column(Integer, ForeignKey("integrations_backend.id"), nullable=False, index=True)
    user_id         = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    credential_type = Column(String(60), nullable=False)
    encrypted_value = Column(Text, nullable=False)      # AES-256 encrypted
    key_hint        = Column(String(20), nullable=True) # e.g. "••••ab12"
    is_active       = Column(Boolean, default=True)
    last_used_at    = Column(DateTime(timezone=True), nullable=True)
    expires_at      = Column(DateTime(timezone=True), nullable=True)
    rotated_at      = Column(DateTime(timezone=True), nullable=True)
    created_at      = Column(DateTime(timezone=True), server_default=func.now())
    updated_at      = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    integration     = relationship("Integration", back_populates="credentials")
    user            = relationship("User", foreign_keys=[user_id], lazy="select")


class ConnectorSyncLog(Base):
    __tablename__ = "connector_sync_logs_backend"

    id              = Column(Integer, primary_key=True, index=True)
    integration_id  = Column(Integer, ForeignKey("integrations_backend.id"), nullable=False, index=True)
    user_id         = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    direction       = Column(String(10), nullable=False)
    status          = Column(String(20), nullable=False)
    records_total   = Column(Integer, default=0)
    records_ok      = Column(Integer, default=0)
    records_failed  = Column(Integer, default=0)
    error_detail    = Column(Text, nullable=True)
    payload         = Column(JSON, default=dict)
    started_at      = Column(DateTime(timezone=True), server_default=func.now())
    finished_at     = Column(DateTime(timezone=True), nullable=True)
    duration_ms     = Column(Integer, nullable=True)

    integration     = relationship("Integration", back_populates="sync_logs")
    user            = relationship("User", foreign_keys=[user_id], lazy="select")

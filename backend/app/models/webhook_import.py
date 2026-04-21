"""
Webhook + Import models — SRP SmartRecruit v4.0
"""

from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Text,
    BigInteger, ForeignKey, JSON
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.connection import Base


# ────────────────────────────────────────────────────────────────────────────
# Webhooks (outbound event subscriptions)
# ────────────────────────────────────────────────────────────────────────────

class WebhookSubscription(Base):
    __tablename__ = "webhook_subscriptions_backend"

    id                = Column(Integer, primary_key=True, index=True)
    user_id           = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name              = Column(String(120), nullable=False)
    target_url        = Column(Text, nullable=False)
    secret            = Column(Text, nullable=False)    # HMAC signing secret (encrypted)
    events            = Column(JSON, default=list)      # list of event strings
    is_active         = Column(Boolean, default=True)
    verify_ssl        = Column(Boolean, default=True)
    timeout_seconds   = Column(Integer, default=10)
    retry_max         = Column(Integer, default=3)
    last_triggered_at = Column(DateTime(timezone=True), nullable=True)
    failure_count     = Column(Integer, default=0)
    created_at        = Column(DateTime(timezone=True), server_default=func.now())
    updated_at        = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user              = relationship("User", foreign_keys=[user_id], lazy="select")
    delivery_logs     = relationship("WebhookDeliveryLog", back_populates="subscription",
                                     cascade="all, delete-orphan", lazy="select")


class WebhookDeliveryLog(Base):
    __tablename__ = "webhook_delivery_logs_backend"

    id              = Column(Integer, primary_key=True, index=True)
    subscription_id = Column(Integer, ForeignKey("webhook_subscriptions_backend.id"),
                             nullable=False, index=True)
    event_type      = Column(String(80), nullable=False)
    payload         = Column(JSON, nullable=False)
    attempt         = Column(Integer, default=1)
    status          = Column(String(20), nullable=False, index=True)
    http_status     = Column(Integer, nullable=True)
    response_body   = Column(Text, nullable=True)
    error_message   = Column(Text, nullable=True)
    duration_ms     = Column(Integer, nullable=True)
    created_at      = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    subscription    = relationship("WebhookSubscription", back_populates="delivery_logs")


# ────────────────────────────────────────────────────────────────────────────
# Import Batches
# ────────────────────────────────────────────────────────────────────────────

class ImportBatch(Base):
    __tablename__ = "import_batches_backend"

    id              = Column(Integer, primary_key=True, index=True)
    user_id         = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    batch_ref       = Column(String(30), unique=True, index=True)
    import_type     = Column(String(40), nullable=False)
    source_label    = Column(String(120), default="Direct Upload")
    file_name       = Column(String(255), nullable=True)
    file_size_bytes = Column(BigInteger, nullable=True)
    status          = Column(String(20), nullable=False, default="pending", index=True)
    total_rows      = Column(Integer, default=0)
    processed_rows  = Column(Integer, default=0)
    success_rows    = Column(Integer, default=0)
    error_rows      = Column(Integer, default=0)
    skipped_rows    = Column(Integer, default=0)
    config          = Column(JSON, default=dict)
    error_summary   = Column(Text, nullable=True)
    started_at      = Column(DateTime(timezone=True), nullable=True)
    finished_at     = Column(DateTime(timezone=True), nullable=True)
    created_at      = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    user            = relationship("User", foreign_keys=[user_id], lazy="select")
    row_errors      = relationship("ImportRowError", back_populates="batch",
                                   cascade="all, delete-orphan", lazy="select")


class ImportRowError(Base):
    __tablename__ = "import_row_errors_backend"

    id            = Column(Integer, primary_key=True, index=True)
    batch_id      = Column(Integer, ForeignKey("import_batches_backend.id"),
                           nullable=False, index=True)
    row_number    = Column(Integer, nullable=False)
    raw_data      = Column(JSON, nullable=True)
    error_type    = Column(String(80), nullable=True)
    error_message = Column(Text, nullable=False)
    resolution    = Column(String(30), nullable=True)
    created_at    = Column(DateTime(timezone=True), server_default=func.now())

    batch         = relationship("ImportBatch", back_populates="row_errors")

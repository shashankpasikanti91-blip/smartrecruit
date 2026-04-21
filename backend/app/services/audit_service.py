"""
Audit Service — SRP SmartRecruit v4.0
Write structured audit records for every important action
"""

from __future__ import annotations
import logging
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.models.enterprise import AuditLog
from app.models.user import User

logger = logging.getLogger(__name__)


def log_action(
    db: Session,
    *,
    action: str,
    resource_type: str,
    user: Optional[User] = None,
    resource_id: Optional[Any] = None,
    details: Optional[dict] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    result: str = "success",
) -> None:
    """
    Write a single audit log entry.
    Failure to write MUST NOT block the main request — errors are caught.
    """
    try:
        entry = AuditLog(
            user_id       = user.id if user else None,
            user_email    = user.email if user else None,
            action        = action,
            resource_type = resource_type,
            resource_id   = str(resource_id) if resource_id is not None else None,
            details       = details or {},
            ip_address    = ip_address,
            user_agent    = user_agent,
            result        = result,
        )
        db.add(entry)
        db.commit()
    except Exception as exc:
        logger.error("Audit log write failed: %s", exc)
        try:
            db.rollback()
        except Exception:
            pass

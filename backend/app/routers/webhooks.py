"""
Webhook Management Router — SRP SmartRecruit v4.0
Register, list, delete outbound webhook subscriptions; view delivery logs
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, HttpUrl
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database.connection import get_db
from app.auth.dependencies import get_current_verified_user
from app.models.user import User
from app.models.webhook_import import WebhookSubscription
from app.services.webhook_service import WebhookService, WEBHOOK_EVENTS
from app.services.secret_service import encrypt_secret

router = APIRouter(prefix="/api/v4/webhooks", tags=["Webhooks"])


# ─────────────────────────────────────────────────────────────────────────────
# Schemas
# ─────────────────────────────────────────────────────────────────────────────

class RegisterWebhookRequest(BaseModel):
    name:            str = Field(..., min_length=2, max_length=120)
    target_url:      str = Field(..., min_length=10)
    secret:          str = Field(..., min_length=16, max_length=256,
                                 description="HMAC signing secret — min 16 chars")
    events:          List[str]
    verify_ssl:      bool = True
    timeout_seconds: int  = Field(10, ge=5, le=30)
    retry_max:       int  = Field(3,  ge=0, le=5)


class UpdateWebhookRequest(BaseModel):
    name:       Optional[str] = None
    events:     Optional[List[str]] = None
    is_active:  Optional[bool] = None


# ─────────────────────────────────────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/events")
async def list_event_types(
    current_user: User = Depends(get_current_verified_user),
):
    """Return all supported webhook event types."""
    return {"events": WEBHOOK_EVENTS}


@router.post("", status_code=status.HTTP_201_CREATED)
async def register_webhook(
    req: RegisterWebhookRequest,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db),
):
    """
    Register a new outbound webhook subscription.
    The secret is encrypted at rest; only a hint is ever returned.
    """
    encrypted_secret = encrypt_secret(req.secret)
    sub = WebhookService.register(
        db, current_user,
        name            = req.name,
        target_url      = req.target_url,
        events          = req.events,
        encrypted_secret = encrypted_secret,
        verify_ssl      = req.verify_ssl,
        timeout_seconds = req.timeout_seconds,
        retry_max       = req.retry_max,
    )
    return {
        "id":              sub.id,
        "name":            sub.name,
        "target_url":      sub.target_url,
        "events":          sub.events,
        "is_active":       sub.is_active,
        "secret_hint":     "••••••••" + req.secret[-4:],
        "created_at":      sub.created_at.isoformat(),
    }


@router.get("")
async def list_webhooks(
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db),
):
    """List all webhook subscriptions for the current tenant."""
    subs = WebhookService.list_subscriptions(db, current_user)
    return {
        "webhooks": [
            {
                "id":                 s.id,
                "name":               s.name,
                "target_url":         s.target_url,
                "events":             s.events,
                "is_active":          s.is_active,
                "failure_count":      s.failure_count,
                "last_triggered_at":  s.last_triggered_at.isoformat() if s.last_triggered_at else None,
                "created_at":         s.created_at.isoformat(),
            }
            for s in subs
        ]
    }


@router.patch("/{webhook_id}")
async def update_webhook(
    webhook_id: int,
    req: UpdateWebhookRequest,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db),
):
    """Update a webhook subscription (name, events, active status)."""
    sub = (
        db.query(WebhookSubscription)
        .filter(WebhookSubscription.id == webhook_id,
                WebhookSubscription.user_id == current_user.id)
        .first()
    )
    if not sub:
        raise HTTPException(404, detail="Webhook not found")

    if req.name is not None:
        sub.name = req.name
    if req.events is not None:
        invalid = [e for e in req.events if e not in WEBHOOK_EVENTS]
        if invalid:
            raise HTTPException(400, detail=f"Invalid event types: {invalid}")
        sub.events = req.events
    if req.is_active is not None:
        sub.is_active = req.is_active

    db.commit()
    db.refresh(sub)
    return {"message": "Webhook updated", "id": sub.id, "is_active": sub.is_active}


@router.delete("/{webhook_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_webhook(
    webhook_id: int,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db),
):
    """Delete a webhook subscription."""
    sub = (
        db.query(WebhookSubscription)
        .filter(WebhookSubscription.id == webhook_id,
                WebhookSubscription.user_id == current_user.id)
        .first()
    )
    if not sub:
        raise HTTPException(404, detail="Webhook not found")
    db.delete(sub)
    db.commit()


@router.get("/{webhook_id}/logs")
async def get_delivery_logs(
    webhook_id: int,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db),
    limit: int = 20,
):
    """Get recent delivery log for a webhook subscription."""
    from app.models.webhook_import import WebhookDeliveryLog
    # Verify ownership
    sub = (
        db.query(WebhookSubscription)
        .filter(WebhookSubscription.id == webhook_id,
                WebhookSubscription.user_id == current_user.id)
        .first()
    )
    if not sub:
        raise HTTPException(404, detail="Webhook not found")

    logs = (
        db.query(WebhookDeliveryLog)
        .filter(WebhookDeliveryLog.subscription_id == webhook_id)
        .order_by(WebhookDeliveryLog.created_at.desc())
        .limit(min(limit, 100))
        .all()
    )
    return {
        "logs": [
            {
                "id":            l.id,
                "event_type":    l.event_type,
                "attempt":       l.attempt,
                "status":        l.status,
                "http_status":   l.http_status,
                "error_message": l.error_message,
                "duration_ms":   l.duration_ms,
                "created_at":    l.created_at.isoformat(),
            }
            for l in logs
        ]
    }

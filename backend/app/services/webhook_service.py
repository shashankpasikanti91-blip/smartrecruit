"""
Webhook Event Service — SRP SmartRecruit v4.0
Outbound event dispatch with HMAC signing and retry logic
"""

from __future__ import annotations
import hashlib
import hmac
import json
import logging
import time
from datetime import datetime, timezone
from typing import Optional

import httpx
from sqlalchemy.orm import Session

from app.models.webhook_import import WebhookSubscription, WebhookDeliveryLog
from app.models.user import User
from app.services.secret_service import decrypt_secret
from app.services.audit_service import log_action

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Supported event types
# ─────────────────────────────────────────────────────────────────────────────

WEBHOOK_EVENTS = [
    "candidate.created",
    "candidate.updated",
    "candidate.screened",
    "candidate.shortlisted",
    "candidate.rejected",
    "job.created",
    "job.updated",
    "job.published",
    "job.closed",
    "bulk.import.completed",
    "interview.scheduled",
    "message.sent",
    "message.failed",
    "integration.connected",
    "integration.disconnected",
]


# ─────────────────────────────────────────────────────────────────────────────
# HMAC signature
# ─────────────────────────────────────────────────────────────────────────────

def _sign_payload(secret: str, payload_bytes: bytes) -> str:
    return "sha256=" + hmac.new(
        secret.encode(), payload_bytes, hashlib.sha256
    ).hexdigest()


# ─────────────────────────────────────────────────────────────────────────────
# Service
# ─────────────────────────────────────────────────────────────────────────────

class WebhookService:

    @staticmethod
    def register(
        db: Session,
        user: User,
        name: str,
        target_url: str,
        events: list[str],
        encrypted_secret: str,
        verify_ssl: bool = True,
        timeout_seconds: int = 10,
        retry_max: int = 3,
    ) -> WebhookSubscription:
        # Validate events
        invalid = [e for e in events if e not in WEBHOOK_EVENTS]
        if invalid:
            from fastapi import HTTPException
            raise HTTPException(400, detail=f"Invalid event types: {invalid}")

        sub = WebhookSubscription(
            user_id         = user.id,
            name            = name,
            target_url      = target_url,
            secret          = encrypted_secret,
            events          = events,
            is_active       = True,
            verify_ssl      = verify_ssl,
            timeout_seconds = timeout_seconds,
            retry_max       = retry_max,
        )
        db.add(sub)
        db.commit()
        db.refresh(sub)
        log_action(db, action="webhook.registered", resource_type="webhook_subscription",
                   resource_id=sub.id, user=user)
        return sub

    # ─────────────────────────────────────────────────────────────────────────

    @staticmethod
    def list_subscriptions(db: Session, user: User) -> list[WebhookSubscription]:
        return (
            db.query(WebhookSubscription)
            .filter(WebhookSubscription.user_id == user.id)
            .order_by(WebhookSubscription.created_at.desc())
            .all()
        )

    # ─────────────────────────────────────────────────────────────────────────

    @staticmethod
    async def dispatch(
        db: Session,
        user: User,
        event_type: str,
        payload: dict,
        attempt: int = 1,
    ) -> None:
        """
        Dispatch an event to all matching active subscriptions for this user.
        Designed to run in background (fire-and-forget).
        """
        subscriptions = (
            db.query(WebhookSubscription)
            .filter(
                WebhookSubscription.user_id == user.id,
                WebhookSubscription.is_active == True,
            )
            .all()
        )

        for sub in subscriptions:
            if event_type not in (sub.events or []):
                continue

            await WebhookService._deliver(db, sub, event_type, payload, attempt)

    # ─────────────────────────────────────────────────────────────────────────

    @staticmethod
    async def _deliver(
        db: Session,
        sub: WebhookSubscription,
        event_type: str,
        payload: dict,
        attempt: int,
    ) -> WebhookDeliveryLog:
        full_payload = {
            "event": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": payload,
        }
        body_bytes = json.dumps(full_payload, default=str).encode()

        try:
            secret_plain = decrypt_secret(sub.secret)
        except Exception:
            secret_plain = sub.secret  # fallback if already plain (legacy)

        signature = _sign_payload(secret_plain, body_bytes)

        delivery = WebhookDeliveryLog(
            subscription_id = sub.id,
            event_type      = event_type,
            payload         = full_payload,
            attempt         = attempt,
            status          = "pending",
        )
        db.add(delivery)
        db.commit()

        t_start = time.monotonic()
        try:
            async with httpx.AsyncClient(
                verify=sub.verify_ssl,
                timeout=sub.timeout_seconds,
            ) as client:
                resp = await client.post(
                    sub.target_url,
                    content=body_bytes,
                    headers={
                        "Content-Type":       "application/json",
                        "X-SRP-Event":        event_type,
                        "X-SRP-Signature":    signature,
                        "X-SRP-Delivery-Id":  str(delivery.id),
                    },
                )
            duration = int((time.monotonic() - t_start) * 1000)
            if resp.is_success:
                delivery.status      = "delivered"
                delivery.http_status = resp.status_code
                delivery.duration_ms = duration
                sub.last_triggered_at = datetime.now(timezone.utc)
                sub.failure_count = 0
            else:
                raise httpx.HTTPStatusError(
                    f"Non-2xx status {resp.status_code}",
                    request=resp.request,
                    response=resp,
                )

        except Exception as exc:
            duration = int((time.monotonic() - t_start) * 1000)
            delivery.status        = "failed"
            delivery.error_message = str(exc)[:500]
            delivery.duration_ms   = duration
            sub.failure_count      = (sub.failure_count or 0) + 1
            logger.warning("Webhook delivery %s failed attempt %s: %s",
                           delivery.id, attempt, exc)

        db.commit()
        db.refresh(delivery)
        return delivery

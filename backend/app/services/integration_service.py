"""
Integration Hub Service — SRP SmartRecruit v4.0
Connector registry CRUD + credential management
"""

from __future__ import annotations
import logging
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.integration import Integration, ConnectorCredential, ConnectorSyncLog
from app.models.user import User
from app.services.secret_service import encrypt_secret, decrypt_secret, build_key_hint
from app.services.audit_service import log_action

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Connector catalogue — what we support (truthful labels, no fake promises)
# ─────────────────────────────────────────────────────────────────────────────

CONNECTOR_CATALOGUE: list[dict] = [
    # Job Portals
    {"slug": "naukri",       "name": "Naukri",       "category": "job_portal",   "mode": "assisted",    "auth_method": "api_key",     "direction": "bidirectional"},
    {"slug": "indeed",       "name": "Indeed",       "category": "job_portal",   "mode": "assisted",    "auth_method": "api_key",     "direction": "bidirectional"},
    {"slug": "monster",      "name": "Monster",      "category": "job_portal",   "mode": "assisted",    "auth_method": "api_key",     "direction": "bidirectional"},
    {"slug": "linkedin_jobs","name": "LinkedIn Jobs","category": "job_portal",   "mode": "coming_soon", "auth_method": "oauth",       "direction": "outbound"},
    {"slug": "shine",        "name": "Shine",        "category": "job_portal",   "mode": "assisted",    "auth_method": "api_key",     "direction": "bidirectional"},
    # Email
    {"slug": "smtp",         "name": "SMTP / Custom","category": "email",        "mode": "live",        "auth_method": "manual_token","direction": "outbound"},
    {"slug": "sendgrid",     "name": "SendGrid",     "category": "email",        "mode": "live",        "auth_method": "api_key",     "direction": "outbound"},
    {"slug": "mailgun",      "name": "Mailgun",      "category": "email",        "mode": "live",        "auth_method": "api_key",     "direction": "outbound"},
    {"slug": "outlook",      "name": "Outlook/O365", "category": "email",        "mode": "live",        "auth_method": "oauth",       "direction": "outbound"},
    {"slug": "gmail",        "name": "Gmail",        "category": "email",        "mode": "live",        "auth_method": "oauth",       "direction": "outbound"},
    # Messaging
    {"slug": "whatsapp",     "name": "WhatsApp",     "category": "messaging",    "mode": "live",        "auth_method": "api_key",     "direction": "outbound"},
    {"slug": "telegram",     "name": "Telegram Bot", "category": "messaging",    "mode": "live",        "auth_method": "api_key",     "direction": "outbound"},
    # Automation
    {"slug": "n8n",          "name": "n8n",          "category": "automation",   "mode": "live",        "auth_method": "api_key",     "direction": "outbound"},
    {"slug": "make",         "name": "Make (Integromat)", "category": "automation","mode": "live",      "auth_method": "webhook",     "direction": "outbound"},
    {"slug": "zapier",       "name": "Zapier",        "category": "automation",  "mode": "live",        "auth_method": "webhook",     "direction": "outbound"},
    # Storage / Import
    {"slug": "google_drive", "name": "Google Drive", "category": "storage",      "mode": "coming_soon", "auth_method": "oauth",       "direction": "inbound"},
    {"slug": "dropbox",      "name": "Dropbox",      "category": "storage",      "mode": "coming_soon", "auth_method": "oauth",       "direction": "inbound"},
]

CATALOGUE_MAP: dict[str, dict] = {c["slug"]: c for c in CONNECTOR_CATALOGUE}


class IntegrationService:

    @staticmethod
    def get_catalogue() -> list[dict]:
        return CONNECTOR_CATALOGUE

    # ─────────────────────────────────────────────────────────────────────────

    @staticmethod
    def list_integrations(db: Session, user: User) -> list[Integration]:
        return (
            db.query(Integration)
            .filter(Integration.user_id == user.id)
            .order_by(Integration.name)
            .all()
        )

    # ─────────────────────────────────────────────────────────────────────────

    @staticmethod
    def get_integration(db: Session, user: User, integration_id: int) -> Integration:
        rec = (
            db.query(Integration)
            .filter(Integration.id == integration_id, Integration.user_id == user.id)
            .first()
        )
        if not rec:
            raise HTTPException(status_code=404, detail="Integration not found")
        return rec

    # ─────────────────────────────────────────────────────────────────────────

    @staticmethod
    def create_or_update_integration(
        db: Session,
        user: User,
        slug: str,
        name: Optional[str] = None,
        config: Optional[dict] = None,
        webhook_url: Optional[str] = None,
    ) -> Integration:
        """
        Upsert an integration. Validates slug against catalogue.
        """
        catalogue_entry = CATALOGUE_MAP.get(slug)
        if not catalogue_entry and slug != "custom":
            raise HTTPException(
                status_code=400,
                detail=f"Unknown connector slug '{slug}'. Check the integration catalogue.",
            )

        existing = (
            db.query(Integration)
            .filter(Integration.user_id == user.id, Integration.slug == slug)
            .first()
        )

        safe_config = {
            k: v for k, v in (config or {}).items()
            if k not in ("api_key", "token", "password", "secret", "client_secret")
        }

        if existing:
            existing.name        = name or existing.name
            existing.config      = {**existing.config, **safe_config}
            existing.webhook_url = webhook_url or existing.webhook_url
            db.commit()
            db.refresh(existing)
            log_action(db, action="integration.updated", resource_type="integration",
                       resource_id=existing.id, user=user,
                       details={"slug": slug})
            return existing

        category     = catalogue_entry["category"]    if catalogue_entry else "custom"
        auth_method  = catalogue_entry["auth_method"] if catalogue_entry else "api_key"
        mode         = catalogue_entry["mode"]        if catalogue_entry else "manual"
        direction    = catalogue_entry["direction"]   if catalogue_entry else "outbound"

        new_rec = Integration(
            user_id     = user.id,
            name        = name or (catalogue_entry["name"] if catalogue_entry else slug),
            slug        = slug,
            category    = category,
            auth_method = auth_method,
            mode        = mode,
            direction   = direction,
            webhook_url = webhook_url,
            config      = safe_config,
            status      = "inactive",
        )
        db.add(new_rec)
        db.commit()
        db.refresh(new_rec)
        log_action(db, action="integration.created", resource_type="integration",
                   resource_id=new_rec.id, user=user,
                   details={"slug": slug, "category": category})
        return new_rec

    # ─────────────────────────────────────────────────────────────────────────

    @staticmethod
    def save_credential(
        db: Session,
        user: User,
        integration_id: int,
        credential_type: str,
        plaintext_value: str,
    ) -> ConnectorCredential:
        """
        Encrypt and store a credential. Replaces existing credential of same type.
        Never returns the plaintext or the full encrypted value to callers.
        """
        rec = IntegrationService.get_integration(db, user, integration_id)

        # Deactivate existing credential of same type
        existing = (
            db.query(ConnectorCredential)
            .filter(
                ConnectorCredential.integration_id == rec.id,
                ConnectorCredential.credential_type == credential_type,
                ConnectorCredential.is_active == True,
            )
            .first()
        )
        if existing:
            existing.is_active = False
            db.commit()

        encrypted = encrypt_secret(plaintext_value)
        hint      = build_key_hint(plaintext_value)

        cred = ConnectorCredential(
            integration_id  = rec.id,
            user_id         = user.id,
            credential_type = credential_type,
            encrypted_value = encrypted,
            key_hint        = hint,
            is_active       = True,
        )
        db.add(cred)
        db.commit()

        log_action(db, action="credential.saved", resource_type="connector_credential",
                   resource_id=str(rec.id), user=user,
                   details={"type": credential_type, "hint": hint})

        return cred

    # ─────────────────────────────────────────────────────────────────────────

    @staticmethod
    def toggle_integration(
        db: Session,
        user: User,
        integration_id: int,
        enable: bool,
    ) -> Integration:
        rec = IntegrationService.get_integration(db, user, integration_id)
        rec.status = "active" if enable else "inactive"
        db.commit()
        db.refresh(rec)
        log_action(db, action="integration.toggled", resource_type="integration",
                   resource_id=rec.id, user=user,
                   details={"status": rec.status})
        return rec

    # ─────────────────────────────────────────────────────────────────────────

    @staticmethod
    def delete_integration(db: Session, user: User, integration_id: int) -> None:
        rec = IntegrationService.get_integration(db, user, integration_id)
        log_action(db, action="integration.deleted", resource_type="integration",
                   resource_id=rec.id, user=user,
                   details={"slug": rec.slug})
        db.delete(rec)
        db.commit()

    # ─────────────────────────────────────────────────────────────────────────

    @staticmethod
    def add_sync_log(
        db: Session,
        user: User,
        integration_id: int,
        direction: str,
        status: str,
        records_total: int = 0,
        records_ok: int = 0,
        records_failed: int = 0,
        error_detail: Optional[str] = None,
        duration_ms: Optional[int] = None,
    ) -> ConnectorSyncLog:
        from datetime import datetime, timezone
        entry = ConnectorSyncLog(
            integration_id = integration_id,
            user_id        = user.id,
            direction      = direction,
            status         = status,
            records_total  = records_total,
            records_ok     = records_ok,
            records_failed = records_failed,
            error_detail   = error_detail,
            finished_at    = datetime.now(timezone.utc) if status != "running" else None,
            duration_ms    = duration_ms,
        )
        db.add(entry)
        db.commit()
        return entry

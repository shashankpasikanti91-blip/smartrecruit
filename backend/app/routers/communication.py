"""
Communication Hub Router — SRP SmartRecruit v4.0
Email / WhatsApp / Telegram providers, templates, send, logs
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database.connection import get_db
from app.auth.dependencies import get_current_verified_user
from app.models.user import User
from app.services.communication_service import CommunicationService
from app.services.secret_service import encrypt_secret

router = APIRouter(prefix="/api/v4/comms", tags=["Communication Hub"])


# ─────────────────────────────────────────────────────────────────────────────
# Schemas
# ─────────────────────────────────────────────────────────────────────────────

class SaveProviderRequest(BaseModel):
    channel:       str = Field(..., description="email|gmail|outlook|whatsapp|telegram")
    provider_name: str = Field(..., max_length=80)
    # SMTP
    smtp_host:     Optional[str] = None
    smtp_port:     Optional[int] = None
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None      # ← encrypted before storage
    use_tls:       Optional[bool] = True
    from_email:    Optional[str] = None
    # SendGrid / Mailgun
    api_key:       Optional[str] = None      # ← encrypted before storage
    domain:        Optional[str] = None      # Mailgun domain
    # Telegram
    bot_token:     Optional[str] = None      # ← encrypted before storage
    # WhatsApp
    phone_number_id: Optional[str] = None


class SaveTemplateRequest(BaseModel):
    name:          str = Field(..., min_length=2, max_length=120)
    channel:       str
    purpose:       str
    body_template: str = Field(..., min_length=5)
    subject:       Optional[str] = None
    variables:     List[str] = Field(default_factory=list)


class SendMessageRequest(BaseModel):
    channel:       str
    recipient:     str = Field(..., description="Email address, Telegram chat_id, or WhatsApp number")
    subject:       Optional[str] = None
    body:          Optional[str] = None
    template_id:   Optional[int] = None
    provider_id:   Optional[int] = None
    template_vars: Optional[dict] = None
    resource_type: Optional[str] = None
    resource_id:   Optional[str] = None


class ToggleProviderRequest(BaseModel):
    enable: bool


# ─────────────────────────────────────────────────────────────────────────────
# Endpoints — Providers
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/providers", status_code=status.HTTP_201_CREATED)
async def save_provider(
    req: SaveProviderRequest,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db),
):
    """
    Save or update a communication provider.
    Secrets (smtp_password, api_key, bot_token) are encrypted at rest.
    """
    config: dict = {}

    # Build safe config — encrypt all secrets
    if req.smtp_host:       config["smtp_host"]     = req.smtp_host
    if req.smtp_port:       config["smtp_port"]     = req.smtp_port
    if req.smtp_username:   config["smtp_username"] = req.smtp_username
    if req.from_email:      config["from_email"]    = req.from_email
    if req.use_tls is not None: config["use_tls"]   = req.use_tls
    if req.domain:          config["domain"]        = req.domain
    if req.phone_number_id: config["phone_number_id"] = req.phone_number_id

    # Encrypt secrets
    if req.smtp_password:
        config["smtp_password_enc"] = encrypt_secret(req.smtp_password)
    if req.api_key:
        config["api_key_enc"] = encrypt_secret(req.api_key)
    if req.bot_token:
        config["bot_token_enc"] = encrypt_secret(req.bot_token)

    provider = CommunicationService.save_provider(
        db, current_user, req.channel, req.provider_name, config
    )
    return {
        "id":            provider.id,
        "channel":       provider.channel,
        "provider_name": provider.provider_name,
        "is_active":     provider.is_active,
        "created_at":    provider.created_at.isoformat(),
    }


@router.get("/providers")
async def list_providers(
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db),
):
    """List all communication providers (secrets never returned)."""
    providers = CommunicationService.list_providers(db, current_user)
    return {
        "providers": [
            {
                "id":            p.id,
                "channel":       p.channel,
                "provider_name": p.provider_name,
                "is_active":     p.is_active,
                "is_default":    p.is_default,
                "test_passed":   p.test_passed,
                "last_tested_at": p.last_tested_at.isoformat() if p.last_tested_at else None,
            }
            for p in providers
        ]
    }


@router.post("/providers/{provider_id}/toggle")
async def toggle_provider(
    provider_id: int,
    req: ToggleProviderRequest,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db),
):
    """Enable or disable a communication provider."""
    p = CommunicationService.toggle_provider(db, current_user, provider_id, req.enable)
    return {"message": f"Provider {'enabled' if req.enable else 'disabled'}",
            "is_active": p.is_active}


# ─────────────────────────────────────────────────────────────────────────────
# Endpoints — Templates
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/templates", status_code=status.HTTP_201_CREATED)
async def save_template(
    req: SaveTemplateRequest,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db),
):
    """Create a reusable message template with {{variable}} placeholders."""
    tmpl = CommunicationService.save_template(
        db, current_user,
        name          = req.name,
        channel       = req.channel,
        purpose       = req.purpose,
        body_template = req.body_template,
        subject       = req.subject,
        variables     = req.variables,
    )
    return {
        "id":       tmpl.id,
        "name":     tmpl.name,
        "channel":  tmpl.channel,
        "purpose":  tmpl.purpose,
        "variables": tmpl.variables,
    }


@router.get("/templates")
async def list_templates(
    channel: Optional[str] = None,
    purpose: Optional[str] = None,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db),
):
    """List message templates, optionally filtered by channel and purpose."""
    templates = CommunicationService.list_templates(db, current_user, channel, purpose)
    return {
        "templates": [
            {
                "id":            t.id,
                "name":          t.name,
                "channel":       t.channel,
                "purpose":       t.purpose,
                "subject":       t.subject,
                "body_template": t.body_template,
                "variables":     t.variables,
                "is_active":     t.is_active,
            }
            for t in templates
        ]
    }


# ─────────────────────────────────────────────────────────────────────────────
# Endpoints — Send
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/send")
async def send_message(
    req: SendMessageRequest,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db),
):
    """
    Send a single message via the specified channel.
    Provide either body directly or template_id + template_vars.
    Message is logged regardless of delivery success.
    """
    if not req.body and not req.template_id:
        raise HTTPException(
            status_code=400,
            detail="Provide either 'body' or 'template_id' with 'template_vars'",
        )

    log = CommunicationService.send_message(
        db, current_user,
        channel       = req.channel,
        recipient     = req.recipient,
        body          = req.body or "",
        subject       = req.subject,
        provider_id   = req.provider_id,
        template_id   = req.template_id,
        resource_type = req.resource_type,
        resource_id   = req.resource_id,
        template_vars = req.template_vars,
    )
    return {
        "id":          log.id,
        "status":      log.status,
        "channel":     log.channel,
        "recipient":   log.recipient,
        "error":       log.error_message if log.status == "failed" else None,
        "sent_at":     log.sent_at.isoformat() if log.sent_at else None,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Endpoints — Logs
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/logs")
async def communication_logs(
    channel: Optional[str] = None,
    status:  Optional[str] = None,
    limit:   int = 50,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db),
):
    """List recent message delivery logs (body preview only — no full PII)."""
    logs = CommunicationService.list_logs(db, current_user, channel, status, limit)
    return {
        "logs": [
            {
                "id":           l.id,
                "channel":      l.channel,
                "recipient":    l.recipient,
                "subject":      l.subject,
                "body_preview": l.body_preview,
                "status":       l.status,
                "error":        l.error_message,
                "sent_at":      l.sent_at.isoformat() if l.sent_at else None,
                "created_at":   l.created_at.isoformat(),
            }
            for l in logs
        ]
    }

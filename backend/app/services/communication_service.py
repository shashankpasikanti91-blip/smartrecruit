"""
Communication Hub Service — SRP SmartRecruit v4.0
Email (SMTP/SendGrid/Mailgun), WhatsApp, Telegram dispatch
with template rendering, delivery logging, and audit trail
"""

from __future__ import annotations
import logging
import os
import re
import smtplib
import ssl
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

from sqlalchemy.orm import Session

from app.models.communication import (
    CommunicationProvider,
    CommunicationTemplate,
    CommunicationLog,
)
from app.models.user import User
from app.services.audit_service import log_action
from app.services.secret_service import decrypt_secret

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Template rendering
# ─────────────────────────────────────────────────────────────────────────────

def render_template(template_body: str, variables: dict) -> str:
    """
    Replace {{variable_name}} placeholders with values.
    Unknown placeholders are left unchanged (safe).
    """
    def replacer(m: re.Match) -> str:
        key = m.group(1).strip()
        return str(variables.get(key, m.group(0)))
    return re.sub(r"\{\{([^}]+)\}\}", replacer, template_body)


# ─────────────────────────────────────────────────────────────────────────────
# Channel dispatchers
# ─────────────────────────────────────────────────────────────────────────────

def _send_smtp(
    host: str,
    port: int,
    username: str,
    password: str,
    use_tls: bool,
    from_address: str,
    to_address: str,
    subject: str,
    body: str,
) -> str:
    """Send via plain SMTP. Returns 'ok' on success, raises on failure."""
    ctx = ssl.create_default_context()
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = from_address
    msg["To"]      = to_address
    msg.attach(MIMEText(body, "plain"))

    if use_tls and port == 465:
        with smtplib.SMTP_SSL(host, port, context=ctx) as server:
            server.login(username, password)
            server.sendmail(from_address, [to_address], msg.as_string())
    else:
        with smtplib.SMTP(host, port) as server:
            if use_tls:
                server.starttls(context=ctx)
            server.login(username, password)
            server.sendmail(from_address, [to_address], msg.as_string())
    return "ok"


def _send_sendgrid(api_key: str, from_address: str, to_address: str,
                   subject: str, body: str) -> str:
    """Send via SendGrid REST API."""
    import httpx
    payload = {
        "personalizations": [{"to": [{"email": to_address}]}],
        "from": {"email": from_address},
        "subject": subject,
        "content": [{"type": "text/plain", "value": body}],
    }
    r = httpx.post(
        "https://api.sendgrid.com/v3/mail/send",
        json=payload,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        timeout=20,
    )
    if not r.is_success:
        raise RuntimeError(f"SendGrid error {r.status_code}: {r.text[:300]}")
    return "ok"


def _send_mailgun(api_key: str, domain: str, from_address: str,
                  to_address: str, subject: str, body: str) -> str:
    """Send via Mailgun REST API."""
    import httpx
    r = httpx.post(
        f"https://api.mailgun.net/v3/{domain}/messages",
        auth=("api", api_key),
        data={"from": from_address, "to": to_address,
              "subject": subject, "text": body},
        timeout=20,
    )
    if not r.is_success:
        raise RuntimeError(f"Mailgun error {r.status_code}: {r.text[:300]}")
    return r.json().get("id", "ok")


def _send_telegram(bot_token: str, chat_id: str, text: str) -> str:
    """Send via Telegram Bot API."""
    import httpx
    r = httpx.post(
        f"https://api.telegram.org/bot{bot_token}/sendMessage",
        json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"},
        timeout=15,
    )
    if not r.is_success:
        raise RuntimeError(f"Telegram error {r.status_code}: {r.text[:300]}")
    return str(r.json().get("result", {}).get("message_id", "ok"))


def _send_whatsapp(api_key: str, phone_number_id: str, to: str, text: str) -> str:
    """
    Send via WhatsApp Business Cloud API (Meta).
    Requires: phone_number_id (from Meta dashboard), api_key (access token).
    """
    import httpx
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": text},
    }
    r = httpx.post(
        f"https://graph.facebook.com/v18.0/{phone_number_id}/messages",
        json=payload,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        timeout=20,
    )
    if not r.is_success:
        raise RuntimeError(f"WhatsApp API error {r.status_code}: {r.text[:300]}")
    return r.json().get("messages", [{}])[0].get("id", "ok")


# ─────────────────────────────────────────────────────────────────────────────
# Main service
# ─────────────────────────────────────────────────────────────────────────────

class CommunicationService:

    # ── Provider CRUD ─────────────────────────────────────────────────────────

    @staticmethod
    def save_provider(
        db: Session,
        user: User,
        channel: str,
        provider_name: str,
        config: dict,           # safe config (no raw secrets)
    ) -> CommunicationProvider:
        existing = (
            db.query(CommunicationProvider)
            .filter(
                CommunicationProvider.user_id      == user.id,
                CommunicationProvider.channel      == channel,
                CommunicationProvider.provider_name == provider_name,
            )
            .first()
        )
        if existing:
            existing.config     = {**existing.config, **config}
            existing.updated_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(existing)
            return existing

        provider = CommunicationProvider(
            user_id       = user.id,
            channel       = channel,
            provider_name = provider_name,
            config        = config,
            is_active     = False,
        )
        db.add(provider)
        db.commit()
        db.refresh(provider)
        log_action(db, action="comm_provider.created", resource_type="communication_provider",
                   resource_id=provider.id, user=user,
                   details={"channel": channel, "provider": provider_name})
        return provider

    @staticmethod
    def list_providers(db: Session, user: User) -> list[CommunicationProvider]:
        return (
            db.query(CommunicationProvider)
            .filter(CommunicationProvider.user_id == user.id)
            .order_by(CommunicationProvider.channel)
            .all()
        )

    @staticmethod
    def toggle_provider(db: Session, user: User, provider_id: int, enable: bool) -> CommunicationProvider:
        provider = (
            db.query(CommunicationProvider)
            .filter(CommunicationProvider.id == provider_id,
                    CommunicationProvider.user_id == user.id)
            .first()
        )
        if not provider:
            from fastapi import HTTPException
            raise HTTPException(404, detail="Provider not found")
        provider.is_active = enable
        db.commit()
        db.refresh(provider)
        return provider

    # ── Template CRUD ─────────────────────────────────────────────────────────

    @staticmethod
    def save_template(
        db: Session,
        user: User,
        name: str,
        channel: str,
        purpose: str,
        body_template: str,
        subject: Optional[str] = None,
        variables: Optional[list] = None,
    ) -> CommunicationTemplate:
        tmpl = CommunicationTemplate(
            user_id       = user.id,
            name          = name,
            channel       = channel,
            purpose       = purpose,
            subject       = subject,
            body_template = body_template,
            variables     = variables or [],
        )
        db.add(tmpl)
        db.commit()
        db.refresh(tmpl)
        return tmpl

    @staticmethod
    def list_templates(
        db: Session, user: User,
        channel: Optional[str] = None,
        purpose: Optional[str] = None,
    ) -> list[CommunicationTemplate]:
        q = db.query(CommunicationTemplate).filter(CommunicationTemplate.user_id == user.id)
        if channel:
            q = q.filter(CommunicationTemplate.channel == channel)
        if purpose:
            q = q.filter(CommunicationTemplate.purpose == purpose)
        return q.order_by(CommunicationTemplate.created_at.desc()).all()

    # ── Send message ──────────────────────────────────────────────────────────

    @staticmethod
    def send_message(
        db: Session,
        user: User,
        channel: str,
        recipient: str,
        body: str,
        subject: Optional[str] = None,
        provider_id: Optional[int] = None,
        template_id: Optional[int] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        template_vars: Optional[dict] = None,
    ) -> CommunicationLog:
        """
        Dispatch a message and record result in communication_logs.
        Supports: email (smtp/sendgrid/mailgun), telegram, whatsapp.
        """
        # Resolve template if provided
        if template_id:
            tmpl = (
                db.query(CommunicationTemplate)
                .filter(CommunicationTemplate.id == template_id,
                        CommunicationTemplate.user_id == user.id)
                .first()
            )
            if tmpl:
                body    = render_template(tmpl.body_template, template_vars or {})
                subject = subject or (
                    render_template(tmpl.subject, template_vars or {}) if tmpl.subject else None
                )

        # Resolve provider
        provider: Optional[CommunicationProvider] = None
        if provider_id:
            provider = (
                db.query(CommunicationProvider)
                .filter(CommunicationProvider.id == provider_id,
                        CommunicationProvider.user_id == user.id)
                .first()
            )
        else:
            provider = (
                db.query(CommunicationProvider)
                .filter(
                    CommunicationProvider.user_id  == user.id,
                    CommunicationProvider.channel  == channel,
                    CommunicationProvider.is_active == True,
                    CommunicationProvider.is_default == True,
                )
                .first()
            )

        # Create log record
        log = CommunicationLog(
            user_id       = user.id,
            provider_id   = provider.id if provider else None,
            template_id   = template_id,
            channel       = channel,
            recipient     = recipient,
            subject       = subject,
            body_preview  = body[:500],
            status        = "pending",
            resource_type = resource_type,
            resource_id   = str(resource_id) if resource_id else None,
        )
        db.add(log)
        db.commit()

        # Dispatch
        try:
            external_id = CommunicationService._dispatch(
                channel, provider, recipient, subject or "", body
            )
            log.status      = "sent"
            log.external_id = external_id
            log.sent_at     = datetime.now(timezone.utc)
        except Exception as exc:
            log.status        = "failed"
            log.error_message = str(exc)[:1000]
            logger.error("CommunicationService send failed: %s", exc)

        db.commit()
        db.refresh(log)
        log_action(db, action=f"message.{log.status}", resource_type="communication_log",
                   resource_id=log.id, user=user,
                   details={"channel": channel, "recipient": recipient[:50]})
        return log

    @staticmethod
    def _dispatch(
        channel: str,
        provider: Optional[CommunicationProvider],
        recipient: str,
        subject: str,
        body: str,
    ) -> str:
        if not provider:
            raise RuntimeError(
                f"No active {channel} provider configured. "
                "Go to Settings → Communication to configure one."
            )

        cfg = provider.config or {}

        # ── Email ────────────────────────────────────────────────────────────
        if provider.channel in ("email", "gmail", "outlook"):
            pname = provider.provider_name.lower()

            if "sendgrid" in pname:
                api_key = decrypt_secret(cfg.get("api_key_enc", ""))
                return _send_sendgrid(api_key, cfg.get("from_email", ""), recipient, subject, body)

            if "mailgun" in pname:
                api_key = decrypt_secret(cfg.get("api_key_enc", ""))
                return _send_mailgun(
                    api_key, cfg.get("domain", ""),
                    cfg.get("from_email", ""), recipient, subject, body
                )

            # Default: SMTP
            return _send_smtp(
                host         = cfg.get("smtp_host", "smtp.gmail.com"),
                port         = int(cfg.get("smtp_port", 587)),
                username     = cfg.get("smtp_username", ""),
                password     = decrypt_secret(cfg.get("smtp_password_enc", "")),
                use_tls      = cfg.get("use_tls", True),
                from_address = cfg.get("from_email", cfg.get("smtp_username", "")),
                to_address   = recipient,
                subject      = subject,
                body         = body,
            )

        # ── Telegram ─────────────────────────────────────────────────────────
        if provider.channel == "telegram":
            bot_token = decrypt_secret(cfg.get("bot_token_enc", ""))
            chat_id   = recipient  # recipient is the chat_id for Telegram
            return _send_telegram(bot_token, chat_id, body)

        # ── WhatsApp ─────────────────────────────────────────────────────────
        if provider.channel == "whatsapp":
            api_key         = decrypt_secret(cfg.get("api_key_enc", ""))
            phone_number_id = cfg.get("phone_number_id", "")
            return _send_whatsapp(api_key, phone_number_id, recipient, body)

        raise RuntimeError(f"Channel '{provider.channel}' dispatch not implemented yet.")

    # ── Logs ──────────────────────────────────────────────────────────────────

    @staticmethod
    def list_logs(
        db: Session, user: User,
        channel: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
    ) -> list[CommunicationLog]:
        q = db.query(CommunicationLog).filter(CommunicationLog.user_id == user.id)
        if channel:
            q = q.filter(CommunicationLog.channel == channel)
        if status:
            q = q.filter(CommunicationLog.status == status)
        return q.order_by(CommunicationLog.created_at.desc()).limit(min(limit, 200)).all()

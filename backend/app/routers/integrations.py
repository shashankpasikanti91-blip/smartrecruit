"""
Integration Hub Router — SRP SmartRecruit v4.0
Connector registry, credential management, sync logs
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database.connection import get_db
from app.auth.dependencies import get_current_verified_user
from app.models.user import User
from app.services.integration_service import IntegrationService

router = APIRouter(prefix="/api/v4/integrations", tags=["Integration Hub"])


# ─────────────────────────────────────────────────────────────────────────────
# Schemas
# ─────────────────────────────────────────────────────────────────────────────

class UpsertIntegrationRequest(BaseModel):
    slug:        str = Field(..., max_length=80)
    name:        Optional[str] = None
    config:      Optional[dict] = None
    webhook_url: Optional[str] = None


class SaveCredentialRequest(BaseModel):
    integration_id:  int
    credential_type: str = Field(..., max_length=60)
    value:           str = Field(..., min_length=1, max_length=10000)


class ToggleRequest(BaseModel):
    enable: bool


def _serialize(rec) -> dict:
    return {
        "id":           rec.id,
        "name":         rec.name,
        "slug":         rec.slug,
        "category":     rec.category,
        "status":       rec.status,
        "auth_method":  rec.auth_method,
        "mode":         rec.mode,
        "direction":    rec.direction,
        "webhook_url":  rec.webhook_url,
        "scopes":       rec.scopes or [],
        "last_sync_at": rec.last_sync_at.isoformat() if rec.last_sync_at else None,
        "last_error":   rec.last_error,
        "error_count":  rec.error_count,
        "created_at":   rec.created_at.isoformat(),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/catalogue")
async def get_catalogue(
    current_user: User = Depends(get_current_verified_user),
):
    """
    Return the full connector catalogue — what the system supports.
    Honest mode labels: live / assisted / manual / coming_soon.
    """
    return {"catalogue": IntegrationService.get_catalogue()}


@router.get("")
async def list_integrations(
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db),
):
    """List all integrations configured by the current tenant."""
    records = IntegrationService.list_integrations(db, current_user)
    return {"integrations": [_serialize(r) for r in records]}


@router.post("", status_code=status.HTTP_201_CREATED)
async def upsert_integration(
    req: UpsertIntegrationRequest,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db),
):
    """Create or update an integration entry."""
    rec = IntegrationService.create_or_update_integration(
        db, current_user,
        slug        = req.slug,
        name        = req.name,
        config      = req.config,
        webhook_url = req.webhook_url,
    )
    return _serialize(rec)


@router.post("/credentials")
async def save_credential(
    req: SaveCredentialRequest,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db),
):
    """
    Save/rotate an encrypted credential for an integration.
    The full secret is NEVER returned in any response.
    """
    cred = IntegrationService.save_credential(
        db, current_user,
        integration_id  = req.integration_id,
        credential_type = req.credential_type,
        plaintext_value = req.value,
    )
    return {
        "message":         "Credential saved successfully",
        "credential_type": cred.credential_type,
        "hint":            cred.key_hint,
        "created_at":      cred.created_at.isoformat(),
    }


@router.post("/{integration_id}/toggle")
async def toggle_integration(
    integration_id: int,
    req: ToggleRequest,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db),
):
    """Enable or disable an integration."""
    rec = IntegrationService.toggle_integration(db, current_user, integration_id, req.enable)
    return {"message": f"Integration {'enabled' if req.enable else 'disabled'}",
            "status": rec.status}


@router.delete("/{integration_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_integration(
    integration_id: int,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db),
):
    """Permanently delete an integration and its credentials."""
    IntegrationService.delete_integration(db, current_user, integration_id)


@router.get("/{integration_id}/sync-logs")
async def get_sync_logs(
    integration_id: int,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db),
    limit: int = 20,
):
    """Get recent sync logs for an integration."""
    # Verify ownership first
    IntegrationService.get_integration(db, current_user, integration_id)

    from app.models.integration import ConnectorSyncLog
    logs = (
        db.query(ConnectorSyncLog)
        .filter(
            ConnectorSyncLog.integration_id == integration_id,
            ConnectorSyncLog.user_id == current_user.id,
        )
        .order_by(ConnectorSyncLog.started_at.desc())
        .limit(min(limit, 50))
        .all()
    )
    return {
        "logs": [
            {
                "id":             l.id,
                "direction":      l.direction,
                "status":         l.status,
                "records_total":  l.records_total,
                "records_ok":     l.records_ok,
                "records_failed": l.records_failed,
                "error_detail":   l.error_detail,
                "duration_ms":    l.duration_ms,
                "started_at":     l.started_at.isoformat(),
                "finished_at":    l.finished_at.isoformat() if l.finished_at else None,
            }
            for l in logs
        ]
    }

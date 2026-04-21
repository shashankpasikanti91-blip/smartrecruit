"""
Import Engine Router — SRP SmartRecruit v4.0
CSV / XLSX candidate import, batch tracking, error reports
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional

from app.database.connection import get_db
from app.auth.dependencies import get_current_verified_user
from app.models.user import User
from app.services.import_service import ImportService

router = APIRouter(prefix="/api/v4/import", tags=["Import Engine"])

_ALLOWED_MIME = {
    "text/csv",
    "application/csv",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "text/plain",
}
_MAX_SIZE = 10 * 1024 * 1024  # 10 MB


@router.post("/candidates", status_code=status.HTTP_202_ACCEPTED)
async def import_candidates_csv(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    source_label: str = Form(default="Direct Upload"),
    duplicate_action: str = Form(default="skip"),
    job_post_id: Optional[str] = Form(default=None),
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db),
):
    """
    Import candidates from a CSV file.

    - File must be CSV (max 10 MB).
    - Required columns: candidate_name or candidate_email (at least one).
    - Optional columns: candidate_phone, current_company, pipeline_stage, reviewer_notes, file_url.
    - duplicate_action: skip | merge | create
    - Returns batch reference immediately; processing runs in background.
    """
    # Security: validate file type
    content_type = file.content_type or ""
    file_name    = file.filename or "upload.csv"

    if not file_name.lower().endswith((".csv", ".txt", ".xlsx", ".xls")):
        raise HTTPException(
            status_code=400,
            detail="Only .csv, .txt, .xlsx, and .xls files are accepted",
        )

    content = await file.read()

    if len(content) > _MAX_SIZE:
        raise HTTPException(status_code=413, detail="File exceeds 10 MB limit")

    if len(content) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    # Validate duplicate_action
    if duplicate_action not in ("skip", "merge", "create"):
        raise HTTPException(400, detail="duplicate_action must be skip | merge | create")

    batch = ImportService.start_batch(
        db, current_user,
        import_type     = "candidates_csv",
        file_name       = file_name,
        file_size_bytes = len(content),
        source_label    = source_label,
    )

    # Process in background so response is immediate
    background_tasks.add_task(
        ImportService.process_candidates_csv,
        db, current_user, content, batch, duplicate_action, job_post_id
    )

    return {
        "message":    "Import started. Check batch status for results.",
        "batch_id":   batch.id,
        "batch_ref":  batch.batch_ref,
        "file_name":  file_name,
        "status":     batch.status,
    }


@router.get("/batches")
async def list_import_batches(
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db),
    limit: int = 20,
):
    """List all import batches for the current user."""
    batches = ImportService.list_batches(db, current_user, limit)
    return {
        "batches": [
            {
                "id":             b.id,
                "batch_ref":      b.batch_ref,
                "import_type":    b.import_type,
                "source_label":   b.source_label,
                "file_name":      b.file_name,
                "status":         b.status,
                "total_rows":     b.total_rows,
                "success_rows":   b.success_rows,
                "error_rows":     b.error_rows,
                "skipped_rows":   b.skipped_rows,
                "started_at":     b.started_at.isoformat() if b.started_at else None,
                "finished_at":    b.finished_at.isoformat() if b.finished_at else None,
                "created_at":     b.created_at.isoformat(),
            }
            for b in batches
        ]
    }


@router.get("/batches/{batch_id}")
async def get_import_batch(
    batch_id: int,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db),
):
    """Get full status and summary of a specific import batch."""
    batch = ImportService.get_batch(db, current_user, batch_id)
    if not batch:
        raise HTTPException(404, detail="Import batch not found")
    return {
        "id":             batch.id,
        "batch_ref":      batch.batch_ref,
        "import_type":    batch.import_type,
        "source_label":   batch.source_label,
        "file_name":      batch.file_name,
        "status":         batch.status,
        "total_rows":     batch.total_rows,
        "processed_rows": batch.processed_rows,
        "success_rows":   batch.success_rows,
        "error_rows":     batch.error_rows,
        "skipped_rows":   batch.skipped_rows,
        "error_summary":  batch.error_summary,
        "started_at":     batch.started_at.isoformat() if batch.started_at else None,
        "finished_at":    batch.finished_at.isoformat() if batch.finished_at else None,
        "created_at":     batch.created_at.isoformat(),
    }


@router.get("/batches/{batch_id}/errors")
async def get_import_errors(
    batch_id: int,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db),
):
    """Get all row-level errors for an import batch."""
    errors = ImportService.get_batch_errors(db, current_user, batch_id)
    return {
        "errors": [
            {
                "row":     e.row_number,
                "type":    e.error_type,
                "message": e.error_message,
            }
            for e in errors
        ],
        "total": len(errors),
    }


@router.get("/column-map")
async def get_column_map(
    current_user: User = Depends(get_current_verified_user),
):
    """
    Return the supported column mapping for CSV import.
    Use this to build the column-mapping UI on the frontend.
    """
    from app.services.import_service import CANDIDATE_COLUMN_MAP
    return {"column_map": CANDIDATE_COLUMN_MAP}

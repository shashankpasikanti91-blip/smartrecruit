"""
Resume upload router for SRP SmartRecruit v3.2
Handle resume file uploads and text extraction
"""

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pathlib import Path
import io
import re
import time
import uuid

import PyPDF2
import docx

from app.database.connection import get_db
from app.auth.dependencies import get_current_verified_user
from app.models.user import User
from app.models.resume import ResumeMetadata

router = APIRouter(prefix="/api/resume", tags=["Resume"])

_THIS_DIR = Path(__file__).resolve().parent
_BACKEND_DIR = _THIS_DIR.parents[1]
_PROJECT_ROOT = _BACKEND_DIR.parent
UPLOAD_DIR = (
    _PROJECT_ROOT / "uploads" / "resumes"
    if _PROJECT_ROOT != Path("/")
    else _BACKEND_DIR / "uploads" / "resumes"
)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc", ".txt"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


def _sanitize_filename(filename: str) -> str:
    safe_name = Path(filename or "resume").name
    safe_name = re.sub(r"[^A-Za-z0-9._-]", "_", safe_name)
    safe_name = safe_name.strip("._")
    return safe_name or "resume"


def _resolve_user_file_path(file_path: str, user_id: int) -> Path:
    resolved = Path(file_path).resolve()
    user_dir = (UPLOAD_DIR / str(user_id)).resolve()

    try:
        resolved.relative_to(user_dir)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Stored resume path is invalid."
        ) from exc

    if not resolved.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume file not found"
        )

    return resolved


def extract_text_from_pdf(file_content: bytes) -> str:
    """Extract text from PDF file"""
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text.strip()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to extract text from PDF: {str(e)}"
        )


def extract_text_from_docx(file_content: bytes) -> str:
    """Extract text from DOCX file"""
    try:
        doc = docx.Document(io.BytesIO(file_content))
        text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
        return text.strip()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to extract text from DOCX: {str(e)}"
        )


def extract_text_from_file(filename: str, file_content: bytes) -> str:
    """Extract text from resume file based on extension"""
    ext = Path(filename).suffix.lower()

    if ext == ".pdf":
        return extract_text_from_pdf(file_content)
    if ext in [".docx", ".doc"]:
        return extract_text_from_docx(file_content)
    if ext == ".txt":
        return file_content.decode("utf-8")

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"Unsupported file type: {ext}"
    )


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_resume(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """
    Upload resume file
    
    Supported formats: PDF, DOCX, TXT
    Max size: 10MB
    
    Automatically extracts text for AI processing
    """
    # Validate file extension
    original_filename = _sanitize_filename(file.filename or "resume")
    file_ext = Path(original_filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Supported: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Read file content
    file_content = await file.read()
    file_size = len(file_content)
    
    # Validate file size
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size: 10MB"
        )
    
    # Extract text from file
    try:
        extracted_text = extract_text_from_file(original_filename, file_content)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to process file: {str(e)}"
        )
    
    # Save file to disk
    user_upload_dir = UPLOAD_DIR / str(current_user.id)
    user_upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate unique filename
    timestamp = int(time.time())
    saved_filename = f"{timestamp}_{uuid.uuid4().hex}_{original_filename}"
    file_path = user_upload_dir / saved_filename
    
    with open(file_path, "wb") as f:
        f.write(file_content)
    
    # Save metadata to database
    resume = ResumeMetadata(
        user_id=current_user.id,
        filename=original_filename,
        file_path=str(file_path),
        file_size=file_size,
        mime_type=file.content_type or "application/octet-stream",
        extracted_text=extracted_text
    )
    db.add(resume)
    db.commit()
    db.refresh(resume)
    
    return {
        "id": resume.id,
        "filename": resume.filename,
        "file_size": resume.file_size,
        "uploaded_at": resume.uploaded_at,
        "text_length": len(extracted_text)
    }


@router.get("/list")
async def list_resumes(
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """List all uploaded resumes for current user"""
    resumes = db.query(ResumeMetadata).filter(
        ResumeMetadata.user_id == current_user.id
    ).order_by(ResumeMetadata.uploaded_at.desc()).all()
    
    return {
        "resumes": [
            {
                "id": r.id,
                "filename": r.filename,
                "file_size": r.file_size,
                "uploaded_at": r.uploaded_at
            }
            for r in resumes
        ]
    }


@router.get("/{resume_id}/file")
async def download_resume_file(
    resume_id: int,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Download the authenticated user's stored resume file."""
    resume = db.query(ResumeMetadata).filter(
        ResumeMetadata.id == resume_id,
        ResumeMetadata.user_id == current_user.id
    ).first()

    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found"
        )

    file_path = _resolve_user_file_path(resume.file_path, current_user.id)
    return FileResponse(
        path=file_path,
        media_type=resume.mime_type or "application/octet-stream",
        filename=resume.filename
    )


@router.get("/{resume_id}")
async def get_resume(
    resume_id: int,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Get resume details by ID"""
    resume = db.query(ResumeMetadata).filter(
        ResumeMetadata.id == resume_id,
        ResumeMetadata.user_id == current_user.id
    ).first()
    
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found"
        )
    
    return {
        "id": resume.id,
        "filename": resume.filename,
        "file_size": resume.file_size,
        "uploaded_at": resume.uploaded_at,
        "extracted_text": resume.extracted_text[:500] + "..." if len(resume.extracted_text) > 500 else resume.extracted_text
    }


@router.delete("/{resume_id}")
async def delete_resume(
    resume_id: int,
    current_user: User = Depends(get_current_verified_user),
    db: Session = Depends(get_db)
):
    """Delete resume"""
    resume = db.query(ResumeMetadata).filter(
        ResumeMetadata.id == resume_id,
        ResumeMetadata.user_id == current_user.id
    ).first()
    
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume not found"
        )
    
    # Delete file from disk
    try:
        _resolve_user_file_path(resume.file_path, current_user.id).unlink(missing_ok=True)
    except HTTPException as exc:
        if exc.status_code != status.HTTP_404_NOT_FOUND:
            raise
    except Exception:
        pass
    
    # Delete from database
    db.delete(resume)
    db.commit()
    
    return {"message": "Resume deleted successfully"}

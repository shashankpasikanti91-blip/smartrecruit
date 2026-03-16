"""
Google Drive Integration for Recruitment AI System
Handles JD and Resume loading from Google Drive
"""

import os
import logging
from typing import Optional, List, Dict, Any
from google.oauth2.service_account import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io
import PyPDF2
from docx import Document

logger = logging.getLogger(__name__)


class DriveLoader:
    """Google Drive loader for JDs and Resumes"""
    
    SCOPES = ["https://www.googleapis.com/auth/drive"]
    
    def __init__(self, credentials_path: Optional[str] = None):
        """Initialize Drive loader"""
        self.credentials_path = credentials_path or os.getenv("GOOGLE_CREDENTIALS_PATH")
        
        if not self.credentials_path:
            raise ValueError("Google credentials path must be provided or set as GOOGLE_CREDENTIALS_PATH")
        
        try:
            self.credentials = Credentials.from_service_account_file(
                self.credentials_path,
                scopes=self.SCOPES
            )
            self.service = build("drive", "v3", credentials=self.credentials)
            logger.info("Google Drive client initialized")
        except Exception as e:
            logger.error(f"Error initializing Google Drive client: {str(e)}")
            raise
    
    def get_file_name(self, file_id: str) -> Optional[str]:
        """Get file name from Drive"""
        try:
            file = self.service.files().get(
                fileId=file_id,
                fields="name,mimeType"
            ).execute()
            return file.get("name")
        except Exception as e:
            logger.error(f"Error getting file name: {str(e)}")
            return None
    
    def download_file(self, file_id: str) -> Optional[bytes]:
        """Download file from Google Drive"""
        try:
            request = self.service.files().get_media(fileId=file_id)
            file_buffer = io.BytesIO()
            downloader = MediaIoBaseDownload(file_buffer, request)
            
            done = False
            while not done:
                status, done = downloader.next_chunk()
            
            file_buffer.seek(0)
            logger.info(f"Downloaded file: {file_id}")
            return file_buffer.getvalue()
        except Exception as e:
            logger.error(f"Error downloading file: {str(e)}")
            return None
    
    def extract_text_from_pdf(self, file_bytes: bytes) -> str:
        """Extract text from PDF"""
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            logger.info("Extracted text from PDF")
            return text.strip()
        except Exception as e:
            logger.error(f"Error extracting PDF text: {str(e)}")
            return ""
    
    def extract_text_from_docx(self, file_bytes: bytes) -> str:
        """Extract text from DOCX"""
        try:
            doc = Document(io.BytesIO(file_bytes))
            text = ""
            for para in doc.paragraphs:
                text += para.text + "\n"
            logger.info("Extracted text from DOCX")
            return text.strip()
        except Exception as e:
            logger.error(f"Error extracting DOCX text: {str(e)}")
            return ""
    
    def load_resume(self, file_id: str) -> Optional[Dict[str, Any]]:
        """Load and extract resume text"""
        try:
            file_name = self.get_file_name(file_id)
            file_bytes = self.download_file(file_id)
            
            if not file_bytes:
                logger.warning(f"Could not download resume: {file_id}")
                return None
            
            # Detect file type
            if file_name.lower().endswith(".pdf"):
                text = self.extract_text_from_pdf(file_bytes)
            elif file_name.lower().endswith(".docx"):
                text = self.extract_text_from_docx(file_bytes)
            else:
                logger.warning(f"Unsupported file format: {file_name}")
                return None
            
            return {
                "file_id": file_id,
                "file_name": file_name,
                "text": text,
                "size_bytes": len(file_bytes)
            }
        except Exception as e:
            logger.error(f"Error loading resume: {str(e)}")
            return None
    
    def load_jd(self, file_id: str) -> Optional[Dict[str, Any]]:
        """Load and extract job description text"""
        return self.load_resume(file_id)  # Same extraction logic
    
    def search_files(
        self,
        folder_id: Optional[str] = None,
        query: Optional[str] = None,
        file_type: str = "pdf,docx"
    ) -> List[Dict[str, Any]]:
        """Search files in Google Drive"""
        try:
            search_query = ""
            if folder_id:
                search_query += f"'{folder_id}' in parents and "
            
            search_query += "trashed = false"
            
            if query:
                search_query += f" and name contains '{query}'"
            
            # Filter by file type
            mime_filters = []
            if "pdf" in file_type:
                mime_filters.append("mimeType='application/pdf'")
            if "docx" in file_type:
                mime_filters.append("mimeType='application/vnd.openxmlformats-officedocument.wordprocessingml.document'")
            
            if mime_filters:
                search_query += " and (" + " or ".join(mime_filters) + ")"
            
            results = self.service.files().list(
                q=search_query,
                spaces="drive",
                fields="files(id, name, mimeType, createdTime, modifiedTime, size)",
                pageSize=50
            ).execute()
            
            files = results.get("files", [])
            logger.info(f"Found {len(files)} files")
            return files
        except Exception as e:
            logger.error(f"Error searching files: {str(e)}")
            return []
    
    def list_folder_contents(
        self,
        folder_id: str,
        file_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List files in a specific folder"""
        try:
            query = f"'{folder_id}' in parents and trashed = false"
            
            if file_type == "pdf":
                query += " and mimeType='application/pdf'"
            elif file_type == "docx":
                query += " and mimeType='application/vnd.openxmlformats-officedocument.wordprocessingml.document'"
            
            results = self.service.files().list(
                q=query,
                spaces="drive",
                fields="files(id, name, mimeType, createdTime, size)",
                pageSize=100,
                orderBy="modifiedTime desc"
            ).execute()
            
            return results.get("files", [])
        except Exception as e:
            logger.error(f"Error listing folder: {str(e)}")
            return []
    
    def create_folder(self, folder_name: str, parent_id: Optional[str] = None) -> Optional[str]:
        """Create a new folder in Google Drive"""
        try:
            file_metadata = {
                "name": folder_name,
                "mimeType": "application/vnd.google-apps.folder"
            }
            
            if parent_id:
                file_metadata["parents"] = [parent_id]
            
            file = self.service.files().create(
                body=file_metadata,
                fields="id"
            ).execute()
            
            folder_id = file.get("id")
            logger.info(f"Created folder: {folder_id}")
            return folder_id
        except Exception as e:
            logger.error(f"Error creating folder: {str(e)}")
            return None
    
    def upload_file(
        self,
        file_path: str,
        folder_id: Optional[str] = None,
        file_name: Optional[str] = None
    ) -> Optional[str]:
        """Upload file to Google Drive"""
        try:
            file_name = file_name or os.path.basename(file_path)
            
            file_metadata = {"name": file_name}
            if folder_id:
                file_metadata["parents"] = [folder_id]
            
            from googleapiclient.http import MediaFileUpload
            
            media = MediaFileUpload(file_path, resumable=True)
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields="id"
            ).execute()
            
            file_id = file.get("id")
            logger.info(f"Uploaded file: {file_id}")
            return file_id
        except Exception as e:
            logger.error(f"Error uploading file: {str(e)}")
            return None

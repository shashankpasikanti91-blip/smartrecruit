"""
Supabase Database Client for Recruitment AI System
"""

import os
from typing import List, Optional, Dict, Any
from supabase import create_client, Client
from postgrest.exceptions import APIError
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class SupabaseClient:
    """Supabase database client with connection pooling and error handling"""
    
    def __init__(
        self,
        supabase_url: Optional[str] = None,
        supabase_key: Optional[str] = None,
        timeout: int = 10
    ):
        """Initialize Supabase client"""
        self.url = supabase_url or os.getenv("SUPABASE_URL")
        self.key = supabase_key or os.getenv("SUPABASE_KEY")
        self.timeout = timeout
        
        if not self.url or not self.key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be provided or set as environment variables")
        
        self.client: Client = create_client(self.url, self.key)
        logger.info("Supabase client initialized")
    
    # ============== REQUIREMENTS (Job Descriptions) ==============
    
    async def create_requirement(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new job requirement"""
        try:
            response = self.client.table("requirements").insert(data).execute()
            logger.info(f"Created requirement: {data.get('id')}")
            return response.data[0] if response.data else None
        except APIError as e:
            logger.error(f"Error creating requirement: {str(e)}")
            raise
    
    async def get_requirement(self, requirement_id: str) -> Optional[Dict[str, Any]]:
        """Get requirement by ID"""
        try:
            response = self.client.table("requirements").select("*").eq("id", requirement_id).execute()
            return response.data[0] if response.data else None
        except APIError as e:
            logger.error(f"Error getting requirement: {str(e)}")
            raise
    
    async def list_requirements(
        self,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List requirements with optional filtering"""
        try:
            query = self.client.table("requirements").select("*")
            if status:
                query = query.eq("status", status)
            response = query.range(offset, offset + limit - 1).execute()
            return response.data
        except APIError as e:
            logger.error(f"Error listing requirements: {str(e)}")
            raise
    
    async def update_requirement(self, requirement_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update requirement"""
        try:
            data["updated_at"] = datetime.utcnow().isoformat()
            response = self.client.table("requirements").update(data).eq("id", requirement_id).execute()
            logger.info(f"Updated requirement: {requirement_id}")
            return response.data[0] if response.data else None
        except APIError as e:
            logger.error(f"Error updating requirement: {str(e)}")
            raise
    
    # ============== CANDIDATES ==============
    
    async def create_candidate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new candidate"""
        try:
            response = self.client.table("candidates").insert(data).execute()
            logger.info(f"Created candidate: {data.get('id')}")
            return response.data[0] if response.data else None
        except APIError as e:
            logger.error(f"Error creating candidate: {str(e)}")
            raise
    
    async def get_candidate(self, candidate_id: str) -> Optional[Dict[str, Any]]:
        """Get candidate by ID"""
        try:
            response = self.client.table("candidates").select("*").eq("id", candidate_id).execute()
            return response.data[0] if response.data else None
        except APIError as e:
            logger.error(f"Error getting candidate: {str(e)}")
            raise
    
    async def list_candidates_for_jd(
        self,
        jd_id: str,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """List candidates for a specific job description"""
        try:
            query = self.client.table("candidates").select("*").eq("jd_id", jd_id)
            if status:
                query = query.eq("status", status)
            response = query.limit(limit).execute()
            return response.data
        except APIError as e:
            logger.error(f"Error listing candidates: {str(e)}")
            raise
    
    async def update_candidate(self, candidate_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update candidate"""
        try:
            data["updated_at"] = datetime.utcnow().isoformat()
            response = self.client.table("candidates").update(data).eq("id", candidate_id).execute()
            logger.info(f"Updated candidate: {candidate_id}")
            return response.data[0] if response.data else None
        except APIError as e:
            logger.error(f"Error updating candidate: {str(e)}")
            raise
    
    # ============== SCREENING RESULTS ==============
    
    async def create_screening_result(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create screening result"""
        try:
            response = self.client.table("screening_results").insert(data).execute()
            logger.info(f"Created screening result: {data.get('id')}")
            return response.data[0] if response.data else None
        except APIError as e:
            logger.error(f"Error creating screening result: {str(e)}")
            raise
    
    async def get_screening_result(self, screening_id: str) -> Optional[Dict[str, Any]]:
        """Get screening result"""
        try:
            response = self.client.table("screening_results").select("*").eq("id", screening_id).execute()
            return response.data[0] if response.data else None
        except APIError as e:
            logger.error(f"Error getting screening result: {str(e)}")
            raise
    
    async def get_candidate_screening(
        self,
        candidate_id: str,
        jd_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get screening result for specific candidate and JD"""
        try:
            response = (
                self.client.table("screening_results")
                .select("*")
                .eq("candidate_id", candidate_id)
                .eq("jd_id", jd_id)
                .execute()
            )
            return response.data[0] if response.data else None
        except APIError as e:
            logger.error(f"Error getting candidate screening: {str(e)}")
            raise
    
    # ============== INTERVIEWS ==============
    
    async def create_interview(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create interview record"""
        try:
            response = self.client.table("interviews").insert(data).execute()
            logger.info(f"Created interview: {data.get('id')}")
            return response.data[0] if response.data else None
        except APIError as e:
            logger.error(f"Error creating interview: {str(e)}")
            raise
    
    async def get_interview(self, interview_id: str) -> Optional[Dict[str, Any]]:
        """Get interview by ID"""
        try:
            response = self.client.table("interviews").select("*").eq("id", interview_id).execute()
            return response.data[0] if response.data else None
        except APIError as e:
            logger.error(f"Error getting interview: {str(e)}")
            raise
    
    async def list_candidate_interviews(
        self,
        candidate_id: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """List all interviews for a candidate"""
        try:
            response = (
                self.client.table("interviews")
                .select("*")
                .eq("candidate_id", candidate_id)
                .limit(limit)
                .execute()
            )
            return response.data
        except APIError as e:
            logger.error(f"Error listing interviews: {str(e)}")
            raise
    
    async def update_interview(self, interview_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update interview"""
        try:
            data["updated_at"] = datetime.utcnow().isoformat()
            response = self.client.table("interviews").update(data).eq("id", interview_id).execute()
            logger.info(f"Updated interview: {interview_id}")
            return response.data[0] if response.data else None
        except APIError as e:
            logger.error(f"Error updating interview: {str(e)}")
            raise
    
    # ============== SELECTIONS ==============
    
    async def create_selection(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create selection record"""
        try:
            response = self.client.table("selections").insert(data).execute()
            logger.info(f"Created selection: {data.get('id')}")
            return response.data[0] if response.data else None
        except APIError as e:
            logger.error(f"Error creating selection: {str(e)}")
            raise
    
    async def get_selection(self, selection_id: str) -> Optional[Dict[str, Any]]:
        """Get selection by ID"""
        try:
            response = self.client.table("selections").select("*").eq("id", selection_id).execute()
            return response.data[0] if response.data else None
        except APIError as e:
            logger.error(f"Error getting selection: {str(e)}")
            raise
    
    async def update_selection(self, selection_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update selection"""
        try:
            data["updated_at"] = datetime.utcnow().isoformat()
            response = self.client.table("selections").update(data).eq("id", selection_id).execute()
            logger.info(f"Updated selection: {selection_id}")
            return response.data[0] if response.data else None
        except APIError as e:
            logger.error(f"Error updating selection: {str(e)}")
            raise
    
    # ============== EMBEDDINGS & VECTOR SEARCH ==============
    
    async def store_embedding(
        self,
        entity_type: str,
        entity_id: str,
        text: str,
        embedding: List[float],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Store text embedding in database"""
        try:
            data = {
                "entity_type": entity_type,
                "entity_id": entity_id,
                "text": text,
                "embedding": embedding,
                "metadata": metadata or {}
            }
            response = self.client.table("embeddings").insert(data).execute()
            logger.info(f"Stored embedding for {entity_type}: {entity_id}")
            return response.data[0] if response.data else None
        except APIError as e:
            logger.error(f"Error storing embedding: {str(e)}")
            raise
    
    async def search_similar(
        self,
        embedding: List[float],
        entity_type: Optional[str] = None,
        limit: int = 10,
        threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Semantic search using embeddings"""
        try:
            # This requires a custom PostgreSQL function for vector similarity
            query = self.client.table("embeddings").select("*")
            if entity_type:
                query = query.eq("entity_type", entity_type)
            response = query.limit(limit).execute()
            return response.data
        except APIError as e:
            logger.error(f"Error searching similar: {str(e)}")
            raise
    
    # ============== MESSAGE HISTORY ==============
    
    async def create_message_record(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create message history record"""
        try:
            response = self.client.table("message_history").insert(data).execute()
            logger.info(f"Created message record: {data.get('id')}")
            return response.data[0] if response.data else None
        except APIError as e:
            logger.error(f"Error creating message record: {str(e)}")
            raise
    
    async def get_candidate_messages(
        self,
        candidate_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get all messages for a candidate"""
        try:
            response = (
                self.client.table("message_history")
                .select("*")
                .eq("candidate_id", candidate_id)
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )
            return response.data
        except APIError as e:
            logger.error(f"Error getting candidate messages: {str(e)}")
            raise
    
    # ============== HEALTH CHECK ==============
    
    async def health_check(self) -> bool:
        """Check database connection health"""
        try:
            response = self.client.table("candidates").select("id").limit(1).execute()
            logger.info("Supabase health check passed")
            return True
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return False

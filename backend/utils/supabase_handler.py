"""
Supabase Database Handler for Recruitment AI v3.2
Isolated module for async database operations
Safe: All operations are non-blocking and gracefully handle failures
"""

import os
import asyncio
import logging
import hashlib
from datetime import datetime
from typing import Optional, Dict, Any, TYPE_CHECKING

# Optional Supabase imports for graceful fallback
try:
    from supabase import create_client
    SUPABASE_AVAILABLE = True
    if TYPE_CHECKING:
        from supabase import Client
except ImportError:
    SUPABASE_AVAILABLE = False
    if TYPE_CHECKING:
        from supabase import Client

logger = logging.getLogger(__name__)


class SupabaseHandler:
    """Safe Supabase client for async database operations"""
    
    _instance = None
    _client: "Optional[Client]" = None
    _ready = False
    
    def __new__(cls):
        """Singleton pattern to reuse client"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize Supabase client if credentials present"""
        if self._ready or self._client is not None:
            return
        
        self._ready = True
        
        if not SUPABASE_AVAILABLE:
            logger.warning("[SUPABASE] Supabase not installed - database operations disabled")
            return
        
        try:
            url = os.getenv('SUPABASE_URL')
            key = os.getenv('SUPABASE_KEY')
            
            if not url or not key:
                logger.info("[SUPABASE] Credentials not configured - database operations disabled")
                return
            
            self._client = create_client(url, key)
            logger.info("[SUPABASE] Client initialized successfully")
        except Exception as e:
            logger.error(f"[SUPABASE] Initialization failed: {e}")
    
    def is_connected(self) -> bool:
        """Check if Supabase is connected"""
        return self._client is not None
    
    @staticmethod
    def _hash_file_content(content: str) -> str:
        """Generate hash for file content to detect duplicates"""
        return hashlib.md5(content.encode()).hexdigest()
    
    def save_resume_metadata(self, 
                                   candidate_name: str,
                                   filename: str,
                                   content: str,
                                   file_pages: int = 1) -> Optional[Dict[str, Any]]:
        """
        Save resume metadata to Supabase
        Returns: resume record with ID or None if failed
        """
        if not self.is_connected():
            logger.warning("[SUPABASE-INSERT] Resume save blocked - not connected")
            return None
        
        try:
            logger.info(f"[SUPABASE-INSERT] Attempting to save resume: {candidate_name}")
            file_hash = self._hash_file_content(content)
            
            data = {
                "candidate_name": candidate_name or "Unknown",
                "file_name": filename,
                "file_hash": file_hash,
                "extracted_text": content[:500]  # Store first 500 chars
            }
            
            logger.info(f"[SUPABASE-INSERT] Inserting to resume_metadata: {data}")
            response = self._client.table("resume_metadata").insert(data).execute()
            
            if response.data and len(response.data) > 0:
                logger.info(f"[SUPABASE-INSERT] SUCCESS - Resume saved: {candidate_name}")
                return response.data[0]
            else:
                logger.warning(f"[SUPABASE-INSERT] FAILED - Resume save returned no data for {candidate_name}")
                return None
                
        except Exception as e:
            logger.error(f"[SUPABASE-INSERT] ERROR - Resume save failed: {type(e).__name__}: {e}")
            import traceback
            logger.error(f"[SUPABASE-INSERT] Traceback: {traceback.format_exc()}")
            return None
    
    def save_screening_result(self,
                                    resume_id: Optional[str],
                                    candidate_name: str,
                                    job_title: str,
                                    match_score: int,
                                    recommendation: str,
                                    assessment: str) -> Optional[Dict[str, Any]]:
        """
        Save screening results to Supabase
        Returns: screening record with ID or None if failed
        """
        if not self.is_connected():
            logger.debug("[SUPABASE] Skipping screening save - not connected")
            return None
        
        try:
            data = {
                "candidate_id": resume_id,
                "job_title": job_title,
                "fit_score": max(0, min(100, match_score)),
                "recommendation": recommendation,
                "summary": assessment[:500],
                "strengths": [],
                "gaps": [],
                "screening_details": {"note": assessment}
            }
            
            response = self._client.table("screening_results").insert(data).execute()
            
            if response.data and len(response.data) > 0:
                logger.info(f"[SUPABASE] Screening saved: {candidate_name} - Score: {match_score}%")
                return response.data[0]
            else:
                logger.warning(f"[SUPABASE] Screening save returned no data")
                return None
                
        except Exception as e:
            logger.error(f"[SUPABASE] Screening save failed: {e}")
            return None
    
    def save_ai_message(self,
                             message_type: str,
                             recipient: str,
                             job_title: str,
                             tone: str,
                             message_content: str) -> Optional[Dict[str, Any]]:
        """
        Save AI-generated messages to Supabase
        Returns: message record with ID or None if failed
        """
        if not self.is_connected():
            logger.debug("[SUPABASE] Skipping message save - not connected")
            return None
        
        try:
            data = {
                "message_type": message_type,
                "candidate_name": recipient,
                "recipient_type": recipient,
                "message_content": message_content[:5000],
                "character_count": len(message_content),
                "ai_model": tone,
                "metadata": {"job_title": job_title}
            }
            
            response = self._client.table("ai_messages").insert(data).execute()
            
            if response.data and len(response.data) > 0:
                logger.info(f"[SUPABASE] Message saved: {message_type} to {recipient}")
                return response.data[0]
            else:
                logger.warning(f"[SUPABASE] Message save returned no data")
                return None
                
        except Exception as e:
            logger.error(f"[SUPABASE] Message save failed: {e}")
            return None
    
    def save_activity_log(self,
                               log_level: str,
                               log_message: str,
                               component: str) -> Optional[Dict[str, Any]]:
        """
        Save activity log entries to Supabase
        Returns: log record with ID or None if failed
        """
        if not self.is_connected():
            logger.debug("[SUPABASE] Skipping activity log save - not connected")
            return None
        
        try:
            data = {
                "action_type": component,
                "action_details": log_message[:1000],
                "status": log_level,
                "metadata": {"component": component}
            }
            
            response = self._client.table("activity_logs").insert(data).execute()
            
            if response.data and len(response.data) > 0:
                logger.debug(f"[SUPABASE] Activity log saved: {component}")
                return response.data[0]
            else:
                logger.debug(f"[SUPABASE] Activity log save returned no data")
                return None
                
        except Exception as e:
            logger.error(f"[SUPABASE] Activity log save failed: {e}")
            return None
    
    def save_job_post(self,
                           job_title: str,
                           location: str,
                           experience: int,
                           platforms: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """
        Save job post generation to Supabase
        Returns: job post record with ID or None if failed
        """
        if not self.is_connected():
            logger.warning("[SUPABASE-INSERT] Job post save blocked - not connected")
            return None
        
        try:
            logger.info(f"[SUPABASE-INSERT] Attempting to save job post: {job_title}")
            import json
            data = {
                "job_title": job_title,
                "job_description": f"Experience: {experience}+ years, Location: {location}",
                "linkedin_post": platforms.get("linkedin", ""),
                "indeed_post": platforms.get("indeed", ""),
                "email_post": platforms.get("email", ""),
                "whatsapp_post": platforms.get("whatsapp", ""),
                "platform_posts": json.dumps(platforms),
                "metadata": {"experience": experience, "location": location}
            }
            
            logger.info(f"[SUPABASE-INSERT] Inserting to job_posts: {data}")
            response = self._client.table("job_posts").insert(data).execute()
            
            if response.data and len(response.data) > 0:
                logger.info(f"[SUPABASE-INSERT] SUCCESS - Job post saved: {job_title}")
                return response.data[0]
            else:
                logger.warning(f"[SUPABASE-INSERT] FAILED - Job post save returned no data")
                return None
                
        except Exception as e:
            logger.error(f"[SUPABASE-INSERT] ERROR - Job post save failed: {type(e).__name__}: {e}")
            import traceback
            logger.error(f"[SUPABASE-INSERT] Traceback: {traceback.format_exc()}")
            return None


# Async helper functions (non-blocking execute)
def execute_async(coro):
    """Execute async function in a way that doesn't block Flask"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(coro)
        loop.close()
        return result
    except Exception as e:
        logger.error(f"[SUPABASE] Async execution failed: {e}")
        return None


# Convenience functions for easy integration (SYNCHRONOUS - will block briefly)
def save_resume_metadata_async(candidate_name: str, filename: str, content: str) -> None:
    """Save resume metadata synchronously"""
    try:
        logger.info("[SUPABASE-CALL] save_resume_metadata_async called")
        handler = SupabaseHandler()
        result = handler.save_resume_metadata(candidate_name, filename, content)
        if result:
            logger.info(f"[SUPABASE-CALL] save_resume_metadata_async SUCCESS: {result}")
        else:
            logger.warning("[SUPABASE-CALL] save_resume_metadata_async returned None")
    except Exception as e:
        logger.error(f"[SUPABASE-CALL] save_resume_metadata_async failed: {e}")
        import traceback
        logger.error(traceback.format_exc())


def save_screening_result_async(resume_id: Optional[str],
                               candidate_name: str,
                               job_title: str,
                               match_score: int,
                               recommendation: str,
                               assessment: str) -> None:
    """Save screening result synchronously"""
    try:
        logger.info("[SUPABASE-CALL] save_screening_result_async called")
        handler = SupabaseHandler()
        result = handler.save_screening_result(resume_id, candidate_name, job_title, 
                                        match_score, recommendation, assessment)
        if result:
            logger.info(f"[SUPABASE-CALL] save_screening_result_async SUCCESS: ID={result.get('id')}")
        else:
            logger.warning("[SUPABASE-CALL] save_screening_result_async returned None")
    except Exception as e:
        logger.error(f"[SUPABASE-CALL] save_screening_result_async failed: {e}")
        import traceback
        logger.error(traceback.format_exc())


def save_ai_message_async(message_type: str,
                         recipient: str,
                         job_title: str,
                         tone: str,
                         message_content: str) -> None:
    """Save AI-generated message synchronously"""
    try:
        logger.info("[SUPABASE-CALL] save_ai_message_async called")
        handler = SupabaseHandler()
        result = handler.save_ai_message(message_type, recipient, job_title, tone, message_content)
        if result:
            logger.info(f"[SUPABASE-CALL] save_ai_message_async SUCCESS: ID={result.get('id')}")
        else:
            logger.warning("[SUPABASE-CALL] save_ai_message_async returned None")
    except Exception as e:
        logger.error(f"[SUPABASE-CALL] save_ai_message_async failed: {e}")
        import traceback
        logger.error(traceback.format_exc())


def save_activity_log_async(log_level: str, log_message: str, component: str) -> None:
    """Save activity log synchronously"""
    try:
        logger.info(f"[SUPABASE-CALL] save_activity_log_async called: {component}")
        handler = SupabaseHandler()
        result = handler.save_activity_log(log_level, log_message, component)
        if result:
            logger.info(f"[SUPABASE-CALL] save_activity_log_async SUCCESS: ID={result.get('id')}")
        else:
            logger.warning("[SUPABASE-CALL] save_activity_log_async returned None")
    except Exception as e:
        logger.error(f"[SUPABASE-CALL] save_activity_log_async failed: {e}")
        import traceback
        logger.error(traceback.format_exc())


def save_job_post_async(job_title: str, 
                        location: str, 
                        experience: int,
                        platforms: Dict[str, str]) -> None:
    """Save job post synchronously"""
    try:
        logger.info(f"[SUPABASE-CALL] save_job_post_async called: {job_title}")
        handler = SupabaseHandler()
        result = handler.save_job_post(job_title, location, experience, platforms)
        if result:
            logger.info(f"[SUPABASE-CALL] save_job_post_async SUCCESS: ID={result.get('id')}")
        else:
            logger.warning("[SUPABASE-CALL] save_job_post_async returned None")
    except Exception as e:
        logger.error(f"[SUPABASE-CALL] save_job_post_async failed: {e}")
        import traceback
        logger.error(traceback.format_exc())

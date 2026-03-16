"""
Main Entry Point for Recruitment AI System
"""

import asyncio
import logging
from typing import Optional, Dict, Any
import uuid
from datetime import datetime

from models import (
    Candidate, CandidateStatus,
    Requirement, RecruitmentType,
    ScreeningResult,
    Interview, InterviewStage,
    Selection, SelectionStatus
)
from agents import ScreeningAgent, MessagingAgent, MatchingEngine
from integrations import DriveLoader, EmbeddingEngine
from database import SupabaseClient
from workflows import N8nClient
from control_panel import ControlPanelManager
from utils import config, logger


class RecruitmentAISystem:
    """Main recruitment AI system orchestrator"""
    
    def __init__(self):
        """Initialize the system"""
        config.validate()
        
        self.logger = logging.getLogger("recruitment_ai")
        
        # Initialize components
        self.screening_agent = ScreeningAgent()
        self.messaging_agent = MessagingAgent()
        self.matching_engine = MatchingEngine()
        self.embedding_engine = EmbeddingEngine()
        self.drive_loader = DriveLoader()
        self.db_client = SupabaseClient()
        self.n8n_client = N8nClient()
        self.control_panel = ControlPanelManager()
        
        self.logger.info("Recruitment AI System initialized successfully")
    
    async def screen_candidate(
        self,
        candidate_id: str,
        resume_text: str,
        jd_id: str,
        jd_text: str
    ) -> Dict[str, Any]:
        """Screen a candidate against a job description"""
        try:
            self.logger.info(f"Starting screening for candidate {candidate_id}")
            
            # AI Screening
            screening_result = self.screening_agent.screen_candidate(
                resume_text=resume_text,
                jd_text=jd_text,
                candidate_id=candidate_id,
                jd_id=jd_id
            )
            
            # Store in database
            await self.db_client.create_screening_result(screening_result)
            
            # Trigger n8n workflow if configured
            if config.N8N_SCREENING_WORKFLOW_ID:
                await self.n8n_client.trigger_screening_workflow(
                    candidate_id=candidate_id,
                    resume_text=resume_text,
                    jd_id=jd_id,
                    jd_text=jd_text
                )
            
            return screening_result
        except Exception as e:
            self.logger.error(f"Error screening candidate: {str(e)}")
            raise
    
    async def process_jd(
        self,
        jd_id: str,
        jd_text: str,
        job_title: str,
        client_name: str
    ) -> Dict[str, Any]:
        """Process job description"""
        try:
            self.logger.info(f"Processing JD: {jd_id}")
            
            # Create requirement record
            requirement = {
                "id": jd_id,
                "job_title": job_title,
                "client": client_name,
                "jd_text": jd_text,
                "status": "open",
                "created_at": datetime.utcnow().isoformat()
            }
            
            await self.db_client.create_requirement(requirement)
            
            # Generate embeddings
            embedding = self.embedding_engine.embed_text(jd_text)
            if embedding:
                await self.db_client.store_embedding(
                    entity_type="requirement",
                    entity_id=jd_id,
                    text=jd_text,
                    embedding=embedding,
                    metadata={"job_title": job_title, "client": client_name}
                )
            
            # Trigger n8n workflow
            if config.N8N_JD_PROCESSING_WORKFLOW_ID:
                result = await self.n8n_client.trigger_jd_processing_workflow(
                    jd_id=jd_id,
                    jd_text=jd_text,
                    job_title=job_title,
                    client_name=client_name
                )
            
            self.logger.info(f"Processed JD: {jd_id}")
            return requirement
        except Exception as e:
            self.logger.error(f"Error processing JD: {str(e)}")
            raise
    
    async def generate_message(
        self,
        message_type: str,
        tone: str,
        platform: str,
        recipient_name: str,
        recipient_email: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate recruitment message"""
        try:
            self.logger.info(f"Generating {message_type} message for {recipient_email}")
            
            # Generate message
            message = self.messaging_agent.generate_message(
                message_type=message_type,
                tone=tone,
                platform=platform,
                recipient_name=recipient_name,
                context=context or {}
            )
            
            # Trigger n8n messaging workflow
            if config.N8N_MESSAGING_WORKFLOW_ID:
                await self.n8n_client.trigger_messaging_workflow(
                    message_type=message_type,
                    recipient_email=recipient_email,
                    recipient_name=recipient_name,
                    context=context or {}
                )
            
            return message
        except Exception as e:
            self.logger.error(f"Error generating message: {str(e)}")
            raise
    
    async def process_form_submission(self, submission_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process form submission from control panel"""
        try:
            parsed = self.control_panel.parse_form_submission(submission_data)
            task_type = parsed.get("task_type")
            
            self.logger.info(f"Processing form submission: {task_type}")
            
            if task_type == "Screen CV against JD":
                # Extract resume and JD from input
                result = await self.handle_cv_screening(parsed)
            
            elif task_type == "Create Job Post":
                result = await self.handle_job_post_creation(parsed)
            
            elif task_type == "AI Writing Agent":
                result = await self.handle_ai_writing(parsed)
            
            else:
                raise ValueError(f"Unknown task type: {task_type}")
            
            # Log execution
            self.control_panel.log_task_execution(
                task_id=str(uuid.uuid4()),
                task_type=task_type,
                status="completed",
                result=result
            )
            
            return result
        except Exception as e:
            self.logger.error(f"Error processing form submission: {str(e)}")
            raise
    
    async def handle_cv_screening(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle CV screening task from form"""
        # Implementation for CV screening
        pass
    
    async def handle_job_post_creation(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle job post creation task from form"""
        # Implementation for job post creation
        pass
    
    async def handle_ai_writing(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle AI writing task from form"""
        # Implementation for AI writing
        pass
    
    async def health_check(self) -> Dict[str, bool]:
        """Check health of all system components"""
        try:
            health = {
                "database": await self.db_client.health_check(),
                "n8n": await self.n8n_client.health_check(),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            self.logger.info(f"Health check: {health}")
            return health
        except Exception as e:
            self.logger.error(f"Error in health check: {str(e)}")
            return {"error": str(e), "timestamp": datetime.utcnow().isoformat()}


async def main():
    """Main entry point"""
    try:
        # Initialize system
        system = RecruitmentAISystem()
        
        # Example usage
        logger.info("Starting Recruitment AI System...")
        
        # Health check
        health = await system.health_check()
        logger.info(f"System health: {health}")
        
        if health.get("error"):
            logger.error("System health check failed")
            return
        
        logger.info("System ready for operations")
        
        # Keep system running
        while True:
            await asyncio.sleep(60)
    
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        raise


if __name__ == "__main__":
    asyncio.run(main())

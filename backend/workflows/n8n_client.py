"""
n8n Workflow Orchestration Integration
"""

import os
import logging
from typing import Optional, Dict, Any, List
import httpx
import json

logger = logging.getLogger(__name__)


class N8nClient:
    """Client for n8n workflow orchestration"""
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None
    ):
        """Initialize n8n client"""
        self.base_url = base_url or os.getenv("N8N_BASE_URL", "http://localhost:5678")
        self.api_key = api_key or os.getenv("N8N_API_KEY", "")
        
        # Remove trailing slash
        self.base_url = self.base_url.rstrip("/")
        
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=self._build_headers()
        )
        logger.info(f"n8n client initialized with base URL: {self.base_url}")
    
    def _build_headers(self) -> Dict[str, str]:
        """Build request headers"""
        headers = {
            "Content-Type": "application/json"
        }
        if self.api_key:
            headers["X-N8N-API-KEY"] = self.api_key
        return headers
    
    async def trigger_workflow(
        self,
        workflow_id: str,
        data: Dict[str, Any],
        wait_for_completion: bool = False
    ) -> Dict[str, Any]:
        """Trigger a workflow"""
        try:
            endpoint = f"/api/v1/workflows/{workflow_id}/execute"
            
            payload = {
                "data": data,
                "waitForCompletion": wait_for_completion
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}{endpoint}",
                    json=payload,
                    headers=self._build_headers(),
                    timeout=60
                )
                response.raise_for_status()
                
                logger.info(f"Triggered workflow: {workflow_id}")
                return response.json()
        except Exception as e:
            logger.error(f"Error triggering workflow: {str(e)}")
            raise
    
    async def get_workflow(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get workflow details"""
        try:
            endpoint = f"/api/v1/workflows/{workflow_id}"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}{endpoint}",
                    headers=self._build_headers(),
                    timeout=10
                )
                response.raise_for_status()
                
                logger.info(f"Retrieved workflow: {workflow_id}")
                return response.json()
        except Exception as e:
            logger.error(f"Error getting workflow: {str(e)}")
            return None
    
    async def list_workflows(self) -> List[Dict[str, Any]]:
        """List all workflows"""
        try:
            endpoint = "/api/v1/workflows"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}{endpoint}",
                    headers=self._build_headers(),
                    timeout=10
                )
                response.raise_for_status()
                
                data = response.json()
                workflows = data.get("data", [])
                logger.info(f"Retrieved {len(workflows)} workflows")
                return workflows
        except Exception as e:
            logger.error(f"Error listing workflows: {str(e)}")
            return []
    
    async def get_execution_history(
        self,
        workflow_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get execution history for a workflow"""
        try:
            endpoint = f"/api/v1/executions?workflowId={workflow_id}&limit={limit}"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}{endpoint}",
                    headers=self._build_headers(),
                    timeout=10
                )
                response.raise_for_status()
                
                data = response.json()
                executions = data.get("data", [])
                logger.info(f"Retrieved {len(executions)} executions for workflow {workflow_id}")
                return executions
        except Exception as e:
            logger.error(f"Error getting execution history: {str(e)}")
            return []
    
    async def trigger_screening_workflow(
        self,
        candidate_id: str,
        resume_text: str,
        jd_id: str,
        jd_text: str
    ) -> Dict[str, Any]:
        """Trigger resume screening workflow"""
        try:
            data = {
                "candidate_id": candidate_id,
                "resume_text": resume_text,
                "jd_id": jd_id,
                "jd_text": jd_text,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Trigger the screening workflow
            result = await self.trigger_workflow(
                workflow_id=os.getenv("N8N_SCREENING_WORKFLOW_ID", "resume_screening"),
                data=data,
                wait_for_completion=True
            )
            
            logger.info(f"Triggered screening workflow for candidate {candidate_id}")
            return result
        except Exception as e:
            logger.error(f"Error triggering screening workflow: {str(e)}")
            raise
    
    async def trigger_messaging_workflow(
        self,
        message_type: str,
        recipient_email: str,
        recipient_name: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Trigger message generation and sending workflow"""
        try:
            data = {
                "message_type": message_type,
                "recipient_email": recipient_email,
                "recipient_name": recipient_name,
                "context": context,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            result = await self.trigger_workflow(
                workflow_id=os.getenv("N8N_MESSAGING_WORKFLOW_ID", "messaging"),
                data=data,
                wait_for_completion=True
            )
            
            logger.info(f"Triggered messaging workflow for {recipient_email}")
            return result
        except Exception as e:
            logger.error(f"Error triggering messaging workflow: {str(e)}")
            raise
    
    async def trigger_jd_processing_workflow(
        self,
        jd_id: str,
        jd_text: str,
        job_title: str,
        client_name: str
    ) -> Dict[str, Any]:
        """Trigger JD processing workflow"""
        try:
            data = {
                "jd_id": jd_id,
                "jd_text": jd_text,
                "job_title": job_title,
                "client_name": client_name,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            result = await self.trigger_workflow(
                workflow_id=os.getenv("N8N_JD_PROCESSING_WORKFLOW_ID", "jd_processing"),
                data=data,
                wait_for_completion=True
            )
            
            logger.info(f"Triggered JD processing workflow for {jd_id}")
            return result
        except Exception as e:
            logger.error(f"Error triggering JD processing workflow: {str(e)}")
            raise
    
    async def health_check(self) -> bool:
        """Check n8n instance health"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/v1/health",
                    timeout=5
                )
                is_healthy = response.status_code == 200
                logger.info(f"n8n health check: {'OK' if is_healthy else 'FAILED'}")
                return is_healthy
        except Exception as e:
            logger.error(f"n8n health check failed: {str(e)}")
            return False


from datetime import datetime

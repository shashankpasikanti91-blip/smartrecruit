"""
Control Panel Integration with JSON Files
Bridges the n8n control panel with Python backend
"""

import json
import logging
import os
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class ControlPanelManager:
    """Manages recruitment control panel configuration and integration"""
    
    def __init__(
        self,
        control_panel_path: Optional[str] = None,
        full_recruitment_path: Optional[str] = None
    ):
        """Initialize control panel manager"""
        self.control_panel_path = control_panel_path or os.getenv(
            "CONTROL_PANEL_PATH",
            "🎯 Recruitment Control Panel copy (1).json"
        )
        self.full_recruitment_path = full_recruitment_path or os.getenv(
            "FULL_RECRUITMENT_PATH",
            "Full Recruitment.json"
        )
        
        self.control_panel_config = self._load_config(self.control_panel_path)
        self.full_recruitment_config = self._load_config(self.full_recruitment_path)
        
        logger.info("Control panel manager initialized")
    
    def _load_config(self, file_path: str) -> Dict[str, Any]:
        """Load JSON configuration file"""
        try:
            if not os.path.exists(file_path):
                logger.warning(f"Config file not found: {file_path}")
                return {}
            
            with open(file_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            
            logger.info(f"Loaded config: {file_path}")
            return config
        except Exception as e:
            logger.error(f"Error loading config {file_path}: {str(e)}")
            return {}
    
    def save_config(self, config: Dict[str, Any], file_path: str) -> bool:
        """Save configuration to JSON file"""
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Saved config: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving config {file_path}: {str(e)}")
            return False
    
    def get_form_fields(self) -> List[Dict[str, Any]]:
        """Extract form field definitions from control panel"""
        try:
            # Find the form trigger node
            nodes = self.control_panel_config.get("nodes", [])
            
            for node in nodes:
                if node.get("type") == "n8n-nodes-base.formTrigger":
                    form_fields = node.get("parameters", {}).get("formFields", {}).get("values", [])
                    logger.info(f"Found {len(form_fields)} form fields")
                    return form_fields
            
            logger.warning("No form trigger node found")
            return []
        except Exception as e:
            logger.error(f"Error getting form fields: {str(e)}")
            return []
    
    def parse_form_submission(self, submission_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse form submission data"""
        try:
            return {
                "task_type": submission_data.get("task_type"),
                "input_text": submission_data.get("input_text"),
                "context_info": submission_data.get("context_info"),
                "message_tone": submission_data.get("message_tone"),
                "output_platform": submission_data.get("output_platform"),
                "revert_type": submission_data.get("Text need to revert like"),
                "file_upload": submission_data.get("Share Document Here"),
                "submitted_at": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error parsing form submission: {str(e)}")
            return {}
    
    def route_task(self, task_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Route task to appropriate agent"""
        routes = {
            "Screen CV against JD": "screening",
            "Create Job Post": "job_post",
            "AI Writing Agent": "messaging"
        }
        
        route = routes.get(task_type, "unknown")
        
        logger.info(f"Routing task {task_type} to {route}")
        
        return {
            "task_type": task_type,
            "route": route,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def generate_task_context(
        self,
        task_type: str,
        input_text: str,
        context_info: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate context for task processing"""
        
        context = {
            "task_type": task_type,
            "input_text": input_text,
            "context_info": context_info,
            "additional_params": kwargs,
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Add specific context based on task type
        if task_type == "Screen CV against JD":
            context.update({
                "task_category": "screening",
                "required_fields": ["resume_text", "jd_text"],
                "output_format": "screening_result"
            })
        
        elif task_type == "Create Job Post":
            context.update({
                "task_category": "job_post_creation",
                "required_fields": ["jd_text"],
                "platforms": ["linkedin", "email", "whatsapp", "indeed"],
                "output_format": "multi_platform_posts"
            })
        
        elif task_type == "AI Writing Agent":
            context.update({
                "task_category": "message_generation",
                "required_fields": ["content"],
                "optional_fields": ["tone", "platform"],
                "output_format": "generated_message"
            })
        
        logger.info(f"Generated context for task: {task_type}")
        return context
    
    def log_task_execution(
        self,
        task_id: str,
        task_type: str,
        status: str,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ) -> bool:
        """Log task execution for audit trail"""
        try:
            log_entry = {
                "task_id": task_id,
                "task_type": task_type,
                "status": status,
                "result": result,
                "error": error,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Append to execution log
            log_file = "task_execution_log.json"
            
            if os.path.exists(log_file):
                with open(log_file, "r") as f:
                    logs = json.load(f)
            else:
                logs = []
            
            logs.append(log_entry)
            
            with open(log_file, "w") as f:
                json.dump(logs, f, indent=2)
            
            logger.info(f"Logged task execution: {task_id}")
            return True
        except Exception as e:
            logger.error(f"Error logging task execution: {str(e)}")
            return False
    
    def get_node_by_id(self, node_id: str) -> Optional[Dict[str, Any]]:
        """Get node configuration by ID"""
        try:
            nodes = self.control_panel_config.get("nodes", [])
            for node in nodes:
                if node.get("id") == node_id:
                    return node
            return None
        except Exception as e:
            logger.error(f"Error getting node: {str(e)}")
            return None
    
    def get_connections(self) -> List[Dict[str, Any]]:
        """Extract node connections from workflow"""
        try:
            connections = self.control_panel_config.get("connections", [])
            logger.info(f"Found {len(connections)} connections")
            return connections
        except Exception as e:
            logger.error(f"Error getting connections: {str(e)}")
            return []
    
    def export_workflow_for_n8n(self) -> Dict[str, Any]:
        """Export workflow configuration for n8n import"""
        try:
            return {
                "name": self.control_panel_config.get("name", "Exported Workflow"),
                "nodes": self.control_panel_config.get("nodes", []),
                "connections": self.control_panel_config.get("connections", []),
                "exported_at": datetime.utcnow().isoformat(),
                "exported_from": "recruitment_ai_system"
            }
        except Exception as e:
            logger.error(f"Error exporting workflow: {str(e)}")
            return {}

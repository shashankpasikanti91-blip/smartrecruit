"""Database models for SRP SmartRecruit v4.0"""

# Core
from app.models.user import User, OTPVerification, Session
from app.models.resume import ResumeMetadata
from app.models.screening import ScreeningResult, InterviewInvite
from app.models.support import SupportTicket

# Enterprise — v4.0
from app.models.enterprise import AuditLog, GeneratedJD, GeneratedBooleanSearch, JDAnalysisResult
from app.models.integration import Integration, ConnectorCredential, ConnectorSyncLog
from app.models.communication import CommunicationProvider, CommunicationTemplate, CommunicationLog
from app.models.webhook_import import WebhookSubscription, WebhookDeliveryLog, ImportBatch, ImportRowError

__all__ = [
    "User", "OTPVerification", "Session",
    "ResumeMetadata", "ScreeningResult", "InterviewInvite", "SupportTicket",
    "AuditLog", "GeneratedJD", "GeneratedBooleanSearch", "JDAnalysisResult",
    "Integration", "ConnectorCredential", "ConnectorSyncLog",
    "CommunicationProvider", "CommunicationTemplate", "CommunicationLog",
    "WebhookSubscription", "WebhookDeliveryLog", "ImportBatch", "ImportRowError",
]

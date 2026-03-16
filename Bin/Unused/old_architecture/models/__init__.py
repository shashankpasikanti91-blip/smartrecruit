"""
Pydantic Models for Recruitment AI System
"""

from .candidate import Candidate, CandidateStatus
from .requirement import Requirement, RecruitmentType
from .interview import Interview, InterviewStage
from .selection import Selection, SelectionStatus
from .screening import ScreeningResult
from .messaging import MessageRequest, MessageResponse

__all__ = [
    "Candidate",
    "CandidateStatus",
    "Requirement",
    "RecruitmentType",
    "Interview",
    "InterviewStage",
    "Selection",
    "SelectionStatus",
    "ScreeningResult",
    "MessageRequest",
    "MessageResponse",
]

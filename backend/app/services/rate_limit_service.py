"""
Rate limiting service for SRP SmartRecruit v3.2
Enforces usage limits based on user role
"""

from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime, timedelta
from fastapi import HTTPException, status

from app.models.user import User
from app.models.screening import ScreeningResult


class RateLimitService:
    """Handle rate limiting and usage tracking"""
    
    # Usage limits per role
    LIMITS = {
        "admin": {
            "single_screenings_per_day": None,  # Unlimited
            "bulk_screenings_per_day": None,    # Unlimited
            "job_posts_per_day": None           # Unlimited
        },
        "premium": {
            "single_screenings_per_day": None,  # Unlimited
            "bulk_screenings_per_day": None,    # Unlimited
            "job_posts_per_day": None           # Unlimited
        },
        "pro": {
            "single_screenings_per_day": None,  # Unlimited
            "bulk_screenings_per_day": None,    # Unlimited
            "job_posts_per_day": None           # Unlimited
        },
        "user": {
            "single_screenings_per_day": 3,     # Free: 3 single screenings/day
            "bulk_screenings_per_day": 5,       # Free: 5 bulk screenings/day
            "job_posts_per_day": 2              # Free: 2 job posts/day
        }
    }
    
    @staticmethod
    def check_screening_limit(db: Session, user: User) -> bool:
        """
        Check if user can perform screening
        
        Args:
            db: Database session
            user: Current user
            
        Returns:
            True if allowed, raises HTTPException if limit exceeded
        """
        # Admin, Premium and Pro have unlimited access
        if user.role in ["admin", "premium", "pro"]:
            return True
        
        # Get today's start and end
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        
        # Count today's screenings
        screening_count = db.query(func.count(ScreeningResult.id)).filter(
            and_(
                ScreeningResult.user_id == user.id,
                ScreeningResult.created_at >= today_start,
                ScreeningResult.created_at < today_end
            )
        ).scalar()
        
        limit = RateLimitService.LIMITS[user.role]["single_screenings_per_day"]
        
        if screening_count >= limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Daily screening limit reached ({limit} per day for free users). Upgrade to Premium for unlimited access."
            )
        
        return True
    
    @staticmethod
    def get_usage_stats(db: Session, user: User) -> dict:
        """
        Get user's current usage statistics
        
        Returns:
            Dictionary with usage stats and limits
        """
        # Get today's start
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = today_start + timedelta(days=1)
        
        # Count today's screenings
        screenings_today = db.query(func.count(ScreeningResult.id)).filter(
            and_(
                ScreeningResult.user_id == user.id,
                ScreeningResult.created_at >= today_start,
                ScreeningResult.created_at < today_end
            )
        ).scalar()
        
        limits = RateLimitService.LIMITS.get(user.role, RateLimitService.LIMITS["user"])
        
        return {
            "role": user.role,
            "screenings": {
                "used_today": screenings_today,
                "limit": limits["screenings_per_day"] or "Unlimited",
                "remaining": None if limits["screenings_per_day"] is None else max(0, limits["screenings_per_day"] - screenings_today)
            },
            "job_posts": {
                "used_today": 0,  # To be implemented when job posting feature is added
                "limit": limits["job_posts_per_day"] or "Unlimited",
                "remaining": limits["job_posts_per_day"]
            }
        }

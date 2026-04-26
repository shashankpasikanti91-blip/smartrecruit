"""
Rate limiting service for SRP SmartRecruit v3.2
Enforces monthly usage limits based on user plan/role.

Plan mapping (role → marketing plan name):
  admin   → Enterprise (custom / internal)
  premium → Scale  ($59/mo  — 400 screenings/month)
  pro     → Growth ($29/mo  — 150 screenings/month)
  user    → Starter (free  —  30 screenings/month)
"""

from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime
from fastapi import HTTPException, status

from app.models.user import User
from app.models.screening import ScreeningResult


class RateLimitService:
    """Handle rate limiting and monthly usage tracking"""

    # Monthly usage limits per role
    LIMITS = {
        "admin": {
            "plan_name": "Enterprise",
            "screenings_per_month": None,   # Unlimited
            "job_posts_per_month": None,    # Unlimited
        },
        "premium": {                        # Scale plan
            "plan_name": "Scale",
            "screenings_per_month": 400,
            "job_posts_per_month": None,    # Unlimited
        },
        "pro": {                            # Growth plan
            "plan_name": "Growth",
            "screenings_per_month": 150,
            "job_posts_per_month": None,    # Unlimited
        },
        "user": {                           # Starter / Free
            "plan_name": "Starter",
            "screenings_per_month": 30,
            "job_posts_per_month": 2,
        },
    }

    # ── helpers ─────────────────────────────────────────────────────────────

    @staticmethod
    def _month_window() -> tuple[datetime, datetime]:
        """Return (month_start, month_end) for the current UTC month."""
        now = datetime.utcnow()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if month_start.month == 12:
            month_end = month_start.replace(year=month_start.year + 1, month=1)
        else:
            month_end = month_start.replace(month=month_start.month + 1)
        return month_start, month_end

    # ── public methods ───────────────────────────────────────────────────────

    @staticmethod
    def check_screening_limit(db: Session, user: User) -> bool:
        """
        Check if user can perform a screening this month.
        Raises HTTP 429 if the monthly quota is exhausted.
        Returns True otherwise.
        """
        limits = RateLimitService.LIMITS.get(user.role, RateLimitService.LIMITS["user"])
        monthly_cap = limits["screenings_per_month"]

        if monthly_cap is None:
            return True  # Unlimited (admin / Enterprise)

        month_start, month_end = RateLimitService._month_window()

        count = db.query(func.count(ScreeningResult.id)).filter(
            and_(
                ScreeningResult.user_id == user.id,
                ScreeningResult.created_at >= month_start,
                ScreeningResult.created_at < month_end,
            )
        ).scalar()

        if count >= monthly_cap:
            plan_name = limits["plan_name"]
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=(
                    f"Monthly screening limit reached ({monthly_cap}/month on the {plan_name} plan). "
                    "Upgrade your plan to unlock more screenings."
                ),
            )

        return True

    @staticmethod
    def get_usage_stats(db: Session, user: User) -> dict:
        """
        Return current monthly usage stats for the user.
        """
        month_start, month_end = RateLimitService._month_window()

        screenings_this_month = db.query(func.count(ScreeningResult.id)).filter(
            and_(
                ScreeningResult.user_id == user.id,
                ScreeningResult.created_at >= month_start,
                ScreeningResult.created_at < month_end,
            )
        ).scalar()

        limits = RateLimitService.LIMITS.get(user.role, RateLimitService.LIMITS["user"])
        monthly_cap = limits["screenings_per_month"]

        return {
            "role": user.role,
            "plan_name": limits["plan_name"],
            "period": "monthly",
            "screenings": {
                "used_this_month": screenings_this_month,
                "limit": monthly_cap if monthly_cap is not None else "Unlimited",
                "remaining": (
                    None if monthly_cap is None
                    else max(0, monthly_cap - screenings_this_month)
                ),
            },
            "job_posts": {
                "limit": limits["job_posts_per_month"] if limits["job_posts_per_month"] is not None else "Unlimited",
            },
        }

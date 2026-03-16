"""
Authentication router for SRP SmartRecruit v3.2
Register, login, OTP verification, password reset
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.schemas import (
    UserRegister, UserLogin, OTPVerifyRequest,
    PasswordResetRequest, PasswordResetConfirm,
    TokenResponse, MessageResponse
)
from app.services.auth_service import AuthService
from app.auth.dependencies import get_current_user, security
from app.models.user import User

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/register", response_model=dict, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegister,
    db: Session = Depends(get_db)
):
    """
    Register a new user
    
    Steps:
    1. Create user account
    2. Send OTP to email for verification
    
    **No Supabase - Pure FastAPI + SQLAlchemy**
    """
    return AuthService.register_user(db, user_data.email, user_data.password)


@router.post("/verify-otp", response_model=MessageResponse)
async def verify_otp(
    otp_data: OTPVerifyRequest,
    db: Session = Depends(get_db)
):
    """
    Verify OTP code for registration
    
    After verification, user can login
    """
    return AuthService.verify_otp(db, otp_data.email, otp_data.otp_code)


@router.post("/login", response_model=TokenResponse)
async def login(
    login_data: UserLogin,
    db: Session = Depends(get_db)
):
    """
    Login user with email and password
    
    Features:
    - JWT token generation
    - Single session enforcement (previous sessions invalidated)
    - Returns user data with token
    
    **High Security - Single Session Only**
    """
    return AuthService.login_user(db, login_data.email, login_data.password)


@router.post("/logout", response_model=MessageResponse)
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Logout current user
    
    Invalidates the current session
    """
    token = credentials.credentials
    return AuthService.logout_user(db, current_user.id, token)


@router.post("/forgot-password", response_model=dict)
async def forgot_password(
    request: PasswordResetRequest,
    db: Session = Depends(get_db)
):
    """
    Request password reset
    
    Sends OTP to user's email
    """
    return AuthService.request_password_reset(db, request.email)


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(
    request: PasswordResetConfirm,
    db: Session = Depends(get_db)
):
    """
    Reset password using OTP
    
    All sessions will be invalidated (logout from all devices)
    """
    return AuthService.reset_password(
        db, 
        request.email, 
        request.otp_code, 
        request.new_password
    )


@router.get("/me")
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Get current user information
    
    Requires authentication
    """
    return {
        "id": current_user.id,
        "email": current_user.email,
        "role": current_user.role,
        "is_active": current_user.is_active,
        "is_verified": current_user.is_verified,
        "created_at": current_user.created_at
    }

"""
Authentication service for SRP SmartRecruit v3.2
Business logic for registration, login, OTP, password reset
"""

from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from datetime import datetime
from typing import Optional

from app.models.user import User, OTPVerification, Session as UserSession
from app.auth.utils import (
    hash_password, 
    verify_password, 
    generate_otp, 
    create_access_token,
    get_otp_expiry,
    is_otp_valid,
    REQUIRE_OTP_ON_LOGIN
)


class AuthService:
    """Authentication service"""
    
    @staticmethod
    def register_user(db: Session, email: str, password: str) -> dict:
        """
        Register a new user
        
        Steps:
        1. Check if email already exists
        2. Create user with hashed password
        3. Generate OTP for email verification
        4. Return success message (OTP would be sent via email)
        """
        # Check if user already exists
        existing_user= db.query(User).filter(User.email == email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create new user
        hashed_pwd = hash_password(password)
        new_user = User(
            email=email,
            hashed_password=hashed_pwd,
            role="user",
            is_active=True,
            is_verified=False
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        # Generate OTP for verification
        otp_code = generate_otp()
        otp = OTPVerification(
            user_id=new_user.id,
            otp_code=otp_code,
            purpose="registration",
            expires_at=get_otp_expiry(),
            used=False
        )
        db.add(otp)
        db.commit()

        import os
        # SECURITY: Only expose OTP in development mode.
        # In production, send via email. Set ENVIRONMENT=production to hide OTP.
        is_dev = os.getenv("ENVIRONMENT", "development").lower() not in ("production", "prod")

        response = {
            "message": "Registration successful. Please verify your email with OTP.",
            "user_id": new_user.id,
            "email": new_user.email,
        }
        if is_dev:
            response["otp_code"] = otp_code  # Dev only — remove when email sending is active
        return response
    
    @staticmethod
    def verify_otp(db: Session, email: str, otp_code: str) -> dict:
        """
        Verify OTP code
        
        Steps:
        1. Find user by email
        2. Find valid OTP
        3. Check if expired
        4. Mark user as verified
        5. Mark OTP as used
        """
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Find the most recent unused OTP for registration
        otp = db.query(OTPVerification).filter(
            OTPVerification.user_id == user.id,
            OTPVerification.otp_code == otp_code,
            OTPVerification.purpose == "registration",
            OTPVerification.used == False
        ).order_by(OTPVerification.created_at.desc()).first()
        
        if not otp:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid OTP code"
            )
        
        # Check if expired
        if not is_otp_valid(otp.expires_at):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="OTP has expired. Please request a new one."
            )
        
        # Mark user as verified
        user.is_verified = True
        otp.used = True
        db.commit()
        
        return {"message": "Email verified successfully. You can now login."}
    
    @staticmethod
    def login_user(db: Session, email: str, password: str) -> dict:
        """
        Login user
        
        Steps:
        1. Validate credentials
        2. Check if verified
        3. Invalidate all previous sessions (single-session enforcement)
        4. Create new session with JWT
        5. Return token
        """
        # Find user
        user = db.query(User).filter(User.email == email).first()
        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )
        
        # Check if verified
        if not user.is_verified:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Please verify your email before logging in"
            )
        
        # Check if active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is inactive"
            )
        
        # SINGLE SESSION ENFORCEMENT: Invalidate all previous sessions
        db.query(UserSession).filter(
            UserSession.user_id == user.id,
            UserSession.is_active == True
        ).update({"is_active": False})
        db.commit()
        
        # Create JWT token
        # NOTE: sub must be a string (python-jose 3.5+ requirement)
        access_token = create_access_token(data={"sub": str(user.id), "email": user.email})
        
        # Create new session
        new_session = UserSession(
            user_id=user.id,
            jwt_token=access_token,
            is_active=True
        )
        db.add(new_session)
        db.commit()
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "role": user.role,
                "is_verified": user.is_verified
            }
        }
    
    @staticmethod
    def logout_user(db: Session, user_id: int, token: str) -> dict:
        """
        Logout user (invalidate current session)
        """
        session = db.query(UserSession).filter(
            UserSession.user_id == user_id,
            UserSession.jwt_token == token
        ).first()
        
        if session:
            session.is_active = False
            db.commit()
        
        return {"message": "Logged out successfully"}
    
    @staticmethod
    def request_password_reset(db: Session, email: str) -> dict:
        """
        Request password reset
        
        Steps:
        1. Find user
        2. Generate OTP
        3. Return success (OTP would be sent via email)
        """
        user = db.query(User).filter(User.email == email).first()
        if not user:
            # Don't reveal that user doesn't exist
            return {"message": "If the email exists, an OTP has been sent."}
        
        # Generate OTP
        otp_code = generate_otp()
        otp = OTPVerification(
            user_id=user.id,
            otp_code=otp_code,
            purpose="password_reset",
            expires_at=get_otp_expiry(),
            used=False
        )
        db.add(otp)
        db.commit()
        
        # In production, send OTP via email
        return {
            "message": "OTP sent to your email",
            "otp_code": otp_code  # REMOVE IN PRODUCTION
        }
    
    @staticmethod
    def reset_password(db: Session, email: str, otp_code: str, new_password: str) -> dict:
        """
        Reset password using OTP
        
        Steps:
        1. Validate OTP
        2. Update password
        3. Invalidate all sessions
        """
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Find valid OTP
        otp = db.query(OTPVerification).filter(
            OTPVerification.user_id == user.id,
            OTPVerification.otp_code == otp_code,
            OTPVerification.purpose == "password_reset",
            OTPVerification.used == False
        ).order_by(OTPVerification.created_at.desc()).first()
        
        if not otp:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid OTP code"
            )
        
        # Check if expired
        if not is_otp_valid(otp.expires_at):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="OTP has expired"
            )
        
        # Update password
        user.hashed_password = hash_password(new_password)
        otp.used = True
        
        # Invalidate all sessions (logout from all devices)
        db.query(UserSession).filter(
            UserSession.user_id == user.id
        ).update({"is_active": False})
        
        db.commit()
        
        return {"message": "Password reset successful. Please login with your new password."}

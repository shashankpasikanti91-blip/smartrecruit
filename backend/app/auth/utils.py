"""
Authentication utilities for SRP SmartRecruit v3.2
Password hashing, JWT, OTP generation
"""

import bcrypt
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
import random
import secrets
import string
import os
from dotenv import load_dotenv

load_dotenv()

# JWT Settings
ENVIRONMENT = os.getenv("ENVIRONMENT", "development").lower()
IS_PRODUCTION = ENVIRONMENT in ("production", "prod")
_INSECURE_SECRET_KEYS = {
    "",
    "your-secret-key-change-in-production-v3-2",
    "change-this",
    "changeme",
    "secret",
}
SECRET_KEY = os.getenv("SECRET_KEY", "")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# OTP Settings
OTP_EXPIRE_MINUTES = int(os.getenv("OTP_EXPIRE_MINUTES", "10"))
REQUIRE_OTP_ON_LOGIN = os.getenv("REQUIRE_OTP_ON_LOGIN", "False").lower() == "true"


if IS_PRODUCTION:
    secret = SECRET_KEY.strip()
    if secret in _INSECURE_SECRET_KEYS or len(secret) < 32:
        raise RuntimeError(
            "SECRET_KEY must be set to a strong random value in production environments."
        )
elif not SECRET_KEY:
    # Keep local development usable without checking in a reusable secret.
    SECRET_KEY = secrets.token_urlsafe(48)


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt
    
    Simple bcrypt implementation - no passlib issues
    """
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    password_bytes = plain_password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_bytes)


def generate_otp() -> str:
    """Generate a 6-digit OTP code"""
    return ''.join(random.choices(string.digits, k=6))


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create JWT access token
    
    Args:
        data: Dictionary containing user data
        expires_delta: Optional custom expiration time
        
    Returns:
        JWT token string
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """
    Decode JWT access token
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded token data or None if invalid
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def get_otp_expiry() -> datetime:
    """Get OTP expiration datetime"""
    return datetime.utcnow() + timedelta(minutes=OTP_EXPIRE_MINUTES)


def is_otp_valid(expires_at: datetime) -> bool:
    """Check if OTP is still valid (not expired)"""
    return datetime.utcnow() < expires_at

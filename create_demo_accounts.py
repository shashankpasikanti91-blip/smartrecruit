#!/usr/bin/env python3
"""Create demo client account on SRP SmartRecruit ATS."""
import sys, os
sys.path.insert(0, '/app')

# Setup env
os.environ.setdefault('DATABASE_URL', 'postgresql://srp_ats:AtsSecure4a16b511b68b557d2bf68af7@db:5432/srp_ats')
os.environ.setdefault('SECRET_KEY', '0b140259123764648e46ac06a3bb8725772b1587dd7e035425d4d58b8a6c424b')

from app.database.connection import SessionLocal
from app.models.user import User
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ACCOUNTS = [
    {
        "email": "demo@srpailabs.com",
        "password": "SRPDemo2026!",
        "role": "admin",
        "label": "Demo Admin"
    },
    {
        "email": "client@srpailabs.com",
        "password": "ClientView2026!",
        "role": "pro",
        "label": "Client View"
    }
]

db = SessionLocal()

for acc in ACCOUNTS:
    existing = db.query(User).filter(User.email == acc["email"]).first()
    if existing:
        # Update password and ensure verified
        existing.hashed_password = pwd_context.hash(acc["password"])
        existing.is_verified = True
        existing.is_active = True
        existing.role = acc["role"]
        db.commit()
        print(f"[UPDATED] {acc['label']}: {acc['email']} / {acc['password']} (role={acc['role']})")
    else:
        user = User(
            email=acc["email"],
            hashed_password=pwd_context.hash(acc["password"]),
            role=acc["role"],
            is_active=True,
            is_verified=True   # Skip OTP - pre-verified
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        print(f"[CREATED] {acc['label']}: {acc['email']} / {acc['password']} (id={user.id}, role={acc['role']})")

# Count users
total = db.query(User).count()
print(f"\nTotal users in DB: {total}")
db.close()
print("\nDemo accounts ready!")

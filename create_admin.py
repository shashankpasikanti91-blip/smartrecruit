#!/usr/bin/env python3
"""
Create Admin Account for SRP SmartRecruit v3.2
Owner Control Panel Access
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.connection import SessionLocal, init_db
from app.models.user import User
from app.auth.utils import hash_password
from datetime import datetime

def create_admin():
    """Create admin account with owner privileges"""
    
    # Initialize database
    init_db()
    
    db = SessionLocal()
    
    try:
        # Admin credentials
        ADMIN_EMAIL = "owner@srp-smartrecruit.com"
        ADMIN_PASSWORD = "SRP@Owner2026!Secure"
        
        # Check if admin already exists
        existing_admin = db.query(User).filter(User.email == ADMIN_EMAIL).first()
        
        if existing_admin:
            print("⚠️  Admin account already exists!")
            print(f"📧 Email: {ADMIN_EMAIL}")
            print("\n💡 To reset password, delete the user first:")
            print(f"   DELETE FROM users WHERE email = '{ADMIN_EMAIL}';")
            return
        
        # Create admin user
        admin_user = User(
            email=ADMIN_EMAIL,
            hashed_password=hash_password(ADMIN_PASSWORD),
            role="admin",
            is_active=True,
            is_verified=True,  # Auto-verified
            created_at=datetime.utcnow()
        )
        
        db.add(admin_user)
        db.commit()
        db.refresh(admin_user)
        
        print("=" * 70)
        print("✅ ADMIN ACCOUNT CREATED SUCCESSFULLY!")
        print("=" * 70)
        print("\n🔐 OWNER CREDENTIALS (Save these securely!):")
        print("-" * 70)
        print(f"📧 Email:    {ADMIN_EMAIL}")
        print(f"🔑 Password: {ADMIN_PASSWORD}")
        print(f"👤 Role:     admin (unlimited access)")
        print(f"🆔 User ID:  {admin_user.id}")
        print("-" * 70)
        print("\n⚠️  IMPORTANT SECURITY NOTES:")
        print("   1. Change password after first login")
        print("   2. Do not share these credentials")
        print("   3. Admin role is hidden from public registration")
        print("   4. Login at: http://localhost:5003/")
        print("\n💡 Admin Privileges:")
        print("   ✅ Unlimited screenings (single & bulk)")
        print("   ✅ Unlimited job postings")
        print("   ✅ Full database access")
        print("   ✅ Can view/manage all users")
        print("   ✅ Can modify system settings")
        print("\n" + "=" * 70)
        
    except Exception as e:
        print(f"\n❌ Error creating admin: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_admin()

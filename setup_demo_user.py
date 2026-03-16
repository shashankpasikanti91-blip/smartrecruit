#!/usr/bin/env python
"""
Create demo user account for testing the ATS system
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database.connection import SessionLocal
from app.models.user import User, OTPVerification
from app.auth.utils import hash_password, generate_otp, get_otp_expiry
from datetime import datetime

def create_demo_user():
    """Create a verified demo user for testing"""
    db = SessionLocal()
    
    try:
        # Demo credentials
        demo_email = "test@smartrecruit.com"
        demo_password = "Demo@123"
        
        print("\n" + "="*70)
        print("  RECRUITMENT ATS v3.2 - DEMO USER SETUP")
        print("="*70)
        
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == demo_email).first()
        if existing_user:
            print(f"\n✓ User already exists: {demo_email}")
            print(f"  Status: {'Verified' if existing_user.is_verified else 'Not Verified'}")
            print(f"  Active: {'Yes' if existing_user.is_active else 'No'}")
            
            # Ensure user is verified and active
            if not existing_user.is_verified or not existing_user.is_active:
                existing_user.is_verified = True
                existing_user.is_active = True
                db.commit()
                print(f"  Updated: User is now verified and active")
        else:
            # Create new user
            hashed_pwd = hash_password(demo_password)
            new_user = User(
                email=demo_email,
                hashed_password=hashed_pwd,
                role="recruiter",
                is_active=True,
                is_verified=True  # Pre-verified for demo
            )
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            
            print(f"\n✓ Demo user created successfully!")
            print(f"  User ID: {new_user.id}")
        
        print("\n" + "-"*70)
        print("  LOGIN CREDENTIALS (Copy these)")
        print("-"*70)
        print(f"  Email:    {demo_email}")
        print(f"  Password: {demo_password}")
        print("-"*70)
        
        print("\n✓ You can now login to the dashboard!")
        print("  1. Go to http://localhost:5003")
        print("  2. Use the credentials above to login")
        print("  3. Start uploading and screening CVs")
        
        print("\n" + "="*70 + "\n")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Error creating demo user: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        db.close()

if __name__ == "__main__":
    success = create_demo_user()
    sys.exit(0 if success else 1)

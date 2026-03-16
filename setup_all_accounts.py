#!/usr/bin/env python
"""
Create owner/admin and demo user accounts for testing the ATS system
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database.connection import SessionLocal
from app.models.user import User
from app.auth.utils import hash_password

def create_accounts():
    """Create both owner and demo user accounts"""
    db = SessionLocal()
    
    try:
        print("\n" + "="*70)
        print("  RECRUITMENT ATS v3.2 - USER ACCOUNT SETUP")
        print("="*70)
        
        # Owner/Admin account
        owner_email = "owner@srp-smartrecruit.com"
        owner_password = "SRP@Owner2026!Secure"
        
        # Check if owner exists
        existing_owner = db.query(User).filter(User.email == owner_email).first()
        if existing_owner:
            print(f"\n✓ Owner account already exists: {owner_email}")
            print(f"  Role: {existing_owner.role}")
            print(f"  Status: {'Verified' if existing_owner.is_verified else 'Not Verified'}")
            print(f"  Active: {'Yes' if existing_owner.is_active else 'No'}")
            
            # Ensure owner is verified, active, and has correct role
            if not existing_owner.is_verified or not existing_owner.is_active or existing_owner.role != "admin":
                existing_owner.is_verified = True
                existing_owner.is_active = True
                existing_owner.role = "admin"
                db.commit()
                print(f"  Updated: Owner is now verified, active, and has admin role")
        else:
            # Create owner account
            hashed_pwd = hash_password(owner_password)
            owner = User(
                email=owner_email,
                hashed_password=hashed_pwd,
                role="admin",
                is_active=True,
                is_verified=True
            )
            db.add(owner)
            db.commit()
            db.refresh(owner)
            
            print(f"\n✓ Owner/Admin account created successfully!")
            print(f"  User ID: {owner.id}")
            print(f"  Role: admin")
        
        # Demo/Recruiter account
        demo_email = "test@smartrecruit.com"
        demo_password = "Demo@123"
        
        existing_demo = db.query(User).filter(User.email == demo_email).first()
        if existing_demo:
            print(f"\n✓ Demo account already exists: {demo_email}")
            print(f"  Role: {existing_demo.role}")
            print(f"  Status: {'Verified' if existing_demo.is_verified else 'Not Verified'}")
            print(f"  Active: {'Yes' if existing_demo.is_active else 'No'}")
            
            # Ensure demo is verified and active
            if not existing_demo.is_verified or not existing_demo.is_active:
                existing_demo.is_verified = True
                existing_demo.is_active = True
                db.commit()
                print(f"  Updated: Demo account is now verified and active")
        else:
            # Create demo account
            hashed_pwd = hash_password(demo_password)
            demo = User(
                email=demo_email,
                hashed_password=hashed_pwd,
                role="recruiter",
                is_active=True,
                is_verified=True
            )
            db.add(demo)
            db.commit()
            db.refresh(demo)
            
            print(f"\n✓ Demo/Recruiter account created successfully!")
            print(f"  User ID: {demo.id}")
            print(f"  Role: recruiter")
        
        # Display credentials
        print("\n" + "="*70)
        print("  LOGIN CREDENTIALS - COPY THESE")
        print("="*70)
        
        print("\n👑 OWNER/ADMIN ACCESS:")
        print("-" * 70)
        print(f"  📧 Email:    {owner_email}")
        print(f"  🔑 Password: {owner_password}")
        print(f"  Role:       Admin (Full system access)")
        print("-" * 70)
        
        print("\n👤 DEMO/RECRUITER ACCESS:")
        print("-" * 70)
        print(f"  📧 Email:    {demo_email}")
        print(f"  🔑 Password: {demo_password}")
        print(f"  Role:       Recruiter (Standard access)")
        print("-" * 70)
        
        print("\n" + "="*70)
        print("  ✓ SYSTEM READY FOR TESTING")
        print("="*70)
        print("\n📍 Go to: http://localhost:5003")
        print("1️⃣  Try Owner login for full admin panel access")
        print("2️⃣  Try Demo login for CV screening features")
        print("3️⃣  Start uploading and screening CVs")
        
        print("\n" + "="*70 + "\n")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Error creating accounts: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        db.close()

if __name__ == "__main__":
    success = create_accounts()
    sys.exit(0 if success else 1)

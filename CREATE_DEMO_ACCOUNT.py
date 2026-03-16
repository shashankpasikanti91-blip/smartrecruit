"""
Create Demo Account for 7-Day Client Trial
SRP SmartRecruit v3.2
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.database.connection import SessionLocal
from app.models.user import User
from app.auth.utils import hash_password

def create_demo_account():
    """Create a demo account valid for 7 days"""
    
    db = SessionLocal()
    
    try:
        # Demo account credentials
        demo_email = "demo@srp-smartrecruit.com"
        demo_password = "Demo@2026"  # Strong password
        demo_role = "premium"  # Give full access for demo
        
        # Check if demo account already exists
        existing_user = db.query(User).filter(User.email == demo_email).first()
        
        if existing_user:
            print("⚠️  Demo account already exists!")
            print(f"📧 Email: {demo_email}")
            print(f"🔑 Password: {demo_password}")
            print(f"🎯 Role: {existing_user.role}")
            print(f"✅ Status: {'Active' if existing_user.is_verified else 'Needs Verification'}")
            
            # Update to premium and verified for demo
            existing_user.role = demo_role
            existing_user.is_verified = True
            db.commit()
            print("\n✅ Updated to Premium and Verified!")
            return
        
        # Create new demo account
        hashed_pw = hash_password(demo_password)
        
        demo_user = User(
            email=demo_email,
            hashed_password=hashed_pw,
            role=demo_role,
            is_verified=True,  # Pre-verified for easy access
            created_at=datetime.utcnow()
        )
        
        db.add(demo_user)
        db.commit()
        db.refresh(demo_user)
        
        print("\n" + "="*60)
        print("   ✅ DEMO ACCOUNT CREATED SUCCESSFULLY!")
        print("="*60)
        print()
        print("📧 Email:", demo_email)
        print("🔑 Password:", demo_password)
        print("🎯 Role: Premium (Full Access)")
        print("✅ Status: Pre-Verified (Ready to use)")
        print()
        print("⏰ Valid for: 7 Days Client Demo")
        print(f"📅 Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📅 Expires: {(datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        print("="*60)
        print("   SHARE WITH CLIENT:")
        print("="*60)
        print()
        print("🌐 Access URL: http://localhost:5003")
        print("   (or use ngrok public URL)")
        print()
        print("📝 Login Credentials:")
        print(f"   Email: {demo_email}")
        print(f"   Password: {demo_password}")
        print()
        print("🎁 Features Included:")
        print("   ✓ Unlimited screenings")
        print("   ✓ Unlimited bulk screenings")
        print("   ✓ Unlimited job posts")
        print("   ✓ Advanced AI insights")
        print("   ✓ All premium features")
        print()
        print("="*60)
        print()
        
    except Exception as e:
        print(f"❌ Error creating demo account: {str(e)}")
        db.rollback()
    finally:
        db.close()


def verify_database():
    """Verify database is working properly"""
    
    print("\n" + "="*60)
    print("   🔍 DATABASE VERIFICATION")
    print("="*60)
    print()
    
    db = SessionLocal()
    
    try:
        # Check if database file exists
        db_path = Path("srp_smartrecruit_v3_2.db")
        if not db_path.exists():
            print("❌ Database file not found!")
            return False
        
        print(f"✅ Database file exists: {db_path.absolute()}")
        print(f"📦 Size: {db_path.stat().st_size / 1024:.2f} KB")
        print()
        
        # Count users
        user_count = db.query(User).count()
        print(f"👥 Total Users: {user_count}")
        
        # List all users
        users = db.query(User).all()
        if users:
            print("\n📋 Registered Users:")
            print("-" * 60)
            for user in users:
                print(f"   📧 {user.email}")
                print(f"      🎯 Role: {user.role}")
                print(f"      ✅ Verified: {'Yes' if user.is_verified else 'No'}")
                print(f"      📅 Created: {user.created_at.strftime('%Y-%m-%d %H:%M:%S') if user.created_at else 'N/A'}")
                print()
        
        print("="*60)
        print("✅ Database is working properly!")
        print("="*60)
        print()
        
        return True
        
    except Exception as e:
        print(f"❌ Database error: {str(e)}")
        return False
    finally:
        db.close()


if __name__ == "__main__":
    print("""
╔════════════════════════════════════════════════════════════╗
║   SRP SmartRecruit v3.2 - Demo Account Setup             ║
╚════════════════════════════════════════════════════════════╝
""")
    
    # First verify database
    if not verify_database():
        print("\n⚠️  Please fix database issues first!")
        input("\nPress Enter to exit...")
        sys.exit(1)
    
    # Create demo account
    create_demo_account()
    
    print("\n✅ Setup complete! Demo account is ready.")
    print("\n💡 TIP: Use START_WITH_NGROK.bat to get public URL for client")
    input("\nPress Enter to exit...")

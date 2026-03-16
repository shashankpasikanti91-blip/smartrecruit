#!/usr/bin/env python3
"""
Quick Database Activity Checker
Shows recent activities logged in the database
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path

def check_database():
    db_path = Path("srp_smartrecruit_v3_2.db")
    
    if not db_path.exists():
        print("❌ Database file not found: srp_smartrecruit_v3_2.db")
        return
    
    print(f"✅ Database found: {db_path} ({db_path.stat().st_size} bytes)")
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Check tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"📋 Tables found: {', '.join(tables)}")
        
        # Check users
        if 'users' in tables:
            cursor.execute("SELECT COUNT(*) FROM users")
            user_count = cursor.fetchone()[0]
            print(f"👤 Users: {user_count}")
            
            if user_count > 0:
                cursor.execute("SELECT id, email FROM users LIMIT 5")
                users = cursor.fetchall()
                for user_id, email in users:
                    print(f"   • User {user_id}: {email}")
        
        # Check screening results (activity logs)
        if 'screening_results' in tables:
            cursor.execute("SELECT COUNT(*) FROM screening_results")
            screening_count = cursor.fetchone()[0]
            print(f"📊 Screening results: {screening_count}")
            
            if screening_count > 0:
                cursor.execute("""
                    SELECT user_id, job_description, score, ai_analysis, created_at 
                    FROM screening_results 
                    ORDER BY created_at DESC 
                    LIMIT 10
                """)
                results = cursor.fetchall()
                print("\n🔍 Recent activities:")
                for user_id, job_desc, score, analysis, created_at in results:
                    try:
                        analysis_data = json.loads(analysis) if analysis else {}
                        if analysis_data.get('activity_log'):
                            action = analysis_data.get('details', {}).get('candidate_name', 'Unknown')
                            activity_type = job_desc.replace('Activity: ', '') if job_desc.startswith('Activity:') else job_desc[:50]
                            print(f"   • {created_at}: User {user_id} - {activity_type} ({action})")
                        else:
                            print(f"   • {created_at}: User {user_id} - Score: {score}% - {job_desc[:50]}...")
                    except:
                        print(f"   • {created_at}: User {user_id} - Score: {score}% - {job_desc[:50]}...")
        
        # Check resume metadata
        if 'resume_metadata' in tables:
            cursor.execute("SELECT COUNT(*) FROM resume_metadata")
            resume_count = cursor.fetchone()[0]
            print(f"📄 Resume metadata: {resume_count}")
        
        # Check interview invites
        if 'interview_invites' in tables:
            cursor.execute("SELECT COUNT(*) FROM interview_invites")
            invite_count = cursor.fetchone()[0]
            print(f"✉️ Interview invites: {invite_count}")
        
        conn.close()
        print("\n✅ Database check completed!")
        
    except Exception as e:
        print(f"❌ Database error: {e}")

if __name__ == "__main__":
    check_database()
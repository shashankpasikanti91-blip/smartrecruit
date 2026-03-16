#!/usr/bin/env python3
"""
Real-Time Database Viewer for SRP SmartRecruit v3.2
View all data activities live - no Supabase needed!
"""
import sqlite3
from datetime import datetime
import time
import os
import sys

DB_PATH = "srp_smartrecruit_v3_2.db"

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def view_all_data():
    """Display all tables data in real-time"""
    if not os.path.exists(DB_PATH):
        print("❌ Database not found! Run the app first with START_V3_2.bat")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        while True:
            clear_screen()
            print("=" * 80)
            print(f"🗄️  SRP SmartRecruit v3.2 - Live Database Monitor")
            print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"📂 Database: {DB_PATH}")
            print("=" * 80)
            
            # Users
            cursor.execute("SELECT COUNT(*), SUM(is_verified), role FROM users GROUP BY role")
            users = cursor.fetchall()
            print("\n👥 USERS:")
            if users:
                for count, verified, role in users:
                    print(f"   {role}: {count} total, {verified or 0} verified")
            else:
                print("   No users yet")
            
            # OTP Codes
            cursor.execute("SELECT COUNT(*) FROM otp_verifications WHERE is_used = 0")
            otp_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM otp_verifications")
            total_otp = cursor.fetchone()[0]
            print(f"\n🔐 OTP CODES: {otp_count} pending, {total_otp} total")
            
            # Active Sessions
            cursor.execute("SELECT COUNT(*) FROM sessions WHERE is_active = 1")
            sessions = cursor.fetchone()[0]
            print(f"🔑 ACTIVE SESSIONS: {sessions}")
            
            # Resumes
            cursor.execute("SELECT COUNT(*) FROM resume_metadata")
            resumes = cursor.fetchone()[0]
            print(f"\n📄 RESUMES: {resumes} uploaded")
            
            # Screenings
            cursor.execute("""
                SELECT COUNT(*), 
                       AVG(score), 
                       SUM(CASE WHEN is_eligible_for_invite = 1 THEN 1 ELSE 0 END)
                FROM screening_results
            """)
            result = cursor.fetchone()
            screen_count = result[0] or 0
            avg_score = result[1] or 0.0
            eligible = result[2] or 0
            
            print(f"🤖 SCREENINGS: {screen_count} total")
            if screen_count > 0:
                print(f"   Average Score: {avg_score:.1f}%")
                print(f"   Eligible for Interview: {eligible}")
            
            # Interview Invites
            cursor.execute("SELECT status, COUNT(*) FROM interview_invites GROUP BY status")
            invites = cursor.fetchall()
            print(f"\n📧 INTERVIEW INVITES:")
            if invites:
                for status, count in invites:
                    print(f"   {status}: {count}")
            else:
                print("   No invites yet")
            
            # Support Tickets
            cursor.execute("SELECT status, COUNT(*) FROM support_tickets GROUP BY status")
            tickets = cursor.fetchall()
            print(f"\n💬 SUPPORT TICKETS:")
            if tickets:
                for status, count in tickets:
                    print(f"   {status}: {count}")
            else:
                print("   No tickets yet")
            
            # Recent Activity
            cursor.execute("""
                SELECT email, created_at FROM users 
                ORDER BY created_at DESC LIMIT 5
            """)
            recent_users = cursor.fetchall()
            print(f"\n📈 RECENT REGISTRATIONS:")
            if recent_users:
                for email, created in recent_users:
                    print(f"   • {email} ({created})")
            else:
                print("   No registrations yet")
            
            # Recent Screenings
            cursor.execute("""
                SELECT sr.score, sr.created_at
                FROM screening_results sr
                ORDER BY sr.created_at DESC LIMIT 3
            """)
            recent_screenings = cursor.fetchall()
            if recent_screenings:
                print(f"\n🔍 RECENT SCREENINGS:")
                for score, created in recent_screenings:
                    print(f"   • Score: {score:.1f}% ({created})")
            
            print("\n" + "=" * 80)
            print("✨ Data is being stored in SQLite (No Supabase)")
            print("🔄 Auto-refreshing every 3 seconds... Press Ctrl+C to exit")
            print("=" * 80)
            
            time.sleep(3)
    except KeyboardInterrupt:
        print("\n\n✅ Database viewer closed.")
    finally:
        conn.close()

def view_specific_table():
    """View specific table data"""
    if not os.path.exists(DB_PATH):
        print("❌ Database not found! Run the app first.")
        return
    
    tables = [
        "users", "otp_verifications", "sessions", 
        "resume_metadata", "screening_results", 
        "interview_invites", "support_tickets"
    ]
    
    print("\n📋 Available Tables:")
    for i, table in enumerate(tables, 1):
        print(f"{i}. {table}")
    
    choice = input("\nEnter table number (1-7): ")
    try:
        table = tables[int(choice) - 1]
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute(f"SELECT * FROM {table} LIMIT 50")
        rows = cursor.fetchall()
        
        cursor.execute(f"PRAGMA table_info({table})")
        columns = [col[1] for col in cursor.fetchall()]
        
        print(f"\n📊 {table.upper()} ({len(rows)} rows shown, max 50):")
        print("-" * 120)
        print(" | ".join(columns))
        print("-" * 120)
        
        if rows:
            for row in rows:
                print(" | ".join(str(val)[:30] for val in row))  # Truncate long values
        else:
            print("   (No data yet)")
        
        conn.close()
        print("\n" + "-" * 120)
        input("\nPress Enter to continue...")
    except (ValueError, IndexError):
        print("❌ Invalid choice!")
    except Exception as e:
        print(f"❌ Error: {e}")

def export_to_csv():
    """Export a table to CSV"""
    if not os.path.exists(DB_PATH):
        print("❌ Database not found!")
        return
    
    tables = [
        "users", "otp_verifications", "sessions", 
        "resume_metadata", "screening_results", 
        "interview_invites", "support_tickets"
    ]
    
    print("\n📋 Available Tables:")
    for i, table in enumerate(tables, 1):
        print(f"{i}. {table}")
    
    choice = input("\nEnter table number (1-7): ")
    try:
        table_name = tables[int(choice) - 1]
        output_file = f"{table_name}_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()
        
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [col[1] for col in cursor.fetchall()]
        
        import csv
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(columns)
            writer.writerows(rows)
        
        conn.close()
        print(f"\n✅ Exported {len(rows)} rows to {output_file}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("=" * 80)
    print("🗄️  Database Viewer - SRP SmartRecruit v3.2")
    print("=" * 80)
    print("\n📂 Database Location:", DB_PATH)
    
    if not os.path.exists(DB_PATH):
        print("⚠️  Warning: Database file not found!")
        print("   Run START_V3_2.bat first to create the database.")
        print("\nPress Enter to exit...")
        input()
        sys.exit(1)
    
    print("\n✨ Options:")
    print("1. 🔄 Real-time monitor (auto-refresh every 3 seconds)")
    print("2. 📊 View specific table")
    print("3. 📁 Export table to CSV")
    print("4. ❌ Exit")
    
    choice = input("\nYour choice (1-4): ")
    
    if choice == "1":
        view_all_data()
    elif choice == "2":
        view_specific_table()
    elif choice == "3":
        export_to_csv()
    else:
        print("\n👋 Goodbye!")
        sys.exit(0)

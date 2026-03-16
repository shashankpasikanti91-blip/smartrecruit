#!/usr/bin/env python3
"""Quick database overview for VSCode"""
import sqlite3
import os

DB_PATH = "srp_smartrecruit_v3_2.db"

if not os.path.exists(DB_PATH):
    print("❌ Database not found!")
    exit(1)

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

print("=" * 70)
print("📊 SRP SmartRecruit v3.2 - Database Overview")
print("=" * 70)

# Get all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = cursor.fetchall()

print("\n✅ TABLES IN DATABASE:\n")
total_rows = 0
for table in tables:
    table_name = table[0]
    cursor.execute(f'SELECT COUNT(*) FROM {table_name}')
    count = cursor.fetchone()[0]
    total_rows += count
    
    # Get a sample of data if exists
    cursor.execute(f'SELECT * FROM {table_name} LIMIT 1')
    sample = cursor.fetchone()
    status = "✅ HAS DATA" if count > 0 else "⚪ EMPTY"
    
    print(f"   📋 {table_name:25} {count:>5} rows  {status}")

print("\n" + "-" * 70)
print(f"   TOTAL: {len(tables)} tables, {total_rows} total rows")
print("-" * 70)

# Show recent activity
print("\n📈 RECENT ACTIVITY:\n")

cursor.execute("SELECT COUNT(*) FROM users")
user_count = cursor.fetchone()[0]
print(f"   👥 Users registered: {user_count}")

cursor.execute("SELECT COUNT(*) FROM sessions WHERE is_active = 1")
active_sessions = cursor.fetchone()[0]
print(f"   🔑 Active sessions: {active_sessions}")

cursor.execute("SELECT COUNT(*) FROM resume_metadata")
resumes = cursor.fetchone()[0]
print(f"   📄 Resumes uploaded: {resumes}")

cursor.execute("SELECT COUNT(*) FROM screening_results")
screenings = cursor.fetchone()[0]
print(f"   🤖 Screening results: {screenings}")

if user_count > 0:
    cursor.execute("SELECT email, created_at FROM users ORDER BY created_at DESC LIMIT 3")
    recent = cursor.fetchall()
    print("\n   📝 Latest users:")
    for email, created in recent:
        print(f"      • {email} ({created})")

conn.close()

print("\n" + "=" * 70)
print("💡 HOW TO VIEW IN VSCODE:")
print("=" * 70)
print("""
1. Look at LEFT SIDEBAR → Find 'SQLite Explorer' section
2. You should see: srp_smartrecruit_v3_2.db
3. Click the ▶ arrow to expand the database
4. Expand any table (users, screening_results, etc.)
5. RIGHT-CLICK on a table → Select "Show Table"
6. View and edit data directly!

TIPS:
- Right-click table → "New Query" to run custom SQL
- Right-click table → "Show Table" to browse data
- Data updates in real-time as you use the API
""")
print("=" * 70)

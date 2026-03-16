# 🗄️ Database Viewer Guide - SRP SmartRecruit v3.2

## 📊 Where is Your Data Stored?

**Database File**: `srp_smartrecruit_v3_2.db` (SQLite database)  
**Location**: Project root folder  
**Type**: SQLite - File-based database  
**Status**: ✅ Active and storing all data

### ❌ Before (v3.1): Supabase
- Data stored in cloud (Supabase)
- Viewed via Supabase web dashboard
- Required internet connection
- **Status**: Removed completely

### ✅ Now (v3.2): SQLite
- Data stored locally in `.db` file
- No internet needed
- Full control over your data
- Fast and reliable

---

## 🔍 Method 1: DB Browser for SQLite (Recommended - GUI)

### Install
1. **Download**: https://sqlitebrowser.org/dl/
2. **Install**: Run installer (5MB)
3. **Open**: Launch DB Browser for SQLite

### View Your Data
1. Click **"Open Database"**
2. Navigate to project folder
3. Select `srp_smartrecruit_v3_2.db`
4. Click **"Browse Data"** tab

### What You'll See:
```
Tables:
├── users (all registered users)
├── otp_verifications (OTP codes)
├── sessions (active JWT sessions)
├── resume_metadata (uploaded resumes)
├── screening_results (AI analysis)
├── interview_invites (sent invites)
└── support_tickets (support requests)
```

### Live Monitoring:
- Click **"Execute SQL"** tab
- Run queries like:
```sql
-- See all users
SELECT * FROM users ORDER BY created_at DESC;

-- See recent screenings
SELECT * FROM screening_results ORDER BY created_at DESC LIMIT 10;

-- Check active sessions
SELECT * FROM sessions WHERE is_active = 1;

-- View interview invites
SELECT * FROM interview_invites ORDER BY created_at DESC;
```

---

## 🔍 Method 2: VSCode Extension (For Developers)

### Install Extension
1. Open VSCode
2. Press `Ctrl+Shift+X` (Extensions)
3. Search: **"SQLite"** by alexcvzz
4. Click **Install**

### View Database
1. Press `Ctrl+Shift+P` (Command Palette)
2. Type: `SQLite: Open Database`
3. Select `srp_smartrecruit_v3_2.db`
4. Click on SQLite Explorer in sidebar
5. Browse tables and data

### Benefits:
- ✅ View data while coding
- ✅ Run SQL queries directly
- ✅ No switching between apps
- ✅ Auto-refresh on changes

---

## 🔍 Method 3: Python Script (Real-Time Monitoring)

### Create Viewer Script
Save this as `view_database.py`:

```python
#!/usr/bin/env python3
"""
Real-Time Database Viewer for SRP SmartRecruit v3.2
"""
import sqlite3
from datetime import datetime
import time
import os

DB_PATH = "srp_smartrecruit_v3_2.db"

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def view_all_data():
    """Display all tables data in real-time"""
    if not os.path.exists(DB_PATH):
        print("❌ Database not found! Run the app first.")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    while True:
        clear_screen()
        print("=" * 80)
        print(f"🗄️  SRP SmartRecruit v3.2 - Database Monitor")
        print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        # Users
        cursor.execute("SELECT COUNT(*), SUM(is_verified), role FROM users GROUP BY role")
        users = cursor.fetchall()
        print("\n👥 USERS:")
        for count, verified, role in users:
            print(f"   {role}: {count} total, {verified or 0} verified")
        
        # OTP Codes
        cursor.execute("SELECT COUNT(*) FROM otp_verifications WHERE is_used = 0")
        otp_count = cursor.fetchone()[0]
        print(f"\n🔐 OTP CODES: {otp_count} pending")
        
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
        screen_count, avg_score, eligible = cursor.fetchone()
        print(f"🤖 SCREENINGS: {screen_count or 0} total")
        print(f"   Average Score: {avg_score or 0:.1f}%")
        print(f"   Eligible for Interview: {eligible or 0}")
        
        # Interview Invites
        cursor.execute("SELECT status, COUNT(*) FROM interview_invites GROUP BY status")
        invites = cursor.fetchall()
        print(f"\n📧 INTERVIEW INVITES:")
        for status, count in invites:
            print(f"   {status}: {count}")
        
        # Support Tickets
        cursor.execute("SELECT status, COUNT(*) FROM support_tickets GROUP BY status")
        tickets = cursor.fetchall()
        print(f"\n💬 SUPPORT TICKETS:")
        for status, count in tickets:
            print(f"   {status}: {count}")
        
        # Recent Activity
        cursor.execute("""
            SELECT email, created_at FROM users 
            ORDER BY created_at DESC LIMIT 3
        """)
        recent_users = cursor.fetchall()
        print(f"\n📈 RECENT REGISTRATIONS:")
        for email, created in recent_users:
            print(f"   • {email} ({created})")
        
        print("\n" + "=" * 80)
        print("Press Ctrl+C to exit | Refreshing every 3 seconds...")
        print("=" * 80)
        
        time.sleep(3)
    
    conn.close()

def view_specific_table():
    """View specific table data"""
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
        
        cursor.execute(f"SELECT * FROM {table}")
        rows = cursor.fetchall()
        
        cursor.execute(f"PRAGMA table_info({table})")
        columns = [col[1] for col in cursor.fetchall()]
        
        print(f"\n📊 {table.upper()} ({len(rows)} rows):")
        print("-" * 80)
        print(" | ".join(columns))
        print("-" * 80)
        
        for row in rows:
            print(" | ".join(str(val) for val in row))
        
        conn.close()
        input("\nPress Enter to continue...")
    except (ValueError, IndexError):
        print("❌ Invalid choice!")

if __name__ == "__main__":
    import sys
    
    print("🗄️  Database Viewer - SRP SmartRecruit v3.2")
    print("\nOptions:")
    print("1. Real-time monitor (auto-refresh)")
    print("2. View specific table")
    print("3. Exit")
    
    choice = input("\nYour choice (1-3): ")
    
    if choice == "1":
        try:
            view_all_data()
        except KeyboardInterrupt:
            print("\n\n✅ Database viewer closed.")
    elif choice == "2":
        view_specific_table()
    else:
        print("Goodbye!")
        sys.exit(0)
```

### Run the Viewer:
```bash
python view_database.py
```

### What You Get:
- ✅ Real-time statistics
- ✅ Auto-refresh every 3 seconds
- ✅ User counts, screenings, invites
- ✅ Recent activity feed
- ✅ No external tools needed

---

## 🔍 Method 4: Web-Based Admin Panel (Future Enhancement)

In future v3.3, we can add:
- Built-in admin dashboard
- Real-time charts and graphs
- Live activity feed
- User management UI
- Database export tools

---

## 📊 Common SQL Queries

### Check if Data is Saving
```sql
-- Count records in each table
SELECT 'users' AS table_name, COUNT(*) AS count FROM users
UNION ALL
SELECT 'screening_results', COUNT(*) FROM screening_results
UNION ALL
SELECT 'interview_invites', COUNT(*) FROM interview_invites
UNION ALL
SELECT 'support_tickets', COUNT(*) FROM support_tickets;
```

### View Latest Activity
```sql
-- Last 10 registrations
SELECT email, role, created_at 
FROM users 
ORDER BY created_at DESC 
LIMIT 10;

-- Latest screening results
SELECT u.email, s.score, s.ai_analysis
FROM screening_results s
JOIN users u ON s.user_id = u.id
ORDER BY s.created_at DESC
LIMIT 5;
```

### Check Active Users
```sql
-- Users with active sessions
SELECT u.email, u.role, s.created_at AS last_login
FROM users u
JOIN sessions s ON u.id = s.user_id
WHERE s.is_active = 1;
```

### Monitor Invitations
```sql
-- Interview invites by status
SELECT status, COUNT(*) AS count
FROM interview_invites
GROUP BY status;

-- Pending invites
SELECT ii.id, u.email, sr.score, ii.status
FROM interview_invites ii
JOIN users u ON ii.user_id = u.id
JOIN screening_results sr ON ii.screening_id = sr.id
WHERE ii.status = 'draft'
ORDER BY ii.created_at DESC;
```

---

## 🔄 Database Backup

### Manual Backup
```bash
# Copy the database file
copy srp_smartrecruit_v3_2.db srp_smartrecruit_v3_2_backup_2026-02-14.db
```

### Automated Backup Script
Create `backup_database.bat`:
```batch
@echo off
set TIMESTAMP=%date:~-4,4%%date:~-7,2%%date:~-10,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set TIMESTAMP=%TIMESTAMP: =0%
copy srp_smartrecruit_v3_2.db "Bin\Backups\backup_%TIMESTAMP%.db"
echo ✅ Database backed up to Bin\Backups\backup_%TIMESTAMP%.db
```

---

## 📈 Data Migration (Supabase → SQLite)

If you have old data in Supabase:

### 1. Export from Supabase
```sql
-- Run in Supabase SQL Editor
COPY (SELECT * FROM users) TO STDOUT WITH CSV HEADER;
COPY (SELECT * FROM screening_results) TO STDOUT WITH CSV HEADER;
```

### 2. Import to SQLite
```python
import sqlite3
import csv

conn = sqlite3.connect('srp_smartrecruit_v3_2.db')
cursor = conn.cursor()

# Import users
with open('users.csv', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        cursor.execute("""
            INSERT INTO users (email, hashed_password, role, is_verified)
            VALUES (?, ?, ?, ?)
        """, (row['email'], row['hashed_password'], row['role'], row['is_verified']))

conn.commit()
conn.close()
```

---

## ⚡ Performance Tips

### For Large Databases
If you have 10,000+ records:

1. **Use indexes** (already configured):
```sql
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id);
```

2. **Query optimization**:
```sql
-- Use LIMIT for large tables
SELECT * FROM screening_results ORDER BY created_at DESC LIMIT 100;

-- Use WHERE clauses to filter
SELECT * FROM users WHERE created_at > date('now', '-7 days');
```

3. **Database vacuum** (maintenance):
```sql
VACUUM;
```

---

## 🚀 Quick Comparison

| Feature | Supabase (v3.1) | SQLite (v3.2) |
|---------|----------------|---------------|
| **Storage** | Cloud ☁️ | Local 💾 |
| **Internet** | Required | Not required |
| **Speed** | ~100-300ms | ~1-5ms |
| **Cost** | $25/month | Free |
| **Control** | Limited | Full control |
| **Viewer** | Web dashboard | Multiple options |
| **Backup** | Automatic | Manual (easy) |
| **Scalability** | High | Medium* |

*For production with 100,000+ users, switch to PostgreSQL (already supported in config)

---

## 🎯 Testing Data Storage

### Test Workflow:
1. **Start app**: `START_V3_2.bat`
2. **Open API docs**: http://localhost:5003/docs
3. **Register user** via `/api/auth/register`
4. **Open DB Browser** → Refresh
5. **See new user** in `users` table ✅
6. **Verify OTP** → Check `otp_verifications` table
7. **Upload resume** → Check `resume_metadata` table
8. **Run screening** → Check `screening_results` table

### Real-Time Test:
```bash
# Terminal 1: Run app
START_V3_2.bat

# Terminal 2: Monitor database
python view_database.py

# Terminal 3: Run tests
python test_v3_2.py
```

Watch data appear in real-time! ✨

---

## ✅ Summary

### Your Data is NOW:
- ✅ Stored locally in `srp_smartrecruit_v3_2.db`
- ✅ Fully accessible via multiple tools
- ✅ Fast (no internet latency)
- ✅ Under your control
- ✅ Easy to backup
- ✅ No monthly costs

### To View Data:
1. **Best for beginners**: DB Browser for SQLite (GUI)
2. **Best for developers**: VSCode SQLite extension
3. **Best for monitoring**: Python viewer script (real-time)
4. **Best for queries**: Direct SQL commands

### No More Supabase! 🎉
- All data operations handled by FastAPI + SQLAlchemy
- Direct database access
- Full transparency
- Complete control

---

**Need help?** Check [README_V3_2_COMPLETE.md](README_V3_2_COMPLETE.md) for full documentation.

**Ready to start?** Run `START_V3_2.bat` and watch your data grow! 🚀

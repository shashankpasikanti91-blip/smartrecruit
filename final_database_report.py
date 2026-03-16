#!/usr/bin/env python3
"""
Final Database Report - Shows all data currently stored
"""
import sqlite3
import json
from datetime import datetime

db_file = 'srp_smartrecruit_v3_2.db'

print("=" * 100)
print("FINAL DATABASE REPORT - ALL STORED DATA")
print("=" * 100)
print(f"Database File: {db_file}")
print(f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

conn = sqlite3.connect(db_file)
cursor = conn.cursor()

# Get all table names
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = [row[0] for row in cursor.fetchall()]

print(f"Total Tables: {len(tables)}")
print("-" * 100)

for table in tables:
    print(f"\n📊 TABLE: {table.upper()}")
    print("-" * 100)
    
    # Get table info
    cursor.execute(f"PRAGMA table_info({table})")
    columns = cursor.fetchall()
    print(f"Columns: {len(columns)}")
    
    # Get row count
    cursor.execute(f"SELECT COUNT(*) FROM {table}")
    count = cursor.fetchone()[0]
    print(f"Records: {count}")
    
    if count > 0:
        # Show first few rows
        cursor.execute(f"SELECT * FROM {table} ORDER BY ROWID DESC LIMIT 10")
        rows = cursor.fetchall()
        
        # Get column names
        col_names = [col[1] for col in columns]
        
        print(f"\nLatest {min(len(rows), 10)} records:")
        for idx, row in enumerate(rows, 1):
            print(f"\n  [{idx}]", end="")
            for col_name, value in zip(col_names, row):
                # Truncate long values
                if isinstance(value, str) and len(value) > 50:
                    display_value = value[:47] + "..."
                else:
                    display_value = value
                print(f"\n      {col_name}: {display_value}", end="")
            print()

print("\n" + "=" * 100)
print("SCREENING RESULTS DETAILED VIEW")
print("=" * 100)

cursor.execute("""
    SELECT id, score, recommendation, status, created_at 
    FROM screening_results 
    ORDER BY id DESC
""")

screening_data = cursor.fetchall()
print(f"\nTotal Screening Records: {len(screening_data)}\n")

for record in screening_data:
    record_id, score, recommendation, status, created_at = record
    print(f"ID {record_id:3} | Score: {score:6.1f}% | Recommendation: {recommendation:8} | Status: {status} | Created: {created_at}")

conn.close()

print("\n" + "=" * 100)
print("✅ DATABASE REPORT COMPLETE")
print("=" * 100)

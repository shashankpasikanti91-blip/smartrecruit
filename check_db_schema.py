#!/usr/bin/env python3
"""
Check database schema
"""
import sqlite3

conn = sqlite3.connect('recruitment_ai.db')
cursor = conn.cursor()

print("=" * 80)
print("SCREENING_RESULTS TABLE SCHEMA")
print("=" * 80)

cursor.execute("PRAGMA table_info(screening_results)")
columns = cursor.fetchall()
print(f"\nColumns ({len(columns)} total):")
for col_id, name, col_type, notnull, default_val, pk in columns:
    print(f"  [{col_id}] {name:30} {col_type:15} {'NOT NULL' if notnull else ''}")

print("\n" + "=" * 80)
print("CHECKING IF job_description COLUMN EXISTS")
print("=" * 80)

has_job_description = any(col[1] == 'job_description' for col in columns)
print(f"job_description exists: {has_job_description}")

if not has_job_description:
    print("\n⚠️  job_description column is MISSING!")
    print("This is why the database insert is failing.")
    print("\nFIX: Need to add this column to the table")
    
conn.close()

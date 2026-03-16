#!/usr/bin/env python3
"""
Check screening_results table schema in the correct database
"""
import sqlite3

conn = sqlite3.connect('srp_smartrecruit_v3_2.db')
cursor = conn.cursor()

print("=" * 80)
print("SCREENING_RESULTS TABLE SCHEMA")
print("=" * 80)

cursor.execute("PRAGMA table_info(screening_results)")
columns = cursor.fetchall()

print(f"\nColumns ({len(columns)} total):")
for col_id, name, col_type, notnull, default_val, pk in columns:
    nullable = '' if notnull else ' [NULLABLE]'
    print(f"  {name:30} {col_type:15}{nullable}")

print("\n" + "=" * 80)
print("CHECKING DATA IN TABLE")
print("=" * 80)

cursor.execute("SELECT COUNT(*) FROM screening_results")
count = cursor.fetchone()[0]
print(f"Total records: {count}")

if count > 0:
    cursor.execute("SELECT id, score, recommendation, created_at FROM screening_results ORDER BY created_at DESC LIMIT 5")
    rows = cursor.fetchall()
    print("\nRecent records:")
    for row in rows:
        print(f"  ID={row[0]}, Score={row[1]}, Recommendation={row[2]}, Created={row[3]}")
else:
    print("No records in table")

conn.close()

#!/usr/bin/env python3
"""
Check which database file exists and has tables
"""
import sqlite3
import os

print("=" * 80)
print("DATABASE FILE CHECK")
print("=" * 80)

databases = ['srp_smartrecruit_v3_2.db', 'recruitment_ai.db']

for db_file in databases:
    if os.path.exists(db_file):
        print(f"\n✓ {db_file} EXISTS (size: {os.path.getsize(db_file)} bytes)")
        try:
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            print(f"  Tables: {len(tables)}")
            for table in tables:
                print(f"    - {table[0]}")
            conn.close()
        except Exception as e:
            print(f"  Error: {e}")
    else:
        print(f"\n✗ {db_file} DOES NOT EXIST")

print("\n" + "=" * 80)
print("Current directory:", os.getcwd())
print("=" * 80)

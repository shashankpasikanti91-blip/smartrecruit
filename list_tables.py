#!/usr/bin/env python3
"""
List all tables in the database
"""
import sqlite3

conn = sqlite3.connect('recruitment_ai.db')
cursor = conn.cursor()

print("=" * 80)
print("TABLES IN DATABASE")
print("=" * 80)

cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()

if tables:
    for table in tables:
        table_name = table[0]
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        print(f"\n{table_name} ({len(columns)} columns):")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
else:
    print("NO TABLES FOUND!")

conn.close()

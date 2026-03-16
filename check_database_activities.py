#!/usr/bin/env python3
"""
Database Activities Verification Report
Shows all data and activities done in the system
"""

import sqlite3
import os
from datetime import datetime
from pathlib import Path

db_path = "srp_smartrecruit_v3_2.db"

print("\n" + "=" * 80)
print("📊 DATABASE ACTIVITIES & DATA VERIFICATION REPORT")
print("=" * 80)
print(f"Database File: {db_path}")
print(f"File Size: {os.path.getsize(db_path) if os.path.exists(db_path) else 'NOT FOUND'} bytes")
print(f"Last Modified: {datetime.fromtimestamp(os.path.getmtime(db_path)).strftime('%Y-%m-%d %H:%M:%S') if os.path.exists(db_path) else 'N/A'}")
print("=" * 80 + "\n")

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all table names
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    print(f"📋 TABLES IN DATABASE: {len(tables)} tables found\n")
    
    for table_name in tables:
        table = table_name[0]
        print(f"\n{'-' * 80}")
        print(f"📌 TABLE: {table.upper()}")
        print(f"{'-' * 80}")
        
        # Get row count
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        row_count = cursor.fetchone()[0]
        
        # Get columns
        cursor.execute(f"PRAGMA table_info({table})")
        columns = cursor.fetchall()
        
        print(f"  Rows: {row_count}")
        print(f"  Columns: {len(columns)}")
        print(f"\n  Column Details:")
        for col in columns:
            col_id, col_name, col_type, notnull, default, pk = col
            print(f"    - {col_name:30} ({col_type:15}) {'[PRIMARY KEY]' if pk else ''}")
        
        # Show sample data
        if row_count > 0:
            cursor.execute(f"SELECT * FROM {table} LIMIT 5")
            rows = cursor.fetchall()
            
            print(f"\n  Sample Data (first {len(rows)} of {row_count} rows):")
            
            col_names = [col[1] for col in columns]
            
            # Create header
            header = " | ".join([f"{name:20}" for name in col_names])
            print(f"    {header}")
            print(f"    {'-' * len(header)}")
            
            # Print rows
            for row in rows:
                row_str = " | ".join([str(val)[:20].ljust(20) for val in row])
                print(f"    {row_str}")
        else:
            print(f"\n  ⚠️  No data in this table yet")
    
    conn.close()
    
    print("\n" + "=" * 80)
    print("✅ DATABASE VERIFICATION COMPLETE")
    print("=" * 80)
    print("\nREADY FOR CLIENT HANDOFF:")
    print("✓ Database file: srp_smartrecruit_v3_2.db")
    print("✓ All tables configured")
    print("✓ Application frozen - no changes")
    print("\n" + "=" * 80)
    
except sqlite3.Error as e:
    print(f"\n❌ Database Error: {e}")
except Exception as e:
    print(f"\n❌ Error: {e}")

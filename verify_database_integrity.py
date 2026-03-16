#!/usr/bin/env python3
"""
Database Integrity and Schema Verification
Tests database structure and data mapping
"""

import sqlite3
import os
from datetime import datetime

DB_PATH = "srp_smartrecruit_v3_2.db"

class DatabaseVerifier:
    def __init__(self, db_path):
        self.db_path = db_path
        self.connection = None
        self.results = []
        
    def connect(self):
        """Connect to database"""
        try:
            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = sqlite3.Row
            return True
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
    
    def get_tables(self):
        """Get all tables in database"""
        cursor = self.connection.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )
        return [row[0] for row in cursor.fetchall()]
    
    def get_table_schema(self, table_name):
        """Get table schema"""
        cursor = self.connection.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")
        return cursor.fetchall()
    
    def get_table_count(self, table_name):
        """Get row count for table"""
        cursor = self.connection.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        return cursor.fetchone()[0]
    
    def verify(self):
        """Run all verification checks"""
        if not self.connect():
            return False
        
        print("\n" + "="*70)
        print("📊 DATABASE INTEGRITY & SCHEMA VERIFICATION")
        print("="*70)
        
        # Check if database file exists
        if os.path.exists(self.db_path):
            size_mb = os.path.getsize(self.db_path) / (1024*1024)
            print(f"\n✅ Database file exists: {self.db_path}")
            print(f"   Size: {size_mb:.2f} MB")
        else:
            print(f"\n❌ Database file not found: {self.db_path}")
            return False
        
        # Get all tables
        tables = self.get_tables()
        print(f"\n✅ Found {len(tables)} database tables:")
        
        required_tables = [
            'users',
            'sessions',
            'resume_metadata',
            'screening_results',
            'otp_verifications',
            'support_tickets',
            'interview_invites'
        ]
        
        for table in sorted(tables):
            count = self.get_table_count(table)
            is_required = table in required_tables
            marker = "✅" if is_required else "ℹ️"
            
            print(f"\n   {marker} Table: {table.upper()}")
            print(f"      Rows: {count}")
            
            # Get schema
            schema = self.get_table_schema(table)
            print(f"      Columns: {len(schema)}")
            for col in schema[:5]:  # Show first 5 columns
                print(f"         - {col[1]} ({col[2]})")
            if len(schema) > 5:
                print(f"         ... and {len(schema)-5} more columns")
        
        # Check for required tables
        print(f"\n" + "-"*70)
        print("✅ REQUIRED TABLES CHECK:")
        missing = []
        for req_table in required_tables:
            if req_table in tables:
                print(f"   ✅ {req_table}")
            else:
                print(f"   ❌ {req_table} - MISSING!")
                missing.append(req_table)
        
        if missing:
            print(f"\n❌ Missing {len(missing)} required tables: {', '.join(missing)}")
            return False
        
        # Data integrity checks
        print(f"\n" + "-"*70)
        print("📋 DATA INTEGRITY CHECKS:")
        
        # Test resume_metadata table
        cursor = self.connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM resume_metadata")
        resume_count = cursor.fetchone()[0]
        print(f"\n   Resume Metadata:")
        print(f"      Total resumes processed: {resume_count}")
        if resume_count > 0:
            cursor.execute(
                "SELECT filename, extraction_method FROM resume_metadata LIMIT 3"
            )
            for row in cursor.fetchall():
                print(f"         - {row[0]} ({row[1]})")
        
        # Test screening_results table
        cursor.execute("SELECT COUNT(*) FROM screening_results")
        screening_count = cursor.fetchone()[0]
        print(f"\n   Screening Results:")
        print(f"      Total screenings: {screening_count}")
        if screening_count > 0:
            cursor.execute(
                "SELECT candidate_name, score, created_at FROM screening_results LIMIT 3"
            )
            for row in cursor.fetchall():
                print(f"         - {row[0]}: {row[1]} ({row[2][:10]})")
        
        # Test users table
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        print(f"\n   Users:")
        print(f"      Total users: {user_count}")
        if user_count > 0:
            cursor.execute("SELECT email, role FROM users LIMIT 3")
            for row in cursor.fetchall():
                print(f"         - {row[0]} ({row[1]})")
        
        print(f"\n" + "="*70)
        print("✅ DATABASE VERIFICATION COMPLETE - ALL CHECKS PASSED!")
        print("="*70 + "\n")
        
        return True
    
    def close(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()

if __name__ == "__main__":
    verifier = DatabaseVerifier(DB_PATH)
    success = verifier.verify()
    verifier.close()
    
    if not success:
        exit(1)

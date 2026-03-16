#!/usr/bin/env python
"""Test Supabase integration via API calls"""

import requests
import json
import time
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

print("=" * 70)
print("TESTING SUPABASE INTEGRATION FROM APP")
print("=" * 70)

API_URL = "http://localhost:5001"

# Test 1: Call screen-candidate endpoint
print("\n[TEST 1] Calling /api/screen-candidate endpoint...")
try:
    test_data = {
        "candidate_name": f"TestUser_{int(time.time())}",
        "job_title": "Software Engineer",
        "resume_text": "Python developer with 5 years experience in Flask and FastAPI. Strong in databases and REST APIs.",
        "jd_text": "We are looking for a Senior Python Developer with 3+ years of experience. Must be proficient in web frameworks and databases."
    }
    
    response = requests.post(f"{API_URL}/api/screen-candidate", json=test_data)
    print(f"  Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"  ✓ Screening successful!")
        print(f"  Match Score: {result.get('match_score')}%")
    else:
        print(f"  ✗ Error: {response.text[:200]}")
except Exception as e:
    print(f"  ✗ Failed: {e}")

# Wait for async operations
print("\n  Waiting 2 seconds for Supabase writes...")
time.sleep(2)

# Test 2: Check Supabase database directly
print("\n[TEST 2] Checking Supabase database...")
try:
    from supabase import create_client
    
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_KEY')
    client = create_client(url, key)
    
    # Get records
    resume_result = client.table("resume_metadata").select("*").execute()
    screening_result = client.table("screening_results").select("*").execute()
    
    print(f"  Resume metadata records: {len(resume_result.data) if resume_result.data else 0}")
    print(f"  Screening results records: {len(screening_result.data) if screening_result.data else 0}")
    
    if resume_result.data:
        latest = resume_result.data[-1]  # Last inserted record
        print(f"\n  Latest Resume Metadata:")
        print(f"    - Candidate: {latest.get('candidate_name')}")
        print(f"    - Created: {latest.get('created_at')}")
        print(f"    ✓ Data is flowing to Supabase!")
    else:
        print(f"\n  ✗ No data found in resume_metadata table")
        
except Exception as e:
    print(f"  ✗ Database check failed: {e}")

print("\n" + "=" * 70)

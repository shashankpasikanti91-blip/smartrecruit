#!/usr/bin/env python
"""
Comprehensive test of all Supabase tables and app endpoints
Tests data flow from app to database for ALL tables
"""

import requests
import json
import time
import os
from dotenv import load_dotenv

load_dotenv()

print("\n" + "=" * 80)
print("COMPREHENSIVE SUPABASE TABLE INTEGRATION TEST")
print("=" * 80)

API_URL = "http://localhost:5001"

def check_table_counts():
    """Check record counts in all tables"""
    from supabase import create_client
    
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_KEY')
    client = create_client(url, key)
    
    tables = {
        "resume_metadata": "Resume Metadata",
        "screening_results": "Screening Results",
        "ai_messages": "AI Messages",
        "activity_logs": "Activity Logs",
        "job_posts": "Job Posts"
    }
    
    counts = {}
    for table, label in tables.items():
        try:
            result = client.table(table).select("*").execute()
            count = len(result.data) if result.data else 0
            counts[table] = count
            print(f"  {label:25s}: {count:3d} records")
        except Exception as e:
            print(f"  {label:25s}: ERROR - {str(e)[:50]}")
    
    return counts

# ============================================================================
# TEST 1: SCREEN-CANDIDATE (resume_metadata + screening_results)
# ============================================================================
print("\n[TEST 1] /api/screen-candidate endpoint")
print("-" * 80)
print("Before test:")
before_counts = check_table_counts()

try:
    test_data = {
        "candidate_name": f"TestCandidate_{int(time.time())}",
        "job_title": "Python Developer",
        "resume_text": "5+ years Python, Flask, FastAPI, PostgreSQL, AWS, Docker, Git",
        "jd_text": "Senior Python Developer: 5+ yrs, Flask/FastAPI, DB design, cloud platforms"
    }
    
    print(f"\nCalling: POST {API_URL}/api/screen-candidate")
    print(f"  Candidate: {test_data['candidate_name']}")
    
    response = requests.post(f"{API_URL}/api/screen-candidate", json=test_data, timeout=30)
    
    if response.status_code == 200:
        result = response.json()
        print(f"  ✓ Success! Status: {response.status_code}")
        print(f"  Match Score: {result.get('match_score')}%")
    else:
        print(f"  ✗ Error: {response.text[:150]}")
        
except Exception as e:
    print(f"  ✗ Failed: {e}")

time.sleep(2)
print("\nAfter test:")
after_counts = check_table_counts()

# Show changes
print("\nChanges:")
for table in before_counts:
    change = after_counts.get(table, 0) - before_counts[table]
    if change > 0:
        print(f"  ✓ {table:25s}: +{change} (NOW: {after_counts.get(table, 0)} total)")
    elif change == 0:
        print(f"  ✗ {table:25s}: No change (still {after_counts.get(table, 0)})")

# ============================================================================
# TEST 2: GENERATE-MESSAGE (ai_messages)
# ============================================================================
print("\n\n[TEST 2] /api/generate-message endpoint")
print("-" * 80)
print("Before test:")
before_counts = check_table_counts()

try:
    test_data = {
        "recipient": "Test Candidate",
        "job_title": "Senior Developer",
        "tone": "professional",
        "type": "email"
    }
    
    print(f"\nCalling: POST {API_URL}/api/generate-message")
    print(f"  Recipient: {test_data['recipient']}")
    
    response = requests.post(f"{API_URL}/api/generate-message", json=test_data, timeout=30)
    
    if response.status_code == 200:
        result = response.json()
        print(f"  ✓ Success! Status: {response.status_code}")
        if result.get('message'):
            print(f"  Message length: {len(result['message'])} chars")
    else:
        print(f"  ✗ Error: {response.text[:150]}")
        
except Exception as e:
    print(f"  ✗ Failed: {e}")

time.sleep(2)
print("\nAfter test:")
after_counts = check_table_counts()

print("\nChanges:")
for table in before_counts:
    change = after_counts.get(table, 0) - before_counts[table]
    if change > 0:
        print(f"  ✓ {table:25s}: +{change} (NOW: {after_counts.get(table, 0)} total)")
    elif change == 0:
        print(f"  ✗ {table:25s}: No change (still {after_counts.get(table, 0)})")

# ============================================================================
# TEST 3: GENERATE-JOB-POST (job_posts)
# ============================================================================
print("\n\n[TEST 3] /api/generate-job-post endpoint")
print("-" * 80)
print("Before test:")
before_counts = check_table_counts()

try:
    test_data = {
        "job_title": "Senior Backend Engineer",
        "requirements": "Python, FastAPI, PostgreSQL, AWS, 5+ years"
    }
    
    print(f"\nCalling: POST {API_URL}/api/generate-job-post")
    print(f"  Job Title: {test_data['job_title']}")
    
    response = requests.post(f"{API_URL}/api/generate-job-post", json=test_data, timeout=30)
    
    if response.status_code == 200:
        result = response.json()
        print(f"  ✓ Success! Status: {response.status_code}")
        if 'posts' in result:
            print(f"  Posts generated: {len(result.get('posts', []))}")
    else:
        print(f"  ✗ Error: {response.text[:150]}")
        
except Exception as e:
    print(f"  ✗ Failed: {e}")

time.sleep(2)
print("\nAfter test:")
after_counts = check_table_counts()

print("\nChanges:")
for table in before_counts:
    change = after_counts.get(table, 0) - before_counts[table]
    if change > 0:
        print(f"  ✓ {table:25s}: +{change} (NOW: {after_counts.get(table, 0)} total)")
    elif change == 0:
        print(f"  ✗ {table:25s}: No change (still {after_counts.get(table, 0)})")

# ============================================================================
# FINAL SUMMARY
# ============================================================================
print("\n\n" + "=" * 80)
print("FINAL DATABASE STATE")
print("=" * 80)
final_counts = check_table_counts()

print("\n" + "=" * 80)
print("INTEGRATION STATUS")
print("=" * 80)

try:
    from supabase import create_client
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_KEY')
    client = create_client(url, key)
    
    # Check each table for recent app-generated data
    print("\nData Flow Verification:")
    
    # Check resume_metadata
    resume_data = client.table("resume_metadata").select("*").order("created_at", desc=True).limit(1).execute()
    if resume_data.data and "TestCandidate" in str(resume_data.data[0].get('candidate_name', '')):
        print(f"  ✓ resume_metadata: App data SAVED (Latest: {resume_data.data[0]['candidate_name']})")
    elif resume_data.data:
        print(f"  ✓ resume_metadata: Table has data (Latest: {resume_data.data[0]['candidate_name']})")
    else:
        print(f"  ✗ resume_metadata: NO DATA")
    
    # Check screening_results
    screening_data = client.table("screening_results").select("*").execute()
    if screening_data.data:
        print(f"  ✓ screening_results: Table has data ({len(screening_data.data)} records)")
    else:
        print(f"  ✗ screening_results: EMPTY")
    
    # Check ai_messages
    messages_data = client.table("ai_messages").select("*").execute()
    if messages_data.data:
        print(f"  ✓ ai_messages: Table has data ({len(messages_data.data)} records)")
    else:
        print(f"  ✗ ai_messages: EMPTY")
    
    # Check job_posts
    posts_data = client.table("job_posts").select("*").execute()
    if posts_data.data:
        print(f"  ✓ job_posts: Table has data ({len(posts_data.data)} records)")
    else:
        print(f"  ✗ job_posts: EMPTY")
    
    # Check activity_logs
    logs_data = client.table("activity_logs").select("*").execute()
    if logs_data.data:
        print(f"  ✓ activity_logs: Table has data ({len(logs_data.data)} records)")
    else:
        print(f"  ✗ activity_logs: EMPTY")

except Exception as e:
    print(f"  ✗ Error checking tables: {e}")

print("\n" + "=" * 80)

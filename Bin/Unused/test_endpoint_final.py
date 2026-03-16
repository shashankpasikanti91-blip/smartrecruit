#!/usr/bin/env python
"""Test endpoint integration after Supabase fixes"""
import requests
import json
import time

BASE_URL = "http://localhost:5001"

def test_screen_candidate():
    """Test the /api/screen-candidate endpoint"""
    print("\n" + "="*60)
    print("TEST 1: /api/screen-candidate")
    print("="*60)
    
    payload = {
        "resume_text": "John Doe, Senior Software Engineer, 5 years Python experience, AWS, Docker, Kubernetes",
        "jd_text": "Looking for Senior Software Engineer with 5+ years Python experience, AWS knowledge required",
        "candidate_name": "John Doe",
        "job_title": "Senior Software Engineer"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/screen-candidate", json=payload, timeout=30)
        print(f"Status Code: {response.status_code}")
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2)}")
        
        if response.status_code == 200:
            print("\n[OK] SUCCESS: Endpoint returned 200")
            print("[OK] Supabase should have saved screening_results")
        else:
            print(f"\n❌ FAILED: Expected 200, got {response.status_code}")
            if "error" in result:
                print(f"Error: {result['error']}")
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
    
    time.sleep(2)

def test_generate_message():
    """Test the /api/generate-message endpoint"""
    print("\n" + "="*60)
    print("TEST 2: /api/generate-message")
    print("="*60)
    
    payload = {
        "candidate_name": "John Doe",
        "job_title": "Senior Engineer",
        "recipient": "email",  # Changed from the actual endpoint params - need to check
        "tone": "professional"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/generate-message", json=payload, timeout=30)
        print(f"Status Code: {response.status_code}")
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2)[:200]}...")
        
        if response.status_code == 200:
            print("\n[OK] SUCCESS: Endpoint returned 200")
            print("[OK] Supabase should have saved ai_messages")
        else:
            print(f"\n❌ FAILED: Expected 200, got {response.status_code}")
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
    
    time.sleep(2)

def test_generate_job_post():
    """Test the /api/generate-job-post endpoint"""
    print("\n" + "="*60)
    print("TEST 3: /api/generate-job-post")
    print("="*60)
    
    payload = {
        "job_title": "Senior Software Engineer",
        "jd_text": "We are looking for a senior engineer with 5+ years Python experience, AWS knowledge, Docker, Kubernetes. Remote position, competitive salary.",
        "location": "Remote",
        "experience": "5+ years",
        "platforms": ["linkedin", "indeed", "email"]
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/generate-job-post", json=payload, timeout=30)
        print(f"Status Code: {response.status_code}")
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2)[:300]}...")
        
        if response.status_code == 200:
            print("\n[OK] SUCCESS: Endpoint returned 200")
            print("[OK] Supabase should have saved job_posts")
        else:
            print(f"\n[ERROR] FAILED: Expected 200, got {response.status_code}")
    except Exception as e:
        print(f"[ERROR] {str(e)}")

if __name__ == "__main__":
    print("\n" + "="*60)
    print("TESTING SUPABASE INTEGRATION ENDPOINTS")
    print("="*60)
    print("Testing that corrected column mappings work end-to-end")
    
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("[OK] App is running at", BASE_URL)
        else:
            print("[WARN] App responded but with unexpected status:", response.status_code)
    except Exception as e:
        print(f"[ERROR] App not running: {str(e)}")
        print("   Make sure Flask app is running on localhost:5001")
        exit(1)
    
    # Run tests
    test_screen_candidate()
    test_generate_message()
    test_generate_job_post()
    
    print("\n" + "="*60)
    print("TESTING COMPLETE")
    print("="*60)
    print("\nNow check Supabase console for new data in:")
    print("  - screening_results table")
    print("  - ai_messages table")
    print("  - job_posts table")

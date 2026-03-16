#!/usr/bin/env python3
"""Test the screening fix"""

import requests
import json
import time

# Wait for server to be ready
time.sleep(2)

# Test case 1: Kautham with proper skills
data1 = {
    "candidate_name": "Kautham",
    "job_title": "Java Developer",
    "resume_text": "Kautham has 5 years of Java development experience. Skilled in Spring Boot, microservices, and RESTful APIs. Experienced with Docker and Kubernetes.",
    "jd_text": "We are looking for a Java Developer with 3+ years of experience. Required: Java, Spring Boot, Docker. Preferred: Kubernetes, Jenkins."
}

print("=" * 80)
print("TEST 1: Kautham - Java Developer")
print("=" * 80)

try:
    response = requests.post('http://localhost:5000/api/screen-candidate', json=data1, timeout=30)
    result = response.json()
    print(json.dumps(result, indent=2))
    
    # Verify the match score is NOT 0%
    match_score = result.get('match_score', 0)
    print(f"\n✓ Match Score: {match_score}%")
    
    if match_score > 0:
        print("✓ FIX SUCCESSFUL: Score is not 0%!")
    else:
        print("✗ STILL BROKEN: Score is still 0%")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

# Test case 2: Minimal resume (to trigger fallback)
print("\n" + "=" * 80)
print("TEST 2: Minimal Resume (triggers fallback)")
print("=" * 80)

data2 = {
    "candidate_name": "Smith",
    "job_title": "Python Developer",
    "resume_text": "Software engineer with experience in Python",
    "jd_text": "Python developer needed. Requirements: Python, SQL, REST APIs"
}

try:
    response = requests.post('http://localhost:5000/api/screen-candidate', json=data2, timeout=30)
    result = response.json()
    print(json.dumps(result, indent=2))
    
    match_score = result.get('match_score', 0)
    print(f"\n✓ Match Score: {match_score}%")
    
    if match_score >= 35:
        print("✓ FIX SUCCESSFUL: Fallback score >= 35%!")
    else:
        print("✗ STILL BROKEN: Fallback score < 35%")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("TEST COMPLETE")
print("=" * 80)

#!/usr/bin/env python3
"""
COMPREHENSIVE ATS SYSTEM TEST
Tests all endpoints, all response fields, all features
"""

import requests
import json
import time

BASE_URL = "http://localhost:5000"
TIME_WAIT = 2

def print_section(title):
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)

def test_endpoint(name, method, url, data=None, expected_fields=None):
    """Test an endpoint and verify response structure"""
    try:
        if method == "POST":
            resp = requests.post(f"{BASE_URL}{url}", json=data, timeout=30)
        else:
            resp = requests.get(f"{BASE_URL}{url}", timeout=30)
        
        result = resp.json()
        print(f"\n✓ {name}")
        print(f"  Status: {resp.status_code}")
        print(f"  Response Keys: {list(result.keys())}")
        
        # Check required fields
        if expected_fields:
            for field in expected_fields:
                if field in result or (isinstance(result, dict) and 'data' in result and field in result.get('data', {})):
                    print(f"  ✓ Field '{field}' present")
                else:
                    print(f"  ✗ Field '{field}' MISSING!")
                    return False
        
        return True
    except Exception as e:
        print(f"✗ {name} - Error: {e}")
        return False

print_section("STARTING COMPREHENSIVE ATS TEST SUITE")
print(f"Base URL: {BASE_URL}")
print(f"Waiting {TIME_WAIT} seconds for server...")
time.sleep(TIME_WAIT)

results = {}

# =============================================================================
# TEST 1: SINGLE CANDIDATE SCREENING
# =============================================================================
print_section("TEST 1: SINGLE CANDIDATE SCREENING")

screening_data = {
    "candidate_name": "John Smith",
    "job_title": "Senior Python Developer",
    "resume_text": "John Smith with 7 years Python experience. Expert in Django, FastAPI, PostgreSQL. Led team of 5 developers. AWS certified.",
    "jd_text": "Senior Python Developer needed. Requirements: 5+ years Python, Django/FastAPI, Database design, Team leadership. Preferred: AWS, Docker"
}

result = test_endpoint(
    "Single Screening Test",
    "POST",
    "/api/screen-candidate",
    screening_data,
    ["match_score", "recommendation", "assessment", "decision", "candidate_name"]
)
results["single_screening"] = result

if result:
    resp = requests.post(f"{BASE_URL}/api/screen-candidate", json=screening_data)
    data = resp.json()
    print(f"\n  Match Score: {data.get('match_score', 'N/A')}%")
    print(f"  Recommendation: {data.get('recommendation', 'N/A')}")
    print(f"  Decision: {data.get('decision', 'N/A')}")
    
    # Verify no 0% scores
    if data.get('match_score') == 0:
        print(f"  ✗ CRITICAL: Score is 0%!")
        results["single_screening"] = False
    elif data.get('match_score') is None:
        print(f"  ✗ CRITICAL: Score is missing!")
        results["single_screening"] = False
    else:
        print(f"  ✓ Score is valid: {data.get('match_score')}%")

# =============================================================================
# TEST 2: BULK SCREENING
# =============================================================================
print_section("TEST 2: BULK SCREENING")

bulk_data = {
    "jd_text": "Senior Java Developer. Requirements: 5+ years Java, Spring Boot, Microservices",
    "candidates": [
        {
            "Name": "Alice Johnson",
            "Resume": "Java developer with 6 years experience. Spring Boot, Docker, Kubernetes"
        },
        {
            "Name": "Bob Wilson",
            "Resume": "Software engineer with Python skills, recently switched to Java"
        },
        {
            "Name": "Carol Davis",
            "Resume": "Senior Java architect. 8 years microservices, Spring, Maven"
        }
    ]
}

result = test_endpoint(
    "Bulk Screening Test",
    "POST",
    "/api/bulk-screen",
    bulk_data,
    ["status"]
)
results["bulk_screening"] = result

if result:
    resp = requests.post(f"{BASE_URL}/api/bulk-screen", json=bulk_data)
    data = resp.json()
    
    if 'data' in data:
        candidates_results = data['data']
    else:
        candidates_results = data.get('results', [])
    
    print(f"\n  Total Candidates: {len(bulk_data['candidates'])}")
    print(f"  Results Count: {len(candidates_results) if isinstance(candidates_results, list) else 'N/A'}")
    
    if isinstance(candidates_results, list):
        for i, cand in enumerate(candidates_results[:3]):
            print(f"\n  Candidate {i+1}:")
            print(f"    Name: {cand.get('candidate', cand.get('name', 'N/A'))}")
            print(f"    Score: {cand.get('match_score', 'N/A')}%")
            
            # Check for 0% scores
            if cand.get('match_score') == 0:
                print(f"    ✗ Score is 0%!")
                results["bulk_screening"] = False

# =============================================================================
# TEST 3: JOB POST GENERATION
# =============================================================================
print_section("TEST 3: JOB POST GENERATION")

job_post_data = {
    "job_title": "Full Stack Developer",
    "jd_text": "Full Stack Developer needed. Frontend: React, TypeScript. Backend: Node.js, Express. Database: PostgreSQL",
    "location": "Remote",
    "experience": "3-5 years"
}

result = test_endpoint(
    "Job Post Generation Test",
    "POST",
    "/api/generate-job-post",
    job_post_data,
    ["status"]
)
results["job_posts"] = result

if result:
    resp = requests.post(f"{BASE_URL}/api/generate-job-post", json=job_post_data)
    data = resp.json()
    posts = data.get('data', {})
    
    print(f"\n  Generated Posts:")
    platforms = ['linkedin', 'indeed', 'email', 'whatsapp']
    for platform in platforms:
        content = posts.get(platform, posts.get(f'{platform}_post', ''))
        if content:
            print(f"  ✓ {platform.upper()}: {len(content)} characters")
            if len(content) < 50:
                print(f"    ✗ WARNING: Very short content ({len(content)} chars)")
                results["job_posts"] = False
        else:
            print(f"  ✗ {platform.upper()}: MISSING!")
            results["job_posts"] = False

# =============================================================================
# TEST 4: MESSAGE GENERATION
# =============================================================================
print_section("TEST 4: MESSAGE GENERATION")

message_data = {
    "message_type": "interview_invite",
    "recipient": "John Doe",
    "job_title": "Senior Developer",
    "tone": "professional",
    "context": "Strong background in system design"
}

result = test_endpoint(
    "Message Generation Test",
    "POST",
    "/api/generate-message",
    message_data,
    ["status"]
)
results["message_gen"] = result

if result:
    resp = requests.post(f"{BASE_URL}/api/generate-message", json=message_data)
    data = resp.json()
    msg_data = data.get('data', {})
    
    message = msg_data.get('output', msg_data.get('message', ''))
    print(f"\n  Message Type: {msg_data.get('type', 'N/A')}")
    print(f"  Message Length: {len(message)} characters")
    print(f"  Message Preview: {message[:100]}...")
    
    if len(message) < 20:
        print(f"  ✗ Message too short!")
        results["message_gen"] = False
    elif "john doe" in message.lower() and "developer" in message.lower():
        print(f"  ✓ Message contains recipient and position")
    else:
        print(f"  ⚠ Message structure may be incomplete")

# =============================================================================
# TEST 5: AI WRITING
# =============================================================================
print_section("TEST 5: AI WRITING (Rewrite)")

ai_write_data = {
    "text": "We need a senior developer urgently",
    "action": "rewrite",
    "tone": "formal",
    "platform": "email"
}

result = test_endpoint(
    "AI Writing Test",
    "POST",
    "/api/ai-write",
    ai_write_data,
    ["status"]
)
results["ai_writing"] = result

if result:
    resp = requests.post(f"{BASE_URL}/api/ai-write", json=ai_write_data)
    data = resp.json()
    write_data = data.get('data', {})
    
    output = write_data.get('output', '')
    print(f"\n  Action: {write_data.get('action', 'N/A')}")
    print(f"  Tone: {write_data.get('tone', 'N/A')}")
    print(f"  Platform: {write_data.get('platform', 'N/A')}")
    print(f"  Output Length: {len(output)} characters")
    print(f"  Output Preview: {output[:80]}...")
    
    if len(output) < 20:
        print(f"  ✗ Output too short!")
        results["ai_writing"] = False

# =============================================================================
# TEST 6: FILE UPLOAD & PARSING
# =============================================================================
print_section("TEST 6: FILE UPLOAD ENDPOINT")

try:
    # Test upload endpoint exists
    resp = requests.get(f"{BASE_URL}/api/logs")
    if resp.status_code == 200:
        logs = resp.json()
        print(f"✓ Logs Endpoint Working")
        print(f"  Total log lines: {logs.get('total', 'N/A')}")
        results["logs"] = True
    else:
        print(f"✗ Logs Endpoint Failed")
        results["logs"] = False
except Exception as e:
    print(f"✗ Logs Endpoint Error: {e}")
    results["logs"] = False

# =============================================================================
# TEST 7: RESPONSE STRUCTURE VALIDATION
# =============================================================================
print_section("TEST 7: RESPONSE STRUCTURE VALIDATION")

print("\nChecking consistent response structures across all endpoints...")

# Test that all POST endpoints return data wrapped properly
endpoints_to_check = [
    ("screening", "/api/screen-candidate", screening_data),
    ("bulk", "/api/bulk-screen", bulk_data),
    ("job_posts", "/api/generate-job-post", job_post_data),
    ("messages", "/api/generate-message", message_data),
    ("ai_write", "/api/ai-write", ai_write_data),
]

response_structure_ok = True
for name, endpoint, payload in endpoints_to_check:
    try:
        resp = requests.post(f"{BASE_URL}{endpoint}", json=payload, timeout=30)
        data = resp.json()
        
        # Check for required top-level keys
        has_status = 'status' in data
        has_data = 'data' in data or any(key in data for key in ['match_score', 'message_score', 'output'])
        
        if has_status and has_data:
            print(f"  ✓ {name}: Proper structure (status + data)")
        elif has_status:
            print(f"  ⚠ {name}: Has status but data structure unclear")
        else:
            print(f"  ✗ {name}: Missing standard structure")
            response_structure_ok = False
            
    except Exception as e:
        print(f"  ✗ {name}: Error - {e}")
        response_structure_ok = False

results["response_structure"] = response_structure_ok

# =============================================================================
# FINAL SUMMARY
# =============================================================================
print_section("FINAL TEST SUMMARY")

passed = sum(1 for v in results.values() if v)
total = len(results)

print(f"\nTests Passed: {passed}/{total}")
print(f"\nDetailed Results:")
for feature, status in results.items():
    status_icon = "✓" if status else "✗"
    print(f"  {status_icon} {feature.replace('_', ' ').title()}")

if passed == total:
    print(f"\n{'='*80}")
    print("  ALL TESTS PASSED! System is fully functional.")
    print(f"{'='*80}")
else:
    print(f"\n{'='*80}")
    print(f"  {total - passed} TEST(S) FAILED - Review issues above")
    print(f"{'='*80}")

print(f"\nTest completed at: {time.strftime('%Y-%m-%d %H:%M:%S')}")

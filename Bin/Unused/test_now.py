#!/usr/bin/env python3
"""Quick test of all fixed endpoints"""
import time
import requests
import json

BASE_URL = "http://localhost:5000"

print("[TEST] Waiting for Flask to start...")
time.sleep(3)

# Test 1: Check if server is running
print("\n[1] Server Status Check")
try:
    resp = requests.get(f"{BASE_URL}/", timeout=5)
    print(f"✓ Server running (Status: {resp.status_code})")
except Exception as e:
    print(f"✗ Server not responding: {e}")
    exit(1)

# Test 2: Single Screening (Match Score Test)
print("\n[2] Single Screening - Match Score Test")
screening_data = {
    "resume_text": "John Smith - Senior Python Developer with 8 years experience in AI/ML",
    "job_description": "Seeking Python developer with 5+ years ML experience"
}
try:
    resp = requests.post(f"{BASE_URL}/screen", json=screening_data, timeout=30)
    result = resp.json()
    if result.get("status") == "success":
        score = result["data"].get("score", 0)
        print(f"✓ Screening works - Score: {score}%")
        if score == 0:
            print("  ✗ ERROR: Score is 0% (bug not fixed)")
        elif score >= 35:
            print(f"  ✓ Score >= 35% (fix verified)")
    else:
        print(f"✗ Screening failed: {result}")
except Exception as e:
    print(f"✗ Screening error: {e}")

# Test 3: Job Posts (Check for Content)
print("\n[3] Job Posts Generation - Field Test")
job_data = {
    "position": "Senior Python Developer",
    "description": "We need an experienced Python developer for our ML team"
}
try:
    resp = requests.post(f"{BASE_URL}/job-posts", json=job_data, timeout=30)
    result = resp.json()
    if result.get("status") == "success":
        data = result["data"]
        platforms = ["linkedin", "indeed", "email", "whatsapp"]
        all_have_content = True
        for platform in platforms:
            content = data.get(platform, "")
            has_content = bool(content and len(content) > 10)
            status = "✓" if has_content else "✗"
            print(f"  {status} {platform}: {len(content)} chars")
            if not has_content:
                all_have_content = False
        if all_have_content:
            print("✓ All platforms have content")
        else:
            print("✗ Some platforms are empty")
    else:
        print(f"✗ Job posts failed: {result}")
except Exception as e:
    print(f"✗ Job posts error: {e}")

# Test 4: Messages Generation
print("\n[4] Messages Generation - Content Test")
msg_data = {
    "candidate_name": "John Smith",
    "position": "Senior Developer",
    "decision": "move_forward",
    "evaluation": "Strong technical skills"
}
try:
    resp = requests.post(f"{BASE_URL}/messages", json=msg_data, timeout=30)
    result = resp.json()
    if result.get("status") == "success":
        output = result["data"].get("output", "")
        if output and len(output) > 20:
            print(f"✓ Message generated: {len(output)} chars")
            print(f"  Preview: {output[:100]}...")
        else:
            print(f"✗ Message is empty or too short: {len(output)} chars")
    else:
        print(f"✗ Messages failed: {result}")
except Exception as e:
    print(f"✗ Messages error: {e}")

# Test 5: Bulk Screening
print("\n[5] Bulk Screening - Multiple Candidates")
bulk_data = {
    "candidates": [
        {"name": "Alice Dev", "resume": "5 years Python experience"},
        {"name": "Bob Dev", "resume": "8 years Python and ML experience"},
        {"name": "Charlie Dev", "resume": "2 years junior developer"}
    ],
    "job_description": "Senior Python Developer with 5+ years experience"
}
try:
    resp = requests.post(f"{BASE_URL}/bulk-screen", json=bulk_data, timeout=30)
    result = resp.json()
    if result.get("status") == "success":
        candidates = result["data"].get("candidates", [])
        print(f"✓ Bulk screening processed {len(candidates)} candidates")
        zero_scores = sum(1 for c in candidates if c.get("score", 0) == 0)
        if zero_scores > 0:
            print(f"  ✗ Found {zero_scores} candidates with 0% score")
        else:
            print(f"  ✓ No zero scores - all >= 35%")
        for i, c in enumerate(candidates[:3], 1):
            print(f"    {i}. {c.get('name')}: {c.get('score')}%")
    else:
        print(f"✗ Bulk screening failed: {result}")
except Exception as e:
    print(f"✗ Bulk screening error: {e}")

print("\n" + "="*60)
print("[SUMMARY] Test complete - Check results above")
print("="*60)

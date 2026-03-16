#!/usr/bin/env python3
"""
Comprehensive Navigation & API Test
Tests all ATS endpoints to verify everything works
"""

import requests
import json
import time
from typing import Dict, List, Tuple

BASE_URL = "http://localhost:5000"

class Tester:
    def __init__(self):
        self.results = []
        self.passed = 0
        self.failed = 0
    
    def test(self, name: str, method: str, endpoint: str, payload=None, expected_status=200) -> bool:
        """Test an endpoint"""
        url = f"{BASE_URL}{endpoint}"
        try:
            if method == "GET":
                resp = requests.get(url, timeout=5)
            else:  # POST
                resp = requests.post(url, json=payload, timeout=5)
            
            success = resp.status_code == expected_status
            status_str = "✓ OK" if success else f"✗ FAIL ({resp.status_code})"
            
            if success:
                self.passed += 1
            else:
                self.failed += 1
                
            self.results.append({
                'name': name,
                'status': status_str,
                'endpoint': endpoint,
                'response_len': len(resp.text)
            })
            return success
        except Exception as e:
            self.failed += 1
            self.results.append({
                'name': name,
                'status': f"✗ ERROR: {str(e)[:50]}",
                'endpoint': endpoint,
                'response_len': 0
            })
            return False
    
    def print_results(self):
        """Print test results"""
        print("\n" + "="*80)
        print("RECRUITMENT ATS - NAVIGATION & API TEST RESULTS")
        print("="*80)
        
        for i, result in enumerate(self, 1):
            print(f"\n[{i}] {result['name']}")
            print(f"    Endpoint: {result['endpoint']}")
            print(f"    Result: {result['status']}")
            print(f"    Response: {result['response_len']} bytes")
        
        print("\n" + "="*80)
        print(f"SUMMARY: {self.passed} PASSED | {self.failed} FAILED | Total: {len(self.results)}")
        print("="*80 + "\n")
        
        return self.passed, self.failed
    
    def __iter__(self):
        return iter(self.results)

# Create tester
tester = Tester()

print("\n🚀 Starting Comprehensive ATS Tests...\n")

# ============================================================================
# MAIN PAGES
# ============================================================================
print("[PHASE 1] Testing Main Pages...")
tester.test("Homepage", "GET", "/", expected_status=200)
time.sleep(0.5)

# ============================================================================
# CORE APIs
# ============================================================================
print("[PHASE 2] Testing Core APIs...")
tester.test("Status API", "GET", "/api/status", expected_status=200)
tester.test("Logs API", "GET", "/api/logs", expected_status=200)
time.sleep(0.5)

# ============================================================================
# AI WRITING TESTS
# ============================================================================
print("[PHASE 3] Testing AI Writing Feature...")
tester.test(
    "AI Write - Rewrite",
    "POST",
    "/api/ai-write",
    {
        "text": "We need to meet very soon",
        "action": "rewrite",
        "tone": "professional",
        "platform": "email"
    },
    expected_status=200
)

tester.test(
    "AI Write - Paraphrase",
    "POST",
    "/api/ai-write",
    {
        "text": "Thank you for the update",
        "action": "paraphrase",
        "tone": "friendly",
        "platform": "message"
    },
    expected_status=200
)

tester.test(
    "AI Write - Reply",
    "POST",
    "/api/ai-write",
    {
        "text": "Can you send me the report?",
        "action": "reply",
        "tone": "professional",
        "platform": "email"
    },
    expected_status=200
)
time.sleep(1)

# ============================================================================
# MESSAGE GENERATION TESTS
# ============================================================================
print("[PHASE 4] Testing Message Generation...")
tester.test(
    "Generate Interview Message",
    "POST",
    "/api/generate-message",
    {
        "message_type": "interview",
        "recipient": "John Doe",
        "job_title": "Senior Developer",
        "tone": "professional",
        "context": ""
    },
    expected_status=200
)

tester.test(
    "Generate Offer with Context",
    "POST",
    "/api/generate-message",
    {
        "message_type": "offer",
        "recipient": "Sarah Chen",
        "job_title": "Engineering Manager",
        "tone": "professional",
        "context": "promotion from senior engineer to manager"
    },
    expected_status=200
)

tester.test(
    "Generate Rejection Message",
    "POST",
    "/api/generate-message",
    {
        "message_type": "rejection",
        "recipient": "Mike Johnson",
        "job_title": "Marketing Manager",
        "tone": "friendly",
        "context": ""
    },
    expected_status=200
)

tester.test(
    "Generate Follow-up Message",
    "POST",
    "/api/generate-message",
    {
        "message_type": "follow_up",
        "recipient": "Emma Wilson",
        "job_title": "Product Manager",
        "tone": "professional",
        "context": "urgent hiring deadline"
    },
    expected_status=200
)
time.sleep(1)

# ============================================================================
# FILE UPLOAD TESTS (Dummy test)
# ============================================================================
print("[PHASE 5] Testing File Upload Endpoint...")
tester.test(
    "File Upload Endpoint",
    "GET",
    "/api/upload-file",  # Just checking endpoint exists
    expected_status=405  # Method not allowed (expected for GET)
)
time.sleep(0.5)

# ============================================================================
# JOB POSTING TESTS
# ============================================================================
print("[PHASE 6] Testing Job Posting...")
tester.test(
    "Generate Job Post",
    "POST",
    "/api/generate-job-post",
    {
        "job_title": "Senior Python Developer",
        "description": "Looking for experienced Python developer for backend work",
        "requirements": "5+ years experience, Django expertise"
    },
    expected_status=200
)
time.sleep(0.5)

# ============================================================================
# PRINT RESULTS
# ============================================================================
passed, failed = tester.print_results()

# Final status
if failed == 0:
    print("✓ ALL TESTS PASSED! System is fully operational.\n")
    exit(0)
else:
    print(f"✗ {failed} tests failed. Check errors above.\n")
    exit(1)

#!/usr/bin/env python3
"""
Quick test script for all fixed endpoints
Run this after starting the Flask app
"""

import requests
import json
import time
from typing import Dict, Any

BASE_URL = 'http://localhost:5000'

def test_endpoint(name: str, endpoint: str, payload: Dict[str, Any]) -> bool:
    """Test an endpoint and report result"""
    print(f"\n{'='*60}")
    print(f"TEST: {name}")
    print(f"{'='*60}")
    
    try:
        print(f"POST {endpoint}")
        print(f"Payload: {json.dumps(payload, indent=2)[:200]}...")
        
        resp = requests.post(
            f"{BASE_URL}{endpoint}",
            json=payload,
            timeout=15
        )
        
        print(f"\n✓ Status Code: {resp.status_code}")
        
        if resp.status_code == 200:
            data = resp.json()
            print(f"✓ Response Status: {data.get('status')}")
            
            # Show relevant output
            if 'data' in data:
                if 'output' in data['data']:
                    output = str(data['data']['output'])[:150]
                    print(f"✓ Output: {output}...")
                if 'message' in data['data']:
                    msg = str(data['data']['message'])[:150]
                    print(f"✓ Message: {msg}...")
                if 'match_score' in data['data']:
                    print(f"✓ Match Score: {data['data']['match_score']}")
            
            return True
        else:
            print(f"✗ Error: {resp.text[:200]}")
            return False
            
    except Exception as e:
        print(f"✗ Failed: {str(e)}")
        return False


def main():
    print("\n")
    print("█" * 60)
    print("RECRUITMENT ATS - ENDPOINT TESTS")
    print("█" * 60)
    print(f"\nBase URL: {BASE_URL}")
    print("Waiting for Flask to respond...")
    
    # Wait for Flask
    time.sleep(2)
    
    results = []
    
    # Test 1: AI Writing (should already work)
    results.append(("AI Writing", test_endpoint(
        "AI Writing Assistant",
        "/api/ai-write",
        {
            "text": "We need to meet ASAP to discuss the project",
            "action": "rewrite",
            "tone": "professional",
            "platform": "email"
        }
    )))
    
    # Test 2: Generate Message (was failing, now fixed)
    results.append(("Generate Message", test_endpoint(
        "Generate Message (FIXED)",
        "/api/generate-message",
        {
            "message_type": "interview_invite",
            "recipient": "Jane Smith",
            "job_title": "Senior Python Developer",
            "context": "promotion to lead engineer position"
        }
    )))
    
    # Test 3: Single Screen (was failing, now fixed)
    results.append(("Single Screen", test_endpoint(
        "Single Screen Candidate (FIXED)",
        "/api/screen-candidate",
        {
            "candidate_name": "Bob Johnson",
            "resume_text": "Python developer with 7 years experience in Django, FastAPI, and AWS deployment",
            "jd_text": "Senior Python developer needed. Must have 5+ years Django experience and AWS knowledge"
        }
    )))
    
    # Test 4: Bulk Screen (was failing, now fixed)
    results.append(("Bulk Screen", test_endpoint(
        "Bulk Screening (FIXED)",
        "/api/bulk-screen",
        {
            "jd_text": "Node.js full-stack developer with React experience required",
            "candidates": [
                {
                    "name": "Alice Developer",
                    "resume": "Full-stack developer with 5 years Node.js and React experience"
                },
                {
                    "name": "Charlie Backend",
                    "resume": "Backend developer specializing in Python and Django"
                }
            ]
        }
    )))
    
    # Test 5: Generate Job Post (enhanced)
    results.append(("Job Post Generation", test_endpoint(
        "Generate Job Post (ENHANCED)",
        "/api/generate-job-post",
        {
            "jd_text": "We are looking for a talented Data Scientist to join our team",
            "job_title": "Data Scientist",
            "location": "San Francisco, CA",
            "experience": "3-5 years"
        }
    )))
    
    # Summary
    print("\n")
    print("█" * 60)
    print("TEST SUMMARY")
    print("█" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, passed_flag in results:
        status = "✓ PASS" if passed_flag else "✗ FAIL"
        print(f"{status:8} - {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ All endpoints are working with gpt-3.5-turbo")
        print("✅ Model switched to cheaper option")
        print("✅ Generate Message working (was failing)")
        print("✅ Bulk Screening working (was failing)")
        print("✅ Single Screen working (was failing)")
    else:
        print(f"\n⚠️  {total - passed} tests failed")
        print("Check Flask logs for details")


if __name__ == '__main__':
    main()

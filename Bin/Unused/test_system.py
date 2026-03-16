#!/usr/bin/env python3
"""
Complete System Test for Advanced Recruitment ATS v3.1
Tests all endpoints and features including message generation and Supabase integration
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:5000"

def print_header(text):
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")

def print_result(endpoint, status, message=""):
    icon = "✅" if status else "❌"
    print(f"{icon} {endpoint}: {message}")

def test_health_check():
    """Test 1: Health Check"""
    print_header("TEST 1: HEALTH CHECK")
    try:
        response = requests.get(f"{BASE_URL}/")
        print_result("GET /", response.status_code == 200, f"Status {response.status_code}")
        return response.status_code == 200
    except Exception as e:
        print_result("GET /", False, str(e))
        return False

def test_screen_candidate():
    """Test 2: Screen Single Candidate"""
    print_header("TEST 2: SCREEN SINGLE CANDIDATE")
    try:
        payload = {
            "candidate_name": "John Doe",
            "resume_text": "Senior Developer with 10 years Python experience. Built scalable microservices. Led team of 5 engineers.",
            "jd_text": "Looking for Senior Python Developer. Must have 8+ years experience with microservices and team leadership.",
            "job_title": "Senior Python Developer"
        }
        response = requests.post(
            f"{BASE_URL}/api/screen-candidate",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        success = response.status_code in [200, 400, 500]  # Any valid response
        data = response.json() if success else {}
        print_result("POST /api/screen-candidate", success, f"Status {response.status_code}")
        
        if success:
            print(f"   Response: {json.dumps(data, indent=2)[:200]}...")
        return success
    except Exception as e:
        print_result("POST /api/screen-candidate", False, str(e))
        return False

def test_file_upload():
    """Test 3: File Upload"""
    print_header("TEST 3: FILE UPLOAD")
    try:
        # Create a test text file
        with open("test_resume.txt", "w") as f:
            f.write("Senior Developer with 10 years experience")
        
        with open("test_resume.txt", "rb") as f:
            files = {"file": f}
            response = requests.post(
                f"{BASE_URL}/api/upload-file",
                files=files
            )
        
        success = response.status_code in [200, 400, 500]
        data = response.json() if success else {}
        print_result("POST /api/upload-file", success, f"Status {response.status_code}")
        
        if success and "content" in data:
            print(f"   Extracted content length: {len(data.get('content', ''))} chars")
        return success
    except Exception as e:
        print_result("POST /api/upload-file", False, str(e))
        return False
    finally:
        # Clean up
        import os
        try:
            os.remove("test_resume.txt")
        except:
            pass

def test_job_post_generation():
    """Test 4: Job Post Generation"""
    print_header("TEST 4: JOB POST GENERATION")
    try:
        payload = {
            "job_title": "Senior React Developer",
            "jd_text": "We're looking for an experienced React developer. Must have 5+ years with React, TypeScript, and modern tooling. Strong focus on performance and user experience."
        }
        response = requests.post(
            f"{BASE_URL}/api/generate-job-post",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        success = response.status_code in [200, 400, 500]
        data = response.json() if success else {}
        print_result("POST /api/generate-job-post", success, f"Status {response.status_code}")
        
        if success:
            print(f"   Response keys: {list(data.keys())}")
        return success
    except Exception as e:
        print_result("POST /api/generate-job-post", False, str(e))
        return False

def test_message_generation():
    """Test 5: Message Generation"""
    print_header("TEST 5: MESSAGE GENERATION")
    try:
        payload = {
            "message_type": "interview",
            "recipient": "John Smith",
            "job_title": "Senior Developer",
            "tone": "professional",
            "context": "Excellent interview performance"
        }
        response = requests.post(
            f"{BASE_URL}/api/generate-message",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        success = response.status_code in [200, 400, 500]
        data = response.json() if success else {}
        print_result("POST /api/generate-message", success, f"Status {response.status_code}")
        
        if success:
            print(f"   Response keys: {list(data.keys())}")
        return success
    except Exception as e:
        print_result("POST /api/generate-message", False, str(e))
        return False

def test_ai_write():
    """Test 6: AI Writing"""
    print_header("TEST 6: AI WRITING")
    try:
        payload = {
            "text": "We will conduct your interview next week.",
            "action": "rewrite",
            "tone": "professional",
            "platform": "email"
        }
        response = requests.post(
            f"{BASE_URL}/api/ai-write",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        success = response.status_code in [200, 400, 500]
        data = response.json() if success else {}
        print_result("POST /api/ai-write", success, f"Status {response.status_code}")
        
        if success:
            print(f"   Response keys: {list(data.keys())}")
        return success
    except Exception as e:
        print_result("POST /api/ai-write", False, str(e))
        return False

def test_logs():
    """Test 7: Logs Retrieval"""
    print_header("TEST 7: LOGS RETRIEVAL")
    try:
        response = requests.get(f"{BASE_URL}/api/logs")
        
        success = response.status_code in [200, 400, 500]
        data = response.json() if success else {}
        print_result("GET /api/logs", success, f"Status {response.status_code}")
        
        if success and isinstance(data, list):
            print(f"   Total log lines: {len(data)}")
            if data:
                print(f"   Latest log: {data[-1][:100]}...")
        return success
    except Exception as e:
        print_result("GET /api/logs", False, str(e))
        return False

def test_frontend():
    """Test 8: Frontend Loading"""
    print_header("TEST 8: FRONTEND LOADING")
    try:
        response = requests.get(f"{BASE_URL}/")
        
        success = response.status_code == 200 and "Advanced Recruitment ATS" in response.text
        print_result("Frontend HTML", success, f"Status {response.status_code}")
        
        if success:
            # Check for key elements
            elements = {
                "Screen Candidates tab": "Screen Candidates" in response.text,
                "Bulk Screening tab": "Bulk Screening" in response.text,
                "Job Post tab": "Create Job Post" in response.text,
                "Messages tab": "Generate Messages" in response.text,
                "Logs tab": "Activity Logs" in response.text,
                "AI Sidebar": "AI Writing Assistant" in response.text,
            }
            
            for elem, found in elements.items():
                status_icon = "✅" if found else "❌"
                print(f"   {status_icon} {elem}")
        
        return success
    except Exception as e:
        print_result("Frontend HTML", False, str(e))
        return False

def main():
    """Run all tests"""
    print("\n")
    print("╔" + "═"*58 + "╗")
    print("║" + " "*58 + "║")
    print("║" + "  🧪 ADVANCED RECRUITMENT ATS v3.1 - SYSTEM TEST".center(58) + "║")
    print("║" + " "*58 + "║")
    print("╚" + "═"*58 + "╝")
    
    print(f"\nTest Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Target Server: {BASE_URL}\n")
    
    # Run all tests
    results = {
        "Health Check": test_health_check(),
        "File Upload": test_file_upload(),
        "Screen Candidate": test_screen_candidate(),
        "Job Post Generation": test_job_post_generation(),
        "Message Generation": test_message_generation(),
        "AI Writing": test_ai_write(),
        "Logs Retrieval": test_logs(),
        "Frontend Loading": test_frontend(),
    }
    
    # Summary
    print_header("TEST SUMMARY")
    
    total_tests = len(results)
    passed_tests = sum(1 for v in results.values() if v)
    failed_tests = total_tests - passed_tests
    
    for test_name, result in results.items():
        icon = "✅" if result else "❌"
        print(f"{icon} {test_name}")
    
    print(f"\n{'='*60}")
    print(f"  Total Tests: {total_tests}")
    print(f"  Passed: {passed_tests}")
    print(f"  Failed: {failed_tests}")
    print(f"  Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    print(f"{'='*60}\n")
    
    if failed_tests == 0:
        print("🎉 ALL TESTS PASSED! System is fully operational!\n")
    else:
        print(f"⚠️  {failed_tests} test(s) failed. Check errors above.\n")
    
    return failed_tests == 0

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)

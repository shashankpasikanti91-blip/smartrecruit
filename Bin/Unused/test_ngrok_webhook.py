#!/usr/bin/env python3
"""
Test script for ngrok webhook URL
Tests both screening and message generation endpoints
"""

import httpx
import json
import sys
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Your ngrok webhook URL
WEBHOOK_URL = os.getenv('NGROK_WEBHOOK_URL', "https://whirly-unfeeble-liv.ngrok-free.dev/webhook/3cef19ce-26fd-4a20-b861-ae5319e35d57")

# Color output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
END = "\033[0m"

def print_section(title):
    print(f"\n{BLUE}{'='*70}{END}")
    print(f"{BLUE}{title}{END}")
    print(f"{BLUE}{'='*70}{END}\n")

def print_success(msg):
    print(f"{GREEN}✓ {msg}{END}")

def print_error(msg):
    print(f"{RED}✗ {msg}{END}")

def print_info(msg):
    print(f"{YELLOW}→ {msg}{END}")

async def test_health():
    """Test health endpoint"""
    print_section("TEST 1: Health Check")
    print_info(f"URL: {WEBHOOK_URL}/health")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{WEBHOOK_URL.rsplit('/', 1)[0]}/health", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                print_success("Health check passed")
                print(f"\nResponse: {json.dumps(data, indent=2)}")
                return True
            else:
                print_error(f"Health check failed: {response.status_code}")
                return False
    except Exception as e:
        print_error(f"Connection error: {str(e)}")
        return False

async def test_screening():
    """Test candidate screening endpoint"""
    print_section("TEST 2: Candidate Screening")
    
    test_data = {
        "candidate_name": "John Doe",
        "candidate_resume": "Senior Python Engineer with 7 years experience. Expert in FastAPI, PostgreSQL, Docker. AWS certified.",
        "job_title": "Senior Backend Engineer",
        "job_description": "Looking for Senior Backend Engineer with 5+ years Python, FastAPI, PostgreSQL. AWS experience a plus."
    }
    
    print_info(f"URL: POST {WEBHOOK_URL}")
    print_info(f"Payload: {json.dumps(test_data, indent=2)}\n")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                WEBHOOK_URL,
                json=test_data,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                print_success("Screening completed")
                print(f"\nResponse:\n{json.dumps(data, indent=2)}")
                
                # Extract score
                if "analysis" in data:
                    analysis = data["analysis"]
                    if isinstance(analysis, str):
                        if "Match Score" in analysis:
                            print_success("AI analysis received")
                return True
            else:
                print_error(f"Screening failed: {response.status_code}")
                print(f"Response: {response.text}")
                return False
    except Exception as e:
        print_error(f"Connection error: {str(e)}")
        return False

async def test_message_generation():
    """Test message generation endpoint"""
    print_section("TEST 3: Message Generation")
    
    test_data = {
        "message_type": "interview_invitation",
        "recipient_name": "John Doe",
        "recipient_email": "john@example.com",
        "job_title": "Senior Backend Engineer"
    }
    
    message_url = WEBHOOK_URL.rsplit('/', 1)[0] + "/generate-message"
    print_info(f"URL: POST {message_url}")
    print_info(f"Payload: {json.dumps(test_data, indent=2)}\n")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                message_url,
                json=test_data,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                print_success("Message generated")
                print(f"\nResponse:\n{json.dumps(data, indent=2)}")
                return True
            else:
                print_error(f"Message generation failed: {response.status_code}")
                print(f"Response: {response.text}")
                return False
    except Exception as e:
        print_error(f"Connection error: {str(e)}")
        return False

async def main():
    print(f"\n{BLUE}╔══════════════════════════════════════════════════════════════════╗{END}")
    print(f"{BLUE}║        NGROK WEBHOOK TEST SUITE                                   ║{END}")
    print(f"{BLUE}║        Testing: {WEBHOOK_URL}  ║{END}")
    print(f"{BLUE}║        Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}                         ║{END}")
    print(f"{BLUE}╚══════════════════════════════════════════════════════════════════╝{END}")
    
    results = {}
    
    # Test 1: Health
    results["Health Check"] = await test_health()
    
    # Test 2: Screening
    results["Candidate Screening"] = await test_screening()
    
    # Test 3: Message Generation
    results["Message Generation"] = await test_message_generation()
    
    # Summary
    print_section("TEST SUMMARY")
    for test_name, passed in results.items():
        status = f"{GREEN}PASSED{END}" if passed else f"{RED}FAILED{END}"
        print(f"  {test_name}: {status}")
    
    passed_count = sum(1 for v in results.values() if v)
    total_count = len(results)
    
    print(f"\nTotal: {passed_count}/{total_count} tests passed")
    
    if passed_count == total_count:
        print_success("All tests passed! Webhook is working correctly.")
        return 0
    else:
        print_error("Some tests failed. Check webhook server and connection.")
        return 1

if __name__ == "__main__":
    import asyncio
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

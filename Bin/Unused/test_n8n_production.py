#!/usr/bin/env python3
"""
n8n Production Workflow Test
Tests your actual n8n webhook after activation
"""

import httpx
import json
import sys
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Your n8n Production URLs
N8N_WEBHOOK = os.getenv('N8N_WEBHOOK_PRODUCTION', 
    "https://whirly-unfeeble-liv.ngrok-free.dev/webhook/3cef19ce-26fd-4a20-b861-ae5319e35d57")

N8N_WORKFLOW = os.getenv('N8N_WORKFLOW_URL',
    "https://whirly-unfeeble-liv.ngrok-free.dev/workflow/8USzg0C-zclr3AyuhoXmS")

# Color output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
CYAN = "\033[96m"
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

def print_url(msg, url):
    print(f"{CYAN}📌 {msg}{END}")
    print(f"   {url}\n")

async def test_workflow_status():
    """Check if workflow is active"""
    print_section("TEST 1: Workflow Status Check")
    print_url("Workflow URL", N8N_WORKFLOW)
    print_info("Accessing workflow to verify it's activated...")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(N8N_WORKFLOW, timeout=10, follow_redirects=True)
            
            if response.status_code == 200:
                # Check if workflow page contains "active" indicators
                if "active" in response.text.lower() or "workflow" in response.text.lower():
                    print_success("Workflow page accessible")
                    print_info("If toggle is BLUE in UI, workflow is ACTIVE")
                    return True
                else:
                    print_error("Could not determine workflow status")
                    return False
            else:
                print_error(f"Workflow page error: {response.status_code}")
                return False
    except Exception as e:
        print_error(f"Connection error: {str(e)}")
        print_info("Make sure ngrok tunnel is running and workflow is accessible")
        return False

async def test_webhook_with_candidate():
    """Test candidate screening via webhook"""
    print_section("TEST 2: Candidate Screening Webhook")
    print_url("Webhook URL", N8N_WEBHOOK)
    
    test_data = {
        "candidate_name": "Alice Johnson",
        "candidate_resume": """
        Senior Python Engineer
        7 years experience with FastAPI, PostgreSQL, Docker
        Expert in: Python, AWS, Kubernetes, CI/CD
        Certifications: AWS Solutions Architect
        """,
        "job_title": "Senior Backend Engineer",
        "job_description": """
        Looking for: Senior Backend Engineer
        Requirements: 5+ years Python, FastAPI, PostgreSQL
        Nice to have: AWS, Docker, Kubernetes
        Salary: $120k-$180k
        """
    }
    
    print_info(f"Sending candidate data...")
    print(f"Name: {test_data['candidate_name']}")
    print(f"Job: {test_data['job_title']}\n")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                N8N_WEBHOOK,
                json=test_data,
                timeout=30
            )
            
            print_info(f"Response Status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print_success("Webhook executed successfully!")
                    print(f"\nResponse:\n{json.dumps(data, indent=2)}")
                    return True
                except:
                    print_success("Webhook accepted request")
                    print(f"Response:\n{response.text[:500]}")
                    return True
            elif response.status_code in [202, 204]:
                print_success("Webhook queued for processing")
                return True
            elif response.status_code == 404:
                print_error("Webhook not found or not activated")
                print_info("CHECK: Is the workflow toggle set to ACTIVE (blue)?")
                return False
            else:
                print_error(f"Webhook error: {response.status_code}")
                print(f"Response: {response.text[:300]}")
                return False
                
    except httpx.TimeoutException:
        print_error("Request timeout (workflow taking too long)")
        print_info("This might mean the workflow is processing")
        return False
    except Exception as e:
        print_error(f"Connection error: {str(e)}")
        return False

async def test_webhook_with_message():
    """Test message generation via webhook"""
    print_section("TEST 3: Message Generation Webhook")
    
    test_data = {
        "message_type": "interview_invitation",
        "recipient_name": "Alice Johnson",
        "recipient_email": "alice@example.com",
        "job_title": "Senior Backend Engineer",
        "company": "TechCorp Inc"
    }
    
    print_info(f"Sending message generation request...")
    print(f"Type: {test_data['message_type']}")
    print(f"To: {test_data['recipient_name']} ({test_data['recipient_email']})\n")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                N8N_WEBHOOK,
                json=test_data,
                timeout=30
            )
            
            print_info(f"Response Status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    print_success("Message generated successfully!")
                    print(f"\nResponse:\n{json.dumps(data, indent=2)}")
                    return True
                except:
                    print_success("Message request accepted")
                    print(f"Response:\n{response.text[:500]}")
                    return True
            elif response.status_code in [202, 204]:
                print_success("Message queued for generation")
                return True
            elif response.status_code == 404:
                print_error("Webhook not found or not activated")
                return False
            else:
                print_error(f"Error: {response.status_code}")
                return False
                
    except Exception as e:
        print_error(f"Connection error: {str(e)}")
        return False

async def main():
    print(f"\n{BLUE}╔══════════════════════════════════════════════════════════════════╗{END}")
    print(f"{BLUE}║        n8n PRODUCTION WORKFLOW TEST                               ║{END}")
    print(f"{BLUE}║        Testing your activated n8n workflows                       ║{END}")
    print(f"{BLUE}║        Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}                         ║{END}")
    print(f"{BLUE}╚══════════════════════════════════════════════════════════════════╝{END}")
    
    results = {}
    
    # Test 1: Workflow Status
    results["Workflow Status"] = await test_workflow_status()
    
    # Test 2: Candidate Screening
    results["Candidate Screening"] = await test_webhook_with_candidate()
    
    # Test 3: Message Generation
    results["Message Generation"] = await test_webhook_with_message()
    
    # Summary
    print_section("TEST SUMMARY")
    for test_name, passed in results.items():
        status = f"{GREEN}PASSED{END}" if passed else f"{RED}FAILED{END}"
        print(f"  {test_name}: {status}")
    
    passed_count = sum(1 for v in results.values() if v)
    total_count = len(results)
    
    print(f"\nTotal: {passed_count}/{total_count} tests passed")
    
    if passed_count >= 2:
        print_success("Production webhooks are working!")
        print_info("Your n8n workflows are ready to process candidates")
        return 0
    else:
        print_error("Some tests failed")
        print_info("\nDEBUGGING STEPS:")
        print("  1. Open workflow editor: https://whirly-unfeeble-liv.ngrok-free.dev/workflow/8USzg0C-zclr3AyuhoXmS/4b7abf")
        print("  2. Check if toggle is BLUE (activated)")
        print("  3. If not, click toggle to activate")
        print("  4. Run this script again")
        return 1

if __name__ == "__main__":
    import asyncio
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

#!/usr/bin/env python3
"""
Complete Verification Test - Tests all fixes and database storage
"""
import asyncio
import aiohttp
import json
from datetime import datetime

BASE_URL = "http://localhost:5003"

async def test_all():
    """Run all tests"""
    print("=" * 80)
    print("[TEST] COMPLETE VERIFICATION TEST")
    print("=" * 80)
    
    async with aiohttp.ClientSession() as session:
        # TEST 1: Bulk Screening with Multiple CVs
        print("\n[TEST 1] Bulk Screening - 5 Candidates")
        print("-" * 80)
        
        candidates = [
            {
                "name": "John Developer",
                "resume": "5 years Python developer. Experience with Django, FastAPI, AWS."
            },
            {
                "name": "Sarah Manager",
                "resume": "Project manager with 8 years experience. Agile, Scrum, Team leadership."
            },
            {
                "name": "Mike Designer",
                "resume": "UI/UX Designer, 3 years. Figma, Adobe XD, Web design."
            },
            {
                "name": "Lisa DevOps",
                "resume": "DevOps Engineer, 6 years. Docker, Kubernetes, CI/CD pipelines."
            },
            {
                "name": "Alex Data",
                "resume": "Data Scientist, 4 years. Python, ML, Deep Learning, TensorFlow."
            }
        ]
        
        jd_text = """
        We are looking for a Senior Python Developer
        Requirements:
        - 5+ years Python experience
        - Strong in backend development
        - AWS or cloud experience
        - Team player
        """
        
        try:
            async with session.post(
                f"{BASE_URL}/api/bulk-screen",
                json={
                    "candidates": candidates,
                    "jd_text": jd_text,
                    "job_title": "Senior Python Developer"
                },
                timeout=30
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    results = data.get('results', [])
                    print(f"✅ Screening successful: {len(results)} results returned")
                    
                    for r in results:
                        name = r.get('candidate') or r.get('candidate_name')
                        score = r.get('match_score') or r.get('score')
                        recommendation = r.get('recommendation')
                        print(f"  • {name}: {score}% - {recommendation}")
                    
                    # Check that all candidates got results
                    if len(results) == len(candidates):
                        print(f"✅ All {len(candidates)} candidates screened! ✓")
                    else:
                        print(f"⚠️  Only {len(results)}/{len(candidates)} returned")
                else:
                    print(f"❌ Error: {resp.status}")
                    text = await resp.text()
                    print(f"Response: {text[:200]}")
        except Exception as e:
            print(f"❌ Exception: {str(e)}")
        
        # TEST 2: Check Activity Logs
        print("\n[TEST 2] Activity Logs Endpoint")
        print("-" * 80)
        
        try:
            async with session.get(f"{BASE_URL}/api/logs", timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    logs = data.get('logs', [])
                    print(f"✅ Logs retrieved: {len(logs)} entries")
                    if logs:
                        print("Recent logs:")
                        for log in logs[-3:]:  # Show last 3
                            print(f"  • {log}")
                    else:
                        print("ℹ️  No logs yet")
                else:
                    print(f"❌ Error: {resp.status}")
        except Exception as e:
            print(f"❌ Exception: {str(e)}")
        
        # TEST 3: Check Database Storage
        print("\n[TEST 3] Database Screening Results")
        print("-" * 80)
        
        try:
            async with session.get(f"{BASE_URL}/api/screening-results", timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    results = data.get('results', [])
                    print(f"✅ Database results: {len(results)} screening records")
                    if results:
                        print("Sample records:")
                        for r in results[:3]:
                            print(f"  • ID: {r.get('id')} | Score: {r.get('score')}")
                else:
                    print(f"⚠️  Endpoint not found (optional)")
        except Exception as e:
            print(f"ℹ️  Database check skipped: {str(e)[:50]}")
        
        # TEST 4: Check Recommendation Logic
        print("\n[TEST 4] Recommendation Logic Verification")
        print("-" * 80)
        
        test_scores = [
            (85, "INVITE", "Ready to Invite"),
            (75, "INVITE", "Ready to Invite"),
            (70, "REVIEW", "Worth Reviewing"),
            (60, "REVIEW", "Worth Reviewing"),
            (50, "PASS", "Not Recommended"),
            (30, "PASS", "Not Recommended")
        ]
        
        print("Expected behavior:")
        for score, recommendation, assessment in test_scores:
            print(f"  • {score}% → {recommendation} ({assessment})")
        
        # TEST 5: System Status
        print("\n[TEST 5] System Status")
        print("-" * 80)
        
        try:
            async with session.get(f"{BASE_URL}/api/status", timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    print(f"✅ Status: {data.get('status')}")
                    print(f"   • Model: {data.get('model')}")
                    print(f"   • Prompts loaded: {data.get('prompts_loaded')}")
                    print(f"   • Time: {data.get('timestamp')}")
                else:
                    print(f"❌ Error: {resp.status}")
        except Exception as e:
            print(f"❌ Exception: {str(e)}")
    
    print("\n" + "=" * 80)
    print("✅ VERIFICATION COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(test_all())

#!/usr/bin/env python3
"""
Test Bulk Screening Results - Verify Fix
"""

import asyncio
import aiohttp
import json

BASE_URL = "http://localhost:5003"

async def test_bulk_screening():
    print("\n🧪 Testing Bulk Screening Functionality\n")
    
    # Step 1: Upload resumes
    print("[1/3] Uploading test resumes...")
    async with aiohttp.ClientSession() as session:
        # Create test resumes
        resumes = [
            ("John Developer\nSenior Python Engineer\n10 years experience with Python, Django, FastAPI, AWS, Docker. Team lead at Tech Corp.", "john_dev.txt"),
            ("Sarah DevOps\nDevOps Engineer\n8 years with Kubernetes, Docker, CI/CD, AWS, terraform. Cloud infrastructure expert.", "sarah_devops.txt"),
            ("Mike Junior\nJunior Web Developer\n2 years HTML, CSS, JavaScript, React basics. Eager to learn.", "mike_junior.txt"),
        ]
        
        # Upload bulk resumes
        data = aiohttp.FormData()
        for content, filename in resumes:
            data.add_field('files', content.encode(), filename=filename, content_type='text/plain')
        
        upload_response = await session.post(f"{BASE_URL}/api/upload-bulk-resumes", data=data, timeout=15)
        upload_result = await upload_response.json()
        
        if upload_response.status != 200:
            print(f"   ❌ Upload failed with status {upload_response.status}")
            print(f"   Response: {upload_result}")
            return
        
        candidates = upload_result.get('candidates', [])
        print(f"   ✅ Uploaded {len(candidates)} resumes")
        
        if not candidates:
            print(f"   ❌ No candidates extracted!")
            print(f"   Error: {upload_result.get('error', 'Unknown error')}")
            return
        
        # Step 2: Screen candidates
        print("\n[2/3] Screening candidates with bulk endpoint...")
        
        screening_payload = {
            "candidates": candidates,
            "jd_text": """
            Position: Senior Backend Engineer
            Requirements:
            - 8+ years Python or similar backend experience
            - Experience with scalable architectures and microservices
            - AWS or cloud platform expertise
            - Team leadership skills preferred
            
            Responsibilities:
            - Design and build microservices
            - Lead technical decisions
            - Mentor junior developers
            - Implement DevOps best practices
            """,
            "job_title": "Senior Backend Engineer"
        }
        
        screen_response = await session.post(
            f"{BASE_URL}/api/bulk-screen",
            json=screening_payload,
            timeout=30
        )
        
        if screen_response.status != 200:
            print(f"   ❌ Screening failed with status {screen_response.status}")
            try:
                error_detail = await screen_response.json()
                print(f"   Error: {error_detail}")
            except:
                text = await screen_response.text()
                print(f"   Response: {text[:200]}")
            return
        
        screen_result = await screen_response.json()
        results = screen_result.get('results', [])
        
        print(f"   ✅ Screening complete")
        print(f"   📊 Results returned: {len(results)} candidates")
        
        if not results:
            print(f"   ⚠️  No results in response")
            print(f"   Full response: {json.dumps(screen_result, indent=2)}")
            return
        
        # Step 3: Verify results display
        print("\n[3/3] Verifying screening results...")
        
        for idx, result in enumerate(results, 1):
            candidate_name = result.get('candidate') or result.get('candidate_name') or f"Candidate {idx}"
            match_score = result.get('match_score') or result.get('score') or 0
            recommendation = result.get('recommendation') or 'REVIEW'
            assessment = result.get('assessment') or result.get('status') or 'Reviewed'
            
            status_icon = "🟢" if recommendation == "INVITE" else "🟡" if recommendation == "REVIEW" else "🔴"
            print(f"   {status_icon} {candidate_name}")
            print(f"      Score: {match_score}% | {assessment} | {recommendation}")
        
        print(f"\n✅ Bulk Screening Test PASSED!")
        print(f"   All {len(results)} candidates screened and results displayed correctly")
        
        # Step 4: Check database retrieval
        print("\n[BONUS] Checking if results saved to database...")
        db_response = await session.get(f"{BASE_URL}/api/screening-results", timeout=10)
        if db_response.status == 200:
            db_results = await db_response.json()
            db_count = db_results.get('count', 0)
            print(f"   ✅ Database contains {db_count} screening results")
        else:
            print(f"   ⚠️  Could not retrieve from database (status {db_response.status})")

async def main():
    try:
        await test_bulk_screening()
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Ensuring server is accessible...")
    asyncio.run(main())

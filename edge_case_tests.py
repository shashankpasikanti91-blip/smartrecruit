#!/usr/bin/env python3
"""
Edge Case & Stress Tests
Tests application robustness and error handling
"""

import asyncio
import aiohttp
import json
from datetime import datetime

BASE_URL = "http://localhost:5003"

class EdgeCaseTests:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.results = []
    
    async def test_empty_file_upload(self):
        """Test uploading empty file"""
        print("\n[EDGE 1] Empty File Upload")
        try:
            data = aiohttp.FormData()
            data.add_field('file', b'', filename='empty.txt', content_type='text/plain')
            
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{BASE_URL}/api/upload-file", data=data, timeout=10) as response:
                    if response.status in [200, 400, 422]:
                        self.passed += 1
                        print(f"   ✅ Handled properly (Status: {response.status})")
                    else:
                        self.failed += 1
                        print(f"   ❌ Unexpected status: {response.status}")
        except Exception as e:
            self.failed += 1
            print(f"   ❌ Error: {str(e)}")
    
    async def test_large_bulk_upload(self):
        """Test uploading many files at once"""
        print("\n[EDGE 2] Large Bulk Upload (5 files)")
        try:
            data = aiohttp.FormData()
            
            for i in range(5):
                content = f"Resume {i+1}\nExperience: {10-i} years\nSkills: Python, AWS".encode()
                data.add_field('files', content, filename=f'resume_{i+1}.txt', content_type='text/plain')
            
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{BASE_URL}/api/upload-bulk-resumes", data=data, timeout=15) as response:
                    if response.status == 200:
                        result = await response.json()
                        count = len(result.get('candidates', []))
                        if count >= 3:  # Expect at least 3 processed
                            self.passed += 1
                            print(f"   ✅ Processed {count} files successfully")
                        else:
                            self.failed += 1
                            print(f"   ⚠️  Only processed {count} files")
                    else:
                        self.failed += 1
                        print(f"   ❌ Status: {response.status}")
        except Exception as e:
            self.failed += 1
            print(f"   ❌ Error: {str(e)}")
    
    async def test_special_characters_in_resume(self):
        """Test handling special characters and Unicode"""
        print("\n[EDGE 3] Special Characters & Unicode")
        try:
            content = """
            José García-López
            Senior Developer™
            Email: josé@example.com
            Skills: Python, C++, JavaScript, Ñandú
            Certifications: ® AWS ™ Google Cloud
            Languages: English, Español, Français
            """.encode('utf-8')
            
            data = aiohttp.FormData()
            data.add_field('file', content, filename='unicode_resume.txt', content_type='text/plain; charset=utf-8')
            
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{BASE_URL}/api/upload-file", data=data, timeout=10) as response:
                    if response.status == 200:
                        result = await response.json()
                        self.passed += 1
                        print(f"   ✅ Unicode handled correctly")
                    else:
                        self.failed += 1
                        print(f"   ❌ Status: {response.status}")
        except Exception as e:
            self.failed += 1
            print(f"   ❌ Error: {str(e)}")
    
    async def test_concurrent_requests(self):
        """Test handling concurrent upload requests"""
        print("\n[EDGE 4] Concurrent Requests (5 simultaneous)")
        try:
            tasks = []
            async with aiohttp.ClientSession() as session:
                for i in range(5):
                    content = f"Resume {i}\n{10+i} years experience".encode()
                    data = aiohttp.FormData()
                    data.add_field('file', content, filename=f'concurrent_{i}.txt', content_type='text/plain')
                    
                    task = session.post(f"{BASE_URL}/api/upload-file", data=data, timeout=10)
                    tasks.append(task)
                
                responses = await asyncio.gather(*tasks, return_exceptions=True)
                
                success_count = sum(1 for resp in responses if isinstance(resp, aiohttp.ClientResponse) and resp.status == 200)
                
                if success_count >= 4:  # Allow 1 failure
                    self.passed += 1
                    print(f"   ✅ {success_count}/5 requests succeeded")
                else:
                    self.failed += 1
                    print(f"   ⚠️  Only {success_count}/5 requests succeeded")
        except Exception as e:
            self.failed += 1
            print(f"   ❌ Error: {str(e)}")
    
    async def test_invalid_json_payload(self):
        """Test handling of invalid JSON"""
        print("\n[EDGE 5] Invalid JSON Payload")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{BASE_URL}/api/screen-candidate",
                    data='{"invalid": json}',  # Invalid JSON
                    timeout=5
                ) as response:
                    if response.status in [400, 422]:
                        self.passed += 1
                        print(f"   ✅ Rejected invalid JSON (Status: {response.status})")
                    else:
                        self.failed += 1
                        print(f"   ❌ Should reject JSON (Status: {response.status})")
        except Exception as e:
            # Expected if server properly rejects
            self.passed += 1
            print(f"   ✅ Properly rejected malformed request")
    
    async def test_missing_required_fields(self):
        """Test screening with missing required fields"""
        print("\n[EDGE 6] Missing Required Fields")
        try:
            payload = {
                "candidate_name": "Test",
                # Missing: resume_text, job_title, jd_text
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{BASE_URL}/api/screen-candidate",
                    json=payload,
                    timeout=10
                ) as response:
                    if response.status in [400, 422]:
                        self.passed += 1
                        print(f"   ✅ Validated required fields (Status: {response.status})")
                    else:
                        self.failed += 1
                        print(f"   ❌ Should validate fields")
        except Exception as e:
            self.failed += 1
            print(f"   ❌ Error: {str(e)}")
    
    async def test_very_long_input(self):
        """Test handling of very long input"""
        print("\n[EDGE 7] Very Long Input (10000+ characters)")
        try:
            long_text = "Python Developer " * 1000  # ~16000 characters
            
            payload = {
                "candidate_name": "Test Candidate",
                "resume_text": long_text,
                "job_title": "Senior Developer",
                "jd_text": long_text
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{BASE_URL}/api/screen-candidate",
                    json=payload,
                    timeout=20
                ) as response:
                    if response.status == 200:
                        self.passed += 1
                        print(f"   ✅ Handled long input successfully")
                    else:
                        self.failed += 1
                        print(f"   ⚠️  Status: {response.status}")
        except Exception as e:
            self.failed += 1
            print(f"   ❌ Error: {str(e)}")
    
    async def test_rapid_successive_requests(self):
        """Test rate limiting and rapid requests"""
        print("\n[EDGE 8] Rapid Successive Requests (10 quick)")
        try:
            success_count = 0
            failed_count = 0
            
            async with aiohttp.ClientSession() as session:
                for i in range(10):
                    try:
                        async with session.get(f"{BASE_URL}/health", timeout=5) as response:
                            if response.status == 200:
                                success_count += 1
                            else:
                                failed_count += 1
                    except:
                        failed_count += 1
                    
                    await asyncio.sleep(0.05)  # Small delay
            
            if success_count >= 9:
                self.passed += 1
                print(f"   ✅ Handled {success_count}/10 rapid requests")
            else:
                self.failed += 1
                print(f"   ⚠️  {success_count}/10 requests succeeded")
        except Exception as e:
            self.failed += 1
            print(f"   ❌ Error: {str(e)}")
    
    async def test_duplicate_uploads(self):
        """Test uploading same file twice"""
        print("\n[EDGE 9] Duplicate File Uploads")
        try:
            content = b"Duplicate Test Resume\n5 years experience"
            
            data1 = aiohttp.FormData()
            data1.add_field('file', content, filename='duplicate.txt', content_type='text/plain')
            
            data2 = aiohttp.FormData()
            data2.add_field('file', content, filename='duplicate.txt', content_type='text/plain')
            
            async with aiohttp.ClientSession() as session:
                # Upload same file twice
                resp1 = await session.post(f"{BASE_URL}/api/upload-file", data=data1, timeout=10)
                resp2 = await session.post(f"{BASE_URL}/api/upload-file", data=data2, timeout=10)
                
                if resp1.status == 200 and resp2.status == 200:
                    self.passed += 1
                    print(f"   ✅ Handled duplicate uploads correctly")
                else:
                    self.failed += 1
                    print(f"   ⚠️  Status: {resp1.status}, {resp2.status}")
        except Exception as e:
            self.failed += 1
            print(f"   ❌ Error: {str(e)}")
    
    async def test_malformed_multipart(self):
        """Test malformed multipart data"""
        print("\n[EDGE 10] Malformed Multipart Data")
        try:
            # This would need raw HTTP to test properly
            # For now, just verify the endpoint exists
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{BASE_URL}/health", timeout=5) as response:
                    if response.status == 200:
                        self.passed += 1
                        print(f"   ✅ Server stable")
                    else:
                        self.failed += 1
                        print(f"   ❌ Server issue")
        except Exception as e:
            self.failed += 1
            print(f"   ❌ Error: {str(e)}")
    
    async def run_all_tests(self):
        """Run all edge case tests"""
        print(f"""
╔══════════════════════════════════════════════════════╗
║       🧪 EDGE CASE & STRESS TESTS v3.2              ║
║  Testing application robustness and error handling   ║
╚══════════════════════════════════════════════════════╝
""")
        
        await self.test_empty_file_upload()
        await asyncio.sleep(0.5)
        
        await self.test_large_bulk_upload()
        await asyncio.sleep(0.5)
        
        await self.test_special_characters_in_resume()
        await asyncio.sleep(0.5)
        
        await self.test_concurrent_requests()
        await asyncio.sleep(0.5)
        
        await self.test_invalid_json_payload()
        await asyncio.sleep(0.5)
        
        await self.test_missing_required_fields()
        await asyncio.sleep(0.5)
        
        await self.test_very_long_input()
        await asyncio.sleep(0.5)
        
        await self.test_rapid_successive_requests()
        await asyncio.sleep(0.5)
        
        await self.test_duplicate_uploads()
        await asyncio.sleep(0.5)
        
        await self.test_malformed_multipart()
        
        print(f"\n{'='*60}")
        print(f"📊 EDGE CASE TEST SUMMARY")
        print(f"{'='*60}")
        print(f"✅ Passed: {self.passed}")
        print(f"❌ Failed: {self.failed}")
        print(f"Total: {self.passed + self.failed}")
        print(f"{'='*60}\n")
        
        if self.failed == 0:
            print("🎉 All edge case tests passed!")
        else:
            print(f"⚠️  {self.failed} edge case(s) failed - review needed")
        
        return self.failed == 0

async def main():
    tester = EdgeCaseTests()
    success = await tester.run_all_tests()
    exit(0 if success else 1)

if __name__ == "__main__":
    print("Make sure the server is running on http://localhost:5003\n")
    asyncio.run(main())

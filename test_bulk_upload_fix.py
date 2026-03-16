#!/usr/bin/env python3
"""
Test bulk upload with correct form field names
This should now work with the fixed frontend/backend compatibility
"""

import aiohttp
import asyncio
import aiofiles

async def test_fixed_bulk_upload():
    url = "http://localhost:5004/api/upload-bulk-resumes"
    
    # Create test content
    test_content = """
JANE SMITH
Senior Software Engineer

EXPERIENCE:
Lead Developer at Innovation Labs (2019-2024)
- Developed scalable web applications using Python/React
- Led cross-functional team of 8 developers
- Implemented CI/CD pipelines and microservices architecture
- Technologies: Python, React, Node.js, Docker, AWS, PostgreSQL

Technical Lead at StartupCorp (2017-2019) 
- Built MVP products from ground up
- Mentored junior developers
- Established coding standards and best practices

EDUCATION:
Master of Computer Science - Tech University (2015-2017)
Bachelor of Engineering - State College (2011-2015)

SKILLS:
Python, JavaScript, React, Node.js, SQL, MongoDB, Docker, Kubernetes, AWS, GCP, 
Machine Learning, Data Analysis, Team Leadership, Agile/Scrum

CERTIFICATIONS:
AWS Solutions Architect, Google Cloud Professional, Certified Scrum Master

PROJECTS:
- E-commerce Platform: Led development of high-traffic platform handling 100k+ users
- AI Analytics Dashboard: Built ML-powered analytics system for business intelligence  
- Open Source Contributor: Active contributor to popular Python libraries

CONTACT:
Email: jane.smith@email.com
Phone: +1-555-0199
LinkedIn: linkedin.com/in/jane-smith
"""

    # Write test file
    async with aiofiles.open("test_resume_bulk.txt", "w") as f:
        await f.write(test_content)
    
    print("🧪 Testing Fixed Bulk Upload")
    print("=" * 40)
    
    try:
        async with aiohttp.ClientSession() as session:
            data = aiohttp.FormData()
            
            # Using the FIXED form field name: 'files' (not 'files[]')
            async with aiofiles.open("test_resume_bulk.txt", 'rb') as f:
                file_content = await f.read()
                data.add_field('files',  # FIXED: was 'files[]' before
                             file_content,
                             filename='test_resume_bulk.txt',
                             content_type='text/plain')
            
            # Add a second test file
            data.add_field('files',  # FIXED: was 'files[]' before
                         b"Test Resume 2\nJohn Doe\nDeveloper\n5 years experience in Java/Spring",
                         filename='test_resume_2.txt',
                         content_type='text/plain')
            
            print(f"📤 Sending 2 test files to: {url}")
            print("   Using correct form field name: 'files'")
            
            async with session.post(url, data=data) as response:
                result = await response.json()
                
                print(f"\n📊 Response Status: {response.status}")
                print(f"📄 Response: {result}")
                
                if response.status == 200 and 'candidates' in result:
                    candidates = result['candidates']
                    print(f"\n✅ SUCCESS! Fixed the bulk upload issue")
                    print(f"   📋 Processed: {len(candidates)} candidates")
                    
                    for i, candidate in enumerate(candidates, 1):
                        name = candidate.get('name', 'Unknown')
                        content_len = len(candidate.get('content', ''))
                        print(f"   {i}. {name}: {content_len} characters extracted")
                    
                    if result.get('processing_errors'):
                        print(f"\n⚠️  Processing errors: {len(result['processing_errors'])}")
                        for error in result['processing_errors']:
                            print(f"   - {error}")
                    
                    print(f"\n🎉 BULK UPLOAD FIX VERIFIED!")
                    print("   The issue was: Frontend sent 'files[]' but backend expected 'files'")
                    print("   ✓ Fixed by changing frontend FormData.append('files[]', file) to FormData.append('files', file)")
                    
                else:
                    print(f"\n❌ Test failed: {result}")
                    
    except aiohttp.ClientConnectorError:
        print("❌ Could not connect to server")
        print("   Make sure FastAPI server is running: uvicorn app.main:app --port 5003")
        print("   Server URL: http://localhost:5003")
    except Exception as e:
        print(f"❌ Test error: {e}")

if __name__ == "__main__":
    asyncio.run(test_fixed_bulk_upload())
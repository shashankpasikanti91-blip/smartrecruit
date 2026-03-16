#!/usr/bin/env python3
"""
Test bulk resume upload endpoint directly
Create sample files and test the endpoint to see what's failing
"""

import asyncio
import aiohttp
import aiofiles
import os
from pathlib import Path

async def create_test_files():
    """Create sample PDF and TXT files for testing"""
    
    # Create a sample text file
    test_txt = """
JOHN SMITH
Software Engineer

EXPERIENCE:
Senior Developer at Tech Corp (2020-2024)
- Developed web applications using Python and React
- Led team of 5 developers
- Built RESTful APIs and microservices

EDUCATION:
Bachelor of Computer Science
State University (2016-2020)

SKILLS:
Python, JavaScript, React, Node.js, SQL, Docker, AWS
"""
    
    async with aiofiles.open("test_resume.txt", "w") as f:
        await f.write(test_txt)
    
    # Create a simple HTML file that we can convert to PDF later
    html_for_pdf = """
<!DOCTYPE html>
<html>
<head><title>Resume</title></head>
<body>
<h1>JANE DOE</h1>
<h2>Data Scientist</h2>
<h3>EXPERIENCE:</h3>
<p>Senior Data Scientist at Data Corp (2019-2024)</p>
<ul>
<li>Built ML models for predictive analytics</li>
<li>Worked with Python, R, TensorFlow</li>
<li>Led data science projects</li>
</ul>
<h3>EDUCATION:</h3>
<p>PhD in Statistics - Research University (2015-2019)</p>
<h3>SKILLS:</h3>
<p>Python, R, TensorFlow, SQL, Tableau, AWS, Machine Learning</p>
</body>
</html>
"""
    
    async with aiofiles.open("test_resume.html", "w") as f:
        await f.write(html_for_pdf)
    
    print("✅ Created test files:")
    print("   - test_resume.txt")
    print("   - test_resume.html (can be used as simple text file)")

async def test_bulk_upload_endpoint():
    """Test the bulk upload endpoint with our test files"""
    
    url = "http://localhost:5003/api/upload-bulk-resumes"
    
    # Check if files exist
    files_to_test = []
    
    if os.path.exists("test_resume.txt"):
        files_to_test.append(("test_resume.txt", "text/plain"))
        
    if os.path.exists("test_resume.html"):
        files_to_test.append(("test_resume.html", "text/html"))
    
    # Look for any existing PDF or DOCX files in uploads dir
    uploads_dir = Path("uploads")
    if uploads_dir.exists():
        for file_path in uploads_dir.glob("*.pdf"):
            files_to_test.append((str(file_path), "application/pdf"))
        for file_path in uploads_dir.glob("*.docx"):
            files_to_test.append((str(file_path), "application/vnd.openxmlformats-officedocument.wordprocessingml.document"))
    
    if not files_to_test:
        print("❌ No test files available")
        return
    
    print(f"🧪 Testing bulk upload with {len(files_to_test)} files")
    
    try:
        async with aiohttp.ClientSession() as session:
            # Prepare form data
            data = aiohttp.FormData()
            
            for file_path, content_type in files_to_test:
                async with aiofiles.open(file_path, 'rb') as f:
                    file_content = await f.read()
                    data.add_field('files',
                                 file_content,
                                 filename=os.path.basename(file_path),
                                 content_type=content_type)
            
            # Make the request
            async with session.post(url, data=data) as response:
                result = await response.json()
                
                print(f"📊 Response Status: {response.status}")
                print(f"📄 Response: {result}")
                
                if 'candidates' in result:
                    print(f"✅ Success: {len(result['candidates'])} candidates processed")
                    for candidate in result['candidates']:
                        print(f"   - {candidate.get('name', 'Unknown')}: {len(candidate.get('content', ''))} chars")
                else:
                    print(f"❌ Failed: {result.get('error', 'Unknown error')}")
                    if 'processing_errors' in result:
                        print("🔍 Processing errors:")
                        for error in result['processing_errors']:
                            print(f"   - {error}")
                
    except aiohttp.ClientConnectorError:
        print("❌ Could not connect to server. Is the FastAPI server running on localhost:5003?")
        print("   Run: uvicorn app.main:app --reload --port 5003")
    except Exception as e:
        print(f"❌ Error testing endpoint: {e}")

async def test_single_file_upload():
    """Test single file upload to compare"""
    url = "http://localhost:5003/api/upload-file"
    
    try:
        async with aiohttp.ClientSession() as session:
            # Test with text file
            if os.path.exists("test_resume.txt"):
                data = aiohttp.FormData()
                async with aiofiles.open("test_resume.txt", 'rb') as f:
                    file_content = await f.read()
                    data.add_field('file',
                                 file_content,
                                 filename='test_resume.txt',
                                 content_type='text/plain')
                
                async with session.post(url, data=data) as response:
                    result = await response.json()
                    print(f"🔍 Single file upload test:")
                    print(f"   Status: {response.status}")
                    print(f"   Result: {result}")
                    
    except Exception as e:
        print(f"❌ Single file test failed: {e}")

async def main():
    print("🚀 Testing Bulk Resume Upload Endpoint")
    print("=" * 50)
    
    # Create test files
    await create_test_files()
    
    print("\n🧪 Testing single file upload first...")
    await test_single_file_upload()
    
    print("\n🧪 Testing bulk file upload...")
    await test_bulk_upload_endpoint()
    
    print("\n📋 Next steps if tests fail:")
    print("1. Check server logs for detailed errors")
    print("2. Verify the FastAPI server is running")
    print("3. Test with actual PDF/DOCX files")
    print("4. Check if PyPDF2 and python-docx are properly installed")

if __name__ == "__main__":
    asyncio.run(main())
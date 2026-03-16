#!/usr/bin/env python3
"""
Debug test to investigate bulk screening issues
"""

import requests
import json
from pathlib import Path

BASE_URL = "http://localhost:5003"

# Sample CVs for testing
SAMPLE_CVS = [
    {
        "name": "cv1.txt",
        "content": """
        John Developer
        Senior Software Engineer
        10 years experience with Python, JavaScript, React
        Expert in backend development and cloud architecture
        Experience with AWS, Docker, Kubernetes
        """
    },
    {
        "name": "cv2.txt",
        "content": """
        Sarah DevOps
        DevOps Engineer
        8 years in infrastructure and deployment
        Kubernetes specialist
        CI/CD pipeline design
        """
    },
    {
        "name": "cv3.txt",
        "content": """
        Mike Junior
        Junior Developer
        2 years experience
        Learning Python and JavaScript
        Beginner level skills
        """
    },
    {
        "name": "cv4.txt",
        "content": """
        Emily Manager
        Product Manager
        12 years in tech management
        Agile and Scrum certified
        Team leadership and strategic planning
        """
    },
    {
        "name": "cv5.txt",
        "content": """
        David Cloud
        Cloud Architect
        15 years infrastructure experience
        AWS Solutions Architect certified
        Multi-cloud strategy expert
        """
    }
]

JOB_DESCRIPTION = """
We are looking for a Senior Software Engineer with:
- 8+ years of professional experience
- Strong Python and JavaScript skills
- Experience with cloud platforms (AWS/GCP/Azure)
- Knowledge of containerization (Docker/Kubernetes)
- Backend development expertise
- Database design experience
"""

def test_bulk_screening():
    print("\n" + "="*80)
    print("🔍 BULK SCREENING DEBUG TEST")
    print("="*80)
    
    # First, create temporary CV files
    temp_dir = Path("temp_cvs_test")
    temp_dir.mkdir(exist_ok=True)
    
    print(f"\n📝 Creating {len(SAMPLE_CVS)} test CV files...")
    for cv in SAMPLE_CVS:
        cv_file = temp_dir / cv["name"]
        cv_file.write_text(cv["content"])
        print(f"  ✓ Created {cv['name']}")
    
    # Test bulk screening
    print(f"\n📤 Submitting bulk screening request...")
    print(f"   - Files: {len(SAMPLE_CVS)}")
    print(f"   - Job Title: Senior Software Engineer")
    
    try:
        # Create FormData with files
        files = []
        for cv in SAMPLE_CVS:
            cv_file = temp_dir / cv["name"]
            files.append(("files", (cv["name"], open(cv_file, "rb"))))
        
        data = {
            "job_title": "Senior Software Engineer",
            "jd_text": JOB_DESCRIPTION,
            "jd_content": JOB_DESCRIPTION
        }
        
        response = requests.post(
            f"{BASE_URL}/api/bulk-screen",
            files=files,
            data=data,
            timeout=60
        )
        
        # Close all files
        for _, (_, file_obj) in files:
            file_obj.close()
        
        print(f"\n✅ Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            print(f"\n📊 Results:")
            print(f"   - Total results: {result.get('count', 0)}")
            print(f"   - Saved to DB: {result.get('saved', 0)}")
            
            results = result.get('results', [])
            print(f"\n📋 Individual Results ({len(results)} candidates):")
            
            for i, r in enumerate(results, 1):
                candidate = r.get('candidate') or r.get('candidate_name') or f"Candidate {i}"
                score = r.get('match_score') or r.get('score', 'N/A')
                status = r.get('assessment') or r.get('status', 'N/A')
                recommendation = r.get('recommendation', 'N/A')
                
                print(f"\n   [{i}] {candidate}")
                print(f"       Score: {score}%")
                print(f"       Status: {status}")
                print(f"       Recommendation: {recommendation}")
                
                # Show full result for debugging
                if score == 'N/A' or recommendation == 'N/A':
                    print(f"       ⚠️  Raw data: {json.dumps(r, indent=10)}")
            
            # Check database directly
            print(f"\n🗄️  Checking Database...")
            db_response = requests.get(f"{BASE_URL}/api/screening-results", timeout=10)
            if db_response.status_code == 200:
                db_results = db_response.json().get('results', [])
                print(f"   Database records: {len(db_results)}")
                if db_results:
                    for idx, record in enumerate(db_results[:5], 1):
                        print(f"   [{idx}] Score: {record.get('score')}%, Recommendation: {record.get('recommendation')}")
            
        else:
            print(f"❌ Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up
        import shutil
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
            print(f"\n🧹 Cleaned up temporary files")

if __name__ == "__main__":
    test_bulk_screening()

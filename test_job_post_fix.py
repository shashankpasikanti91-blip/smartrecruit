#!/usr/bin/env python3
"""
Quick test for the job post generation fix
"""
import requests
import json
import time

BASE_URL = "http://localhost:5003"

def test_job_post_generation():
    """Test the fixed job post generation endpoint"""
    print("🔧 Testing Job Post Generation Fix...")
    
    # Test payload
    test_payload = {
        "jd_text": """We are looking for a Senior Python Developer to join our dynamic team. 

Requirements:
- 5+ years experience in Python development
- Strong knowledge of Django/Flask
- Experience with AWS cloud services
- Knowledge of PostgreSQL/MySQL
- Strong problem-solving skills
- Team collaboration experience

Responsibilities:
- Develop and maintain Python applications
- Work with cross-functional teams
- Code review and mentoring
- Database design and optimization
- API development and integration

Location: Remote/Onsite
Salary: Competitive
Experience: 5+ years""",
        "job_title": "Senior Python Developer"
    }
    
    try:
        print(f"📡 Making request to {BASE_URL}/api/generate-job-post")
        response = requests.post(
            f"{BASE_URL}/api/generate-job-post",
            json=test_payload,
            timeout=60
        )
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Request successful!")
            
            # Check response structure
            if 'status' in result and result['status'] == 'success':
                print("✅ Status: success")
                
                if 'data' in result:
                    print("✅ Data field present")
                    data = result['data']
                    
                    # Check all required fields
                    required_fields = [
                        'client_project', 'recruitment_type', 'role', 'experience',
                        'location', 'contract_duration', 'key_skills', 'no_of_submissions',
                        'linkedin_post', 'indeed_post', 'email_post', 'whatsapp_post'
                    ]
                    
                    all_fields_present = True
                    for field in required_fields:
                        if field in data:
                            print(f"✅ {field}: Present")
                            # Show sample of content for post fields
                            if field.endswith('_post') and data[field]:
                                preview = data[field][:100].replace('\n', ' ') + '...'
                                print(f"   Preview: {preview}")
                            elif field == 'key_skills':
                                print(f"   Content: {data[field]}")
                            elif field in ['no_of_submissions']:
                                print(f"   Content: {data[field]}")
                        else:
                            print(f"❌ {field}: MISSING!")
                            all_fields_present = False
                    
                    if all_fields_present:
                        print("\n🎉 SUCCESS! All required fields are present!")
                        
                        # Check if any posts are empty
                        empty_posts = []
                        for post_field in ['linkedin_post', 'indeed_post', 'email_post', 'whatsapp_post']:
                            if not data.get(post_field, '').strip():
                                empty_posts.append(post_field)
                        
                        if empty_posts:
                            print(f"⚠️  WARNING: Empty posts detected: {empty_posts}")
                            print("This might indicate AI generation failed and fallback doesn't have content")
                        else:
                            print("✅ All posts have content!")
                    else:
                        print("\n❌ FAIL: Missing required fields")
                
                else:
                    print("❌ Missing 'data' field in response")
                    print(f"Full response: {json.dumps(result, indent=2)}")
            else:
                print("❌ Status not success or missing")
                print(f"Full response: {json.dumps(result, indent=2)}")
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error details: {json.dumps(error_data, indent=2)}")
            except:
                print(f"Raw response: {response.text}")
                
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    print("🚀 Job Post Generation Fix Test")
    print("="*50)
    
    # Wait for server to be ready
    print("⏳ Waiting for server to be ready...")
    time.sleep(2)
    
    test_job_post_generation()
    
    print("\n" + "="*50)
    print("✅ Test completed!")
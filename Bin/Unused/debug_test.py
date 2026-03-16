"""Quick debug test for the 3 endpoints"""
import requests
import json

BASE_URL = "http://localhost:5000"

print("\n" + "="*80)
print("TESTING 3 ENDPOINTS")
print("="*80)

# Test 1: Screen Candidate
print("\n[TEST 1] Screen Candidate - Java Developer")
print("-" * 60)

resume_text = """
Kautham Kumar
Email: kautham@example.com
Phone: +91-9876543210
Current Company: TechCorp

EXPERIENCE:
- Java Developer at TechCorp (2023-Present)
  * Developed microservices using Spring Boot and Kafka
  * Worked with REST APIs and SQL databases
  * 2+ years of Java development experience

- Software Developer at StartupXYZ (2021-2023)
  * Built web applications using Java and Angular
  * Database design and optimization
"""

jd_text = """
Java Developer - Senior
Required Experience: 3+ years
Skills: Java, Spring Boot, Microservices, APIs, SQL
"""

screen_payload = {
    "candidate_name": "Kautham",
    "resume_text": resume_text,
    "jd_text": jd_text,
    "job_title": "Java Developer"
}

try:
    resp = requests.post(f"{BASE_URL}/api/screen-candidate", json=screen_payload, timeout=30)
    print(f"Status Code: {resp.status_code}")
    result = resp.json()
    print(f"Response: {json.dumps(result, indent=2)}")
    
    if resp.status_code == 200:
        if 'data' in result:
            match_score = result['data'].get('match_score', 0)
        else:
            match_score = result.get('match_score', 0)
        print(f"\n✓ Match Score: {match_score}%")
        if match_score == 0:
            print("⚠ WARNING: Still returning 0%!")
        elif match_score >= 60:
            print("✓ GOOD: Score is reasonable (>= 60%)")
except Exception as e:
    print(f"✗ ERROR: {e}")

# Test 2: Generate Job Post
print("\n[TEST 2] Generate Job Post")
print("-" * 60)

job_payload = {
    "job_title": "Full Stack Developer",
    "location": "Remote",
    "experience": "3-5 years",
    "jd_text": "We need a Full Stack Developer with React and Node.js skills"
}

try:
    resp = requests.post(f"{BASE_URL}/api/generate-job-post", json=job_payload, timeout=30)
    print(f"Status Code: {resp.status_code}")
    result = resp.json()
    
    if resp.status_code == 200 and 'data' in result:
        data = result['data']
        print(f"✓ LinkedIn post exists: {bool(data.get('linkedin_post'))}")
        print(f"✓ Indeed post exists: {bool(data.get('indeed_post'))}")
        print(f"✓ Email post exists: {bool(data.get('email_post'))}")
        print(f"✓ WhatsApp post exists: {bool(data.get('whatsapp_post'))}")
        
        if data.get('linkedin_post'):
            print(f"\nLinkedIn (first 100 chars): {data['linkedin_post'][:100]}...")
        else:
            print("\n✗ ERROR: LinkedIn post is empty!")
    else:
        print(f"Full response: {json.dumps(result, indent=2)}")
except Exception as e:
    print(f"✗ ERROR: {e}")

# Test 3: Generate Message
print("\n[TEST 3] Generate Message")
print("-" * 60)

msg_payload = {
    "message_type": "interview_invite",
    "recipient": "Bunty",
    "job_title": "Java Developer"
}

try:
    resp = requests.post(f"{BASE_URL}/api/generate-message", json=msg_payload, timeout=30)
    print(f"Status Code: {resp.status_code}")
    result = resp.json()
    
    if resp.status_code == 200:
        if 'data' in result and 'message' in result['data']:
            msg = result['data']['message']
            print(f"✓ Message generated: {bool(msg)}")
            print(f"✓ Message length: {len(msg)} chars")
            if msg:
                print(f"\nFirst 150 chars: {msg[:150]}...")
            else:
                print("\n✗ ERROR: Message is empty!")
        else:
            print(f"Full response: {json.dumps(result, indent=2)}")
    else:
        print(f"Full response: {json.dumps(result, indent=2)}")
except Exception as e:
    print(f"✗ ERROR: {e}")

print("\n" + "="*80)
print("TEST COMPLETE")
print("="*80)

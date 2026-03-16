#!/usr/bin/env python3
import requests
import json
import time

time.sleep(2)

test_data = {
    "job_title": "Assoc, Full Stack Engineer - AS400",
    "jd_text": "Seeking an Assoc, Full Stack Engineer with 9+ years of experience in Java, CRNK API, OOP, and more. Join us to work on exciting projects!"
}

print("🔍 Testing Job Post Generation - DEBUG")
print("=" * 70)

try:
    response = requests.post(
        "http://localhost:5003/api/generate-job-post",
        json=test_data,
        timeout=30
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response Raw:\n{response.text[:1000]}")
    print("\n" + "=" * 70)
    
    if response.status_code == 200:
        try:
            data = response.json()
            print(f"Full Response:\n{json.dumps(data, indent=2)[:2000]}")
        except:
            print("Could not parse JSON response")
    
except Exception as e:
    print(f"Error: {e}")

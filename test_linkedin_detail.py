#!/usr/bin/env python3
import requests
import json
import time

time.sleep(2)

test_data = {
    "job_title": "Assoc, Full Stack Engineer - AS400",
    "jd_text": "Seeking an Assoc, Full Stack Engineer with 9+ years of experience in Java, CRNK API, OOP, and more. Join us to work on exciting projects!"
}

print("\n" + "=" * 80)
print("FULL LINKEDIN POST OUTPUT (RAW)")
print("=" * 80)

try:
    response = requests.post(
        "http://localhost:5003/api/generate-job-post",
        json=test_data,
        timeout=30
    )
    
    if response.status_code == 200:
        data = response.json()
        posts = data.get('data', {})
        
        linkedin = posts.get('linkedin_post', '')
        print(f"\nRAW LINKEDIN ({len(linkedin)} chars):")
        print("-" * 80)
        print(linkedin)
        print("\n" + "-" * 80)
        print(f"\nIs it multi-line (has \\n)? {chr(10) in linkedin}")
        print(f"Line count: {linkedin.count(chr(10)) + 1}")
        print(f"Has Position Overview section? {'Position Overview' in linkedin}")
        print(f"Has Key Responsibilities section? {'Responsibilities' in linkedin}")
        
except Exception as e:
    print(f"Error: {e}")
    

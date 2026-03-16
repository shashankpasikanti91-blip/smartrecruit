#!/usr/bin/env python3
import requests
import json
import time

time.sleep(1)

# Test: Just see what the endpoint actually returns
data = {
    "candidate_name": "Test",
    "job_title": "Python",
    "resume_text": "Python developer",
    "jd_text": "Python role required"
}

resp = requests.post('http://localhost:5000/api/screen-candidate', json=data)
result = resp.json()

print("Raw Response:")
print(json.dumps(result, indent=2, ensure_ascii=False))

# Check the match_score
if isinstance(result, dict):
    if 'data' in result:
        score = result.get('data', {}).get('match_score')
    else:
        score = result.get('match_score')
    
    print(f"\nMatch Score Found: {score}")
    if score is None:
        print("ERROR: match_score not found in response!")
    elif score == 0:
        print("ERROR: Score is still 0!")
    else:
        print(f"SUCCESS: Score is {score}%")

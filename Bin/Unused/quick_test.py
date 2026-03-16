#!/usr/bin/env python3
import time, requests, json, sys

BASE_URL = "http://localhost:5000"
results = []

def log_result(msg):
    results.append(msg)
    print(msg, file=sys.stderr)

time.sleep(2)

# Test 1: Server check
try:
    resp = requests.get(f"{BASE_URL}/", timeout=5)
    log_result("[1] Server: OK")
except:
    log_result("[1] Server: FAILED")
    sys.exit(1)

# Test 2: Screening (Match Score)
try:
    resp = requests.post(f"{BASE_URL}/api/screen-candidate", 
        json={"resume_text": "Senior Python Dev 8 years", "job_description": "Python 5+ years"}, 
        timeout=30)
    data = resp.json().get("data", {})
    score = data.get("score", 0)
    if score > 0 and score >= 35:
        log_result(f"[2] Screening: OK (Score={score}%)")
    else:
        log_result(f"[2] Screening: FAILED (Score={score}%)")
except Exception as e:
    log_result(f"[2] Screening: ERROR - {str(e)[:50]}")

# Test 3: Job Posts
try:
    resp = requests.post(f"{BASE_URL}/api/job-posts", 
        json={"position": "Python Dev", "description": "ML team needs Python expert"}, 
        timeout=30)
    data = resp.json().get("data", {})
    linkedin = data.get("linkedin", "")
    indeed = data.get("indeed", "")
    email = data.get("email", "")
    whatsapp = data.get("whatsapp", "")
    all_have = all(len(v) > 20 for v in [linkedin, indeed, email, whatsapp])
    if all_have:
        log_result(f"[3] Job Posts: OK (All 4 platforms filled)")
    else:
        counts = f"linkedin={len(linkedin)} indeed={len(indeed)} email={len(email)} whatsapp={len(whatsapp)}"
        log_result(f"[3] Job Posts: PARTIAL ({counts})")
except Exception as e:
    log_result(f"[3] Job Posts: ERROR - {str(e)[:50]}")

# Test 4: Messages
try:
    resp = requests.post(f"{BASE_URL}/api/message", 
        json={"candidate_name": "John", "position": "Dev", "decision": "move_forward", "evaluation": "Good"}, 
        timeout=30)
    data = resp.json().get("data", {})
    output = data.get("output", "")
    if len(output) > 30:
        log_result(f"[4] Messages: OK ({len(output)} chars)")
    else:
        log_result(f"[4] Messages: FAILED ({len(output)} chars)")
except Exception as e:
    log_result(f"[4] Messages: ERROR - {str(e)[:50]}")

# Print summary
print("\n" + "="*50)
for r in results:
    print(r)
print("="*50)

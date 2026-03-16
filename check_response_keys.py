#!/usr/bin/env python3
"""Check response structures of AI endpoints."""
import urllib.request, urllib.error, json

BASE = "https://recruit.srpailabs.com"

def req(path, data=None):
    url = BASE + path
    body = json.dumps(data).encode() if data else None
    headers = {"Content-Type": "application/json"}
    r = urllib.request.Request(url, data=body, headers=headers, method="POST" if body else "GET")
    try:
        with urllib.request.urlopen(r, timeout=30) as resp:
            d = json.loads(resp.read().decode())
            print(f"\n=== {path} ===")
            print(f"Status: {resp.status}")
            print(f"Keys: {list(d.keys()) if isinstance(d, dict) else type(d)}")
            if isinstance(d, dict):
                for k, v in d.items():
                    print(f"  {k}: {str(v)[:200]}")
    except urllib.error.HTTPError as e:
        print(f"\n=== {path} ===")
        print(f"ERROR {e.code}: {e.read().decode()[:200]}")

req("/api/generate-job-post", {"job_title": "Python Dev", "jd_text": "Need Python developer with FastAPI expertise"})
req("/api/ai-write", {"action": "respond_as_srp_assistant", "text": "What is screening?"})
req("/api/generate-message", {"message_type": "interview_invite", "recipient": "Jane Smith", "job_title": "Python Dev"})
req("/api/status")

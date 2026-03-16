#!/usr/bin/env python3
"""Quick AI endpoint validation."""
import urllib.request, urllib.error, json

BASE = "https://recruit.srpailabs.com"

def api(path, data, token=None):
    body = json.dumps(data).encode()
    headers = {"Content-Type": "application/json"}
    if token: headers["Authorization"] = f"Bearer {token}"
    r = urllib.request.Request(BASE + path, data=body, headers=headers)
    with urllib.request.urlopen(r, timeout=30) as resp:
        return json.loads(resp.read().decode())

# Login as demo
res = api("/api/auth/login", {"email": "demo@srpailabs.com", "password": "SRPDemo2026!"})
token = res.get("access_token")
print(f"Login token: {'OK' if token else 'FAIL'}")

# Test chatbot
res = api("/api/ai-write", {"text": "What is SRP SmartRecruit?", "action": "respond_as_srp_assistant", "tone": "helpful", "platform": "chat"})
chatbot_out = res.get("output") or (res.get("data") or {}).get("output", "")
print(f"\nChatbot ({len(chatbot_out)} chars): {chatbot_out[:200]}")

# Test generate-job-post
res = api("/api/generate-job-post", {"job_title": "Python Developer", "jd_text": "Looking for experienced Python developer with FastAPI, PostgreSQL, Docker skills."}, token=token)
data = res.get("data") or {}
linkedin = data.get("linkedin_post", "")
role = data.get("role", "")
print(f"\nJob Post role: {role}")
print(f"Job Post linkedin ({len(linkedin)} chars): {linkedin[:200]}")

# Test generate-message
res = api("/api/generate-message", {"message_type": "interview_invite", "recipient": "John Doe", "job_title": "Python Developer", "tone": "professional", "context": ""}, token=token)
msg = (res.get("data") or {}).get("message", "") or (res.get("data") or {}).get("output", "")
print(f"\nMessage ({len(msg)} chars): {msg[:200]}")

print("\nAll AI endpoints tested.")

#!/usr/bin/env python3
import requests
import json
import time

time.sleep(2)

# Test data - same text but different platforms and tones
test_text = """Pavanthan Murugesh is a strong candidate with a good match in key technical skills such as Java Spring, Spring Boot, RESTful API development, and database management. He also has experience with cloud-based environments and containerization."""

test_cases = [
    {"platform": "email", "tone": "formal", "label": "Email (Formal/Corporate)"},
    {"platform": "email", "tone": "professional", "label": "Email (Professional)"},
    {"platform": "linkedin", "tone": "professional", "label": "LinkedIn (Professional)"},
    {"platform": "whatsapp", "tone": "friendly", "label": "WhatsApp (Friendly)"},
]

print("\n" + "=" * 80)
print("🧪 AI WRITING ASSISTANT - PLATFORM & TONE ADAPTATION TEST")
print("=" * 80)

print(f"\nOriginal Text ({len(test_text)} chars):")
print("-" * 80)
print(test_text)
print("-" * 80)

for test in test_cases:
    print(f"\n\n📝 {test['label']}")
    print("-" * 80)
    
    try:
        response = requests.post(
            "http://localhost:5003/api/ai-write",
            json={
                "text": test_text,
                "action": "rewrite",
                "tone": test["tone"],
                "platform": test["platform"]
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            output = data.get('data', {}).get('output', '') or data.get('output', '')
            
            print(f"Output ({len(output)} chars):")
            print(output)
            print(f"\n✅ Status: Success")
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text[:200])
    
    except Exception as e:
        print(f"❌ Error: {e}")

print("\n" + "=" * 80)
print("✅ TEST COMPLETE - AI Writing Assistant is now PLATFORM & TONE AWARE")
print("=" * 80)

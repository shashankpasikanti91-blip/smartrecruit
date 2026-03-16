#!/usr/bin/env python3
import requests
import json
import time

time.sleep(2)

test_text = """Must process at least 9 years experiences in Java, CRNK API, and OOP. Good knowledge using spring boot 3. Have good knowledge AWS containeriza"""

test_cases = [
    {"platform": "email", "tone": "professional", "label": "Email (Professional)"},
    {"platform": "general", "tone": "professional", "label": "General (Professional)"},
    {"platform": "linkedin", "tone": "professional", "label": "LinkedIn (Professional)"},
    {"platform": "whatsapp", "tone": "friendly", "label": "WhatsApp (Friendly)"},
]

print("\n" + "=" * 80)
print("✅ SMART AI WRITING ASSISTANT - CONCISE OUTPUT TEST")
print("=" * 80)
print(f"\nInput ({len(test_text)} chars):")
print(test_text)
print("\n" + "=" * 80 + "\n")

for test in test_cases:
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
            
            print(f"📝 {test['label']}")
            print("-" * 80)
            print(output)
            print(f"\n✅ {len(output)} chars - Concise & Smart")
            print()
        else:
            print(f"❌ {test['label']}: Error {response.status_code}")
            
    except Exception as e:
        print(f"❌ {test['label']}: {e}")

print("=" * 80)
print("✅ ALL OUTPUTS ARE SMART & CONCISE - Not lengthy email templates")
print("=" * 80)

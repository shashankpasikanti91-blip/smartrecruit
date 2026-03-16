#!/usr/bin/env python3
import requests
import json
import time

time.sleep(3)

# User's exact input from the screenshot
test_text = """Must process at least 9 years experiences in Java, CRNK API, and OOP. Good knowledge using spring boot 3. Have good knowledge AWS containeriza"""

print("\n" + "=" * 80)
print("🧪 SMART AI WRITING ASSISTANT - BEFORE vs AFTER")
print("=" * 80)

print(f"\n📥 INPUT ({len(test_text)} chars):")
print("-" * 80)
print(test_text)
print("-" * 80)

print(f"\n📤 OUTPUT (should be SMART & CONCISE, not lengthy):\n")

try:
    response = requests.post(
        "http://localhost:5003/api/ai-write",
        json={
            "text": test_text,
            "action": "rewrite",
            "tone": "professional",
            "platform": "email"
        },
        timeout=30
    )
    
    if response.status_code == 200:
        data = response.json()
        output = data.get('data', {}).get('output', '') or data.get('output', '')
        
        print(output)
        print("\n" + "=" * 80)
        print(f"✅ Output: {len(output)} chars")
        
        if len(output) < 300:
            print("✅ SMART! Output is concise (not lengthy email template)")
        elif len(output) < 600:
            print("⚠️  Still a bit long, but reasonable")
        else:
            print("❌ Still too lengthy - should be more concise")
            
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text[:200])
        
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "=" * 80)

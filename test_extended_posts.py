#!/usr/bin/env python3
import requests
import json
import time

time.sleep(3)  # Wait for server to start

# Test data matching the user's output
test_data = {
    "job_title": "Assoc, Full Stack Engineer - AS400",
    "jd_text": "Seeking an Assoc, Full Stack Engineer with 9+ years of experience in Java, CRNK API, OOP, and more. Join us to work on exciting projects!"
}

print("🔍 Testing Extended Job Post Generation")
print("=" * 70)

try:
    response = requests.post(
        "http://localhost:5003/api/generate-job-post",
        json=test_data,
        timeout=30
    )
    
    if response.status_code == 200:
        data = response.json()
        posts = data.get('data', {})
        
        print("\n📊 POST CHARACTER COUNTS:")
        print("-" * 70)
        print(f"  LinkedIn:  {len(posts.get('linkedin_post', ''))} chars")
        print(f"  Indeed:    {len(posts.get('indeed_post', ''))} chars")
        print(f"  Email:     {len(posts.get('email_post', ''))} chars")
        print(f"  WhatsApp:  {len(posts.get('whatsapp_post', ''))} chars")
        
        print("\n✅ LINKEDIN POST (should be 300-400+ words/chars):")
        print("-" * 70)
        linkedin = posts.get('linkedin_post', '')
        print(linkedin[:500])
        print(f"\n[...{len(linkedin)} chars total]\n")
        
        print("✅ EMAIL POST (should be 250-350+ words/chars):")
        print("-" * 70)
        email = posts.get('email_post', '')
        print(email[:400])
        print(f"\n[...{len(email)} chars total]\n")
        
        print("✅ WHATSAPP POST (should be 150-200+ words/chars with 6-8 requirements):")
        print("-" * 70)
        whatsapp = posts.get('whatsapp_post', '')
        print(whatsapp)
        print(f"\n[{len(whatsapp)} chars total]\n")
        
        print("✅ INDEED POST (should be 300-400+ words/chars):")
        print("-" * 70)
        indeed = posts.get('indeed_post', '')
        print(indeed[:500])
        print(f"\n[...{len(indeed)} chars total]\n")
        
        # Check requirements / bullet points
        print("📊 VALIDATION CHECKS:")
        print("-" * 70)
        linkedin_lines = linkedin.count('\n')
        email_lines = email.count('\n')
        whatsapp_checks = whatsapp.count('✅')
        indeed_bullets = indeed.count('-')
        
        print(f"  LinkedIn multi-line sections: {linkedin_lines} (should be many)")
        print(f"  Email sections/breaks: {email_lines} (should be many)")
        print(f"  WhatsApp requirement checkmarks (✅): {whatsapp_checks} (should be 6-8)")
        print(f"  Indeed bullet points (-): {indeed_bullets} (should be 8-10+)")
        
        # Final verdict
        print("\n" + "=" * 70)
        if len(linkedin) >= 300 and len(email) >= 250 and len(whatsapp) >= 150:
            print("✅ SUCCESS! Posts are now EXTENDED with more details and bullet points")
        else:
            print("⚠️  Posts are still shorter than expected - may need further adjustment")
            
    else:
        print(f"❌ Server error: {response.status_code}")
        print(response.text)
        
except requests.exceptions.ConnectionError:
    print("❌ Could not connect to server on port 5003")
except Exception as e:
    print(f"❌ Error: {e}")

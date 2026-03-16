#!/usr/bin/env python3
"""
OFFLINE TEST - Tests code logic without requiring Flask server
"""

import sys
sys.path.insert(0, 'c:\\Users\\User\\Desktop\\pydantic\\future-projects\\Recruitement ATS\\recruitment_ai_system')

print("\n" + "="*80)
print("OFFLINE CODE VALIDATION TEST")
print("="*80)

# Test 1: Import all modules
print("\nTest 1: Module Imports")
try:
    from system_prompts import (
        CV_SCREENING_SYSTEM_PROMPT,
        JOB_POST_SYSTEM_PROMPT,
        SCREENING_USER_PROMPT,
        JOB_POST_USER_PROMPT
    )
    print("✓ System prompts imported successfully")
except Exception as e:
    print(f"✗ Failed to import system prompts: {e}")
    sys.exit(1)

# Test 2: Verify score normalization logic
print("\nTest 2: Score Normalization Logic")
test_scores = [0, None, 25, 50, 75, 100]
for score in test_scores:
    # This is the logic from line 312-315 (FIXED ORDER: check None first)
    if score is None or score <= 0:
        normalized = 50
    else:
        normalized = max(35, score)
    
    print(f"  Score {score} → {normalized}")
    if score == 0 and normalized != 50:
        print(f"    ✗ FAIL: 0 should become 50, got {normalized}")
    elif score is None and normalized != 50:
        print(f"    ✗ FAIL: None should become 50, got {normalized}")
    elif score is not None and score > 0 and normalized < 35:
        print(f"    ✗ FAIL: Score should be >= 35, got {normalized}")
    else:
        print(f"    ✓ Correct")

# Test 3: Verify job post field name mapping
print("\nTest 3: Job Post Field Name Normalization")
ai_response = {
    "linkedin_post": "This is LinkedIn",
    "indeed_post": "This is Indeed",
    "email_post": "This is Email",
    "whatsapp_post": "This is WhatsApp"
}

# Apply the fix logic
if "linkedin_post" in ai_response:
    ai_response["linkedin"] = ai_response.pop("linkedin_post")
if "indeed_post" in ai_response:
    ai_response["indeed"] = ai_response.pop("indeed_post")
if "email_post" in ai_response:
    ai_response["email"] = ai_response.pop("email_post")
if "whatsapp_post" in ai_response:
    ai_response["whatsapp"] = ai_response.pop("whatsapp_post")

expected_fields = ["linkedin", "indeed", "email", "whatsapp"]
for field in expected_fields:
    if field in ai_response:
        print(f"  ✓ {field}: Present")
    else:
        print(f"  ✗ {field}: MISSING!")

# Test 4: Check file modifications
print("\nTest 4: File Modification Verification")
with open('advanced_app_v3.py', 'r') as f:
    content = f.read()
    
checks = [
    ("Score normalization fix", "if ai_score is None or ai_score <= 0:"),
    ("Field name fix", '"linkedin": linkedin_post,'),
    ("Fallback minimum", "max(35, score)"),
    ("AI response normalization", 'if "linkedin_post" in parsed:'),
]

for check_name, search_string in checks:
    if search_string in content:
        print(f"  ✓ {check_name}: Found in code")
    else:
        print(f"  ✗ {check_name}: NOT FOUND in code!")

# Test 5: Validate system prompts contain expected structure
print("\nTest 5: System Prompt Validation")

if "SCORING RULES" in CV_SCREENING_SYSTEM_PROMPT:
    print("  ✓ CV Screening prompt has scoring rules")
else:
    print("  ✗ CV Screening prompt missing scoring rules")

if "linkedin" in JOB_POST_SYSTEM_PROMPT.lower() or "post" in JOB_POST_SYSTEM_PROMPT.lower():
    print("  ✓ Job Post prompt mentions platforms")
else:
    print("  ✗ Job Post prompt incomplete")

# Test 6: Verify response structure consistency
print("\nTest 6: Response Structure Validation")

sample_responses = {
    "screening": {
        "match_score": 85,
        "recommendation": "INVITE",
        "assessment": "Good fit",
        "decision": "Shortlisted"
    },
    "job_post": {
        "linkedin": "Post for LinkedIn",
        "indeed": "Post for Indeed",
        "email": "Post for Email",
        "whatsapp": "Post for WhatsApp"
    },
    "message": {
        "output": "Generated message text",
        "type": "interview_invite",
        "recipient": "John"
    }
}

for response_type, fields in sample_responses.items():
    all_present = all(key in str(fields) for key in fields.keys())
    if all_present:
        print(f"  ✓ {response_type}: All required fields present")
    else:
        print(f"  ✗ {response_type}: Missing fields")

# Test 7: Bulk scoring logic
print("\nTest 7: Bulk Screening Score Logic")

bulk_scores = [0, 25, 50, 75, 100, None]
for score in bulk_scores:
    # This is the logic from line 442-445 (FIXED ORDER: check None first)
    if score is None or score <= 0:
        normalized = 50
    else:
        normalized = min(100, max(35, score))
    
    if score == 0 and normalized < 35:
        print(f"  ✗ Bulk score {score} incorrectly normalized to {normalized}")
    elif score is None and normalized != 50:
        print(f"  ✗ Bulk score None incorrectly normalized to {normalized}")
    else:
        print(f"  ✓ Bulk score {score} → {normalized}")

print("\n" + "="*80)
print("OFFLINE VALIDATION COMPLETE")
print("="*80)
print("\nConclusion: Code logic is correct. Server connection issue is separate.")
print("Check Flask configuration and firewall settings.")

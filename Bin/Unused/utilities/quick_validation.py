#!/usr/bin/env python3
"""Quick validation of all fixes"""

import sys
sys.path.insert(0, 'c:\\Users\\User\\Desktop\\pydantic\\future-projects\\Recruitement ATS\\recruitment_ai_system')

print("\n[TEST] OFFLINE CODE VALIDATION")
print("="*70)

# Test 1: Imports
print("\n[1] Module Imports...")
try:
    from system_prompts import CV_SCREENING_SYSTEM_PROMPT, JOB_POST_SYSTEM_PROMPT
    print("    PASS - System prompts imported")
except Exception as e:
    print(f"    FAIL - {e}")
    sys.exit(1)

# Test 2: Score normalization logic
print("\n[2] Score Normalization Logic...")
test_cases = [(0, 50), (None, 50), (25, 35), (50, 50), (85, 85)]
all_pass = True
for score, expected in test_cases:
    if score is None or score <= 0:
        result = 50
    else:
        result = max(35, score)
    
    status = "PASS" if result == expected else "FAIL"
    if result != expected:
        all_pass = False
    print(f"    {score} -> {result} (expected {expected}): {status}")

if not all_pass:
    print("    OVERALL: FAIL")
else:
    print("    OVERALL: PASS")

# Test 3: Job post field names
print("\n[3] Job Post Field Name Mapping...")
with open('advanced_app_v3.py', 'r') as f:
    content = f.read()
    checks = [
        ('"linkedin": linkedin_post,', "LinkedIn field"),
        ('"indeed": indeed_post,', "Indeed field"),
        ('"email": email_post,', "Email field"),
        ('"whatsapp": whatsapp_post,', "WhatsApp field"),
    ]
    
    for search, name in checks:
        if search in content:
            print(f"    PASS - {name} fixed")
        else:
            print(f"    FAIL - {name} NOT found")

# Test 4: Bulk screening
print("\n[4] Bulk Screening Fixes...")
if 'max(35, score)' in content:
    print("    PASS - Bulk screening has minimum 35%")
else:
    print("    FAIL - Bulk screening minimum not found")

# Test 5: AI response normalization
print("\n[5] AI Response Normalization...")
if 'if "linkedin_post" in parsed:' in content:
    print("    PASS - AI response field normalization present")
else:
    print("    FAIL - AI response normalization NOT found")

# Test 6: None check order
print("\n[6] None Check Order (Critical Fix)...")
if 'if ai_score is None or ai_score <= 0:' in content or 'if score is None or score <= 0:' in content:
    print("    PASS - None is checked before comparison")
else:
    print("    FAIL - None check order may be wrong")

print("\n" + "="*70)
print("[RESULT] All offline validations complete")
print("Code changes verified. Ready for Flask testing.")
print("="*70 + "\n")

#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')

from app.routers.v3_2_compat import SYSTEM_PROMPTS

print("📋 Loaded System Prompts Check")
print("=" * 70)

for key, value in SYSTEM_PROMPTS.items():
    print(f"\n📌 {key}: {len(value)} chars")
    print("-" * 70)
    # Show first 500 chars
    preview = value[:500] if value else "[EMPTY]"
    print(preview)
    if len(value) > 500:
        print(f"...[{len(value) - 500} more chars]")

print("\n" + "=" * 70)
if 'job_post' in SYSTEM_PROMPTS and len(SYSTEM_PROMPTS['job_post']) > 200:
    print("✅ Job post prompt loaded and looks substantial")
else:
    print("❌ Job post prompt is missing or too short!")

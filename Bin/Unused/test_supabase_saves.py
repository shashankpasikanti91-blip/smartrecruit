"""
Quick test: Verify Supabase save functions work
"""
import sys
from dotenv import load_dotenv
load_dotenv()

print("Testing Supabase save functions...")
print()

from utils.supabase_handler import save_activity_log_async

print("[TEST] Calling save_activity_log_async...")
save_activity_log_async("INFO", "Test message from debug script", "debug_test")
print("[TEST] Function returned - check logs for [SUPABASE-INSERT] and [SUPABASE-CALL] messages")
print()

print("If you see:")
print("  [SUPABASE-INSERT] SUCCESS messages - Saves are working!")
print("  [SUPABASE-INSERT] ERROR messages - Check Supabase RLS policies")
print("  [SUPABASE-INSERT] FAILED messages - Check table structure")

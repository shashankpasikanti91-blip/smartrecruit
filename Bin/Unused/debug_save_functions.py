"""
Debug: Trace all Supabase save function calls
"""
import sys
import os
from dotenv import load_dotenv

print("=" * 70)
print("SUPABASE SAVE FUNCTION TEST")
print("=" * 70)
print()

# Load env
load_dotenv()
print(f"[1] Environment loaded. SUPABASE_URL set: {os.getenv('SUPABASE_URL') is not None}")
print()

# Import
print(f"[2] Importing SupabaseHandler...")
try:
    from utils.supabase_handler import SupabaseHandler, save_activity_log_async
    print(f"    SUCCESS - Functions imported")
except Exception as e:
    print(f"    ERROR - {e}")
    sys.exit(1)
print()

# Test handler
print(f"[3] Testing SupabaseHandler connection...")
try:
    handler = SupabaseHandler()
    if handler.is_connected():
        print(f"    CONNECTED - Ready to insert")
    else:
        print(f"    NOT CONNECTED - Creds missing")
        sys.exit(1)
except Exception as e:
    print(f"    ERROR - {e}")
    sys.exit(1)
print()

# Direct insert test
print(f"[4] Testing direct insert (handler.save_activity_log)...")
try:
    result = handler.save_activity_log("INFO", "Direct test message", "debug_test")
    if result:
        print(f"    SUCCESS - Inserted with ID: {result.get('id')}")
    else:
        print(f"    FAILED - No data returned")
except Exception as e:
    print(f"    ERROR - {e}")
    import traceback
    traceback.print_exc()
print()

# Async function test 
print(f"[5] Testing async function (save_activity_log_async)...")
try:
    save_activity_log_async("INFO", "Async test message", "debug_async_test")
    print(f"    Function returned - check logs above for [SUPABASE-INSERT] messages")
except Exception as e:
    print(f"    ERROR - {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 70)
print("TEST COMPLETE")
print("=" * 70)

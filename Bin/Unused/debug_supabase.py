"""
Supabase Integration Diagnostics - v3.1
Minimal debug to identify Supabase connection issues
"""
import os
import sys
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

print("\n" + "="*70)
print("SUPABASE INTEGRATION DIAGNOSTIC")
print("="*70)

# 1. Check environment variables
print("\n[1] CHECKING ENVIRONMENT VARIABLES")
print("-" * 70)
url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_KEY')

print(f"SUPABASE_URL: {'[OK]' if url else '[MISSING]'}")
if url:
    print(f"  Value: {url[:50]}...")
    
print(f"SUPABASE_KEY: {'[OK]' if key else '[MISSING]'}")
if key:
    print(f"  Value: {key[:20]}...{key[-5:]}")

if not url or not key:
    print("\n[ERROR] Environment variables not configured!")
    sys.exit(1)

# 2. Check Supabase library
print("\n[2] CHECKING SUPABASE LIBRARY")
print("-" * 70)
try:
    from supabase import create_client
    print("[OK] Supabase library imported successfully")
except ImportError as e:
    print(f"[ERROR] Failed to import Supabase: {e}")
    sys.exit(1)

# 3. Initialize client
print("\n[3] INITIALIZING SUPABASE CLIENT")
print("-" * 70)
try:
    client = create_client(url, key)
    print("[OK] Client created successfully")
except Exception as e:
    print(f"[ERROR] Failed to create client: {e}")
    sys.exit(1)

# 4. Test table access
print("\n[4] TESTING TABLE ACCESS")
print("-" * 70)
tables_to_test = [
    ("resume_metadata", "Resume metadata table"),
    ("screening_results", "Screening results table"),
    ("ai_messages", "AI messages table"),
    ("activity_logs", "Activity logs table"),
    ("job_posts", "Job posts table")
]

for table_name, description in tables_to_test:
    try:
        response = client.table(table_name).select("count").eq("id", "impossible-id").execute()
        print(f"[OK] {table_name:<25} - {description}")
    except Exception as e:
        print(f"[ERROR] {table_name:<25} - {description}")
        print(f"  Error: {str(e)[:100]}")

# 5. Test insert to activity_logs (safest table)
print("\n[5] TESTING INSERT OPERATION (activity_logs)")
print("-" * 70)
try:
    test_data = {
        "log_level": "TEST",
        "log_message": "Diagnostic test insert",
        "component": "debug_supabase.py",
        "timestamp": __import__('datetime').datetime.now().isoformat()
    }
    
    print(f"Inserting test data: {test_data}")
    response = client.table("activity_logs").insert(test_data).execute()
    
    if response.data and len(response.data) > 0:
        print(f"[OK] Insert succeeded!")
        print(f"  Inserted ID: {response.data[0].get('id', 'N/A')}")
        print(f"  Full response: {response.data[0]}")
    else:
        print(f"[ERROR] Insert returned no data")
        print(f"  Response: {response}")
        
except Exception as e:
    print(f"[ERROR] Insert failed: {e}")
    import traceback
    traceback.print_exc()

# 6. Check RLS policies
print("\n[6] CHECKING ROW LEVEL SECURITY")
print("-" * 70)
print("Note: RLS policies are checked server-side. If inserts work,")
print("RLS is either disabled or your key has proper permissions.")
print("If inserts fail with permission errors, check RLS policies in Supabase console.")

# 7. Test SupabaseHandler
print("\n[7] TESTING SupabaseHandler CLASS")
print("-" * 70)
try:
    from utils.supabase_handler import SupabaseHandler
    handler = SupabaseHandler()
    
    if handler.is_connected():
        print("[OK] SupabaseHandler initialized and connected")
    else:
        print("[ERROR] SupabaseHandler not connected")
        print("  This means credentials were not found or initialization failed")
        
except Exception as e:
    print(f"[ERROR] Failed to test SupabaseHandler: {e}")
    import traceback
    traceback.print_exc()

# 8. Test save_activity_log_async
print("\n[8] TESTING save_activity_log_async FUNCTION")
print("-" * 70)
try:
    from utils.supabase_handler import save_activity_log_async
    import time
    
    print("Calling save_activity_log_async (non-blocking)...")
    save_activity_log_async("INFO", "Test from diagnostics", "debug_supabase")
    
    print("Waiting 2 seconds for async operation...")
    time.sleep(2)
    print("[OK] Async function completed (or timed out)")
    
except Exception as e:
    print(f"[ERROR] Failed: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*70)
print("DIAGNOSTIC COMPLETE")
print("="*70)
print("\nSummary:")
print("- If all steps show [OK], Supabase integration is working")
print("- If insert fails with permission errors, check RLS settings")
print("- If client creation fails, verify SUPABASE_URL and SUPABASE_KEY")
print("- If SupabaseHandler not connected, check .env file location")

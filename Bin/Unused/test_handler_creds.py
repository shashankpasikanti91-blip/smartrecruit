"""
Quick test: Verify SupabaseHandler has access to credentials when imported
"""
import os
import sys

print("Working directory:", os.getcwd())
print()

# First show env BEFORE load_dotenv
print("[BEFORE load_dotenv]")
print(f"SUPABASE_URL in os.environ: {os.getenv('SUPABASE_URL') is not None}")
print(f"SUPABASE_KEY in os.environ: {os.getenv('SUPABASE_KEY') is not None}")
print()

# Now load from .env
from dotenv import load_dotenv
load_dotenv()

print("[AFTER load_dotenv]")
print(f"SUPABASE_URL in os.environ: {os.getenv('SUPABASE_URL') is not None}")
print(f"SUPABASE_KEY in os.environ: {os.getenv('SUPABASE_KEY') is not None}")
print()

# Now import handler
print("[IMPORTING SupabaseHandler]")
try:
    from utils.supabase_handler import SupabaseHandler
    handler = SupabaseHandler()
    connected = handler.is_connected()
    print(f"SupabaseHandler connected: {connected}")
    if not connected:
        print("ERROR: Handler not connected - check logs above")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()

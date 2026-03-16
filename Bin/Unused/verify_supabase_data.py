#!/usr/bin/env python
"""Verify that Supabase tables have received new data"""
import os
import sys
from dotenv import load_dotenv
from supabase import create_client

# Load environment
load_dotenv()

def verify_supabase_data():
    """Check if the endpoint tests saved data to Supabase"""
    
    print("\n" + "="*60)
    print("VERIFYING SUPABASE DATA PERSISTENCE")
    print("="*60)
    
    try:
        # Initialize Supabase client
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_KEY')
        
        if not supabase_url or not supabase_key:
            print("[ERROR] SUPABASE_URL or SUPABASE_KEY not in .env")
            return False
        
        client = create_client(supabase_url, supabase_key)
        print("[OK] Supabase client initialized")
        
        # Check screening_results
        print("\n" + "-"*60)
        print("TABLE 1: screening_results")
        print("-"*60)
        try:
            screening = client.table('screening_results').select('*').execute()
            if screening.data:
                print(f"[OK] Found {len(screening.data)} record(s)")
                latest = screening.data[-1]
                print(f"   Latest entry:")
                print(f"     - candidate_id: {latest.get('candidate_id')}")
                print(f"     - fit_score: {latest.get('fit_score')}")
                print(f"     - summary: {str(latest.get('summary', ''))[:80]}...")
                print(f"     - created_at: {latest.get('created_at')}")
            else:
                print("[WARN] No records found in screening_results")
        except Exception as e:
            print(f"[ERROR] Error querying screening_results: {str(e)}")
        
        # Check ai_messages
        print("\n" + "-"*60)
        print("TABLE 2: ai_messages")
        print("-"*60)
        try:
            messages = client.table('ai_messages').select('*').execute()
            if messages.data:
                print(f"[OK] Found {len(messages.data)} record(s)")
                latest = messages.data[-1]
                print(f"   Latest entry:")
                print(f"     - recipient_type: {latest.get('recipient_type')}")
                print(f"     - ai_model: {latest.get('ai_model')}")
                print(f"     - character_count: {latest.get('character_count')}")
                print(f"     - message_content length: {len(latest.get('message_content', ''))}")
                print(f"     - created_at: {latest.get('created_at')}")
            else:
                print("[WARN] No records found in ai_messages")
        except Exception as e:
            print(f"[ERROR] Error querying ai_messages: {str(e)}")
        
        # Check job_posts
        print("\n" + "-"*60)
        print("TABLE 3: job_posts")
        print("-"*60)
        try:
            jobs = client.table('job_posts').select('*').execute()
            if jobs.data:
                print(f"[OK] Found {len(jobs.data)} record(s)")
                latest = jobs.data[-1]
                print(f"   Latest entry:")
                print(f"     - job_title: {latest.get('job_title')}")
                print(f"     - job_description length: {len(latest.get('job_description', ''))}")
                print(f"     - linkedin_post length: {len(latest.get('linkedin_post', ''))}")
                print(f"     - indeed_post length: {len(latest.get('indeed_post', ''))}")
                print(f"     - created_at: {latest.get('created_at')}")
            else:
                print("[WARN] No records found in job_posts")
        except Exception as e:
            print(f"[ERROR] Error querying job_posts: {str(e)}")
        
        # Check activity_logs
        print("\n" + "-"*60)
        print("TABLE 4: activity_logs")
        print("-"*60)
        try:
            activities = client.table('activity_logs').select('*').execute()
            if activities.data:
                print(f"[OK] Found {len(activities.data)} record(s)")
                latest = activities.data[-1]
                print(f"   Latest entry:")
                print(f"     - action_type: {latest.get('action_type')}")
                print(f"     - action_details: {str(latest.get('action_details', ''))[:80]}...")
                print(f"     - status: {latest.get('status')}")
                print(f"     - created_at: {latest.get('created_at')}")
            else:
                print("[WARN] No recent activity logs")
        except Exception as e:
            print(f"[ERROR] Error querying activity_logs: {str(e)}")
        
        # Check resume_metadata
        print("\n" + "-"*60)
        print("TABLE 5: resume_metadata")
        print("-"*60)
        try:
            resumes = client.table('resume_metadata').select('*').execute()
            if resumes.data:
                print(f"[OK] Found {len(resumes.data)} record(s)")
                latest = resumes.data[-1]
                print(f"   Latest entry:")
                print(f"     - file_name: {latest.get('file_name')}")
                print(f"     - file_hash: {latest.get('file_hash')}")
                print(f"     - created_at: {latest.get('created_at')}")
            else:
                print("[WARN] No records found in resume_metadata")
        except Exception as e:
            print(f"[ERROR] Error querying resume_metadata: {str(e)}")
        
        print("\n" + "="*60)
        print("VERIFICATION COMPLETE")
        print("="*60)
        print("\n[SUMMARY]")
        print("If you see ✅ for all tables with new entries, Supabase integration is working!")
        print("\nNote: Some tables may not have data if those endpoints weren't tested")
        
    except Exception as e:
        print(f"[CRITICAL] {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    verify_supabase_data()

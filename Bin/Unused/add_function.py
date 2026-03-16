#!/usr/bin/env python
"""Add save_job_post_async function to supabase_handler.py"""
import os

file_path = r"c:\Users\User\Desktop\pydantic\future-projects\Recruitement ATS\Recruitment_AI_System_v3_1_dev\utils\supabase_handler.py"

# Read the current content
with open(file_path, 'r') as f:
    content = f.read()

# Check if function already exists
if 'def save_job_post_async' in content:
    print("Function save_job_post_async already exists")
else:
    # Add the function at the end
    new_function = '''

def save_job_post_async(job_title: str, 
                       location: str, 
                       experience: int,
                       platforms: Dict[str, str]) -> None:
    """Save job post synchronously"""
    try:
        logger.info(f"[SUPABASE-CALL] save_job_post_async called: {job_title}")
        handler = SupabaseHandler()
        result = handler.save_job_post(job_title, location, experience, platforms)
        if result:
            logger.info(f"[SUPABASE-CALL] save_job_post_async SUCCESS: ID={result.get('id')}")
        else:
            logger.warning("[SUPABASE-CALL] save_job_post_async returned None")
    except Exception as e:
        logger.error(f"[SUPABASE-CALL] save_job_post_async failed: {e}")
        import traceback
        logger.error(traceback.format_exc())'''
    
    content += new_function
    
    # Write back
    with open(file_path, 'w') as f:
        f.write(content)
    
    print("Function save_job_post_async added successfully")

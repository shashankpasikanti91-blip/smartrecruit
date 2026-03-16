#!/usr/bin/env python
"""Simple demo test without menu"""

import os
import sys
from dotenv import load_dotenv
load_dotenv()

print('='*80)
print('SIMPLE DEMO TEST - Direct API Call')
print('='*80)
print()

try:
    # Test data
    candidate_name = 'John Software Engineer'
    candidate_role = 'Senior Software Engineer'
    candidate_exp = 7.5
    candidate_salary = 150000
    candidate_skills = ['Python (expert)', 'FastAPI (advanced)', 'PostgreSQL (advanced)', 'Docker (intermediate)']
    
    print('CANDIDATE PROFILE:')
    print(f'  Name: {candidate_name}')
    print(f'  Experience: {candidate_exp} years')
    print(f'  Skills: {", ".join(candidate_skills)}')
    
    print()
    print('JOB REQUIREMENT:')
    job_title = 'Senior Backend Developer'
    job_company = 'InnovateCorp Inc'
    job_skills = ['Python', 'FastAPI', 'PostgreSQL', 'Docker', 'AWS']
    print(f'  Title: {job_title}')
    print(f'  Company: {job_company}')
    print(f'  Required Skills: {", ".join(job_skills)}')
    
    print()
    print('ANALYZING WITH OpenAI GPT-4o...')
    print('-'*80)
    
    # Build prompt
    prompt = f"""You are an expert recruiter. Analyze this candidate-job match:

CANDIDATE:
- Name: {candidate_name}
- Role: {candidate_role}
- Experience: {candidate_exp} years
- Skills: {', '.join(candidate_skills)}

JOB OPENING:
- Title: {job_title}
- Company: {job_company}
- Required Skills: {', '.join(job_skills)}

Provide: 1) Match score, 2) Strengths, 3) Gaps, 4) Recommendation"""
    
    # Direct API call with httpx only
    import httpx
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print('[ERROR] No OPENAI_API_KEY')
        sys.exit(1)
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    data = {
        'model': 'gpt-4o',
        'messages': [
            {'role': 'system', 'content': 'You are an expert recruiter.'},
            {'role': 'user', 'content': prompt}
        ],
        'max_tokens': 500,
        'temperature': 0.7
    }
    
    print('[Calling OpenAI API...]')
    response = httpx.post(
        'https://api.openai.com/v1/chat/completions',
        headers=headers,
        json=data,
        timeout=30.0
    )
    
    print()
    if response.status_code == 200:
        result = response.json()
        analysis = result['choices'][0]['message']['content']
        print('AI ANALYSIS:')
        print('-'*80)
        print(analysis)
        print()
    else:
        print(f'[ERROR] Status {response.status_code}')
        print(response.text[:200])
        sys.exit(1)
    
    print('='*80)
    print('SUCCESS!')
    print('='*80)
    
except Exception as e:
    import traceback
    print()
    print('[ERROR]')
    traceback.print_exc()
    sys.exit(1)

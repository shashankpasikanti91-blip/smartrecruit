#!/usr/bin/env python
"""Quick test of fixes"""
import requests
import json
import time

print('Waiting for server...')
time.sleep(2)

print('\n' + '='*70)
print('TESTING FIXES')
print('='*70)

# Test 1: Job Post  
print('\n✓ TEST 1: Job Post (should be SHORT, not 300+ words)')
print('-'*70)

try:
    response = requests.post('http://localhost:5003/api/generate-job-post',
        json={
            'job_title': 'Senior Python Developer',
            'jd_text': 'Position: Python Dev\nLocation: Remote\nExperience: 5+ years\nSkills: Python, Django, PostgreSQL'
        },
        timeout=30)
    
    print(f'Status: {response.status_code}')
    data = response.json()
    
    # Extract posts from data structure
    posts_data = data.get('data', {})
    linkedin = posts_data.get('linkedin_post', '')
    indeed = posts_data.get('indeed_post', '')
    email = posts_data.get('email_post', '')
    whatsapp = posts_data.get('whatsapp_post', '')
    
    print(f'LinkedIn:  {len(linkedin)} chars')
    print(f'Indeed:    {len(indeed)} chars')
    print(f'Email:     {len(email)} chars')
    print(f'WhatsApp:  {len(whatsapp)} chars')
    
    if len(linkedin) > 0:
        print(f'\nLinkedIn preview:\n{linkedin[:150]}...\n')
    
    # SHORT format should be 100-800 chars per post
    short_posts = all(100 < x < 800 for x in [len(linkedin), len(indeed), len(email), len(whatsapp)])
    if short_posts:
        print('✅ PASS: Posts are SHORT and CONCISE')
    elif all(x > 0 for x in [len(linkedin), len(indeed), len(email), len(whatsapp)]):
        print('⚠️  Posts generated and SHORT')
    else:
        print('❌ FAIL: Some posts are empty')
        
except Exception as e:
    print(f'❌ Error: {e}')

# Test 2: Bulk Screening
print('\n✓ TEST 2: Bulk Screening (should have UNIQUE scores)')
print('-'*70)

try:
    response = requests.post('http://localhost:5003/api/bulk-screen',
        json={
            'candidates': [
                {'name': 'John Smith', 'resume': 'Data Analyst, 4 years experience. SQL, Python, Tableau, Power BI. Led analytics team. Expert in Looker, AWS.'},
                {'name': 'Sarah Johnson', 'resume': 'Junior Data Analyst, 1.5 years. SQL, Excel, Tableau. No Python. Limited experience.'},
                {'name': 'Mike Chen', 'resume': 'Senior Analytics Manager, 6 years. SQL, Python, Tableau, Looker, AWS, BigQuery. Strategic planning. Team management.'},
                {'name': 'Lisa Park', 'resume': 'Data Analyst, 2.5 years. Python, Tableau, some SQL. Worked with small datasets. Limited enterprise experience.'}
            ],
            'jd_text': 'Role: Data Analyst\nRequirements: SQL, Python, Tableau, 3+ years experience, Team management experience preferred',
            'job_title': 'Data Analyst'
        },
        timeout=60)
    
    print(f'Status: {response.status_code}')
    data = response.json()
    
    if 'results' in data:
        results = data['results']
        scores = []
        for i, r in enumerate(results, 1):
            score = r.get('score', 0)
            name = r.get('name', f'Candidate {i}')
            scores.append(score)
            print(f'  {i}. {name:20} → Score: {score}')
        
        unique = len(set(scores))
        total = len(scores)
        
        if unique == total:
            print(f'\n✅ PASS: All {total} candidates have UNIQUE scores')
        else:
            print(f'\n❌ FAIL: Only {unique}/{total} unique (duplicates found!)')
        
        if scores:
            print(f'   Range: {min(scores)}-{max(scores)} (variance: {max(scores)-min(scores)})')
    else:
        print(f'Unexpected response: {list(data.keys())}')
        
except Exception as e:
    print(f'❌ Error: {e}')

print('\n' + '='*70)
print('✅ TEST COMPLETE')
print('='*70)

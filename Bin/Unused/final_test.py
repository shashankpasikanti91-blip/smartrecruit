import requests, time, sys

BASE = 'http://localhost:5000'

# Test 1: Job Posts
print('[1] JOB POSTS - All 4 Platforms')
try:
    r = requests.post(f'{BASE}/api/job-posts', json={'position': 'Python Dev', 'description': 'ML expert'}, timeout=30)
    d = r.json()['data']
    for p in ['linkedin', 'indeed', 'email', 'whatsapp']:
        sz = len(d.get(p, ''))
        print(f'    {p}: {sz} chars')
except Exception as e:
    print(f'    ERROR: {e}')

# Test 2: Unique Messages
print()
print('[2] MESSAGES - Should be Different')
try:
    r1 = requests.post(f'{BASE}/api/generate-message', json={'message_type': 'interview_invite', 'recipient': 'Alice', 'job_title': 'Dev', 'context': 'great'}, timeout=30)
    m1 = r1.json()['data']['message']
    time.sleep(0.3)
    r2 = requests.post(f'{BASE}/api/generate-message', json={'message_type': 'interview_invite', 'recipient': 'Bob', 'job_title': 'Dev', 'context': 'excellent'}, timeout=30)
    m2 = r2.json()['data']['message']
    print(f'    Msg1: {len(m1)} chars')
    print(f'    Msg2: {len(m2)} chars')
    print(f'    Different: {m1 != m2}')
except Exception as e:
    print(f'    ERROR: {e}')

print()
print('DONE')

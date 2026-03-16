import requests, json, time

time.sleep(3)

print('[TEST 1] Job Posts - Structure + Variation Check')
for i in range(1, 3):
    resp = requests.post('http://localhost:5000/api/generate-job-post', 
        json={'position': 'Python Developer', 'description': 'We need Python expert for ML projects'}, 
        timeout=30)
    data = resp.json()
    posts = data.get('data', {})
    ln = len(posts.get('linkedin', ''))
    ind = len(posts.get('indeed', ''))
    em = len(posts.get('email', ''))
    wh = len(posts.get('whatsapp', ''))
    print(f'Run {i}: linkedin={ln} indeed={ind} email={em} whatsapp={wh}')

print('\n[TEST 2] Messages - Context/Variation Check')
for i in range(1, 3):
    resp = requests.post('http://localhost:5000/api/generate-message', 
        json={'message_type': 'interview_invite', 'recipient': f'Candidate{i}', 'job_title': 'Senior Developer', 'context': f'Scenario {i}'}, 
        timeout=30)
    data = resp.json()
    msg = data.get('data', {}).get('output', '')
    print(f'Run {i}: {len(msg)} chars - {msg[:60]}...')

print('\n[DONE] All tests complete')

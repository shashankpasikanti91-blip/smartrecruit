# n8n Quick Start - 15 Minutes

## Step 1: Start Services (3 Terminal Windows)

### Terminal 1 - Recruitment App
```bash
cd recruitment_ai_system
python run_simple.py
```

### Terminal 2 - Webhook Server
```bash
cd recruitment_ai_system
pip install fastapi uvicorn
python n8n_webhook_receiver.py
```

Expected output:
```
================================================================================
RECRUITMENT AI - n8n WEBHOOK BRIDGE
================================================================================

Starting webhook server on http://localhost:8000
```

### Terminal 3 - n8n
```bash
n8n
```

Expected output:
```
n8n ready on http://localhost:5678
```

---

## Step 2: Access n8n Dashboard

1. Open browser: http://localhost:5678
2. Create account (email/password)
3. Click "Create Workflow"

---

## Step 3: Create Screening Workflow (5 min)

### Build this workflow:

```
[Webhook Trigger] → [HTTP Request] → [If Score > 70] → [Email Send]
                                           ↓
                                     [Email Rejection]
```

### Detailed Steps:

**1. Add Webhook Trigger Node**
- Click "+", search "Webhook"
- Method: POST
- Path: `screen`
- Click "Test Webhook" and copy URL

**2. Add HTTP Request Node**
- Click "+" → "HTTP Request"
- Method: POST
- URL: `http://localhost:8000/webhook/screen-candidate`
- Body:
  ```json
  {
    "candidate_name": "{{ $json.name }}",
    "candidate_resume": "{{ $json.resume }}",
    "job_title": "{{ $json.job_title }}",
    "job_description": "{{ $json.jd }}"
  }
  ```
- Headers:
  ```
  Content-Type: application/json
  ```

**3. Add If/Condition Node**
- Click "+" → "If"
- Condition 1: `analysis` contains "GOOD MATCH"
- If TRUE: High score path
- If FALSE: Low score path

**4. Add Email Nodes (High Score)**
- Click "+" on TRUE path → "Gmail" or "Email" (depends on your setup)
- To: `{{ $json.email }}`
- Subject: `Interview Invitation - {{ $json.job_title }}`
- Body:
  ```
  Dear {{ $json.candidate_name }},

  Great news! We would like to invite you for an interview for the {{ $json.job_title }} position.

  Your qualifications match our requirements very well. Please confirm your availability for a 30-minute video call.

  Best regards,
  Recruitment Team
  ```

**5. Add Email Node (Low Score)**
- Click "+" on FALSE path → Email
- Subject: `Application Status - {{ $json.job_title }}`
- Body:
  ```
  Dear {{ $json.candidate_name }},

  Thank you for applying for the {{ $json.job_title }} position. After review, we've decided to pursue other candidates.

  Best regards,
  Recruitment Team
  ```

---

## Step 4: Test Workflow

### Option A: Manual Test

1. Click "Test Workflow" in top right
2. Fill test data:
   ```json
   {
     "name": "John Doe",
     "email": "john@test.com",
     "resume": "Senior Python developer with 7 years experience in FastAPI and PostgreSQL...",
     "job_title": "Senior Backend Developer",
     "jd": "We need an experienced backend developer with Python, FastAPI, PostgreSQL skills..."
   }
   ```
3. Click "Execute"
4. Watch it process in the workflow

### Option B: Webhook Test

Get webhook URL from trigger node, then:

```bash
curl -X POST http://localhost:5678/webhook/YOUR_WEBHOOK_ID \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Jane Smith",
    "email": "jane@test.com",
    "resume": "Full stack developer...",
    "job_title": "Full Stack Developer",
    "jd": "Looking for experienced full stack developer..."
  }'
```

---

## Step 5: Activate Workflow

1. Click "Activate" toggle (top right)
2. Toggle turns green = Workflow is live
3. Workflow will now respond to webhooks

---

## Step 6: Create Message Generation Workflow (3 min)

Similar to above but simpler:

```
[Webhook Trigger] → [HTTP Request to Message API] → [Email Send]
```

### Configure:

**Webhook Path:** `message`

**HTTP Request URL:** `http://localhost:8000/webhook/generate-message`

**Body:**
```json
{
  "message_type": "{{ $json.type }}",
  "recipient_name": "{{ $json.name }}",
  "recipient_email": "{{ $json.email }}",
  "job_title": "{{ $json.job_title }}"
}
```

**Email:**
- To: `{{ $json.email }}`
- Subject: `{{ $json.subject }}`
- Body: `{{ $json.message }}`

---

## Step 7: Test Complete Integration

### Test Screening + Email:

```bash
# Terminal 4 - Send test request
curl -X POST http://localhost:5678/webhook/YOUR_SCREENING_WEBHOOK_ID \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Alice Johnson",
    "email": "alice@example.com",
    "resume": "Software Engineer with 8 years experience in Python, Django, PostgreSQL, Docker, AWS...",
    "job_title": "Senior Backend Engineer",
    "jd": "Seeking senior backend developer. Required: Python, FastAPI, PostgreSQL, Docker. Nice to have: AWS, Kubernetes"
  }'
```

**What happens:**
1. ✅ n8n receives request
2. ✅ Sends to Python webhook server
3. ✅ Python calls OpenAI GPT-4 mini
4. ✅ AI analyzes candidate
5. ✅ n8n receives analysis
6. ✅ If score > 70: Sends interview email
7. ✅ If score < 70: Sends rejection email

---

## Advanced: Add Slack Notification

1. Create Slack workspace/channel if needed
2. Get Slack webhook URL
3. In n8n workflow, add "Slack" node after Email
4. Configure:
   - URL: Your Slack webhook
   - Message:
     ```
     🎯 Candidate Screening Complete
     Name: {{ $json.candidate_name }}
     Score: {{ $json.analysis }}
     Status: {{ $json.status }}
     ```

---

## Advanced: Add Database Logging

1. In your workflow, add "PostgreSQL" node before sending email
2. Configure with Supabase credentials
3. Execute SQL:
   ```sql
   INSERT INTO screening_results (candidate_name, analysis, status)
   VALUES ('{{ $json.candidate_name }}', '{{ $json.analysis }}', 'processed')
   ```

---

## Troubleshooting

### Webhook not working?
- Check n8n is running and workflow is activated
- Copy full webhook URL from trigger node
- Test with curl first

### Email not sending?
- Configure Gmail/Email credentials in n8n
- Check spam folder
- Use test email addresses

### Python webhook returning errors?
- Check `python n8n_webhook_receiver.py` is running
- Verify OpenAI API key in .env
- Test health: `curl http://localhost:8000/webhook/health`

---

## Commands Reference

**Webhook URL Pattern:**
```
http://localhost:5678/webhook/<workflow_id>
```

**Health Check:**
```bash
curl http://localhost:8000/webhook/health
```

**Test Screening:**
```bash
curl -X POST http://localhost:8000/webhook/screen-candidate \
  -H "Content-Type: application/json" \
  -d '{"candidate_name":"Test","candidate_resume":"...","job_title":"...","job_description":"..."}'
```

**Test Message:**
```bash
curl -X POST http://localhost:8000/webhook/generate-message \
  -H "Content-Type: application/json" \
  -d '{"message_type":"interview_invite","recipient_name":"John","recipient_email":"john@test.com","job_title":"Developer"}'
```

---

## Next Steps

1. ✅ Test workflows with sample data
2. Create bulk import workflow (upload CSV of candidates)
3. Add analytics dashboard in n8n
4. Setup scheduled daily screening jobs
5. Configure error notifications
6. Deploy to production server

---

**Support:**
- n8n Docs: https://docs.n8n.io
- Our Python Bridge: `n8n_webhook_receiver.py`
- Issues? Check logs in Terminal 2 & 3

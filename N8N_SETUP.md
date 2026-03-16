# n8n Integration Guide - Complete Setup

## Phase 1: Verify n8n is Running

### Check if n8n is installed:
```bash
npm list -g n8n
```

### If not installed:
```bash
npm install -g n8n
```

### Start n8n:
```bash
n8n
```

### Access Dashboard:
- Open browser: http://localhost:5678
- Create account and login

---

## Phase 2: Get n8n API Key

1. In n8n dashboard, click **Settings** (gear icon, bottom left)
2. Click **API Keys**
3. Click **Create an API Key**
4. Copy the key and save to `.env`:

```bash
# In .env file, add:
N8N_BASE_URL=http://localhost:5678
N8N_API_KEY=your_api_key_here
```

---

## Phase 3: Create Python-to-n8n Bridge Script

Create file: `n8n_webhook_receiver.py`

```python
#!/usr/bin/env python
"""Webhook receiver for n8n triggers"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx
import os
from dotenv import load_dotenv
import json

load_dotenv()

app = FastAPI(title="Recruitment AI - n8n Bridge")

# Enable CORS for n8n
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/webhook/screen-candidate")
async def webhook_screen_candidate(data: dict):
    """
    Webhook endpoint for candidate screening
    
    Expected data:
    {
        "candidate_name": "John Doe",
        "candidate_resume": "resume text...",
        "job_title": "Senior Developer",
        "job_description": "jd text..."
    }
    """
    try:
        candidate_name = data.get("candidate_name", "Unknown")
        resume = data.get("candidate_resume", "")
        job_title = data.get("job_title", "")
        jd = data.get("job_description", "")
        
        if not resume or not jd:
            raise HTTPException(status_code=400, detail="Missing resume or JD")
        
        # Call OpenAI API directly
        import httpx
        api_key = os.getenv("OPENAI_API_KEY")
        
        prompt = f"""You are an expert recruiter. Analyze this candidate-job match:

CANDIDATE RESUME:
{resume}

JOB DESCRIPTION:
{jd}

Provide:
1. Match score (0-100)
2. Key strengths (2-3 bullets)
3. Skill gaps (2-3 bullets)
4. Recommendation (STRONG MATCH / GOOD MATCH / POSSIBLE / POOR MATCH)

Format as JSON."""
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        response = httpx.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json={
                "model": "gpt-4-mini",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 500
            },
            timeout=30.0
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        
        result = response.json()
        analysis = result["choices"][0]["message"]["content"]
        
        return {
            "success": True,
            "candidate_name": candidate_name,
            "analysis": analysis,
            "timestamp": str(__import__('datetime').datetime.now())
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/webhook/generate-message")
async def webhook_generate_message(data: dict):
    """
    Webhook endpoint for message generation
    
    Expected data:
    {
        "message_type": "interview_invite",  # or "rejection", "offer", etc
        "recipient_name": "John",
        "recipient_email": "john@example.com",
        "job_title": "Senior Developer",
        "context": {}
    }
    """
    try:
        msg_type = data.get("message_type", "interview_invite")
        recipient_name = data.get("recipient_name", "")
        job_title = data.get("job_title", "")
        
        templates = {
            "interview_invite": f"""Dear {recipient_name},

We are pleased to invite you for an interview for the {job_title} position at our company.

Please let us know your availability for a 30-minute video interview.

Best regards,
Recruitment Team""",
            
            "rejection": f"""Dear {recipient_name},

Thank you for your interest in the {job_title} position. After careful review of your application, we have decided to move forward with other candidates at this time.

We appreciate your time and effort.

Best regards,
Recruitment Team""",
            
            "offer": f"""Dear {recipient_name},

Congratulations! We are pleased to offer you the {job_title} position.

Please review the attached offer letter and let us know your acceptance.

Best regards,
Recruitment Team"""
        }
        
        message = templates.get(msg_type, templates["interview_invite"])
        
        return {
            "success": True,
            "message_type": msg_type,
            "recipient": recipient_name,
            "email": data.get("recipient_email", ""),
            "message": message,
            "subject": f"{msg_type.title().replace('_', ' ')} - {job_title}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/webhook/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "Recruitment AI - n8n Bridge",
        "timestamp": str(__import__('datetime').datetime.now())
    }

if __name__ == "__main__":
    import uvicorn
    print("Starting n8n Bridge on http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### Install dependencies:
```bash
pip install fastapi uvicorn httpx
```

### Run webhook server:
```bash
python n8n_webhook_receiver.py
```

Server will run on: `http://localhost:8000`

---

## Phase 4: Create n8n Workflows

### Workflow 1: Candidate Screening

**In n8n Dashboard:**

1. **Create New Workflow** → Click "+" button
2. **Add nodes in this order:**

   **Node 1: Webhook Trigger**
   - Click "+" → Search "Webhook"
   - Method: POST
   - URL: `/screen-candidate`
   - Authentication: None
   - Save

   **Node 2: HTTP Request**
   - Click "+" → Search "HTTP Request"
   - Method: POST
   - URL: `http://localhost:8000/webhook/screen-candidate`
   - Send Body: `{ "candidate_name": "{{ $json.name }}", "candidate_resume": "{{ $json.resume }}", "job_title": "{{ $json.job_title }}", "job_description": "{{ $json.jd }}" }`
   - Headers: `Content-Type: application/json`
   - Send

   **Node 3: Condition (Score Check)**
   - Click "+" → Search "If"
   - Condition: `{{ $json.analysis }}` contains "9" (high score)
   - Add condition

   **Node 4a: Send Email (If High Score)**
   - Click "+" → Search "Gmail" or "Email" (depending on your setup)
   - To: `{{ $json.email }}`
   - Subject: `Interview Invitation - {{ $json.job_title }}`
   - Body: `Hello {{ $json.name }}, we'd like to invite you...`

   **Node 4b: Send Email (If Low Score)**
   - Similar to above but with rejection message

3. **Activate** workflow (toggle in top right)

---

### Workflow 2: Auto Message Generation

1. **Create New Workflow**
2. **Webhook Trigger Node**
   - URL: `/generate-message`

3. **HTTP Request Node**
   - POST to `http://localhost:8000/webhook/generate-message`
   - Pass message type, recipient, job title

4. **Email Node**
   - Send generated message

5. **Slack Node** (Optional)
   - Post to channel: `#recruitment`
   - Message: `Message sent to {{ $json.recipient }}`

---

## Phase 5: Test Webhook Integration

### Test Screening Webhook:
```bash
curl -X POST http://localhost:8000/webhook/screen-candidate \
  -H "Content-Type: application/json" \
  -d '{
    "candidate_name": "John Doe",
    "candidate_resume": "Senior Python developer with 7 years experience. Skilled in FastAPI, PostgreSQL, Docker...",
    "job_title": "Senior Backend Developer",
    "job_description": "Looking for experienced backend developer. Must know Python, FastAPI, PostgreSQL, Docker. AWS a plus."
  }'
```

### Expected Response:
```json
{
  "success": true,
  "candidate_name": "John Doe",
  "analysis": "Match score: 85/100...",
  "timestamp": "2026-02-05T..."
}
```

### Test Message Webhook:
```bash
curl -X POST http://localhost:8000/webhook/generate-message \
  -H "Content-Type: application/json" \
  -d '{
    "message_type": "interview_invite",
    "recipient_name": "John",
    "recipient_email": "john@example.com",
    "job_title": "Senior Developer"
  }'
```

---

## Phase 6: Trigger from n8n

### Option A: Manual Trigger (Testing)
1. Open any workflow
2. Click **"Execute Workflow"** button
3. Results show in bottom panel

### Option B: Webhook Trigger
1. External apps POST to: `http://localhost:5678/webhook/YOUR_WEBHOOK_ID`
2. Find webhook ID in workflow → Trigger node → URL

### Option C: Schedule Trigger
1. Add **"Schedule"** node at start
2. Set frequency: Daily, Weekly, Monthly
3. Workflow runs automatically

---

## Phase 7: Production Checklist

- [ ] n8n running on dedicated server/VM
- [ ] Python webhook server running on port 8000
- [ ] Both services behind reverse proxy (nginx)
- [ ] SSL certificates configured
- [ ] Error notifications setup (Slack/Email)
- [ ] Logs stored (both services)
- [ ] Database backups scheduled
- [ ] Rate limiting configured
- [ ] API keys rotated monthly

---

## Common Issues & Solutions

### Issue: Webhook not triggering
**Solution:**
1. Check n8n is running: `curl http://localhost:5678`
2. Check workflow is activated (green toggle)
3. Verify webhook URL in trigger node
4. Check n8n logs: n8n console output

### Issue: Python webhook returns 500 error
**Solution:**
1. Check OpenAI API key in .env
2. Test API directly: `curl -X GET https://api.openai.com/v1/models -H "Authorization: Bearer YOUR_KEY"`
3. Check Python server logs

### Issue: Email not sending from n8n
**Solution:**
1. Configure email service (Gmail, SendGrid, etc)
2. Add credentials in n8n Email node
3. Test email node separately

### Issue: Connection between n8n and Python refused
**Solution:**
1. Verify Python server is running: `curl http://localhost:8000/webhook/health`
2. Check firewall allows port 8000
3. Verify URL in n8n HTTP node is `http://localhost:8000` (not `127.0.0.1`)

---

## Next Steps After Setup

1. **Test full pipeline**: Candidate → Screening → Email
2. **Add Slack notifications**: Alert team of strong matches
3. **Setup database logging**: Store all screening results
4. **Create dashboard**: Track metrics (total screened, pass rate, etc)
5. **Scale up**: Process bulk candidate files automatically

---

## File Structure After Setup

```
recruitment_ai_system/
├── run_simple.py              # Main app
├── n8n_webhook_receiver.py    # Webhook server
├── .env                        # Credentials
├── logs/
│   └── recruitment_ai.log
└── n8n_workflows/
    ├── screening_workflow.json
    ├── messaging_workflow.json
    └── autoresponse_workflow.json
```

---

**Commands to Keep Running (3 terminals):**

Terminal 1 - Recruitment App:
```bash
cd recruitment_ai_system
python run_simple.py
```

Terminal 2 - Webhook Server:
```bash
cd recruitment_ai_system
python n8n_webhook_receiver.py
```

Terminal 3 - n8n (if local):
```bash
n8n
```

---

**Support Resources:**
- n8n Docs: https://docs.n8n.io
- n8n Community: https://community.n8n.io
- OpenAI API: https://platform.openai.com/docs


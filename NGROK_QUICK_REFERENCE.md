# ngrok Webhook Setup - Quick Reference

## Status: OFFLINE ⚠️

Your ngrok URL is currently offline. Here's how to activate it:

```
https://whirly-unfeeble-liv.ngrok-free.dev/webhook/3cef19ce-26fd-4a20-b861-ae5319e35d57
```

---

## 🚀 QUICK START (5 Minutes)

### Step 1: Start All Services
```powershell
cd "c:\Users\User\Desktop\pydantic\future-projects\Recruitement ATS\recruitment_ai_system"

# Option A: Use the batch file (automatic)
START_SERVICES.bat

# Option B: Manual (3 terminals)
# Terminal 1:
python n8n_webhook_receiver.py

# Terminal 2:
ngrok http 8000

# Terminal 3:
n8n
```

### Step 2: Get Your ngrok URL
When ngrok starts, you'll see:
```
Session Status                online                                             
Account                       <your-account>                                    
Version                        <version>                                        
Region                         us (United States)                               
Latency                        100ms                                            
Web Interface                  http://127.0.0.1:4040                           
Forwarding                     https://xxxx-xxxx-xxxx.ngrok-free.dev -> http://localhost:8000
```

**Copy the Forwarding URL** (e.g., `https://xxxx-xxxx-xxxx.ngrok-free.dev`)

### Step 3: Test Your Webhook
```powershell
python test_ngrok_webhook.py
```

### Step 4: Use in n8n
In n8n workflows, use your ngrok URL:
```
POST https://[YOUR-NGROK-URL]/webhook/screen-candidate
POST https://[YOUR-NGROK-URL]/webhook/generate-message
GET https://[YOUR-NGROK-URL]/webhook/health
```

---

## 📋 Service Ports

| Service | Port | URL |
|---------|------|-----|
| Webhook Server | 8000 | http://localhost:8000 |
| ngrok Tunnel | 4040 | http://localhost:4040 |
| n8n Dashboard | 5678 | http://localhost:5678 |
| OpenAI API | - | https://api.openai.com |
| Supabase | - | Your configured URL |

---

## 🔧 Troubleshooting

### Webhook Server Not Starting
```powershell
# Check if port 8000 is in use
netstat -ano | findstr :8000

# Kill process if needed
taskkill /PID <PID> /F

# Restart server
python n8n_webhook_receiver.py
```

### ngrok Issues
```powershell
# Make sure ngrok is installed
ngrok --version

# Start fresh
ngrok http 8000 --region us
```

### Webhook Still Not Working
```powershell
# 1. Check webhook server logs
python n8n_webhook_receiver.py  # Look for errors

# 2. Test local endpoint first
curl -X GET http://localhost:8000/webhook/health

# 3. Then test through ngrok
curl -X GET https://[YOUR-NGROK-URL]/webhook/health
```

---

## 📝 Webhook Endpoints

### 1. Health Check
```bash
GET /webhook/health

# Response:
{
  "status": "running",
  "openai": "connected",
  "timestamp": "2026-02-05T15:22:40"
}
```

### 2. Candidate Screening
```bash
POST /webhook/screen-candidate

# Request:
{
  "candidate_name": "John Doe",
  "candidate_resume": "7 years Python experience...",
  "job_title": "Senior Backend Engineer",
  "job_description": "Looking for 5+ years Python..."
}

# Response:
{
  "candidate_name": "John Doe",
  "match_score": 85,
  "analysis": "Excellent match...",
  "timestamp": "2026-02-05T15:22:40"
}
```

### 3. Generate Message
```bash
POST /webhook/generate-message

# Request:
{
  "message_type": "interview_invitation",
  "recipient_name": "John Doe",
  "recipient_email": "john@example.com",
  "job_title": "Senior Backend Engineer"
}

# Response:
{
  "message_type": "interview_invitation",
  "subject": "Interview Invitation - Senior Backend Engineer",
  "body": "Dear John, We are pleased to invite you...",
  "email": "john@example.com",
  "timestamp": "2026-02-05T15:22:40"
}
```

---

## 🎯 Next Steps

1. ✅ Start services (`START_SERVICES.bat` or manual)
2. ✅ Get ngrok URL from tunnel dashboard
3. ✅ Test webhook (`python test_ngrok_webhook.py`)
4. ✅ Copy ngrok URL to n8n workflows
5. ✅ Create screening workflow in n8n
6. ✅ Test with real candidate data
7. ✅ Activate workflows

---

## 💡 Pro Tips

- **ngrok URL changes** every time you restart → Update n8n workflows
- **Keep tunnels open** - don't close terminal windows
- **Monitor ngrok dashboard** at http://localhost:4040 to see all requests
- **Test locally first** (http://localhost:8000) before using ngrok URL
- **Save successful ngrok URL** for reference if using ngrok pro

---

**Version**: 1.0  
**Date**: February 5, 2026  
**Status**: READY FOR DEPLOYMENT


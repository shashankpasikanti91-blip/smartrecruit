# Webhook Architecture - Clarified

## Current Setup Understanding

```
Your Data
   ↓
┌─────────────────────────────────────────────┐
│ SETUP OPTION 1: Your Local Python Webhook  │
│                                             │
│  Terminal 1: python n8n_webhook_receiver.py│
│              ↓ (port 8000)                  │
│  Terminal 2: ngrok http 8000                │
│              ↓ (generates new URL)          │
│  Terminal 3: n8n                            │
│              ↓ (creates webhooks)           │
│                                             │
│  n8n uses YOUR ngrok URL to call Python    │
└─────────────────────────────────────────────┘
   ↓
AI Screening + Messages
```

---

## 🎯 Action Plan

### Step 1: Start Your Python Webhook Server

**Terminal 1:**
```powershell
cd "c:\Users\User\Desktop\pydantic\future-projects\Recruitement ATS\recruitment_ai_system"
python n8n_webhook_receiver.py
```

Output should show:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Step 2: Tunnel It with ngrok

**Terminal 2:**
```powershell
ngrok http 8000
```

Output will show:
```
Forwarding    https://[NEW-URL].ngrok-free.dev -> http://localhost:8000
```

**⭐ COPY THIS NEW URL ⭐**

### Step 3: Start n8n

**Terminal 3:**
```powershell
n8n
```

Access: http://localhost:5678

### Step 4: Update .env with YOUR Webhook Server URL

```powershell
# Edit .env
# Replace OLD n8n URL with YOUR NEW ngrok URL
```

Example:
```
NGROK_WEBHOOK_URL=https://[YOUR-NEW-URL].ngrok-free.dev/webhook/screen-candidate
```

### Step 5: Test Your Setup

```powershell
python test_ngrok_webhook.py
```

Should return:
```
✓ Health check passed
✓ Screening completed
✓ Message generated
```

---

## 📋 URL Reference

| Type | URL | Purpose |
|------|-----|---------|
| **Your Webhook (Local)** | `http://localhost:8000` | Python server |
| **Your Webhook (Tunneled)** | `https://[NEW].ngrok-free.dev` | n8n calls this |
| **n8n Dashboard** | `http://localhost:5678` | Create workflows |
| **n8n Webhook URL** | `https://whirly-unfeeble-liv.ngrok-free.dev/webhook/3cef19ce...` | (This is THEIR endpoint, not yours) |

---

## ⚠️ Key Point

The URL you provided (`https://whirly-unfeeble-liv.ngrok-free.dev/webhook/3cef19ce...`) is an **n8n INCOMING webhook**.

You need:
1. **YOUR Python server** → tunnel with ngrok → Get new URL
2. **n8n calls your URL** → processes → returns results
3. **Your URL then calls n8n** → completes automation

---

## Ready to Proceed?

**Next step:** Start with Terminal 1 (Python server) and we'll get your new ngrok URL


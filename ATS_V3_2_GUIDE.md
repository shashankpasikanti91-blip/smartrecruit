# Advanced Recruitment ATS v3.0
## Professional All-in-One Applicant Tracking System

**Built with:** Python Flask | Real-time AI Chat | n8n Automation | Modern UI

---

## What's New in v3.0

### ✅ Complete Features
- **📄 Resume + JD File Uploads** (PDF, DOC, DOCX, CSV support)
- **🔍 Single Candidate Screening** with detailed AI analysis  
- **📊 Bulk Candidate Screening** with CSV batch processing
- **📢 Job Post Generation** for LinkedIn, Indeed, Email, WhatsApp
- **✨ AI Writing Assistant** (Rewrite, Paraphrase, Reply)
- **✉️ Message Generation** (Interview, Rejection, Offer, Follow-up)
- **💬 AI Chat Sidebar** for real-time writing assistance
- **📋 Real-Time Activity Logs** with live updates
- **📈 Advanced Analytics** & processing stats

---

## Architecture

```
User Browser (Modern UI)
        ↓
Flask Backend (advanced_app_v3.py)
   - File Processing (PDF/DOC/CSV)
   - Error Handling & Logging
        ↓
n8n Automation Webhook
   - Recruitment Control Panel
   - Resume Screening
   - Job Post Generation
   - AI Writing Agent
        ↓
AI & Database Results
   - OpenAI GPT-4-mini
   - Supabase PostgreSQL
```

---

## Quick Start

### 1. **Install Dependencies**
```bash
pip install -r requirements.txt
```

### 2. **Configure Environment**
Ensure `.env` has:
```
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4-mini
N8N_WEBHOOK_PRODUCTION=https://your-n8n-webhook-url
```

### 3. **Start the App**
```bash
python advanced_app_v3.py
```

### 4. **Open in Browser**
```
http://localhost:5000
```

---

## File Structure

```
recruitment_ai_system/
├── advanced_app_v3.py              # Main Flask app (PRODUCTION)
├── templates/
│   └── advanced_index.html         # Professional UI with all features
├── logs/
│   └── recruitment_ai.log          # Real-time activity logs
├── uploads/                        # Temporary file storage (auto-cleaned)
├── .env                            # Credentials (secure)
└── requirements.txt                # Python dependencies
```

---

## Tabs & Features

### 🎯 Tab 1: Screen Candidates
**Single candidate screening against job description**
- Upload resume (PDF/DOC/DOCX)
- Upload job description (PDF/DOC/DOCX)
- AI evaluates fit, strengths, weaknesses
- Returns screening score & recommendation

### 📊 Tab 2: Bulk Screening
**Process multiple candidates at once**
- Upload CSV with candidate data
- Upload job description
- Screen all candidates automatically
- View stats: Processed, Skipped, Errors
- Download results

### 📢 Tab 3: Create Job Post
**Generate multi-platform job postings**
- Input job title & description
- AI generates posts for:
  - LinkedIn (professional tone)
  - Indeed (detailed format)
  - Email (concise version)
  - WhatsApp (brief message)

### ✉️ Tab 4: Generate Messages
**Create candidate communications**
- Message Types: Interview, Rejection, Offer, Follow-up
- Customizable tones: Professional, Formal, Friendly, Casual
- Auto-personalizes with candidate name & role

### 📋 Tab 5: Activity Logs
**Real-time system monitoring**
- View all API calls and operations
- Color-coded status (Success/Error)
- Auto-refreshes every 10 seconds
- Last 100 log entries visible

### 💬 AI Chat Sidebar
**Always available writing assistant**
- Rewrite text professionally
- Paraphrase for clarity
- Generate replies to messages
- Choose tone & platform
- Instant AI responses

---

## File Upload Support

| Format | Extensions | Use Case |
|--------|-----------|----------|
| **PDF** | .pdf | Resume, Job Description |
| **Word** | .doc, .docx | Resume, Job Description |
| **Text** | .txt | Plain text documents |
| **CSV** | .csv | Bulk candidate data (name, resume columns) |

**Max File Size:** 50MB

**CSV Format Example:**
```
name,resume
John Smith,"Senior React Developer with 5 years experience..."
Jane Doe,"Full stack engineer specializing in Python..."
```

---

## API Endpoints

### File Upload
```
POST /api/upload-file
- Uploads and extracts text from PDF/DOC/DOCX/CSV
- Returns: filename, type, extracted content
```

### Single Screening
```
POST /api/screen-candidate
{
  "candidate_name": "John Smith",
  "resume_text": "...",
  "job_title": "Senior Developer",
  "jd_text": "..."
}
```

### Bulk Screening
```
POST /api/bulk-screen
{
  "candidates": [{"name": "...", "resume": "..."}],
  "job_title": "...",
  "jd_text": "..."
}
```

### Job Post Generation
```
POST /api/generate-job-post
{
  "job_title": "Senior React Developer",
  "jd_text": "..."
}
```

### AI Writing
```
POST /api/ai-write
{
  "text": "...",
  "action": "rewrite|paraphrase|reply",
  "tone": "professional|formal|friendly|casual",
  "platform": "email|whatsapp|linkedin|message"
}
```

### Generate Message
```
POST /api/generate-message
{
  "message_type": "interview|rejection|offer|followup",
  "recipient": "John Smith",
  "job_title": "Senior Developer",
  "tone": "professional"
}
```

### Activity Logs
```
GET /api/logs
- Returns: last 100 log lines, total count
```

---

## Error Handling

All endpoints include:
- ✅ **Try-Catch Blocks** - Graceful error handling
- ✅ **Timeout Protection** - 60-second webhook timeout
- ✅ **File Validation** - Size & format checks
- ✅ **Detailed Logging** - Every action logged with timestamps
- ✅ **User-Friendly Alerts** - Clear error messages in UI

---

## n8n Integration Points

### Workflow 1: Resume Screening
**Input:** Candidate resume + Job description
**Output:** Screening score, fit assessment, recommendations
**n8n Node:** AI Agent with structured output parser

### Workflow 2: Job Post Generation
**Input:** Job description
**Output:** Posts for LinkedIn, Indeed, Email, WhatsApp
**n8n Node:** Job Post AI with multiple formatting templates

### Workflow 3: AI Writing Agent
**Input:** Text + Action + Tone + Platform
**Output:** Rewritten/paraphrased text optimized for platform
**n8n Node:** GPT-4 mini with custom prompts

### Workflow 4: Control Panel
**Input:** Any recruitment task
**Routes to:** Appropriate workflow based on task_type
**Output:** Unified response format

---

## Logging & Debugging

**Log File Location:** `logs/recruitment_ai.log`

**Log Format:**
```
[TIMESTAMP] - [MODULE] - [LEVEL] - [MESSAGE]
2026-02-05 17:25:10,253 - advanced_app_v3 - INFO - [STARTUP] Starting Flask Server
```

**Log Levels:**
- `INFO` - Normal operations (uploads, screening, posts)
- `WARNING` - Missing data, skipped records
- `ERROR` - Processing failures, webhook errors

**Real-Time Viewing:**
- Activity Logs tab in UI (auto-refresh 10s)
- Or: `tail -f logs/recruitment_ai.log`

---

## Performance Metrics

| Operation | Duration | Notes |
|-----------|----------|-------|
| Single Resume Screening | 5-10s | Depends on webhook |
| Bulk Screening (10 candidates) | 45-60s | Parallel would be faster |
| Job Post Generation | 3-5s | All platforms generated |
| AI Writing (message) | 2-3s | Real-time in chat |
| File Upload & Extraction | <1s | PDF extraction included |

---

## Customization Guide

### Add New Message Type
1. Open `templates/advanced_index.html`
2. Find `<select id="message_type">`
3. Add: `<option value="new_type">Custom Message</option>`
4. Type is sent to n8n workflow automatically

### Change Color Scheme
Edit CSS variables in `advanced_index.html`:
```css
:root {
    --primary: #6366f1;        /* Indigo */
    --secondary: #ec4899;      /* Pink */
    --success: #10b981;        /* Green */
    /* ... more colors */
}
```

### Modify File Upload Limits
In `advanced_app_v3.py`:
```python
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB instead of 50MB
```

---

## Troubleshooting

### **App Won't Start**
- Check Python version: `python --version` (3.10+)
- Install deps: `pip install -r requirements.txt`
- Check port 5000 available: `netstat -ano | findstr :5000`

### **File Upload Fails**
- Check file size < 50MB
- Supported format? (PDF, DOC, DOCX, CSV, TXT)
- Temp folder writable? `ls uploads/`

### **n8n Webhook Not Responding**
- Verify webhook URL in `.env`
- Check n8n workflow active & published
- Network connection: `curl [WEBHOOK_URL]`

### **No Logs Appearing**
- Logs go to: `logs/recruitment_ai.log`
- Check terminal for startup messages
- Verify logging permissions

### **Encoding Errors on Windows**
- Solution: Using UTF-8 file handler in logging
- Clear logs if corrupted: `rm logs/recruitment_ai.log`

---

## Security Notes

✅ **Best Practices Implemented:**
- Credentials in `.env` (never hardcoded)
- File uploads to temp folder (auto-cleanup)
- Secure filename handling (malicious names blocked)
- Error messages don't leak sensitive info
- UTF-8 encoding for international characters

⚠️ **For Production:**
- Use environment variables for all secrets
- Enable HTTPS (nginx + SSL)
- Rate limiting on API endpoints
- Database encryption for stored results
- User authentication & authorization

---

## Development & Contribution

### Add New Feature
1. Create endpoint in `advanced_app_v3.py`
2. Add UI in `templates/advanced_index.html`
3. Call webhook to n8n workflow
4. Add logging for debugging
5. Test with curl/Postman

### Testing
```bash
# Health check
curl http://localhost:5000/api/status

# Upload test file
curl -F "file=@resume.pdf" http://localhost:5000/api/upload-file

# View logs
curl http://localhost:5000/api/logs
```

---

## Support & Documentation

- **n8n Workflows:** See `N8N_SETUP.md`
- **Webhook Details:** See `WEBHOOK_ARCHITECTURE.md`
- **API Reference:** See `API_REFERENCE.md`
- **Deployment:** See `DEPLOYMENT.md`

---

## What's Included

| Component | File | Purpose |
|-----------|------|---------|
| Backend | `advanced_app_v3.py` | Flask server + API |
| Frontend | `advanced_index.html` | Modern responsive UI |
| Logging | `logs/` | Real-time activity tracking |
| Config | `.env` | Secure credentials |
| Docs | `README.md` (this file) | Complete guide |

---

## Next Steps

1. ✅ **Start App:** `python advanced_app_v3.py`
2. ✅ **Open Browser:** `http://localhost:5000`
3. ✅ **Upload Resume:** Try the screening feature
4. ✅ **Test Bulk CSV:** Upload multiple candidates
5. ✅ **Try AI Chat:** Use sidebar writing assistant
6. ✅ **Monitor Logs:** Watch activity logs in real-time

---

**Version:** 3.0  
**Release Date:** February 2026  
**Status:** Production Ready  
**License:** Private

---

**Built for professional recruitment teams who want AI-powered screening with modern UI.**

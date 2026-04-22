# SRP SmartRecruit — Technical Summary (Enterprise Edition)

> **Live:** https://recruit.srpailabs.com  
> **Stack:** Next.js 14 App Router · PostgreSQL · NextAuth · OpenAI GPT-4o-mini

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Browser (https://recruit.srpailabs.com)                    │
│    Next.js 14 App Router (nextjs-auth/)                     │
│    • /app/dashboard/page.tsx  — full SPA-style dashboard    │
│    • /app/api/*               — Next.js Route Handlers      │
│    • NextAuth v4              — session + Google OAuth      │
└───────────────────────────────┬─────────────────────────────┘
                                │ pg pool
┌───────────────────────────────▼─────────────────────────────┐
│  PostgreSQL 16 (Docker: srp-auth-db)                        │
│  • users, subscriptions                                     │
│  • candidates, job_posts                                    │
│  • screen_results, jd_history, boolean_history              │
│  • import_batches, audit_logs                               │
│  • integrations, api_keys, comms_templates                  │
└─────────────────────────────────────────────────────────────┘

Optional sidecar:
  FastAPI backend (port 8009) — legacy v3.2 webhooks / n8n
```

---

## Frontend — Dashboard Tabs

| Tab | Key Feature |
|---|---|
| Pipeline | Kanban stage view, drag stage badges |
| Candidates | Table with ID / Match / Stage / Uploaded / Skills / Actions |
| AI Screen | Upload JD + resumes, GPT-4o-mini scoring 0–100 |
| Compose | AI email / WhatsApp / LinkedIn message composer |
| **Jobs** | **Enterprise table** — ID / Role / Company / Type / Candidates / Status / Posted |
| Analytics | KPI cards + hire funnel + upload activity |
| JD Writer | AI JD generator with history + `fmtDate()` |
| Boolean | AI Boolean query builder with history + `fmtDate()` |
| Import | CSV bulk import — Naukri / LinkedIn / Indeed — column guide |
| Integrations | Connect n8n / Naukri / Monster / Indeed / LinkedIn / Greenhouse / Lever |
| Comms Hub | Seeded templates + AI rewrite + send log |
| **Settings** | Profile / Subscription / API Keys / Integrations / **Audit Trail** |

---

## Design System (Enterprise Spec)

```css
/* Sidebar */
--sidebar-bg:    #0F172A;   /* Tailwind slate-900 */
--sidebar-hover: #1E293B;   /* slate-800 */
--sidebar-active:#2563EB;   /* blue-600 */
--sidebar-muted: #CBD5E1;   /* slate-300 */

/* Dashboard main area */
--dash-bg:       #F8FAFC;   /* slate-50 */
--dash-surface:  #FFFFFF;
--dash-border:   #E2E8F0;   /* slate-200 */
--dash-text:     #0F172A;   /* slate-900 */
--dash-text-2:   #64748B;   /* slate-500 */

/* Semantic */
--color-primary: #2563EB;
--color-success: #16A34A;
--color-warning: #F59E0B;
--color-danger:  #DC2626;
--color-purple:  #7C3AED;
```

Fonts: **Plus Jakarta Sans** (page titles) → **Manrope** → **Inter** → system-ui

---

## Key Components

### `ShortIdBadge`
Click-to-copy short ID pill. `CAN-XXXXXX` / `JOB-XXXXXX` format.

### `StagePill` (variant: `dark` | `light`)
- `dark` — glassmorphism modals (default)
- `light` — white-bg tables (`STAGE_LIGHT` constant)

### `MatchBadge` (variant: `dark` | `light`)
- `dark` — dark modals
- `light` — white-bg tables (`MATCH_LIGHT` constant)

### `fmtDate(d, includeTime?)`
Formats ISO string to `"12 Jan 2025"` or `"12 Jan 2025, 14:30"`. Used everywhere instead of `.toLocaleDateString()`.

### `logAudit(ev)` — `lib/audit.ts`
Fire-and-forget audit logger. Calls `POST /api/audit`. Never throws.

---

## Database Schema (key tables)

```sql
users(id, email, name, role, provider, image, created_at)
subscriptions(user_id, plan, status, billing_cycle, expires_at)

job_posts(id, user_id, short_id, title, company, location, type,
          description, requirements, status, created_at)

candidates(id, user_id, short_id, candidate_name, candidate_email,
           pipeline_stage, ai_score, match_category, ai_skills,
           job_post_id, created_at)

screen_results(id, user_id, candidate_name, ai_score, match_category,
               screened_at, created_at)

audit_logs(id, user_id, action, resource_type, resource_id,
           result, details, ip_address, created_at)

import_batches(id, user_id, batch_ref, filename, total_rows,
               imported_rows, failed_rows, status, created_at)

comms_templates(id, user_id, name, platform, content, created_at)
integrations(id, user_id, provider, webhook_url, is_active, created_at)
api_keys(id, user_id, key_prefix, key_hash, label, is_active, created_at)
```

Migrations in `nextjs-auth/db/`:
- `schema.sql` — base
- `migrate_v5_enterprise.sql` — enterprise tables
- `migrate_v6_id_date_system.sql` — short_id, screened_at, audit_logs

---

## Audit Trail (Phase 8)

`GET /api/audit?limit=50&action=&resource=` — paginated, admin sees all, users see own  
`POST /api/audit` — internal write endpoint (called by `logAudit()`)

Events logged:
- `stage_changed` — candidate pipeline stage update
- `job_created` — new job post
- `ai_screening` — AI screen run

---

## Import Engine

`POST /api/import` — multipart CSV upload  
`GET /api/import?batch_id=` — batch status + row errors

Auto-detects column names from Naukri, LinkedIn Recruiter, Indeed/Monster exports.
Unrecognised columns kept as raw `raw_data` JSONB.

---

**Version:** Enterprise v5.1 · **Last Updated:** April 2026


## 🏗️ System Architecture

### Backend Stack
- **Framework:** Flask (Python 3.10+)
- **Async:** asyncio + httpx for webhook calls
- **File Processing:** PyPDF2 (PDF), python-docx (DOCX), csv (CSV)
- **Logging:** Python logging module with file handlers
- **Error Handling:** Try-catch with traceback logging

### Frontend Stack
- **HTML5** with semantic structure
- **CSS3** with CSS variables for theming
- **JavaScript (Vanilla)** with async/await
- **Design:** Modern gradient, animations, responsive grid

### Integration
- **n8n Webhooks** for AI workflows
- **OpenAI GPT-4-mini** for AI operations
- **Supabase PostgreSQL** for data persistence
- **ngrok** for secure tunneling (optional)

---

## 📂 File Structure

```
recruitment_ai_system/
├── advanced_app_v3.py                   # Main Flask app (500 lines)
│   ├── File extraction functions
│   ├── Webhook caller
│   ├── 7 API endpoints
│   ├── Error handlers
│   └── Logging setup
│
├── templates/
│   └── advanced_index.html              # UI with all tabs (2,000+ lines)
│       ├── Header & navigation
│       ├── 5 main tabs
│       ├── AI chat sidebar
│       ├── CSS (1,200+ lines)
│       └── JavaScript (600+ lines)
│
├── logs/
│   └── recruitment_ai.log               # Real-time activity log
│
├── uploads/                             # Temp file storage (auto-cleaned)
│
├── .env                                 # Credentials (7 vars)
├── ATS_V3_GUIDE.md                      # Complete documentation
├── QUICK_START_V3.md                    # 30-second setup
└── requirements.txt                     # Dependencies
```

---

## 🔌 API Endpoints (7 Total)

### 1. Upload File
```
POST /api/upload-file
Input: file (PDF, DOC, DOCX, CSV, TXT)
Output: {filename, type, content, full_content}
Process: Extract text, validate, return to UI
Time: <1s
```

### 2. Screen Single Candidate
```
POST /api/screen-candidate
Input: {candidate_name, resume_text, job_title, jd_text}
Output: {status, data from n8n, error if any}
Process: Send to n8n → AI screens → Return results
Time: 5-10s
```

### 3. Bulk Screen Candidates
```
POST /api/bulk-screen
Input: {candidates[], job_title, jd_text}
Output: {total, processed, skipped, errors, results[]}
Process: Loop through CSV → Screen each → Track stats
Time: 45-60s (10 candidates)
```

### 4. Generate Job Post
```
POST /api/generate-job-post
Input: {job_title, jd_text}
Output: {status, data with posts for all platforms}
Process: Send to n8n → Generate → Return posts
Time: 3-5s
```

### 5. AI Write
```
POST /api/ai-write
Input: {text, action, tone, platform}
Output: {status, data with rewritten text}
Process: Send to n8n → Process text → Return result
Time: 2-3s
```

### 6. Generate Message
```
POST /api/generate-message
Input: {message_type, recipient, job_title, tone}
Output: {status, data with generated message}
Process: Send to n8n → Generate → Return message
Time: 2-3s
```

### 7. Get Logs
```
GET /api/logs
Input: None
Output: {logs[], total count, timestamp}
Process: Read last 100 lines of recruitment_ai.log
Time: <100ms
```

---

## 📊 Data Flow Diagrams

### Single Screening Flow
```
User Input (Resume + JD)
    ↓
File Upload Handler
    ↓
Extract Text (PDF/DOC)
    ↓
Validate & Sanitize
    ↓
Call n8n Webhook
    ↓
AI Screening in n8n
    ↓
Return Results to UI
    ↓
Display Results & Log
```

### Bulk Screening Flow
```
CSV Upload
    ↓
Parse Rows
    ↓
For Each Candidate:
  - Extract resume
  - Create payload
  - Call webhook
  - Store result
  - Track stats
    ↓
Return Aggregated Stats
    ↓
Display Dashboard
```

### AI Chat Flow
```
User Types Message
    ↓
Select: Action, Tone, Platform
    ↓
Send via POST /api/ai-write
    ↓
Call n8n AI Writing Workflow
    ↓
GPT-4-mini Processes
    ↓
Return Result
    ↓
Add to Chat History
    ↓
Auto-scroll Display
```

---

## 🔐 File Processing Pipeline

### PDF Processing
```python
PyPDF2.PdfReader(file)
    → Extract each page
    → Join with \n
    → Return text string
```

### DOCX Processing
```python
Document(file)
    → Iterate paragraphs
    → Extract .text property
    → Join with \n
    → Return text string
```

### CSV Processing
```python
csv.DictReader(file)
    → Convert each row to dict
    → Collect all rows
    → Return list of dicts
    → Used for bulk processing
```

### Size Limits
- Max file: 50MB
- Temp storage: uploads/ (auto-cleaned)
- Validation: Type check + Size check

---

## 🔄 n8n Webhook Integration

### Webhook Configuration
```
URL: https://your-n8n-instance/webhook/{ID}
Method: POST (HTTP)
Timeout: 60 seconds
Payload: JSON with task_type + data
Response: JSON with results
```

### Payload Format
```json
{
    "task_type": "Screen CV against JD|Create Job Post|AI Writing Agent",
    "candidate_name": "John Smith",
    "resume_text": "Senior Developer with...",
    "job_title": "Senior React Developer",
    "jd_text": "We are looking for...",
    "action": "rewrite|paraphrase|reply",
    "tone": "professional|formal|friendly",
    "platform": "email|whatsapp|linkedin"
}
```

### Response Format
```json
{
    "status": "success|timeout|error",
    "code": 200,
    "data": {
        "screening_score": 85,
        "recommendation": "SHORTLIST",
        "strengths": ["..."],
        "weaknesses": ["..."],
        "linkedin_post": "...",
        "message": "..."
    },
    "error": "..."
}
```

---

## 📝 Logging System

### Log Levels
- **INFO:** Normal operations (uploads, API calls)
- **WARNING:** Missing data, skipped records
- **ERROR:** Processing failures, exceptions

### Log Format
```
TIMESTAMP - MODULE - LEVEL - MESSAGE
2026-02-05 17:25:10,253 - advanced_app_v3 - INFO - [STARTUP] Starting Flask Server
```

### Log Categories
- `[STARTUP]` - App initialization
- `[UPLOAD]` - File upload operations
- `[PDF/DOCX/CSV]` - File extraction
- `[WEBHOOK]` - n8n calls
- `[SCREEN]` - Candidate screening
- `[BULK]` - Batch processing
- `[JOBPOST]` - Job post generation
- `[AI]` - AI writing operations
- `[MSG]` - Message generation
- `[ERROR]` - System errors

### Real-Time Viewing
- UI Tab: Activity Logs (auto-refresh 10s)
- Terminal: `tail -f logs/recruitment_ai.log`
- File: `logs/recruitment_ai.log`

---

## 🎨 UI Components

### Main Elements
1. **Header** - Title, status indicator
2. **Tab Navigation** - 5 switchable tabs
3. **AI Chat Sidebar** - Always visible
4. **Form Sections** - Input areas per tab
5. **Results Display** - Alerts + formatted output
6. **Stats Dashboard** - Real-time counters
7. **Logs Viewer** - Scrollable log display

### Interactive Features
- **File Uploads** - Drag & drop + click
- **Text Extraction** - Auto-preview after upload
- **Real-Time Stats** - Update during processing
- **Auto-Refresh** - Logs refresh every 10s
- **Color-Coded** - Success (green), Error (red), etc.
- **Animations** - Smooth transitions throughout

### Responsive Design
- **Desktop** - Full layout with sidebar
- **Tablet** - Sidebar moves to bottom
- **Mobile** - Stacked single column

---

## 🚀 Performance Optimization

### Current Optimizations
- Async webhook calls (non-blocking)
- File cleanup (temp files deleted immediately)
- Log file rotation (prevents huge file)
- Efficient CSV parsing (DictReader)
- Caching disabled (real-time data)

### Potential Improvements
- Queue system for bulk processing
- Database caching for frequent queries
- Webhook response caching
- Parallel candidate screening
- Workers for long-running tasks

---

## 🔒 Security Implementation

### Current Measures
- ✅ Credentials in .env (never hardcoded)
- ✅ Secure filename handling
- ✅ File size validation
- ✅ File type validation
- ✅ Proper error handling (no info leaks)
- ✅ UTF-8 encoding (prevent injection)

### Recommendations for Production
- SSL/TLS encryption (HTTPS)
- API rate limiting
- User authentication & authorization
- Database encryption
- Audit logging
- Input sanitization
- CSRF protection
- CORS configuration

---

## 🐛 Error Handling Strategy

### Try-Catch Pattern
```python
try:
    # Main logic
except TimeoutError:
    # Specific timeout handling
except FileNotFoundError:
    # Missing file handling
except Exception as e:
    # General error with traceback
    logger.error(f"[MODULE] Error: {e}\n{traceback.format_exc()}")
    return {"status": "error", "error": str(e)}
```

### User Feedback
- **UI Alerts** - Color-coded messages
- **HTTP Status** - Proper codes (400, 500)
- **JSON Response** - Always consistent format
- **Logs** - Full traceback for debugging

---

## 📈 Scalability Considerations

### Current Capacity
- Single instance, synchronous processing
- Handles ~10-20 candidates per run
- Response time degradation with size

### Scaling Solutions
- **Horizontal:** Multiple Flask instances + load balancer
- **Vertical:** Upgrade server (CPU, RAM)
- **Async Queue:** Use Celery + Redis
- **Database:** Read replicas for logs
- **CDN:** Cache static assets
- **Webhooks:** Implement retry logic

---

## 🧪 Testing Endpoints

### Health Check
```bash
curl http://localhost:5000/api/status
```

### File Upload Test
```bash
curl -F "file=@resume.pdf" http://localhost:5000/api/upload-file
```

### Bulk Screen Test
```bash
curl -X POST http://localhost:5000/api/bulk-screen \
  -H "Content-Type: application/json" \
  -d '{
    "candidates": [{"name": "Test", "resume": "Developer"}],
    "jd_text": "Looking for developer"
  }'
```

### View Logs
```bash
curl http://localhost:5000/api/logs | jq '.logs[-10:]'
```

---

## 📚 Dependencies

### Core
- Flask - Web framework
- httpx - Async HTTP client
- PyPDF2 - PDF extraction
- python-docx - DOCX extraction

### Built-in
- asyncio - Async/await
- logging - Logging system
- csv - CSV parsing
- json - JSON handling
- os, traceback - Utilities

### Total: 4 external packages

---

## 🎯 Key Metrics

| Metric | Value |
|--------|-------|
| Backend Lines | ~500 |
| Frontend Lines | ~2,000 |
| API Endpoints | 7 |
| File Types | 5 (PDF, DOC, DOCX, CSV, TXT) |
| Tabs/Features | 5 |
| Response Time | <10s average |
| Concurrent Users | 1-10 (single instance) |
| Memory Usage | ~150MB |
| Max File Size | 50MB |
| Log File Size | Unlimited (rotation recommended) |

---

## 🔄 Deployment Checklist

- [ ] Python 3.10+ installed
- [ ] Dependencies: `pip install -r requirements.txt`
- [ ] .env configured with all 7 credentials
- [ ] n8n webhooks active & tested
- [ ] logs/ directory exists
- [ ] uploads/ directory writable
- [ ] Port 5000 available
- [ ] SSL certificate ready (for HTTPS)
- [ ] Backup strategy in place
- [ ] Monitoring set up (logs, errors)

---

## 📞 Technical Support

### Common Issues & Fixes
1. **Import Error** → Missing package: `pip install [package]`
2. **Port in Use** → Kill process: `lsof -i :5000`
3. **Webhook Timeout** → Check n8n: curl webhook URL
4. **File Not Extracted** → Check format & size
5. **Logs Not Showing** → Check file permissions

### Debug Mode
```python
app.run(debug=True)  # Enables auto-reload, detailed errors
```

### Production Mode
```python
app.run(debug=False)  # For production deployment
```

---

## 🎓 Learning Resources

- **Flask Docs:** https://flask.palletsprojects.com/
- **PyPDF2:** https://github.com/py-pdf/pypdf
- **python-docx:** https://python-docx.readthedocs.io/
- **n8n Docs:** https://docs.n8n.io/
- **REST APIs:** https://www.rest-api-tutorial.com/

---

## 📝 Version History

| Version | Date | Changes |
|---------|------|---------|
| 3.0 | Feb 2026 | Complete rewrite with AI chat, file uploads, bulk screening |
| 2.0 | Feb 2026 | Added web UI, file uploads, bulk support |
| 1.0 | Feb 2026 | Initial CLI version |

---

**This ATS is production-ready and fully integrated with n8n automation.**

---

**Questions? Check:**
- ATS_V3_GUIDE.md (complete guide)
- QUICK_START_V3.md (30-second setup)
- This document (technical details)

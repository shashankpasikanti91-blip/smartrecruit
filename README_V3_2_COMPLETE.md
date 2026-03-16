# SRP SmartRecruit v3.2 - Complete Documentation

> **HIGH-SECURITY AI-POWERED APPLICANT TRACKING SYSTEM**  
> Version: 3.2.0 | Built with FastAPI + SQLAlchemy + Pydantic  
> **NO SUPABASE -** Pure Python Backend

---

## 🚀 Quick Start

```bash
# 1. Install dependencies
pip install -r requirements_v3.2.txt

# 2. Configure environment
copy .env.example .env
# Edit .env with your API keys

# 3. Start server
uvicorn app.main:app --reload --port 5003

# Or use the batch file:
START_V3_2.bat
```

**Server will be running at:** http://localhost:5003  
**API Documentation:** http://localhost:5003/docs  
**Health Check:** http://localhost:5003/health

---

## 📋 Table of Contents

1. [What's New in v3.2](#whats-new-in-v32)
2. [Architecture](#architecture)
3. [Features](#features)
4. [API Endpoints](#api-endpoints)
5. [Database Schema](#database-schema)
6. [Authentication & Security](#authentication--security)
7. [AI Integration](#ai-integration)
8. [Deployment](#deployment)
9. [Upgrading from v3.1](#upgrading-from-v31)
10. [Troubleshooting](#troubleshooting)

---

## 🎯 What's New in v3.2

### Major Changes from v3.1

✅ **Removed Supabase** - Now uses pure FastAPI + SQLAlchemy  
✅ **PostgreSQL Support** - Production-ready database  
✅ **SQLite Fallback** - Easy local development  
✅ **High Security** - JWT + OTP + Single-session enforcement  
✅ **Role-based Access** - Admin, Pro, Free tiers  
✅ **Rate Limiting** - Per-role usage quotas  
✅ **AI Writing Assistant** - Pydantic-AI integration ready  
✅ **Interview Invites** - Auto-generated emails for qualified candidates  
✅ **Support Chatbot** - Integrated ticketing system  

### Tech Stack

| Component | Technology |
|-----------|------------|
| Framework | FastAPI 0.109+ |
| ORM | SQLAlchemy 2.0+ |
| Validation | Pydantic 2.5+ |
| Auth | JWT (python-jose) + bcrypt |
| Database | PostgreSQL / SQLite |
| AI | Pydantic-AI (OpenAI/Anthropic/Gemini) |
| Email | SMTP (aiosmtplib) |

---

## 🏗️ Architecture

```
/app
├── main.py                 # FastAPI application entry
├── schemas.py              # Pydantic models
├── auth/
│   ├── utils.py           # Password hashing, JWT, OTP
│   └── dependencies.py    # Auth middleware
├── models/
│   ├── user.py           # User, OTP, Session models
│   ├── resume.py         # Resume metadata
│   ├── screening.py      # Screening & invites
│   └── support.py        # Support tickets
├── services/
│   ├── auth_service.py    # Auth business logic
│   ├── screening_service.py
│   ├── rate_limit_service.py
│   └── pydantic_ai_agents.py
├── routers/
│   ├── auth.py           # /api/auth/*
│   ├── resume.py         # /api/resume/*
│   ├── screening.py      # /api/screening/*
│   ├── ai_assistant.py   # /api/ai/*
│   └── support.py        # /api/support/*
├── database/
│   └── connection.py     # SQLAlchemy setup
└── templates/
    └── index.html        # Frontend UI
```

---

## ✨ Features

### 1. Authentication System (Phase 4)

**✅ Email + Password Registration**
- BCrypt password hashing
- OTP email verification
- Secure password reset

**✅ JWT Authentication**
- HS256 signing
- 30-minute token expiry
- Refresh mechanism ready

**✅ Single-Session Enforcement**
- Only ONE active session per user
- Login elsewhere = auto-logout on old device
- Session tracking in database

**✅ OTP System**
- 6-digit codes
- 10-minute expiry
- Used for: Registration, Login (optional), Password Reset

### 2. Role-Based Access Control (Phase 5)

| Role | Screenings/Day | Job Posts/Day | Features |
|------|----------------|---------------|----------|
| **Free User** | 1 | 1 | Basic features |
| **Pro** | Unlimited | Unlimited | All features |
| **Admin** | Unlimited | Unlimited | Full access + admin panel |

### 3. Resume Screening (Phase 6)

**✅ File Upload**
- Supports:PDF, DOCX, TXT
- Max size: 10MB
- Auto text extraction

**✅ AI Screening**
- Match candidates to job descriptions
- Score: 0-100
- Detailed analysis (strengths, concerns)
- Recommendation: hire/interview/reject

**✅ Interview Invites**
- Auto-eligibility for score >= 75%
- Professional email templates
- Track invite status (draft/sent/accepted/rejected)

### 4. AI Writing Assistant (Phase 8)

**✅ Content Improvement**
- Job descriptions
- Interview invitations
- Emails
- Internal communications

**✅ Features**
- Real-time suggestions
- Tone analysis
- Professional formatting

### 5. Support Chatbot (Phase 7)

**✅ Ticket Management**
- Anonymous + authenticated users
- Categories: technical, billing, general
- Priority levels
- Admin responses

**✅ Admin Panel**
- View all tickets
- Update status
- Add replies

---

## 📡 API Endpoints

### Authentication (`/api/auth`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/register` | Create new account + send OTP |
| POST | `/verify-otp` | Verify email with OTP |
| POST | `/login` | Login (JWT + single session) |
| POST | `/logout` | Logout current session |
| POST | `/forgot-password` | Request password reset OTP |
| POST | `/reset-password` | Reset password with OTP |
| GET | `/me` | Get current user info |

### Resume (`/api/resume`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/upload` | Upload resume (PDF/DOCX/TXT) |
| GET | `/list` | List user's resumes |
| GET | `/{resume_id}` | Get resume details |
| DELETE | `/{resume_id}` | Delete resume |

### Screening (`/api/screening`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/screen` | Screen resume vs job description |
| GET | `/results/{id}` | Get screening result |
| GET | `/results` | List all screening results |
| POST | `/invite` | Create interview invitation |
| POST | `/invite/{id}/send` | Send invitation email |
| GET | `/usage` | Get usage stats & limits |

### AI Assistant (`/api/ai`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/writing-assist` | Improve any text |
| POST | `/generate-job-description` | Generate job description |
| POST | `/improve-email` | Improve email content |
| POST | `/quick-suggestions` | Quick writing tips |

### Support (`/api/support`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/ticket` | Create support ticket |
| GET | `/tickets` | User's tickets |
| GET | `/admin/tickets` | All tickets (admin only) |
| PATCH | `/admin/ticket/{id}` | Update ticket (admin only) |

---

## 🗄️ Database Schema

### Users Table
```sql
- id (PK)
- email (unique)
- hashed_password
- role (user/pro/admin)
- is_active
- is_verified
- created_at
```

### OTP Verifications Table
```sql
- id (PK)
- user_id (FK)
- otp_code (6 digits)
- purpose (registration/login/password_reset)
- expires_at
- used (boolean)
- created_at
```

### Sessions Table
```sql
- id (PK)
- user_id (FK)
- jwt_token (unique)
- is_active
- created_at
- last_activity
```

### Resume Metadata Table
```sql
- id (PK)
- user_id (FK)
- filename
- file_path
- file_size
- mime_type
- extracted_text
- parsed_data (JSON)
- uploaded_at
```

### Screening Results Table
```sql
- id (PK)
- user_id (FK)
- resume_id (FK)
- job_description
- score (0-100)
- status
- ai_analysis (JSON)
- strengths (JSON)
- concerns (JSON)
- recommendation
- is_eligible_for_invite
- created_at
```

### Interview Invites Table
```sql
- id (PK)
- user_id (FK)
- screening_id (FK)
- candidate_name
- candidate_email
- email_subject
- email_body
- invite_status (draft/sent/accepted/rejected)
- sent_at
- created_at
```

### Support Tickets Table
```sql
- id (PK)
- user_id (FK, nullable)
- user_email
- message
- category
- priority
- status (open/in_progress/resolved/closed)
- admin_reply
- created_at
- updated_at
```

---

## 🔐 Authentication & Security

### Password Security
- **Hashing**: BCrypt with automatic salt
- **Min Length**: 8 characters
- **Storage**: Never stored in plain text

### JWT Tokens
- **Algorithm**: HS256
- **Expiry**: 30 minutes
- **Secret**: Configured in `.env`
- **Claims**: User ID, email, expiration

### OTP Security
- **Length**: 6 digits
- **Expiry**: 10 minutes
- **One-time use**: Marked as used after verification
- **Delivery**: Email (SMTP)

### Single-Session Enforcement
```python
# When user logs in:
1. Invalidate all previous sessions
2. Create new session with JWT
3. If user logs in elsewhere, old session invalidated
4. Old device gets 401 Unauthorized on next request
```

### Rate Limiting
```python
# Free users
- 1 screening per day (resets at midnight UTC)
- 1 job post per day

# Checked before each screening
# Returns 429 Too Many Requests if limit exceeded
```

---

## 🤖 AI Integration

### Current Status
**Mock Implementation Active** - Ready for real AI

The system includes placeholder AI functions that work without API keys. To enable real AI:

### 1. Add API Keys to `.env`
```env
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=...
```

### 2. Update `app/services/pydantic_ai_agents.py`
Replace mock functions with pydantic-ai agents:

```python
from pydantic_ai import Agent

agent = Agent('openai:gpt-4')
result = await agent.run("Your prompt here")
```

### AI Features
- **Resume Analysis**: Extract structured data from resumes
- **Job Matching**: Score candidates (0-100) vs job requirements
- **Writing Assistant**: Improve job descriptions & emails
- **Smart Suggestions**: Real-time writing help

---

## 🚀 Deployment

### Development (SQLite)
```bash
# Uses SQLite automatically
uvicorn app.main:app --reload --port 5003
```

### Production (PostgreSQL)

**1. Setup PostgreSQL**
```bash
# Create database
createdb srp_ats_v3_2

# Or use Docker
docker run -d \
  --name postgres-ats \
  -e POSTGRES_PASSWORD=yourpassword \
  -e POSTGRES_DB=srp_ats_v3_2 \
  -p 5432:5432 \
  postgres:15
```

**2. Update `.env`**
```env
DATABASE_URL=postgresql://username:password@localhost:5432/srp_ats_v3_2
```

**3. Run with Gunicorn**
```bash
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:5003
```

### Docker Deployment
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements_v3.2.txt .
RUN pip install --no-cache-dir -r requirements_v3.2.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5003"]
```

---

## 📈 Upgrading from v3.1

### Migration Steps

**1. Backup v3.1 Data**
```bash
# Export from Supabase
# Save as CSV/JSON
```

**2. Install v3.2**
```bash
cd "Updated 13 Feb 2026 Recruitment_AI_System_v3_2_dev"
pip install -r requirements_v3.2.txt
```

**3. Configure Environment**
```bash
# Copy and edit .env
cp .env.example .env
```

**4. Import Data (Optional)**
```python
# Create migration script to import old data
# Map Supabase tables to new SQLAlchemy models
```

**5. Test**
```bash
# Start server
uvicorn app.main:app --reload --port 5003

# Run tests
python test_v3_2.py
```

### Key Differences

| Feature | v3.1 | v3.2 |
|---------|------|------|
| Database | Supabase | FastAPI + SQLAlchemy |
| Auth | Supabase Auth | JWT + OTP (custom) |
| Storage | Supabase Storage | Local filesystem |
| AI | Mixed | Pydantic-AI ready |
| Sessions | Browser-based | Server-side (DB) |

---

## 🔧 Troubleshooting

### Server Won't Start

**Error: Module not found**
```bash
# Install dependencies
pip install -r requirements_v3.2.txt
```

**Error: Port 5003 already in use**
```bash
# Change port in command
uvicorn app.main:app --port 5004

# Or kill existing process
# Windows: Get-Process -Name "python" | Stop-Process
# Linux: kill $(lsof -t -i:5003)
```

### Database Issues

**Error: Database locked (SQLite)**
- Only one process can write to SQLite
- Switch to PostgreSQL for production

**Error: Connection refused (PostgreSQL)**
```bash
# Check PostgreSQL is running
pg_isready

# Check connection string in .env
DATABASE_URL=postgresql://...
```

### Authentication Issues

**OTP not received**
- Check SMTP settings in `.env`
- For testing, OTP is returned in API response (remove in production)

**Session expired**
- JWT tokens expire after 30 minutes
- Login again to get new token

**Logged out automatically**
- Single-session enforcement: login elsewhere invalidates previous session

### File Upload Issues

**Error: File too large**
- Max size: 10MB
- Configured in `app/routers/resume.py`

**Error: Unsupported file type**
- Supported: PDF, DOCX, TXT
- Add more types in `ALLOWED_EXTENSIONS`

---

## 📞 Support

**Email**: support@smartrecruit.com  
**Documentation**: http://localhost:5003/docs  
**GitHub**: [Your Repo]

---

## 📝 License

Proprietary - SRP SmartRecruit v3.2  
© 2026 All Rights Reserved

---

## 🎯 Roadmap to v3.3

- [ ] Email templates with HTML
- [ ] Advanced analytics dashboard
- [ ] Bulk resume screening
- [ ] Calendar integration
- [ ] Video interview scheduling
- [ ] Candidate portal
- [ ] Mobile app (React Native)

---

**Built with ❤️ using FastAPI, SQLAlchemy, and Pydantic**  
**Version: 3.2.0 | February 13, 2026**

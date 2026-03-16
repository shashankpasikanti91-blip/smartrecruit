# SRP SmartRecruit v3.2 - Quick Start Guide

## 🚀 Getting Started

### Step 1: Install Dependencies
```bash
pip install -r requirements_v3.2.txt
```

### Step 2: Configure Environment
1. Copy `.env.example` to `.env`
2. Update the configuration values (especially SECRET_KEY and AI API keys)

### Step 3: Start the Server

**Option A: Using the startup script (Windows)**
```bash
START_V3_2.bat
```

**Option B: Manual start**
```bash
uvicorn app.main:app --reload --port 5003
```

### Step 4: Access the Application
Open your browser and navigate to:
- **API Documentation**: http://localhost:5003/docs
- **Health Check**: http://localhost:5003/health
- **Main App**: http://localhost:5003/app (after Phase 3)

---

## 📁 Project Structure

```
/app
  ├── main.py              # FastAPI entry point
  ├── auth/                # Authentication (Phase 4)
  ├── models/              # SQLAlchemy models
  ├── services/            # Business logic
  ├── database/            # Database config
  ├── routers/             # API routes
  ├── templates/           # HTML templates
  └── static/              # CSS, JS, images
```

---

## 🔧 Current Status

✅ **Phase 1 & 2 Complete:**
- Clean project structure created
- FastAPI setup complete
- SQLAlchemy configured
- SQLite fallback ready
- PostgreSQL ready for production

⏳ **Coming Next:**
- Phase 3: Database models
- Phase 4: Authentication system
- Phase 5: Role-based access
- Phase 6: Screening & invites
- Phase 7: Chatbot
- Phase 8: AI Writing Assistant

---

## 🛢️ Database

**Development:** SQLite (automatic)
**Production:** PostgreSQL (configure in .env)

The database will be automatically created on first run.

---

## 📦 Tech Stack

- **Framework:** FastAPI
- **ORM:** SQLAlchemy
- **Database:** PostgreSQL / SQLite
- **Auth:** JWT + OTP
- **AI:** OpenAI, Anthropic, Google Gemini
- **Security:** Bcrypt, Single-session enforcement

---

## ⚠️ Important Notes

- This is **v3.2** - a fresh start with NO Supabase
- Based on stable v3.1 UI (no UI redesign)
- High-security implementation
- Production-ready code structure

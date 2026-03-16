# SRP SmartRecruit — AI-Powered ATS v3.2

**Live:** https://recruit.srpailabs.com  
**GitHub:** https://github.com/shashankpasikanti91-blip/smartrecruit

AI-powered Applicant Tracking System built with FastAPI + PostgreSQL. Screen candidates, post jobs, and automate your hiring pipeline.

---

## Features

- **Resume Screening** — AI scores candidates against job descriptions (0–100)
- **Bulk Screening** — Upload multiple resumes, rank all at once
- **Job Post Generator** — AI writes job descriptions for 9+ platforms
- **AI Writing Assistant** — Improve emails, messages, and JDs
- **Support Tickets** — Internal helpdesk for recruitment issues
- **JWT Auth** — Secure login with OTP email verification
- **Activity Log** — Track every action (logins, uploads, screenings, tickets) per user
- **Landing Page** — Marketing page at `/`, dashboard at `/app`

---

## Tech Stack

| Layer | Technology |
|---|---|
| API | FastAPI 0.129, Python 3.11 |
| Database | PostgreSQL 16 (Docker) |
| ORM | SQLAlchemy 2.0 |
| AI | pydantic-ai, OpenAI GPT |
| Auth | python-jose (JWT), bcrypt |
| Server | gunicorn + uvicorn workers |
| Reverse Proxy | nginx + Let's Encrypt SSL |
| Container | Docker + docker-compose |

---

## Quick Start (Local Dev)

### 1. Prerequisites
- Python 3.11+
- PostgreSQL running locally
- Docker (optional, for containerised DB)

### 2. Setup

```bash
# Clone
git clone https://github.com/shashankpasikanti91-blip/smartrecruit.git
cd smartrecruit

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux/Mac

# Install dependencies
pip install -r requirements.production.txt

# Copy and configure environment
cp .env.production.template .env
# Edit .env — set DATABASE_URL, SECRET_KEY, OPENAI_API_KEY
```

### 3. Setup local PostgreSQL database

```bash
# Creates srp_ats user + database in your local PostgreSQL
python setup_local_db.py
```

> This creates `srp_ats` user and `srp_ats` database. Your `.env` default:
> `DATABASE_URL=postgresql://srp_ats:ats_dev_password@localhost:5432/srp_ats`

### 4. Run the app

```bash
uvicorn app.main:app --port 8767 --reload
```

Open: http://localhost:8767 (landing page) | http://localhost:8767/app (dashboard) | http://localhost:8767/docs (API)

---

## Docker (Full Stack)

```bash
# Development (postgres exposed on port 5435 for DB tools)
docker compose -f docker-compose.dev.yml up -d --build

# Production (matches server setup)
docker compose up -d --build
```

---

## Production Deployment (Hetzner + Cloudflare)

### Server: `5.223.67.236` | Domain: `recruit.srpailabs.com`

```bash
# On server
mkdir -p /opt/srp-ats && cd /opt/srp-ats

# Copy your code
scp -r ./* root@5.223.67.236:/opt/srp-ats/

# Create .env from template (fill in real values)
cp .env.production.template .env
nano .env   # set POSTGRES_PASSWORD, SECRET_KEY, OPENAI_API_KEY, CORS_ORIGINS

# Build and start
docker compose up -d --build

# Check logs
docker compose logs -f app
```

### nginx + SSL (already configured on server)
- Config: `/etc/nginx/sites-available/recruit.srpailabs.com`
- SSL: Let's Encrypt via certbot (auto-renews)
- Port: app runs on `127.0.0.1:8009`, nginx proxies to HTTPS

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `DATABASE_URL` | YES | PostgreSQL connection URL |
| `POSTGRES_PASSWORD` | YES | PostgreSQL container password |
| `SECRET_KEY` | YES | JWT signing key (use `python -c "import secrets; print(secrets.token_hex(32))"`) |
| `OPENAI_API_KEY` | YES | OpenAI API key for AI features |
| `ENVIRONMENT` | YES | `production` or `development` |
| `CORS_ORIGINS` | prod | `https://recruit.srpailabs.com` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | no | default 1440 (24h) |

See [`.env.production.template`](.env.production.template) for all variables.

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Health check + DB status |
| POST | `/api/auth/register` | Register new user |
| POST | `/api/auth/verify-otp` | Verify email OTP |
| POST | `/api/auth/login` | Login, get JWT |
| GET | `/api/auth/me` | Current user info |
| POST | `/api/resume/upload` | Upload resume (PDF/DOCX) |
| POST | `/api/screening/screen` | Screen candidate vs job |
| POST | `/api/screening/bulk` | Bulk screen multiple resumes |
| POST | `/api/ai/writing-assist` | AI writing improvement |
| POST | `/api/support/ticket` | Create support ticket |

Full API docs: https://recruit.srpailabs.com/docs

---

## Activity Log

The **Activity Log** (visible in the dashboard sidebar) tracks every significant action in the system:

- User logins and logouts
- Resume uploads
- Candidate screenings (single + bulk)
- Job post generations
- Support ticket creation
- AI writing requests

This gives HR teams a full audit trail — who did what, and when. Useful for compliance, debugging, and team oversight.

---

## Database Schema

7 tables auto-created on startup:
- `users` — accounts with OTP and subscription
- `sessions` — active JWT sessions (single-session enforcement)
- `resumes` — uploaded resume metadata + extracted text
- `job_screenings` — screening results with AI scores
- `job_posts` — generated job descriptions
- `support_tickets` — helpdesk tickets
- `activity_logs` — audit trail of all user actions

---

## Security

- JWT tokens signed with `HS256`, expire in 24h
- Single session per user (new login invalidates old token)
- OTP hidden in responses when `ENVIRONMENT=production`
- CORS locked to `CORS_ORIGINS` env var in production
- PostgreSQL not exposed to host network in production Docker
- `.env` excluded from git via `.gitignore`

---

## License

Private — SRP AI Labs © 2026

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│      n8n Workflow Orchestration         │
│   (Control Panel + Automation)          │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│  Python Backend (Recruitment AI)        │
│  ┌────────────────────────────────────┐ │
│  │ Agents & Engines                   │ │
│  │ - Screening Agent (GPT-4o)        │ │
│  │ - Messaging Agent (GPT-4o)        │ │
│  │ - Matching Engine (Embeddings)    │ │
│  └────────────────────────────────────┘ │
└──────────────┬──────────────────────────┘
               │
    ┌──────────┼──────────┬──────────────┐
    │          │          │              │
┌───▼──┐  ┌───▼──┐  ┌───▼────┐  ┌──────▼────┐
│Google│  │ Supa │  │ OpenAI │  │  n8n API  │\n│Drive │  │base │  │       │  │ Workflows │\n└──────┘  └──────┘  └────────┘  └───────────┘\n```

## 📁 Project Structure

```
recruitment_ai_system/
├── models/                 # Pydantic data models
│   ├── candidate.py       # Candidate model with skills and experience
│   ├── requirement.py     # Job description model
│   ├── interview.py       # Interview scheduling and feedback
│   ├── selection.py       # Offer and selection tracking
│   ├── screening.py       # Screening results
│   └── messaging.py       # Message generation models
│
├── agents/                # AI Agents
│   ├── screening_agent.py     # Resume-to-JD matching
│   ├── messaging_agent.py     # Message generation
│   └── matching_engine.py     # Semantic similarity matching
│
├── database/              # Database layer
│   └── supabase_client.py # Supabase integration with async support
│
├── integrations/          # External integrations
│   ├── drive_loader.py       # Google Drive JD/Resume loading\n│   └── embedding_engine.py    # OpenAI embeddings\n│\n├── workflows/             # Orchestration\n│   └── n8n_client.py        # n8n workflow triggering\n│\n├── control_panel/         # Control panel integration\n│   └── control_panel_manager.py  # JSON form configuration\n│\n├── utils/                 # Utilities\n│   ├── config.py         # Configuration management\n│   └── logging_config.py # Logging setup\n│\n├── main.py               # Main entry point\n├── requirements.txt      # Dependencies\n└── .env.example          # Environment template\n```\n\n## 🚀 Quick Start\n\n### 1. Installation\n\n```bash\ncd recruitment_ai_system\npip install -r requirements.txt\n```\n\n### 2. Configuration\n\n```bash\ncp .env.example .env\n# Edit .env with your credentials\n```\n\n### 3. Setup Supabase\n\nCreate these tables in Supabase:\n\n```sql\n-- Requirements table\nCREATE TABLE requirements (\n  id UUID PRIMARY KEY,\n  job_title TEXT NOT NULL,\n  client TEXT NOT NULL,\n  jd_text TEXT,\n  required_skills TEXT[] DEFAULT '{}',\n  min_experience FLOAT,\n  status TEXT DEFAULT 'open',\n  created_at TIMESTAMP DEFAULT NOW()\n);\n\n-- Candidates table\nCREATE TABLE candidates (\n  id UUID PRIMARY KEY,\n  name TEXT NOT NULL,\n  email TEXT NOT NULL,\n  phone TEXT,\n  resume_text TEXT,\n  jd_id UUID REFERENCES requirements(id),\n  status TEXT DEFAULT 'new',\n  total_experience FLOAT,\n  skills TEXT[] DEFAULT '{}',\n  created_at TIMESTAMP DEFAULT NOW()\n);\n\n-- Screening results table\nCREATE TABLE screening_results (\n  id UUID PRIMARY KEY,\n  candidate_id UUID REFERENCES candidates(id),\n  jd_id UUID REFERENCES requirements(id),\n  overall_score FLOAT,\n  recommendation TEXT,\n  strengths TEXT[] DEFAULT '{}',\n  gaps TEXT[] DEFAULT '{}',\n  created_at TIMESTAMP DEFAULT NOW()\n);\n\n-- Interviews table\nCREATE TABLE interviews (\n  id UUID PRIMARY KEY,\n  candidate_id UUID REFERENCES candidates(id),\n  jd_id UUID REFERENCES requirements(id),\n  stage TEXT,\n  scheduled_at TIMESTAMP,\n  status TEXT DEFAULT 'scheduled',\n  created_at TIMESTAMP DEFAULT NOW()\n);\n\n-- Selections table\nCREATE TABLE selections (\n  id UUID PRIMARY KEY,\n  candidate_id UUID REFERENCES candidates(id),\n  jd_id UUID REFERENCES requirements(id),\n  status TEXT DEFAULT 'pending',\n  overall_score FLOAT,\n  created_at TIMESTAMP DEFAULT NOW()\n);\n\n-- Embeddings table (for vector search)\nCREATE TABLE embeddings (\n  id UUID PRIMARY KEY,\n  entity_type TEXT,\n  entity_id TEXT,\n  text TEXT,\n  embedding VECTOR(1536),\n  metadata JSONB DEFAULT '{}',\n  created_at TIMESTAMP DEFAULT NOW()\n);\n\n-- Message history table\nCREATE TABLE message_history (\n  id UUID PRIMARY KEY,\n  candidate_id UUID REFERENCES candidates(id),\n  platform TEXT,\n  subject TEXT,\n  body TEXT,\n  status TEXT DEFAULT 'pending',\n  created_at TIMESTAMP DEFAULT NOW()\n);\n```\n\n### 4. Setup Google Drive Credentials\n\n1. Create a Google service account\n2. Download credentials JSON\n3. Place in `credentials/google_service_account.json`\n4. Share Google Drive folders with service account email\n\n### 5. Setup n8n (Optional)\n\nFor local n8n instance:\n\n```bash\nnpm install -g n8n\nn8n\n```\n\nThen import workflows and connect with your API key.\n\n## 💻 Usage Examples\n\n### Screen a Candidate\n\n```python\nfrom recruitment_ai_system.main import RecruitmentAISystem\nimport asyncio\n\nasync def main():\n    system = RecruitmentAISystem()\n    \n    result = await system.screen_candidate(\n        candidate_id=\"cand_123\",\n        resume_text=\"John has 5 years Python experience...\",\n        jd_id=\"jd_456\",\n        jd_text=\"We need a senior Python developer with...\"\n    )\n    \n    print(result)\n\nasyncio.run(main())\n```\n\n### Generate a Message\n\n```python\nmessage = await system.generate_message(\n    message_type=\"interview_invite\",\n    tone=\"professional\",\n    platform=\"email\",\n    recipient_name=\"John\",\n    recipient_email=\"john@example.com\",\n    context={\n        \"job_title\": \"Senior Developer\",\n        \"interview_date\": \"2026-02-15\",\n        \"interview_link\": \"zoom_link\"\n    }\n)\n```\n\n### Process Form Submission\n\n```python\nresult = await system.process_form_submission({\n    \"task_type\": \"Screen CV against JD\",\n    \"input_text\": \"CV content here...\",\n    \"context_info\": \"Backend role\"\n})\n```\n\n## 🤖 Agents Overview\n\n### Screening Agent\n- Analyzes resume vs job description\n- Provides matching score (0-1)\n- Identifies skill gaps\n- Recommends interview questions\n- Returns decision (proceed/conditional/reject)\n\n### Messaging Agent\n- Generates personalized messages\n- Supports multiple platforms (Email, WhatsApp, LinkedIn)\n- Offers different tones (Formal, Professional, Friendly)\n- Multi-language capable\n- Platform-specific formatting\n\n### Matching Engine\n- Semantic similarity using embeddings\n- Skill overlap calculation\n- Experience matching\n- Composite scoring\n- Term-based matching\n\n## 🗄️ Database Schema\n\nAll tables include:\n- UUID primary keys\n- Foreign key relationships\n- Audit timestamps (created_at, updated_at)\n- Status fields for workflow tracking\n- JSONB fields for flexible metadata\n\n## 🔗 n8n Integration\n\nThe system automatically triggers n8n workflows for:\n\n1. **Resume Screening Workflow**\n   - Triggered when candidate screening starts\n   - Can add manual review steps\n   - Updates screening results\n\n2. **Messaging Workflow**\n   - Triggered for message generation\n   - Handles email/WhatsApp/LinkedIn sending\n   - Tracks delivery and reads\n\n3. **JD Processing Workflow**\n   - Triggered when new JD is processed\n   - Generates multi-platform job posts\n   - Updates database\n\n## 🔐 Security Considerations\n\n- Store credentials in `.env` (never commit)\n- Use service accounts for Google Drive\n- Enable Supabase RLS (Row Level Security)\n- Validate all input data with Pydantic\n- Log sensitive operations (no passwords/keys in logs)\n- Use HTTPS for API communication\n\n## 📊 Monitoring\n\n- Health checks for all components\n- Structured logging to file and console\n- Execution audit trail\n- Error tracking and notifications\n- Performance metrics\n\n## 🧪 Testing\n\n```bash\npytest tests/ -v\npytest --cov=recruitment_ai_system tests/\n```\n\n## 📈 Scaling\n\n- Async/await throughout for concurrency\n- Batch processing for large candidate lists\n- Vector database for semantic search\n- Connection pooling to Supabase\n- Workflow queueing via n8n\n\n## 🤝 Contributing\n\n1. Create feature branch\n2. Add tests\n3. Format with black\n4. Type checking with mypy\n5. Submit pull request\n\n## 📝 License\n\nProprietary - Recruitment AI System\n\n## 📞 Support\n\nFor API keys and integration help:\n- OpenAI: https://platform.openai.com\n- Supabase: https://supabase.com\n- n8n: https://n8n.io\n- Google Drive API: https://developers.google.com/drive\n\n---\n\n**Built with ❤️ for modern recruitment automation**\n
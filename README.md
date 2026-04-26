# SRP SmartRecruit — AI-Powered ATS

**Live:** https://recruit.srpailabs.com  
**Stack:** Next.js 14 · TypeScript · FastAPI · PostgreSQL · Docker · Tailwind CSS

AI-powered Applicant Tracking System for sourcing, screening, tracking, and hiring talent.

---

## Features

| Feature | Description |
|---|---|
| **Pipeline Board** | Kanban-style pipeline — Sourced → Applied → Screening → Interview → Offer → Hired |
| **AI Resume Screening** | Scores candidates (0–100) against JDs — STRONG / KAV / REJECT classification |
| **Bulk CV Screening** | Upload multiple resumes at once, rank all results |
| **Job Post Generator** | AI writes job descriptions for LinkedIn, Naukri, Indeed, WhatsApp, and more |
| **JD Intelligence** | Upload any JD file and extract structured data |
| **Boolean Search** | Advanced sourcing query builder |
| **Candidate Tracker** | Filter by stage, match, job, skill, date. Source + phone visible |
| **Job Filter** | Filter jobs by status (Active/Closed/Draft) and type (Full-time/Contract/Remote/…) |
| **Multi-Tenant** | Each company is fully isolated — all queries scoped to `tenant_id` |
| **Google OAuth** | One-click sign-in via NextAuth + Google Cloud |
| **Owner Panel** | Admin view — users, activity log, token usage, subscriptions |
| **Telegram + Email** | Real-time notifications on signup, login, errors |
| **Integrations** | Connect SMTP, SendGrid, Mailgun, Telegram, and more |
| **Audit Trail** | Full log of every action — who, what, when |
| **Rate Limiting** | Monthly AI call limits per plan tier |
| **Unique IDs** | Every job (`JOB-000001`) and candidate (`RES-000001`) gets a searchable short ID |

---

## Architecture

```
Internet
   │
   ▼
nginx (HTTPS — recruit.srpailabs.com)
   ├── / → Next.js  :3010  (UI, auth, API routes)
   └── /api/v1/*  → FastAPI  :8009  (AI screening, JD gen, boolean, comms)

Docker Compose (docker-compose.yml)
   ├── srp-auth-app    — Next.js 14 (TypeScript)
   ├── srp-auth-db     — PostgreSQL 16
   ├── srp-ats-app     — FastAPI (Python 3.11)
   └── srp-ats-db      — PostgreSQL 16
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 14 (App Router), TypeScript, Tailwind CSS |
| Auth | NextAuth v4 — JWT + Google OAuth |
| Next.js API | Route Handlers (`/app/api/**`) |
| AI Backend | FastAPI 0.129, Python 3.11 |
| AI Models | OpenRouter → GPT-4.1-mini |
| Database | PostgreSQL 16 (Docker) |
| Validation | `lib/validate.ts` (Next.js), Pydantic (FastAPI) |
| Container | Docker + docker-compose |
| Reverse Proxy | nginx + Let's Encrypt SSL |
| Notifications | Telegram Bot + Gmail SMTP |

---

## Project Structure

```
srp-smartrecruit/
├── nextjs-auth/              # Next.js 14 frontend + all API routes
│   ├── app/
│   │   ├── dashboard/        # Main dashboard (pipeline, jobs, candidates, AI screen…)
│   │   ├── api/              # All Next.js API route handlers
│   │   ├── login/            # Auth pages
│   │   └── owner/            # Admin owner panel
│   ├── lib/
│   │   ├── db.ts             # PostgreSQL query helpers
│   │   ├── tenant.ts         # Multi-tenant auth guard (requireTenant)
│   │   ├── validate.ts       # Input sanitization + validation
│   │   ├── limits.ts         # Plan-based rate limits
│   │   └── audit.ts          # Audit log helpers
│   ├── db/                   # SQL migrations (run in order v2→v9)
│   └── .env.local            # Local env — NEVER commit
│
├── backend/                  # FastAPI AI backend
│   ├── app/
│   │   ├── routers/          # API endpoints (screening, jd, bool, comms, …)
│   │   ├── services/         # Business logic (screening_service, jd_service, …)
│   │   ├── models/           # SQLAlchemy models
│   │   └── main.py           # FastAPI app entry point
│   ├── system_prompts.txt    # All AI prompts (screening, JD gen, social posts)
│   └── requirements.txt
│
├── deployment/               # Deployment scripts + nginx config
│   ├── deploy.sh             # Main deploy script
│   ├── remote_deploy.py      # Remote server deployment helper
│   ├── smoke_test.py         # Post-deploy smoke tests
│   ├── e2e_test.py           # End-to-end tests
│   └── recruit.srpailabs.com.nginx  # nginx site config
│
├── db/                       # Legacy SQL utilities (cleanup, seed)
├── docker-compose.yml        # Production Docker Compose
├── docker-compose.dev.yml    # Development Docker Compose
├── .env.production.template  # Environment variable template — copy to .env
└── README.md
```

---

## Quick Start (Local Dev)

### Prerequisites
- Node.js 20+
- Docker Desktop
- Git

### 1. Clone & configure

```bash
git clone --recurse-submodules https://github.com/shashankpasikanti91-blip/smartrecruit.git
cd smartrecruit

# Backend environment
cp .env.production.template .env
# Edit .env — set OPENAI_API_KEY, POSTGRES_PASSWORD, SECRET_KEY

# Frontend environment
cd nextjs-auth
cp .env.local.example .env.local
# Edit .env.local — set NEXTAUTH_SECRET, GOOGLE_CLIENT_ID/SECRET, DATABASE_URL
```

### 2. Run with Docker

```bash
# From project root
docker compose -f docker-compose.dev.yml up -d --build

# Check logs
docker compose logs -f
```

- **Frontend:** http://localhost:3000
- **API docs (FastAPI):** http://localhost:8009/docs

### 3. Run migrations

```bash
# Connect to the Next.js Postgres container and run migrations
cd nextjs-auth/db
node migrate.js
```

---

## Environment Variables

### Backend (`.env` at root)

| Variable | Required | Description |
|---|---|---|
| `OPENAI_API_KEY` | YES | OpenRouter or OpenAI API key |
| `OPENAI_BASE_URL` | YES | `https://openrouter.ai/api/v1` |
| `OPENAI_MODEL` | YES | e.g. `openai/gpt-4.1-mini` |
| `DATABASE_URL` | YES | PostgreSQL connection string |
| `POSTGRES_PASSWORD` | YES | PostgreSQL password |
| `SECRET_KEY` | YES | JWT signing key — min 32 chars random string |
| `ENVIRONMENT` | YES | `production` or `development` |
| `CORS_ORIGINS` | prod | `https://recruit.srpailabs.com` |

### Frontend (`nextjs-auth/.env.local`)

| Variable | Required | Description |
|---|---|---|
| `NEXTAUTH_SECRET` | YES | Random 32-char string (`openssl rand -base64 32`) |
| `NEXTAUTH_URL` | YES | `http://localhost:3000` (dev) or production URL |
| `GOOGLE_CLIENT_ID` | YES | From Google Cloud Console |
| `GOOGLE_CLIENT_SECRET` | YES | From Google Cloud Console |
| `DATABASE_URL` | YES | PostgreSQL URL for Next.js |
| `TELEGRAM_BOT_TOKEN` | optional | Owner notifications |
| `TELEGRAM_CHAT_ID` | optional | Owner chat ID |

> **Never commit `.env` or `.env.local`** — both are in `.gitignore`

---

## Production Deployment (Hetzner + Cloudflare)

**Server:** `5.223.67.236` | **Domain:** `recruit.srpailabs.com`

```bash
# SSH to server
ssh root@5.223.67.236

# Pull latest
cd /opt/srp-smartrecruit-auth && git pull origin main
cd /opt/srp-ats && git pull origin clean_main

# Rebuild and restart Next.js
cd /opt/srp-smartrecruit-auth
docker compose build --no-cache
docker compose up -d

# Restart FastAPI (if system_prompts or backend code changed)
cd /opt/srp-ats
docker compose restart app

# Verify
docker ps | grep srp
curl https://recruit.srpailabs.com/api/health
```

---

## Database Migrations

Migrations are in `nextjs-auth/db/`. Run in order:

```
migrate_v2.sql         → Base tables
migrate_v3.sql         → Screening schema
migrate_v4_demo_user.sql
migrate_v5_enterprise.sql  → Multi-tenant, integrations
migrate_v6_id_date_system.sql  → Short IDs (RES-/JOB-)
migrate_v7_globalisation.sql
migrate_v8_multitenant.sql     → Tenant isolation
migrate_v8b_patch.sql
migrate_v8c_final.sql           → API keys, audit columns
migrate_v9_prod_fix.sql
```

---

## Security

- All API routes wrapped with `requireTenant()` — tenant isolation enforced on every query
- JWT (HS256) tokens, 24h expiry, single-session enforcement
- Input validation via `lib/validate.ts` — `isValidUUID`, `sanitizeText`, `sanitizeEnum`
- CORS locked to `CORS_ORIGINS` env var in production
- Security headers on every response: `X-Content-Type-Options`, `X-Frame-Options`, `HSTS`
- PostgreSQL not exposed to host network in production Docker
- Secrets loaded from env vars — no hardcoded keys in source
- Audit log of all user actions (login, upload, screen, stage change)
- API docs (`/docs`, `/redoc`) disabled in production

---

## License

Private — SRP AI Labs © 2026


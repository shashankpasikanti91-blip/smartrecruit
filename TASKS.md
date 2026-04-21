# SRP SmartRecruit — Project Tasks

## In Progress
- [ ] Deploy to production (Hetzner 5.223.67.236 → recruit.srpailabs.com)

## Backend
- [x] Restructure into `backend/` folder
- [x] Security headers middleware (X-Frame-Options, X-XSS-Protection, HSTS, etc.)
- [x] Global exception handlers — no stack traces in responses
- [x] Hide Swagger/ReDoc in production
- [x] TrustedHostMiddleware guard (production)
- [x] CORS locked to CORS_ORIGINS env var in production
- [x] Health check pings database
- [x] Fix dev port (5003 → 8000, localhost only)
- [x] Replace all print() with structured logger calls
- [x] Fix all CWD-relative paths → absolute __file__-based paths
- [x] Boolean search endpoint (`/api/boolean-search`)
- [x] JD generator endpoint (`/api/generate-jd`)
- [x] Enterprise system prompts (6 sections)
- [ ] File upload: server-side MIME type validation
- [ ] File upload: 10 MB size limit enforcement
- [ ] Bulk screening: cap max candidates (20 limit)
- [ ] Input validation: max text length on all AI endpoints
- [ ] Rate limiting: per-IP limits on AI endpoints
- [ ] Add pytest unit tests for core endpoints

## Frontend
- [x] Restructure into `frontend/` folder
- [x] Boolean Search tab in dashboard
- [x] JD Generator tab in dashboard
- [x] Enhanced bulk screening table (8 columns + expandable rows)
- [ ] Audit all innerHTML injections — ensure escapeHtml() used everywhere
- [ ] Add loading skeletons for AI calls
- [ ] Mobile responsive review

## Infrastructure
- [x] Dockerfile: multi-stage build, non-root user, correct COPY paths
- [x] Dockerfile: remove broken symlink
- [x] .dockerignore: updated for new folder layout
- [x] docker-compose.yml: isolated DB network, named volumes
- [x] gunicorn.conf.py: production-ready
- [x] Nginx config: SSL, rate limits, proxy headers
- [x] Clean project root (removed Bin/, scattered SQL/MD files)
- [ ] Rotate OPENAI_API_KEY (currently exposed in .env — regenerate at OpenRouter)
- [ ] Confirm .env is in .gitignore (never commit secrets)

## Deployment Steps (Hetzner)
```bash
# On server — /opt/srp-ats
git pull
docker compose down
docker compose up -d --build
docker compose logs -f app

# Update nginx config
cp deployment/recruit.srpailabs.com.nginx /etc/nginx/sites-available/recruit.srpailabs.com
nginx -t && systemctl reload nginx

# Check certbot renewal
certbot renew --dry-run
```

## Project Structure
```
SRP Smartrecruit/
├── backend/                  # Python FastAPI app
│   ├── app/
│   │   ├── auth/             # JWT + bcrypt auth
│   │   ├── database/         # SQLAlchemy + PostgreSQL
│   │   ├── models/           # ORM models
│   │   ├── routers/          # API route handlers
│   │   ├── services/         # Business logic
│   │   ├── main.py           # App entry point
│   │   └── schemas.py        # Pydantic models
│   ├── utils/                # Config, logging helpers
│   ├── workflows/            # n8n workflow client
│   ├── system_prompts.txt    # AI system prompts (6 sections)
│   ├── gunicorn.conf.py      # Production server config
│   └── requirements.txt      # Python dependencies
├── frontend/                 # Templates + static assets
│   ├── templates/
│   │   ├── dashboard_v3_2.html   # Main app UI
│   │   ├── landing.html          # Marketing page
│   │   └── index.html
│   └── static/               # Images, CSS, JS
├── db/                       # Database scripts (SQL)
├── deployment/               # Nginx config, systemd service
├── docs/                     # Technical documentation
├── nextjs-auth/              # Next.js auth companion app
├── uploads/                  # Resume file storage (Docker volume)
├── logs/                     # App logs (Docker volume)
├── docker-compose.yml        # Production containers
├── docker-compose.dev.yml    # Dev containers
├── Dockerfile                # Multi-stage production build
├── .env                      # Secrets — NEVER commit
└── TASKS.md                  # This file
```

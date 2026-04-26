# SRP SmartRecruit — Project Tasks

## ✅ Completed (Enterprise Edition)

### Bug Fixes
- [x] Integration Hub blank page (API auth + error UI)
- [x] Boolean Search missing file upload → LightFileUploadZone added
- [x] JD Intelligence missing file upload → LightFileUploadZone added
- [x] Communication Hub no templates → seeded 7 default templates

### Phase 1–2: Universal IDs + Date Formatting
- [x] `ShortIdBadge` component — click-to-copy short IDs (CAN-/JOB-)
- [x] `fmtDate()` utility — consistent "12 Jan 2025" format across all tabs

### Phase 3–4: Search + Filters
- [x] Global search by short ID — CAN- prefix → Candidates tab, JOB- prefix → Jobs tab
- [x] Date filter dropdown — filter candidates by upload date (today/7d/30d/90d)
- [x] Date filter wired to `/api/candidates?from=` query param

### Phase 5–6: Table UX Improvements
- [x] Candidates table — "Uploaded" column with fmtDate()
- [x] Job cards/rows — posted date visible
- [x] Candidate detail modal — "Uploaded: date" in header

### Phase 7: Analytics
- [x] Analytics tab — "Upload Activity" card showing weekly upload trend

### Phase 8: Audit Logging (Backend)
- [x] `nextjs-auth/lib/audit.ts` — fire-and-forget `logAudit()` helper
- [x] `GET/POST /api/audit` — paginated audit log API (admin sees all, users see own)
- [x] Pipeline stage changes (PATCH `/api/candidates/[id]`) → logAudit
- [x] Job creation (POST `/api/jobs`) → logAudit
- [x] AI screening (POST `/api/screen`) → logAudit + screened_at timestamp

### Phase 9: AI Output Timestamps
- [x] JD Intelligence history — dates use fmtDate() instead of toLocaleDateString()
- [x] Boolean Search history — dates use fmtDate() instead of toLocaleDateString()

### Phase 10: Audit Trail UI
- [x] Settings tab — "Audit Trail" card showing last 50 events
- [x] Table columns: Action, Resource, ID, Result, When
- [x] Loads via `GET /api/audit` on settings tab open; refresh button

### Phase 11: Import Enhancements
- [x] Import tab — Column Mapping Guide card (Naukri / LinkedIn / Indeed column names)
- [x] Auto-detection explained; unrecognised columns kept as raw metadata

### Enterprise UI Upgrade
- [x] `globals.css` — CSS variables updated to exact spec (#0F172A sidebar, #2563EB active, #E2E8F0 borders)
- [x] `globals.css` — Added Plus Jakarta Sans font; `.page-title`, `.ent-table`, `.drawer-panel`, `.stage-*` utility classes
- [x] Sidebar — inline style colors updated to match spec
- [x] `STAGE_LIGHT` constant — light-bg stage pill variants (for white-bg tables)
- [x] `MATCH_LIGHT` constant — light-bg match badge variants
- [x] `StagePill` — `variant="light"` prop; candidates table uses it
- [x] `MatchBadge` — `variant="light"` prop; candidates table uses it
- [x] **Jobs tab — card grid → professional table** (ID / Role / Company / Location / Type / Candidates / Status / Posted / Actions)
- [x] DB migration v6 (`migrate_v6_audit_trail.sql`)

## ✅ Recently Completed

### Deploy v5.1 Enterprise to Production
- [x] Deploy updated nextjs-auth build to production (Hetzner 5.223.67.236)
- [x] E2E smoke test after deploy — ALL 6 CHECKS PASSED
- [x] Fix `/app` route serving old Jinja2 `dashboard_v3_2.html` — now 301 → `/dashboard` (Next.js)
- [x] Fix nginx: add all enterprise API prefixes (jd, boolean-search, import, integrations, comm, audit, webhooks, profile) to Next.js route regex
- [x] Fix nginx: remove dead duplicate `recruit.srpailabs.com` block from `srpailabs.conf` (was routing to non-existent port 3004)
- [x] Update `backend/app/main.py`: remove old `/app` Jinja2 render, keep `/app` → 301 → `/dashboard`

### AI Screening Hardening & Token Savings (commits b5ade5b → 9c6ed8c)
- [x] Fix: `ai_screening_data` was missing from `GET /api/candidates` SELECT — candidate modal "AI Screening" tab now shows full structured report
- [x] Feat: Duplicate CV guard — amber warning + "View existing record" link when same email uploaded twice (409 response from resumes POST)
- [x] Feat: Token-saving "From Candidates" screening mode — 3rd mode in AI Screening tab; picks candidates from DB by stored `raw_text`; `skipAlreadyScreened` toggle (default ON); shows savings count; zero re-API-calls for already-screened candidates
- [x] Feat: `ai_screening_data` auto-saved to DB on every screen; displayed in modal without extra API call
- [x] DB: `migrate_v11_dup_index.sql` — partial unique index on `(tenant_id, candidate_email)` applied to production
- [x] DB: `migrate_v10_invite_hardening.sql` — invite token hashing + expiry applied to production
- [x] Fix: Multi-tenant invite flow end-to-end (hashed token validation, accept page)
- [x] Deployed all changes to production — Docker Compose build passed (Next.js 16.2.3)

## 🔄 In Progress
## ❌ Backlog / Next Sprint
- [ ] File upload: server-side MIME type validation
- [ ] File upload: 10 MB size limit enforcement
- [ ] Input validation: max text length on all AI endpoints
- [ ] Rate limiting: per-IP limits on AI endpoints

### Testing
- [ ] Add pytest unit tests for core backend endpoints
- [ ] Add Playwright E2E tests for dashboard happy paths

### Frontend Polish
- [ ] Mobile responsive review (sidebar collapse on < 768px)
- [ ] Loading skeletons for AI calls > 2s
- [ ] Keyboard shortcut: `Cmd/Ctrl + K` for global search

### Future Features
- [ ] Candidate bulk status update (select rows → change stage)
- [ ] Job posting → direct apply link / public job board page
- [ ] Email notifications on stage change (via n8n trigger)
- [ ] Webhook inbound: parse external ATS pushes

## Deployment Reference

```bash
# On Hetzner server — /opt/srp-smartrecruit-auth (Docker Compose)
cd /opt/srp-smartrecruit-auth
git pull origin main
docker compose build --no-cache app
docker compose up -d --force-recreate app

# Verify containers
docker ps | grep srp
curl https://recruit.srpailabs.com/api/health
```

## Project Structure (current)

```
SRP Smartrecruit/
├── nextjs-auth/                  # Next.js 16.2.3 App Router — PRIMARY FRONTEND
│   ├── app/
│   │   ├── dashboard/page.tsx    # Main dashboard (~4000 lines, all tabs)
│   │   ├── globals.css           # Enterprise design system CSS
│   │   ├── api/                  # Next.js API routes
│   │   │   ├── audit/            # GET/POST audit logs
│   │   │   ├── candidates/       # CRUD + stage changes + duplicate guard
│   │   │   ├── jobs/             # Job CRUD
│   │   │   ├── screen/           # AI screening + ai_screening_data persistence
│   │   │   ├── import/           # CSV bulk import
│   │   │   ├── jd/               # JD generation
│   │   │   ├── boolean-search/   # Boolean search
│   │   │   ├── tenant/           # Multi-tenant invite flow
│   │   │   └── ...
│   ├── lib/
│   │   ├── audit.ts              # Fire-and-forget logAudit()
│   │   ├── db.ts                 # PostgreSQL pool
│   │   └── auth.ts               # NextAuth config
│   └── db/
│       ├── schema.sql            # Base schema
│       ├── migrate_v5_enterprise.sql
│       ├── migrate_v7_ai_screening_data.sql  # ai_screening_data JSONB column
│       ├── migrate_v8c_final.sql             # API keys, audit columns
│       ├── migrate_v10_invite_hardening.sql  # Invite token hashing
│       └── migrate_v11_dup_index.sql         # Partial email uniqueness index
├── backend/                      # Legacy FastAPI backend (v3.2)
├── frontend/                     # Legacy HTML templates
├── docs/                         # Technical documentation
├── deployment/                   # nginx, systemd, deploy scripts
└── db/                           # Legacy DB scripts
```

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

# GitHub Actions — Required Secrets

Both repos need these secrets configured in **Settings → Secrets and variables → Actions**.

## Backend repo (`/opt/srp-ats` → `clean_main` branch)

| Secret | Value |
|--------|-------|
| `HETZNER_HOST` | `5.223.67.236` |
| `HETZNER_USER` | `deploy` (or your SSH user) |
| `HETZNER_SSH_KEY` | Private SSH key (paste full PEM including headers) |
| `HETZNER_PORT` | `22` (optional, defaults to 22) |
| `PRODUCTION_ENV_BACKEND` | Full contents of `/opt/srp-ats/.env` on the server |

### Generate SSH key pair (one-time on any machine)

```bash
ssh-keygen -t ed25519 -C "github-actions-srp" -f ~/.ssh/srp_deploy_ed25519 -N ""
# Add public key to server:
cat ~/.ssh/srp_deploy_ed25519.pub >> ~/.ssh/authorized_keys   # on the server
# Paste private key content into HETZNER_SSH_KEY secret:
cat ~/.ssh/srp_deploy_ed25519
```

### `PRODUCTION_ENV_BACKEND` contents (fill in real values)

```env
OPENAI_API_KEY=sk-or-v1-YOUR_KEY
OPENAI_BASE_URL=https://openrouter.ai/api/v1
OPENAI_MODEL=openai/gpt-4.1-mini
POSTGRES_PASSWORD=YOUR_STRONG_PASSWORD
ENVIRONMENT=production
DEBUG=False
LOG_LEVEL=INFO
SECRET_KEY=YOUR_64_CHAR_RANDOM_STRING
CORS_ORIGINS=https://recruit.srpailabs.com
ALLOWED_HOSTS=recruit.srpailabs.com
ENABLE_LEGACY_COMPAT_ROUTES=false
DB_AUTO_INIT=false
N8N_BASE_URL=https://n8n.srpailabs.com
SEED_DEMO=false
```

---

## Frontend repo (`/opt/srp-smartrecruit-auth` → `main` branch)

| Secret | Value |
|--------|-------|
| `HETZNER_HOST` | `5.223.67.236` |
| `HETZNER_USER` | `deploy` |
| `HETZNER_SSH_KEY` | Same private key as above |
| `HETZNER_PORT` | `22` (optional) |
| `PRODUCTION_ENV` | Full contents of `/opt/srp-smartrecruit-auth/.env` on server |
| `NEXT_PUBLIC_SUPABASE_URL` | Your Supabase project URL (used in CI build step only) |

### `PRODUCTION_ENV` contents

```env
NEXTAUTH_URL=https://recruit.srpailabs.com
NEXTAUTH_SECRET=<openssl rand -base64 32>
GOOGLE_CLIENT_ID=<your-google-client-id>
GOOGLE_CLIENT_SECRET=<your-google-client-secret>
DATABASE_URL=postgresql://srp_auth:YOUR_PASSWORD@db:5432/srp_auth
POSTGRES_PASSWORD=YOUR_PASSWORD
OPENAI_API_KEY=sk-or-v1-YOUR_KEY
OPENAI_BASE_URL=https://openrouter.ai/api/v1
OPENAI_MODEL=openai/gpt-4.1-mini
TELEGRAM_BOT_TOKEN=7776487199:AAGrDPIIA50a8ipVK6F4UJ1Hrn5HsXvK7vw
TELEGRAM_CHAT_ID=7144152487
OWNER_EMAIL=pasikantishashank24@gmail.com
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=pasikantishashank24@gmail.com
SMTP_PASS=YOUR_GMAIL_APP_PASSWORD
NODE_ENV=production
NEXT_PUBLIC_OWNER_EMAIL=pasikantishashank24@gmail.com
```

---

## Manual deploy (from server)

```bash
# Deploy both services at once (no-disturbance):
bash /opt/srp-ats/deployment/deploy_all.sh

# Deploy backend only:
bash /opt/srp-ats/deployment/deploy.sh

# Deploy frontend only:
cd /opt/srp-smartrecruit-auth && bash deploy.sh

# Run E2E tests manually:
cd /opt/srp-ats
SRP_DEPLOY_HOST=5.223.67.236 \
SRP_DEPLOY_USER=deploy \
SRP_DEPLOY_KEY_PATH=~/.ssh/srp_deploy_ed25519 \
SRP_DEPLOY_DOMAIN=recruit.srpailabs.com \
  python3 deployment/e2e_test.py
```

---

## Port & network map

| Container | Internal port | Host binding | Project network |
|-----------|--------------|-------------|-----------------|
| `srp-ats-app` (FastAPI) | 8000 | `127.0.0.1:8009` | `srp_ats_internal` |
| `srp-ats-db` (Postgres) | 5432 | **none** | `srp_ats_internal` |
| `srp-auth-app` (Next.js) | 3000 | `127.0.0.1:3010` | `srp_auth_net` |
| `srp-auth-db` (Postgres) | 5432 | **none** | `srp_auth_net` |

Nginx routes:
- `https://recruit.srpailabs.com/health` → FastAPI :8009  
- `https://recruit.srpailabs.com/api/auth/(providers|csrf|session|...)` → Next.js :3010  
- `https://recruit.srpailabs.com/api/(screen|jobs|candidates|...)` → Next.js :3010  
- `https://recruit.srpailabs.com/api/auth/` → FastAPI :8009  
- `https://recruit.srpailabs.com/api/` → FastAPI :8009 (catch-all)  
- `https://recruit.srpailabs.com/` → Next.js :3010  

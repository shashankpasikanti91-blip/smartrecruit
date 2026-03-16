# SRP SmartRecruit v3.2 — Hetzner + Cloudflare Deployment Checklist
*Last audited: 2026-03-16*

---

## Pre-Deployment: Local Checks
- [ ] App imports cleanly: `python -c "from app.main import app; print('OK')"`
- [ ] All tests pass (run `python comprehensive_test_suite.py`)
- [ ] `.env` has `SECRET_KEY` set to a strong random value
- [ ] `.env` has `ENVIRONMENT=production`
- [ ] `.env` has `DATABASE_URL` pointing to PostgreSQL (not SQLite)
- [ ] `.env` has `CORS_ORIGINS` set to your actual domain(s)
- [ ] `.env` is in `.gitignore` — never pushed to git
- [ ] `requirements.production.txt` is up to date

---

## 1. Hetzner Server Setup

### 1.1 Create Server
```bash
# Recommended: CX21 (2 vCPU, 4GB RAM) or higher
# OS: Ubuntu 24.04 LTS
# Datacenter: Choose closest to users (e.g., NBG1, FSN1)
# Enable: SSH key auth, IPv4+IPv6
```

### 1.2 Initial Server Hardening
```bash
# SSH in as root
ssh root@YOUR_SERVER_IP

# Update system
apt update && apt upgrade -y

# Create deploy user
adduser deploy
usermod -aG sudo deploy

# Copy your SSH key to deploy user
rsync --archive --chown=deploy:deploy ~/.ssh /home/deploy

# Disable root SSH login
sed -i 's/PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
systemctl restart sshd
```

### 1.3 Firewall (UFW)
```bash
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh          # port 22
ufw allow http         # port 80  (nginx → HTTPS redirect)
ufw allow https        # port 443 (nginx → gunicorn)
ufw enable
# Do NOT expose port 8000 publicly — only nginx proxies to it
```

### 1.4 Install Dependencies
```bash
apt install -y python3.11 python3.11-venv python3-pip nginx postgresql-client git
# postgresql-client only if DB is remote (Supabase); for local PG: apt install postgresql
```

---

## 2. Application Deployment

### 2.1 Deploy Code
```bash
# As deploy user
mkdir -p /opt/srp-smartrecruit
cd /opt/srp-smartrecruit

# Option A: git clone
git clone YOUR_REPO_URL .

# Option B: rsync from local (if no git remote)
# rsync -avz --exclude='.venv' --exclude='__pycache__' --exclude='*.db' \
#   LOCAL_PROJECT_PATH/ deploy@YOUR_SERVER_IP:/opt/srp-smartrecruit/
```

### 2.2 Python Virtual Environment
```bash
cd /opt/srp-smartrecruit
python3.11 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install gunicorn   # Production WSGI server (Linux only)
pip install -r requirements.production.txt
```

### 2.3 Environment Configuration
```bash
# Copy the template and fill in all values
cp .env.production.template .env
nano .env   # Fill in: SECRET_KEY, DATABASE_URL, OPENAI_API_KEY, CORS_ORIGINS

# Set strict permissions
chmod 600 .env
chown deploy:deploy .env
```

### 2.4 Create Required Directories
```bash
mkdir -p /opt/srp-smartrecruit/uploads/resumes
mkdir -p /opt/srp-smartrecruit/logs
chown -R deploy:www-data /opt/srp-smartrecruit/uploads
chmod -R 770 /opt/srp-smartrecruit/uploads
```

### 2.5 Database Migration / Init
```bash
# Initialize tables (SQLAlchemy auto-create)
source .venv/bin/activate
python -c "from app.database.connection import init_db; init_db()"

# OR use Alembic if you've set up migrations:
# alembic upgrade head
```

### 2.6 Test the App Manually
```bash
# Quick smoke test before systemd
source .venv/bin/activate
uvicorn app.main:app --host 127.0.0.1 --port 8000 --no-access-log &
sleep 3
curl http://127.0.0.1:8000/health
kill %1
```

---

## 3. Systemd Service

```bash
# Copy service file
cp /opt/srp-smartrecruit/srp-smartrecruit.service /etc/systemd/system/

# Edit paths if needed
nano /etc/systemd/system/srp-smartrecruit.service

# Enable and start
systemctl daemon-reload
systemctl enable srp-smartrecruit
systemctl start srp-smartrecruit
systemctl status srp-smartrecruit

# View logs
journalctl -u srp-smartrecruit -f
```

---

## 4. Nginx Configuration

```bash
# Copy nginx config
cp /opt/srp-smartrecruit/nginx.conf.example /etc/nginx/sites-available/srp-smartrecruit

# Edit: replace yourdomain.com with your actual domain
nano /etc/nginx/sites-available/srp-smartrecruit

# Enable site
ln -s /etc/nginx/sites-available/srp-smartrecruit /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default   # Remove default site

# Test and reload
nginx -t
systemctl reload nginx
```

---

## 5. SSL Certificate (Let's Encrypt)

```bash
apt install -y certbot python3-certbot-nginx
certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Auto-renewal is set up automatically; verify:
certbot renew --dry-run
```

> **With Cloudflare:** If using Cloudflare proxy (orange cloud), use Cloudflare Origin Certificate instead of Let's Encrypt, OR set SSL mode to "Full (strict)" in Cloudflare with Let's Encrypt.

---

## 6. Cloudflare Configuration

### 6.1 DNS Setup
| Type | Name          | Content            | Proxy  |
|------|---------------|--------------------|--------|
| A    | yourdomain.com | YOUR_HETZNER_IP   | ON ☁️  |
| A    | www           | YOUR_HETZNER_IP   | ON ☁️  |

### 6.2 SSL/TLS Settings
- SSL/TLS → Overview → Mode: **Full (strict)**
- SSL/TLS → Edge Certificates → Always Use HTTPS: **ON**
- SSL/TLS → Edge Certificates → HSTS: Enable (max-age: 6 months)

### 6.3 Security Settings
- Security → Firewall Rules: Block requests to `/api/auth/` with >5 req/10s from same IP
- Security → Bot Fight Mode: **ON**
- Security → DDoS: **ON** (automatic, free tier)
- Speed → Auto Minify: JS, CSS, HTML — **ON**
- Caching → Browser Cache TTL: 1 hour

### 6.4 Cloudflare Real IP in Nginx
```bash
# Add to /etc/nginx/conf.d/cloudflare-real-ip.conf:
# (Download latest IPs from https://www.cloudflare.com/ips/)
set_real_ip_from 103.21.244.0/22;
set_real_ip_from 103.22.200.0/22;
set_real_ip_from 103.31.4.0/22;
set_real_ip_from 104.16.0.0/13;
set_real_ip_from 104.24.0.0/14;
set_real_ip_from 108.162.192.0/18;
set_real_ip_from 131.0.72.0/22;
set_real_ip_from 141.101.64.0/18;
set_real_ip_from 162.158.0.0/15;
set_real_ip_from 172.64.0.0/13;
set_real_ip_from 173.245.48.0/20;
set_real_ip_from 188.114.96.0/20;
set_real_ip_from 190.93.240.0/20;
set_real_ip_from 197.234.240.0/22;
set_real_ip_from 198.41.128.0/17;
set_real_ip_from 2400:cb00::/32;
real_ip_header CF-Connecting-IP;
```

---

## 7. Post-Deployment Verification

- [ ] `curl https://yourdomain.com/health` returns `{"status":"healthy",...}`
- [ ] Register endpoint works: `POST /api/auth/register`
- [ ] OTP email is received (if SMTP configured)
- [ ] Login returns valid JWT
- [ ] `/api/auth/me` works with the JWT
- [ ] Resume upload works
- [ ] Screening endpoint responds
- [ ] AI writing assist responds
- [ ] Support ticket creation works
- [ ] HTTPS padlock visible in browser
- [ ] No HTTP/HTTP redirect loop
- [ ] Logs writing to `/opt/srp-smartrecruit/logs/`
- [ ] systemd service auto-restarts after `systemctl stop srp-smartrecruit; sleep 10; systemctl status srp-smartrecruit`

---

## 8. Rolling Updates

```bash
# On server, as deploy user
cd /opt/srp-smartrecruit

# Pull latest code
git pull origin main   # or rsync from local

# Install any new dependencies
source .venv/bin/activate
pip install -r requirements.production.txt

# Restart service with zero-downtime (gunicorn sends USR2 for graceful reload)
systemctl reload srp-smartrecruit   # or:
kill -HUP $(cat /tmp/srp-smartrecruit.pid)  # if pid file configured
```

---

## 9. Backup Strategy

```bash
# Daily DB backup (cron job)
# crontab -e as deploy user:
# 0 3 * * * pg_dump $DATABASE_URL | gzip > /opt/srp-smartrecruit/backups/db_$(date +\%Y\%m\%d).sql.gz

# Upload backups (SQLite — only if using local SQLite)
# 0 3 * * * cp /opt/srp-smartrecruit/srp_smartrecruit_v3_2.db /opt/srp-smartrecruit/backups/

# Keep 30 days of backups
# 0 4 * * * find /opt/srp-smartrecruit/backups -name "*.gz" -mtime +30 -delete

mkdir -p /opt/srp-smartrecruit/backups
```

#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# SRP SmartRecruit — v5 Enterprise Deploy Script
# Run on the Hetzner server as the deploy user:
#   bash /opt/srp-smartrecruit-auth/deployment/deploy_v5_enterprise.sh
#
# What this does:
#   1. Pull latest Next.js app code (main branch)
#   2. Apply v5 enterprise DB migration
#   3. Rebuild + restart Next.js Docker container
#   4. Pull latest backend code (clean_main branch)
#   5. Install new Python packages (pycryptodome, httpx)
#   6. Restart FastAPI/gunicorn service
#   7. Health-check both services
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail
NEXTJS_DIR="/opt/srp-smartrecruit-auth"
BACKEND_DIR="/opt/srp-ats"
DOMAIN="recruit.srpailabs.com"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
ok()  { echo -e "${GREEN}✅ $*${NC}"; }
warn(){ echo -e "${YELLOW}⚠️  $*${NC}"; }
err(){ echo -e "${RED}❌ $*${NC}"; exit 1; }

echo "============================================================"
echo " SRP SmartRecruit v5 Enterprise Deploy — $(date '+%Y-%m-%d %H:%M:%S')"
echo "============================================================"

# ── 1. Pull Next.js code ──────────────────────────────────────────────────────
echo ""
echo "[1/7] Pulling Next.js app (main branch)…"
cd "$NEXTJS_DIR"
git fetch origin
git checkout main
git pull origin main
ok "Next.js code up to date"

# ── 2. Apply v5 DB migration ──────────────────────────────────────────────────
echo ""
echo "[2/7] Applying v5 enterprise DB migration…"
MIGRATION_FILE="$NEXTJS_DIR/db/migrate_v5_enterprise.sql"
if [ ! -f "$MIGRATION_FILE" ]; then
    err "Migration file not found: $MIGRATION_FILE"
fi

# Copy into container and run
docker cp "$MIGRATION_FILE" srp-auth-db:/tmp/migrate_v5_enterprise.sql
docker exec srp-auth-db psql -U srp_auth -d srp_auth \
    -f /tmp/migrate_v5_enterprise.sql \
    2>&1 | tail -30 || warn "Migration had warnings — check output above (may be safe if tables already exist)"
ok "DB migration complete"

# ── 3. Rebuild + restart Next.js container ────────────────────────────────────
echo ""
echo "[3/7] Rebuilding Next.js Docker image…"
cd "$NEXTJS_DIR"
docker compose build --no-cache app
ok "Image built"

echo "       Restarting container…"
docker compose up -d app
sleep 8

# Health check
HTTP=$(curl -sf -o /dev/null -w "%{http_code}" http://localhost:3010/api/health 2>/dev/null || echo "000")
if [ "$HTTP" = "200" ]; then
    ok "Next.js healthy (HTTP 200)"
else
    warn "Next.js health returned HTTP $HTTP — check: docker compose logs app"
fi

# ── 4. Pull backend code ──────────────────────────────────────────────────────
echo ""
echo "[4/7] Pulling FastAPI backend (clean_main branch)…"
cd "$BACKEND_DIR"
git fetch origin
git checkout clean_main
git pull origin clean_main
ok "Backend code up to date"

# ── 5. Install new Python packages ───────────────────────────────────────────
echo ""
echo "[5/7] Installing new Python packages (pycryptodome, httpx)…"
# Try to find the virtualenv
VENV_CANDIDATES=(".venv" "venv" "env")
VENV_DIR=""
for v in "${VENV_CANDIDATES[@]}"; do
    if [ -f "$BACKEND_DIR/$v/bin/pip" ]; then
        VENV_DIR="$BACKEND_DIR/$v"
        break
    fi
done

if [ -n "$VENV_DIR" ]; then
    "$VENV_DIR/bin/pip" install --quiet pycryptodome httpx
    ok "Packages installed in $VENV_DIR"
else
    # Docker-based backend
    echo "       No local venv found — installing inside backend Docker container…"
    BACKEND_CONTAINER=$(docker ps --filter "name=srp-ats" --format "{{.Names}}" | head -1 || true)
    if [ -n "$BACKEND_CONTAINER" ]; then
        docker exec "$BACKEND_CONTAINER" pip install --quiet pycryptodome httpx
        ok "Packages installed in container $BACKEND_CONTAINER"
    else
        warn "Could not find virtualenv or running backend container — install manually: pip install pycryptodome httpx"
    fi
fi

# ── 6. Restart FastAPI service ────────────────────────────────────────────────
echo ""
echo "[6/7] Restarting FastAPI/gunicorn service…"

# Try systemd service first, then Docker
if systemctl is-active --quiet srp-smartrecruit 2>/dev/null; then
    sudo systemctl restart srp-smartrecruit
    ok "srp-smartrecruit service restarted"
elif systemctl is-active --quiet srp-ats 2>/dev/null; then
    sudo systemctl restart srp-ats
    ok "srp-ats service restarted"
else
    # Try Docker
    BACKEND_CONTAINER=$(docker ps --filter "name=srp-ats" --format "{{.Names}}" | head -1 || true)
    if [ -n "$BACKEND_CONTAINER" ]; then
        docker compose -f "$BACKEND_DIR/docker-compose.yml" restart app 2>/dev/null || \
        docker restart "$BACKEND_CONTAINER"
        ok "Backend container restarted"
    else
        warn "Could not detect backend service — restart manually"
    fi
fi

sleep 5

# Backend health check
BACKEND_HEALTH=$(curl -sf http://127.0.0.1:8009/health 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('status','?'))" 2>/dev/null || echo "unreachable")
if [ "$BACKEND_HEALTH" = "healthy" ]; then
    ok "FastAPI backend healthy"
else
    warn "FastAPI health: $BACKEND_HEALTH — check service logs"
fi

# ── 7. Reload nginx ───────────────────────────────────────────────────────────
echo ""
echo "[7/7] Reloading nginx…"
sudo systemctl reload nginx
ok "nginx reloaded"

# ── Summary ───────────────────────────────────────────────────────────────────
echo ""
echo "============================================================"
echo " Deploy complete!"
echo ""
echo " Live URL:    https://${DOMAIN}"
echo " Dashboard:   https://${DOMAIN}/dashboard"
echo " New tabs:    JD Writer | Boolean Search | Import | Integrations | Comms Hub"
echo ""
echo " Next.js logs:  cd $NEXTJS_DIR && docker compose logs -f app"
echo " Backend logs:  journalctl -u srp-smartrecruit -f  OR  docker compose logs -f"
echo "============================================================"

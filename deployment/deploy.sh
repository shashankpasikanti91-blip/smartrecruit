#!/usr/bin/env bash
# SRP SmartRecruit v3.2 — Production Deploy Script
# Server: Hetzner 5.223.67.236  |  Domain: recruit.srpailabs.com
# Run this on the server: bash deployment/deploy.sh
set -euo pipefail

APP_DIR="/opt/srp-ats"
NGINX_CONF="/etc/nginx/sites-available/recruit.srpailabs.com"
NGINX_ENABLED="/etc/nginx/sites-enabled/recruit.srpailabs.com"

echo "============================================================"
echo " SRP SmartRecruit — Deploy $(date '+%Y-%m-%d %H:%M:%S')"
echo "============================================================"

# ── 1. Pull latest code ────────────────────────────────────────
echo "[1/7] Pulling latest code..."
cd "$APP_DIR"
git pull origin main

# ── 2. Update nginx config ────────────────────────────────────
echo "[2/7] Updating nginx config..."
cp "$APP_DIR/deployment/recruit.srpailabs.com.nginx" "$NGINX_CONF"
ln -sf "$NGINX_CONF" "$NGINX_ENABLED" 2>/dev/null || true
nginx -t
echo "      Nginx config OK"

# ── 3. Stop running containers ────────────────────────────────
echo "[3/7] Stopping containers..."
docker compose down --remove-orphans

# ── 4. Build fresh image ──────────────────────────────────────
echo "[4/7] Building Docker image (no cache)..."
docker compose build --no-cache app

# ── 5. Start services ─────────────────────────────────────────
echo "[5/7] Starting services..."
docker compose up -d

# ── 6. Wait for health check ──────────────────────────────────
echo "[6/7] Waiting for app to become healthy..."
for i in $(seq 1 30); do
    STATUS=$(curl -sf http://127.0.0.1:8009/health 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('status','?'))" 2>/dev/null || echo "waiting")
    if [ "$STATUS" = "healthy" ]; then
        echo "      App is healthy!"
        break
    fi
    echo "      Attempt $i/30 — status: $STATUS"
    sleep 3
done

# ── 7. Reload nginx ───────────────────────────────────────────
echo "[7/7] Reloading nginx..."
systemctl reload nginx

echo ""
echo "============================================================"
echo " Deploy complete!"
echo " Live URL: https://recruit.srpailabs.com"
echo " App:      https://recruit.srpailabs.com/app"
echo " Health:   https://recruit.srpailabs.com/health"
echo "============================================================"
echo ""
echo "Logs: docker compose logs -f app"
echo "DB:   docker compose exec db psql -U srp_ats -d srp_ats"

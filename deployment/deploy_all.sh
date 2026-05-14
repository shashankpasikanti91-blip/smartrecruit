#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# SRP SmartRecruit — Full-Stack Deploy Script (no-disturbance)
# Rebuilds & redeploys BOTH services on the Hetzner server.
# Other projects (mediflow, n8n, etc.) are never touched.
#
# Usage (on the server):
#   bash /opt/srp-ats/deployment/deploy_all.sh
#
# What it does:
#   1. Pull latest backend code  (clean_main branch → /opt/srp-ats)
#   2. Pull latest frontend code (main branch       → /opt/srp-smartrecruit-auth)
#   3. Rebuild backend Docker image  (only srp-ats-app — DB stays up)
#   4. Rebuild frontend Docker image (only srp-auth-app — DB stays up)
#   5. Health-check both services
#   6. Reload nginx
#   7. Run local E2E smoke tests
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

BACKEND_DIR="/opt/srp-ats"
FRONTEND_DIR="/opt/srp-smartrecruit-auth"
DOMAIN="recruit.srpailabs.com"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
ok()   { echo -e "${GREEN}  ✅ $*${NC}"; }
warn() { echo -e "${YELLOW}  ⚠️  $*${NC}"; }
err()  { echo -e "${RED}  ❌ $*${NC}"; exit 1; }
step() { echo -e "\n${CYAN}══════════════════════════════════════════════${NC}"; echo -e "${CYAN}  $*${NC}"; echo -e "${CYAN}══════════════════════════════════════════════${NC}"; }

echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║   SRP SmartRecruit — Full-Stack Deploy               ║"
echo "║   $(date '+%Y-%m-%d %H:%M:%S UTC')                       ║"
echo "╚══════════════════════════════════════════════════════╝"

# ── Guard: verify both project dirs exist ─────────────────────────────────────
[ -d "$BACKEND_DIR/.git" ]  || err "Backend dir not found: $BACKEND_DIR"
[ -d "$FRONTEND_DIR/.git" ] || err "Frontend dir not found: $FRONTEND_DIR"

# ══════════════════════════════════════════════════════════════════════════════
step "[1/7] Pull latest backend code (clean_main)"
cd "$BACKEND_DIR"
git fetch origin
git checkout clean_main
git pull --ff-only origin clean_main
ok "Backend code up to date"

# ══════════════════════════════════════════════════════════════════════════════
step "[2/7] Pull latest frontend code (main)"
cd "$FRONTEND_DIR"
git fetch origin
git checkout main
git pull --ff-only origin main
ok "Frontend code up to date"

# ══════════════════════════════════════════════════════════════════════════════
step "[3/7] Rebuild backend Docker image (DB untouched)"
cd "$BACKEND_DIR"

# Only stop/remove the app container — srp-ats-db keeps running
docker compose stop app  2>/dev/null || true
docker compose rm -f app 2>/dev/null || true

docker compose build --no-cache app
docker compose up -d
ok "Backend image built and started"

# Wait for FastAPI to become healthy
echo "  Waiting for FastAPI health..."
for i in $(seq 1 30); do
  STATUS=$(curl -sf http://127.0.0.1:8009/health 2>/dev/null \
    | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('status','?'))" 2>/dev/null \
    || echo "waiting")
  if [ "$STATUS" = "healthy" ]; then
    ok "FastAPI healthy (attempt $i)"
    break
  fi
  if [ "$i" -eq 30 ]; then
    warn "FastAPI health check timed out — check: docker logs srp-ats-app"
  fi
  echo "    attempt $i/30 — $STATUS"
  sleep 3
done

# ══════════════════════════════════════════════════════════════════════════════
step "[4/7] Rebuild frontend Docker image (DB untouched)"
cd "$FRONTEND_DIR"

# Only stop/remove the app container — srp-auth-db keeps running
docker compose stop app  2>/dev/null || true
docker compose rm -f app 2>/dev/null || true

docker compose build --no-cache app
docker compose up -d
ok "Frontend image built and started"

# Wait for Next.js to become healthy
echo "  Waiting for Next.js health..."
for i in $(seq 1 25); do
  HTTP=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:3010/api/health 2>/dev/null || echo "000")
  if [ "$HTTP" = "200" ]; then
    ok "Next.js healthy (attempt $i)"
    break
  fi
  if [ "$i" -eq 25 ]; then
    warn "Next.js health check timed out — check: docker logs srp-auth-app"
  fi
  echo "    attempt $i/25 — HTTP $HTTP"
  sleep 4
done

# ══════════════════════════════════════════════════════════════════════════════
step "[5/7] Reload nginx"
nginx -t 2>&1 | tail -5
systemctl reload nginx
ok "Nginx reloaded"

# ══════════════════════════════════════════════════════════════════════════════
step "[6/7] Container status (all projects)"
echo ""
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# ══════════════════════════════════════════════════════════════════════════════
step "[7/7] Local E2E smoke tests"

CHECKS_PASS=0
CHECKS_FAIL=0

smoke() {
  local label="$1" cmd="$2" expected="$3"
  local out
  out=$(eval "$cmd" 2>/dev/null || true)
  if echo "$out" | grep -qi "$expected"; then
    echo -e "  ${GREEN}[PASS]${NC} $label"
    CHECKS_PASS=$((CHECKS_PASS + 1))
  else
    echo -e "  ${RED}[FAIL]${NC} $label  ← got: ${out:0:100}"
    CHECKS_FAIL=$((CHECKS_FAIL + 1))
  fi
}

smoke "FastAPI /health (local)"           "curl -sf http://127.0.0.1:8009/health"            "healthy"
smoke "Next.js /api/health (local)"       "curl -sf http://127.0.0.1:3010/api/health"        "ok\|healthy\|200"
smoke "HTTPS /health via nginx"           "curl -sk https://$DOMAIN/health"                  "healthy"
smoke "HTTPS / (Next.js landing)"        "curl -skI https://$DOMAIN/ | head -1"             "200\|301\|302\|307"
smoke "HTTPS /login (Next.js)"           "curl -skI https://$DOMAIN/login | head -1"        "200\|301\|302\|307"
smoke "HTTPS /api/auth/csrf via nginx"   "curl -sk https://$DOMAIN/api/auth/csrf"           "csrfToken"
smoke "HTTPS /api/auth/providers"        "curl -sk https://$DOMAIN/api/auth/providers"      "credentials\|{"
smoke "FastAPI guard /api/auth/me"       "curl -sk -o /dev/null -w '%{http_code}' https://$DOMAIN/api/auth/me" "401\|403\|405"
smoke "srp-ats-app container Up"         "docker ps --filter name=srp-ats-app --format '{{.Status}}'"  "Up"
smoke "srp-auth-app container Up"        "docker ps --filter name=srp-auth-app --format '{{.Status}}'" "Up"
smoke "srp-ats-db container Up"          "docker ps --filter name=srp-ats-db --format '{{.Status}}'"   "Up"
smoke "srp-auth-db container Up"         "docker ps --filter name=srp-auth-db --format '{{.Status}}'"  "Up"

echo ""
TOTAL=$((CHECKS_PASS + CHECKS_FAIL))
if [ "$CHECKS_FAIL" -eq 0 ]; then
  echo -e "${GREEN}  ✅ All ${TOTAL} smoke checks passed${NC}"
else
  warn "$CHECKS_FAIL/$TOTAL checks failed — review output above"
fi

# ── Summary ───────────────────────────────────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║  Deploy complete!                                    ║"
echo "║  FastAPI: https://$DOMAIN/health         ║"
echo "║  App:     https://$DOMAIN/               ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""
echo "  Logs:"
echo "    docker logs -f srp-ats-app   # FastAPI"
echo "    docker logs -f srp-auth-app  # Next.js"
echo ""

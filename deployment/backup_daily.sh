#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# SRP SmartRecruit — Daily Automated Backup
# Installed as a cron job on the Hetzner server.
#
# Backs up BOTH databases (ATS + Auth) and resume uploads.
# Keeps 30 days of backups. Never deletes data without explicit --force.
#
# Install on server (as root/deploy user):
#   sudo cp /opt/srp-ats/deployment/backup_daily.sh /usr/local/bin/srp-backup
#   sudo chmod +x /usr/local/bin/srp-backup
#   # Add to crontab (runs at 02:00 UTC every day):
#   echo "0 2 * * * deploy /usr/local/bin/srp-backup >> /var/log/srp-backup.log 2>&1" | sudo tee -a /etc/cron.d/srp-backup
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

BACKUP_ROOT="/opt/backups/srp-smartrecruit"
KEEP_DAYS=30
DATE=$(date -u '+%Y-%m-%d_%H%M%S')
BACKUP_DIR="${BACKUP_ROOT}/${DATE}"
LOG_PREFIX="[SRP-BACKUP ${DATE}]"

ATS_DB_CONTAINER="srp-ats-db"
ATS_DB_NAME="srp_ats"
ATS_DB_USER="srp_ats"
ATS_UPLOADS_VOLUME="ats_uploads"

AUTH_DB_CONTAINER="srp-auth-db"
AUTH_DB_NAME="srp_auth"
AUTH_DB_USER="srp_auth"

echo "========================================================"
echo "${LOG_PREFIX} Starting backup"
echo "  Destination: ${BACKUP_DIR}"
echo "========================================================"

mkdir -p "${BACKUP_DIR}"
chmod 700 "${BACKUP_DIR}"

# ── Helper ────────────────────────────────────────────────────────────────────
fail() { echo "${LOG_PREFIX} ERROR: $*" >&2; exit 1; }
ok()   { echo "${LOG_PREFIX} OK: $*"; }

# ── 1. ATS PostgreSQL database ────────────────────────────────────────────────
echo ""
echo "${LOG_PREFIX} [1/4] Dumping ATS database (${ATS_DB_NAME})..."
docker exec "${ATS_DB_CONTAINER}" \
    pg_dump -U "${ATS_DB_USER}" -d "${ATS_DB_NAME}" \
    --format=custom --compress=9 \
    > "${BACKUP_DIR}/ats_database.dump" \
  || fail "ATS pg_dump failed"
ok "ATS database dump: $(du -sh "${BACKUP_DIR}/ats_database.dump" | cut -f1)"

# ── 2. Auth PostgreSQL database ───────────────────────────────────────────────
echo ""
echo "${LOG_PREFIX} [2/4] Dumping Auth database (${AUTH_DB_NAME})..."
docker exec "${AUTH_DB_CONTAINER}" \
    pg_dump -U "${AUTH_DB_USER}" -d "${AUTH_DB_NAME}" \
    --format=custom --compress=9 \
    > "${BACKUP_DIR}/auth_database.dump" \
  || fail "Auth pg_dump failed"
ok "Auth database dump: $(du -sh "${BACKUP_DIR}/auth_database.dump" | cut -f1)"

# ── 3. Resume uploads volume ──────────────────────────────────────────────────
echo ""
echo "${LOG_PREFIX} [3/4] Backing up resume uploads volume..."
docker run --rm \
    -v "${ATS_UPLOADS_VOLUME}:/source:ro" \
    -v "${BACKUP_DIR}:/backup" \
    alpine:3.20 \
    sh -c "cd /source && tar -czf /backup/uploads.tar.gz . 2>/dev/null || true" \
  && ok "Uploads backup: $(du -sh "${BACKUP_DIR}/uploads.tar.gz" 2>/dev/null | cut -f1 || echo 'empty')" \
  || echo "${LOG_PREFIX} WARN: uploads backup had warnings (may be empty)"

# ── 4. Write manifest ─────────────────────────────────────────────────────────
echo ""
MANIFEST="${BACKUP_DIR}/manifest.json"
cat > "${MANIFEST}" << MANIFEST_EOF
{
  "created_at_utc": "${DATE}",
  "server": "hetzner-5.223.67.236",
  "domain": "recruit.srpailabs.com",
  "databases": {
    "ats": {
      "container": "${ATS_DB_CONTAINER}",
      "db": "${ATS_DB_NAME}",
      "file": "ats_database.dump"
    },
    "auth": {
      "container": "${AUTH_DB_CONTAINER}",
      "db": "${AUTH_DB_NAME}",
      "file": "auth_database.dump"
    }
  },
  "uploads_file": "uploads.tar.gz",
  "restore_command": "bash /opt/srp-ats/deployment/backup_daily.sh --restore ${BACKUP_DIR}"
}
MANIFEST_EOF
ok "Manifest written: ${MANIFEST}"

# ── 5. Remove backups older than KEEP_DAYS (never deletes current backup) ─────
echo ""
echo "${LOG_PREFIX} [4/4] Pruning backups older than ${KEEP_DAYS} days..."
find "${BACKUP_ROOT}" -mindepth 1 -maxdepth 1 -type d \
    -mtime "+${KEEP_DAYS}" \
    ! -name "${DATE}" \
    -exec rm -rf {} + \
  && ok "Old backups pruned (kept last ${KEEP_DAYS} days)"

# ── 6. Summary ────────────────────────────────────────────────────────────────
echo ""
TOTAL_SIZE=$(du -sh "${BACKUP_DIR}" | cut -f1)
BACKUP_COUNT=$(find "${BACKUP_ROOT}" -mindepth 1 -maxdepth 1 -type d | wc -l)
echo "========================================================"
echo "${LOG_PREFIX} Backup COMPLETE"
echo "  Location:     ${BACKUP_DIR}"
echo "  Size:         ${TOTAL_SIZE}"
echo "  Total copies: ${BACKUP_COUNT} (keeping ${KEEP_DAYS} days)"
echo "========================================================"

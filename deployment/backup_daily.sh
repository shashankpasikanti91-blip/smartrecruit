#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# SRP SmartRecruit — Daily Automated Backup
# Installed as a cron job on the Hetzner server.
#
# Backs up BOTH databases (ATS + Auth) and resume uploads.
# LOCAL:  /opt/backups/srp-smartrecruit/ — 30-day retention
# ONLINE: Supabase Storage bucket "srp-backups" — permanent, offsite
# EMAIL:  Owner notified after every backup (success or failure)
#
# Install on server (as root/deploy user):
#   sudo bash /opt/srp-ats/deployment/install_backup_cron.sh
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

# ── Load credentials from the server's Next.js .env ──────────────────────────
# These are written by CI/CD during every deploy.
ENV_FILE="/opt/srp-smartrecruit-auth/.env"
SUPABASE_URL=""
SUPABASE_KEY=""
SMTP_HOST=""; SMTP_PORT="587"; SMTP_USER=""; SMTP_PASS=""; OWNER_EMAIL=""

if [[ -f "$ENV_FILE" ]]; then
    while IFS='=' read -r key value; do
        [[ "$key" =~ ^# ]] && continue
        value="${value%%#*}"         # strip inline comments
        value="${value//\"/}"        # strip quotes
        value="${value// /}"         # strip spaces around =
        case "$key" in
            NEXT_PUBLIC_SUPABASE_URL)  SUPABASE_URL="$value" ;;
            SUPABASE_SERVICE_ROLE_KEY) SUPABASE_KEY="$value" ;;
            SMTP_HOST)                 SMTP_HOST="$value" ;;
            SMTP_PORT)                 SMTP_PORT="$value" ;;
            SMTP_USER)                 SMTP_USER="$value" ;;
            SMTP_PASS)                 SMTP_PASS="$value" ;;
            OWNER_EMAIL|OWNER_EMAILS)  OWNER_EMAIL="$value" ;;
        esac
    done < <(grep -v '^$' "$ENV_FILE")
fi

SUPABASE_BUCKET="srp-backups"
CLOUD_UPLOAD_OK=0
EMAIL_SENT=0

echo "========================================================"
echo "${LOG_PREFIX} Starting backup"
echo "  Local:  ${BACKUP_DIR}"
echo "  Online: supabase://${SUPABASE_BUCKET}/${DATE}/"
echo "========================================================"

mkdir -p "${BACKUP_DIR}"
chmod 700 "${BACKUP_DIR}"

# ── Helper ────────────────────────────────────────────────────────────────────
fail() { echo "${LOG_PREFIX} ERROR: $*" >&2; exit 1; }
ok()   { echo "${LOG_PREFIX} OK: $*"; }
warn() { echo "${LOG_PREFIX} WARN: $*"; }

# ── 1. ATS PostgreSQL database ────────────────────────────────────────────────
echo ""
echo "${LOG_PREFIX} [1/6] Dumping ATS database (${ATS_DB_NAME})..."
docker exec "${ATS_DB_CONTAINER}" \
    pg_dump -U "${ATS_DB_USER}" -d "${ATS_DB_NAME}" \
    --format=custom --compress=9 \
    > "${BACKUP_DIR}/ats_database.dump" \
  || fail "ATS pg_dump failed"
ok "ATS database dump: $(du -sh "${BACKUP_DIR}/ats_database.dump" | cut -f1)"

# ── 2. Auth PostgreSQL database ───────────────────────────────────────────────
echo ""
echo "${LOG_PREFIX} [2/6] Dumping Auth database (${AUTH_DB_NAME})..."
docker exec "${AUTH_DB_CONTAINER}" \
    pg_dump -U "${AUTH_DB_USER}" -d "${AUTH_DB_NAME}" \
    --format=custom --compress=9 \
    > "${BACKUP_DIR}/auth_database.dump" \
  || fail "Auth pg_dump failed"
ok "Auth database dump: $(du -sh "${BACKUP_DIR}/auth_database.dump" | cut -f1)"

# ── 3. Resume uploads volume ──────────────────────────────────────────────────
echo ""
echo "${LOG_PREFIX} [3/6] Backing up resume uploads volume..."
docker run --rm \
    -v "${ATS_UPLOADS_VOLUME}:/source:ro" \
    -v "${BACKUP_DIR}:/backup" \
    alpine:3.20 \
    sh -c "cd /source && tar -czf /backup/uploads.tar.gz . 2>/dev/null || true" \
  && ok "Uploads backup: $(du -sh "${BACKUP_DIR}/uploads.tar.gz" 2>/dev/null | cut -f1 || echo 'empty')" \
  || echo "${LOG_PREFIX} WARN: uploads backup had warnings (may be empty)"

# ── 4. Write manifest ─────────────────────────────────────────────────────────
echo ""
echo "${LOG_PREFIX} [4/6] Writing manifest..."
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
echo "${LOG_PREFIX} [5/6] Pruning local backups older than ${KEEP_DAYS} days..."
find "${BACKUP_ROOT}" -mindepth 1 -maxdepth 1 -type d \
    -mtime "+${KEEP_DAYS}" \
    ! -name "${DATE}" \
    -exec rm -rf {} + \
  && ok "Old local backups pruned (kept last ${KEEP_DAYS} days)"

# ── 6. Upload to Supabase Storage (offsite cloud backup) ─────────────────────
echo ""
echo "${LOG_PREFIX} [6/6] Uploading to Supabase Storage (offsite)..."

supabase_upload() {
    local file_path="$1"
    local remote_name="$2"
    local remote_key="${DATE}/${remote_name}"
    local file_size
    file_size=$(du -b "${file_path}" 2>/dev/null | cut -f1 || echo 0)

    if [[ -z "$SUPABASE_URL" || -z "$SUPABASE_KEY" ]]; then
        warn "Supabase credentials not found — skipping cloud upload of ${remote_name}"
        return 1
    fi
    if [[ ! -f "$file_path" ]]; then
        warn "File not found, skipping upload: ${file_path}"
        return 1
    fi

    echo "  Uploading ${remote_name} ($(du -sh "${file_path}" | cut -f1))..."
    local http_code
    http_code=$(curl -s -o /dev/null -w "%{http_code}" \
        -X POST \
        "${SUPABASE_URL}/storage/v1/object/${SUPABASE_BUCKET}/${remote_key}" \
        -H "Authorization: Bearer ${SUPABASE_KEY}" \
        -H "Content-Type: application/octet-stream" \
        -H "x-upsert: true" \
        --data-binary @"${file_path}" \
        --max-time 300)

    if [[ "$http_code" =~ ^2 ]]; then
        ok "  Cloud upload OK — ${SUPABASE_URL}/storage/v1/object/public/${SUPABASE_BUCKET}/${remote_key}"
        return 0
    else
        warn "  Cloud upload failed: HTTP ${http_code} for ${remote_name}"
        return 1
    fi
}

# Ensure bucket exists (idempotent — 409 = already exists, both are fine)
if [[ -n "$SUPABASE_URL" && -n "$SUPABASE_KEY" ]]; then
    BUCKET_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
        -X POST \
        "${SUPABASE_URL}/storage/v1/bucket" \
        -H "Authorization: Bearer ${SUPABASE_KEY}" \
        -H "Content-Type: application/json" \
        -d "{\"id\":\"${SUPABASE_BUCKET}\",\"name\":\"${SUPABASE_BUCKET}\",\"public\":false}")
    if [[ "$BUCKET_CODE" == "200" || "$BUCKET_CODE" == "409" ]]; then
        ok "Supabase bucket '${SUPABASE_BUCKET}' ready"
    else
        warn "Could not ensure bucket exists (HTTP ${BUCKET_CODE}) — will still attempt upload"
    fi

    UPLOAD_ERRORS=0
    supabase_upload "${BACKUP_DIR}/ats_database.dump"  "ats_database.dump"  || UPLOAD_ERRORS=$((UPLOAD_ERRORS+1))
    supabase_upload "${BACKUP_DIR}/auth_database.dump" "auth_database.dump" || UPLOAD_ERRORS=$((UPLOAD_ERRORS+1))
    supabase_upload "${BACKUP_DIR}/uploads.tar.gz"     "uploads.tar.gz"     || UPLOAD_ERRORS=$((UPLOAD_ERRORS+1))
    supabase_upload "${BACKUP_DIR}/manifest.json"      "manifest.json"      || true  # manifest is small, best effort

    if [[ $UPLOAD_ERRORS -eq 0 ]]; then
        CLOUD_UPLOAD_OK=1
        ok "All files uploaded to Supabase Storage"
    else
        warn "${UPLOAD_ERRORS} file(s) failed to upload — local backup still intact"
    fi
else
    warn "Supabase not configured — only local backup was created"
fi

# ── 7. Email notification ─────────────────────────────────────────────────────
if [[ -n "$SMTP_HOST" && -n "$SMTP_USER" && -n "$SMTP_PASS" && -n "$OWNER_EMAIL" ]]; then
    echo ""
    TOTAL_SIZE=$(du -sh "${BACKUP_DIR}" | cut -f1)
    CLOUD_STATUS="✅ Uploaded to Supabase Storage"
    [[ $CLOUD_UPLOAD_OK -eq 0 ]] && CLOUD_STATUS="⚠️ Cloud upload failed — local only"

    SUBJECT="✅ SRP SmartRecruit Backup — ${DATE}"
    BODY="SRP SmartRecruit Daily Backup Report

Date:         ${DATE} UTC
Local path:   ${BACKUP_DIR}
Total size:   ${TOTAL_SIZE}
Cloud:        ${CLOUD_STATUS}
Bucket:       ${SUPABASE_BUCKET}/${DATE}/

Files backed up:
  • ats_database.dump   (ATS PostgreSQL)
  • auth_database.dump  (Auth PostgreSQL — harish, priya, shashank, owner accounts)
  • uploads.tar.gz      (Resume files)

Retention: ${KEEP_DAYS} days local + permanent cloud.
No data was deleted. Backup is read-only."

    # Send via curl + SMTP (no external tools needed)
    curl -s \
        --url "smtp://${SMTP_HOST}:${SMTP_PORT}" \
        --ssl-reqd \
        --mail-from "${SMTP_USER}" \
        --mail-rcpt "${OWNER_EMAIL}" \
        --user "${SMTP_USER}:${SMTP_PASS}" \
        -T <(printf "From: SRP Backup <${SMTP_USER}>\r\nTo: ${OWNER_EMAIL}\r\nSubject: ${SUBJECT}\r\n\r\n${BODY}\r\n") \
        2>/dev/null \
    && { EMAIL_SENT=1; ok "Email notification sent to ${OWNER_EMAIL}"; } \
    || warn "Email notification failed (backup is still fine)"
fi

# ── 8. Summary ────────────────────────────────────────────────────────────────
echo ""
TOTAL_SIZE=$(du -sh "${BACKUP_DIR}" | cut -f1)
BACKUP_COUNT=$(find "${BACKUP_ROOT}" -mindepth 1 -maxdepth 1 -type d | wc -l)
CLOUD_MSG="NOT uploaded (no credentials)"
[[ $CLOUD_UPLOAD_OK -eq 1 ]] && CLOUD_MSG="Uploaded to Supabase Storage ✓"
EMAIL_MSG="not sent"
[[ $EMAIL_SENT -eq 1 ]] && EMAIL_MSG="sent to ${OWNER_EMAIL}"
echo "========================================================"
echo "${LOG_PREFIX} Backup COMPLETE"
echo "  Local path:   ${BACKUP_DIR}"
echo "  Size:         ${TOTAL_SIZE}"
echo "  Local copies: ${BACKUP_COUNT} (${KEEP_DAYS}-day retention)"
echo "  Cloud:        ${CLOUD_MSG}"
echo "  Email:        ${EMAIL_MSG}"
echo "========================================================"

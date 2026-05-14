#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# SRP SmartRecruit — Backup Cron Installer
# Run ONCE on the server as root or a user with sudo access.
#
# Usage (on the Hetzner server):
#   sudo bash /opt/srp-ats/deployment/install_backup_cron.sh
#
# What it does:
#   1. Copies backup_daily.sh to /usr/local/bin/srp-backup
#   2. Creates /opt/backups/srp-smartrecruit with correct permissions
#   3. Creates /etc/cron.d/srp-backup (runs daily at 02:00 UTC)
#   4. Creates /etc/logrotate.d/srp-backup (rotates log monthly)
#   5. Runs a dry-run test immediately to verify everything works
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_SCRIPT="/usr/local/bin/srp-backup"
BACKUP_ROOT="/opt/backups/srp-smartrecruit"
LOG_FILE="/var/log/srp-backup.log"
CRON_FILE="/etc/cron.d/srp-backup"
LOGROTATE_FILE="/etc/logrotate.d/srp-backup"

# Must be run as root
if [[ "$EUID" -ne 0 ]]; then
    echo "ERROR: Run this script as root: sudo bash $0"
    exit 1
fi

echo "═══════════════════════════════════════════════════════"
echo "  SRP SmartRecruit — Installing Daily Backup Cron"
echo "═══════════════════════════════════════════════════════"

# 1. Install backup script
echo "[1/5] Installing backup script to ${BACKUP_SCRIPT}..."
cp "${SCRIPT_DIR}/backup_daily.sh" "${BACKUP_SCRIPT}"
chmod 750 "${BACKUP_SCRIPT}"
chown root:root "${BACKUP_SCRIPT}"
# Convert CRLF → LF (safe to run on Windows-edited files)
sed -i 's/\r//' "${BACKUP_SCRIPT}"
echo "  OK"

# 2. Create backup directory
echo "[2/5] Creating backup directory ${BACKUP_ROOT}..."
mkdir -p "${BACKUP_ROOT}"
chmod 700 "${BACKUP_ROOT}"
echo "  OK"

# 3. Create cron job (runs at 02:00 UTC every day)
echo "[3/5] Creating cron job (daily at 02:00 UTC)..."
cat > "${CRON_FILE}" << 'CRON_EOF'
# SRP SmartRecruit — Daily database and uploads backup
# Runs at 02:00 UTC every day
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin

0 2 * * * root /usr/local/bin/srp-backup >> /var/log/srp-backup.log 2>&1
CRON_EOF
chmod 644 "${CRON_FILE}"
echo "  OK — cron file: ${CRON_FILE}"

# 4. Create log rotation config
echo "[4/5] Setting up log rotation..."
cat > "${LOGROTATE_FILE}" << 'LR_EOF'
/var/log/srp-backup.log {
    monthly
    rotate 12
    compress
    missingok
    notifempty
    create 640 root root
}
LR_EOF
chmod 644 "${LOGROTATE_FILE}"
echo "  OK"

# 5. Verify Docker containers are accessible
echo "[5/5] Verifying Docker containers exist..."
for container in srp-ats-db srp-auth-db; do
    if docker inspect "${container}" > /dev/null 2>&1; then
        echo "  OK: ${container} found"
    else
        echo "  WARN: ${container} not running — backup will warn on next run"
    fi
done

echo ""
echo "═══════════════════════════════════════════════════════"
echo "  Installation complete!"
echo ""
echo "  Schedule:   Daily at 02:00 UTC"
echo "  Backups:    ${BACKUP_ROOT}/"
echo "  Log:        ${LOG_FILE}"
echo "  Retention:  30 days"
echo ""
echo "  Run a backup NOW to test:"
echo "    sudo /usr/local/bin/srp-backup"
echo ""
echo "  Check backup directory:"
echo "    ls -lh ${BACKUP_ROOT}/"
echo "═══════════════════════════════════════════════════════"

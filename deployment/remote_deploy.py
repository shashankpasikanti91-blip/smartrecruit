#!/usr/bin/env python3
"""
SRP SmartRecruit v5 — Remote deploy via SSH (password auth)
Usage: python remote_deploy.py
"""
import sys, time
import paramiko

HOST = "5.223.67.236"
USER = "root"
PASS = "856Reey@nsh"

COMMANDS = [
    # ── Next.js: pull + migrate DB + rebuild ──────────────────────────────
    ("Pulling Next.js code (main branch)",
     "cd /opt/srp-smartrecruit-auth && git fetch origin && git checkout main && git pull origin main"),

    ("Applying v5 enterprise DB migration",
     "cd /opt/srp-smartrecruit-auth && "
     "docker cp db/migrate_v5_enterprise.sql srp-auth-db:/tmp/migrate_v5.sql && "
     "docker exec srp-auth-db psql -U srp_auth -d srp_auth -f /tmp/migrate_v5.sql 2>&1 | tail -20"),

    ("Applying v6 short_id/audit_logs DB migration",
     "cd /opt/srp-smartrecruit-auth && "
     "docker cp db/migrate_v6_id_date_system.sql srp-auth-db:/tmp/migrate_v6.sql && "
     "docker exec srp-auth-db psql -U srp_auth -d srp_auth -f /tmp/migrate_v6.sql 2>&1 | tail -5"),

    ("Rebuilding Next.js Docker image (this may take 2-3 min)",
     "cd /opt/srp-smartrecruit-auth && docker compose build --no-cache app 2>&1 | tail -10"),

    ("Restarting Next.js container",
     "cd /opt/srp-smartrecruit-auth && docker compose up -d app 2>&1"),

    ("Checking Next.js health",
     "sleep 8 && curl -sf -o /dev/null -w 'HTTP %{http_code}' http://localhost:3010/api/health || echo 'not ready yet'"),

    # ── FastAPI backend: pull + install packages + restart ────────────────
    ("Pulling FastAPI backend (clean_main branch)",
     "cd /opt/srp-ats && git fetch origin && git checkout clean_main && git pull origin clean_main"),

    ("Installing new Python packages (pycryptodome, httpx)",
     "cd /opt/srp-ats && "
     "( [ -f .venv/bin/pip ] && .venv/bin/pip install -q pycryptodome httpx ) || "
     "( [ -f venv/bin/pip ] && venv/bin/pip install -q pycryptodome httpx ) || "
     "pip install -q pycryptodome httpx"),

    ("Restarting FastAPI service",
     "sudo systemctl restart srp-smartrecruit 2>/dev/null || "
     "sudo systemctl restart srp-ats 2>/dev/null || "
     "( cd /opt/srp-ats && docker compose restart app 2>/dev/null ) || "
     "echo 'WARNING: could not detect service name — restart manually'"),

    ("Checking FastAPI health",
     "sleep 5 && curl -sf http://127.0.0.1:8009/health 2>/dev/null | python3 -c \""
     "import sys,json; d=json.load(sys.stdin); print('FastAPI:', d.get('status','?'))\" "
     "2>/dev/null || echo 'FastAPI: not responding'"),

    # ── Reload nginx ──────────────────────────────────────────────────────
    ("Reloading nginx",
     "sudo systemctl reload nginx && echo 'nginx reloaded'"),
]

def run_step(client, label, cmd, timeout=180):
    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"{'='*60}")
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout, get_pty=False)
    out = stdout.read().decode(errors='replace').strip()
    err = stderr.read().decode(errors='replace').strip()
    if out:
        print(out)
    if err:
        # Many commands write informational output to stderr — show but don't abort
        print(f"[stderr] {err[:800]}")
    return out

def main():
    print("=== SRP SmartRecruit v5 Remote Deploy ===")
    print(f"Connecting to {USER}@{HOST}…")

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(HOST, username=USER, password=PASS, timeout=15,
                       look_for_keys=False, allow_agent=False)
    except Exception as e:
        print(f"SSH connect failed: {e}")
        sys.exit(1)

    print("Connected!\n")

    for label, cmd in COMMANDS:
        try:
            result = run_step(client, label, cmd)
        except Exception as e:
            print(f"[ERROR] {e}")

    client.close()
    print("\n" + "="*60)
    print("  Deploy complete!")
    print("  Live URL: https://recruit.srpailabs.com/dashboard")
    print("="*60)

if __name__ == "__main__":
    main()

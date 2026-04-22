import paramiko, time

HOST = "5.223.67.236"
USER = "root"
PASS = "856Reey@nsh"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, username=USER, password=PASS, timeout=30)

steps = [
    # ── 1. Pull latest FastAPI code (includes main.py /app fix) ──────────────
    ("Pull FastAPI latest code",
     "cd /opt/srp-ats && git checkout -- . && git pull origin clean_main 2>&1 | tail -8"),

    # ── 2. Restart FastAPI ────────────────────────────────────────────────────
    ("Restart FastAPI container",
     "cd /opt/srp-ats && docker compose restart app 2>&1"),

    # ── 3. Fix srpailabs.conf: remove dead recruit block and HTTP 80 entry ────
    # Remove 'recruit.srpailabs.com' from the multi-domain HTTP 80 server_name
    ("Remove recruit from srpailabs.conf HTTP block",
     r"sed -i 's/recruit\.srpailabs\.com\s*//g' /etc/nginx/sites-enabled/srpailabs.conf && echo 'HTTP block cleaned'"),

    # Remove 'mediflow.srpailabs.com recruit.srpailabs.com' references
    ("Clean up whitespace in srpailabs.conf",
     r"sed -i '/^\s*$/d;/server_name recruit.srpailabs.com;/,/^}/d' /etc/nginx/sites-enabled/srpailabs.conf 2>&1 | head -3 && echo 'done'"),
    
    # ── 4. Apply our fixed nginx conf (already done via SFTP but re-apply from repo) ─
    ("Re-apply correct recruit nginx conf from repo",
     "cp /opt/srp-ats/deployment/recruit.srpailabs.com.nginx /etc/nginx/sites-available/recruit.srpailabs.com && echo 'nginx conf applied'"),

    # ── 5. Test and reload nginx ──────────────────────────────────────────────
    ("Test nginx config",
     "nginx -t 2>&1"),

    ("Reload nginx",
     "systemctl reload nginx && echo 'nginx reloaded'"),

    # ── 6. Wait for FastAPI to be healthy ─────────────────────────────────────
    ("Check FastAPI health after restart",
     "sleep 6 && curl -sf http://127.0.0.1:8009/health 2>/dev/null"),

    # ── 7. Verify /app now redirects ─────────────────────────────────────────
    ("Test /app redirect",
     "curl -sk -o /dev/null -w 'HTTP %{http_code}' https://recruit.srpailabs.com/app"),

    # ── 8. Verify /dashboard serves Next.js ──────────────────────────────────
    ("Test /dashboard",
     "curl -sk -o /dev/null -w 'HTTP %{http_code}' https://recruit.srpailabs.com/dashboard"),

    # ── 9. Verify API routes go to Next.js ───────────────────────────────────
    ("Test enterprise API routes",
     "for ep in jd boolean-search import integrations comm audit profile; do code=$(curl -sk -o /dev/null -w '%{http_code}' https://recruit.srpailabs.com/api/$ep); echo \"  /api/$ep -> HTTP $code\"; done"),
]

print("=== SRP SmartRecruit — Full Fix & Deploy ===\n")
for label, cmd in steps:
    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"{'='*60}")
    try:
        _, stdout, stderr = client.exec_command(cmd, timeout=60)
        out = stdout.read().decode(errors='replace').strip()
        err = stderr.read().decode(errors='replace').strip()
        print(out or err or "(empty)")
    except Exception as e:
        print(f"[ERROR] {e}")

client.close()
print("\n=== Done ===")

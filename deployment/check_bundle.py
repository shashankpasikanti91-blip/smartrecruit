import paramiko

HOST = "5.223.67.236"
USER = "root"
PASS = "856Reey@nsh"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, username=USER, password=PASS, timeout=30)

checks = [
    # Check the pre-rendered dashboard HTML from Next.js standalone output
    ("dashboard html content", "docker exec srp-auth-app cat /app/.next/server/app/dashboard.html 2>/dev/null | grep -o 'JD Intelligence\\|audit_logs\\|STAGE_LIGHT\\|Jobs table\\|JobsTab\\|ent-table\\|Plus Jakarta\\|short_id\\|0F172A' | sort -u | head -20 || echo 'cannot exec into container'"),
    # Instead read via docker cp
    ("copy dashboard html", "docker cp srp-auth-app:/app/.next/server/app/dashboard.html /tmp/dashboard_check.html 2>&1 && grep -o 'JD\\|audit\\|STAGE\\|enterprise\\|0F172A\\|JobsTab' /tmp/dashboard_check.html | sort -u | head -20"),
    # Check what JS chunks have 
    ("build chunks", "docker exec srp-auth-app ls /app/.next/static/chunks/ 2>/dev/null | head -20 || docker cp srp-auth-app:/app/.next/static/chunks /tmp/chunks_list 2>/dev/null && ls /tmp/chunks_list | head -20 || echo 'failed'"),
    # Check what the actual rsc file for dashboard looks like
    ("copy dashboard rsc", "docker cp srp-auth-app:/app/.next/server/app/dashboard.rsc /tmp/dashboard.rsc 2>&1 && grep -oa 'JD Intelligence\\|audit_logs\\|STAGE_LIGHT\\|0F172A' /tmp/dashboard.rsc | sort -u | head -20 || echo 'no rsc'"),
    # Direct HTTP test
    ("http login page", "curl -sk http://localhost:3010/login | grep -o 'bg-\\[#[0-9a-fA-F]*\\]\\|Plus Jakarta\\|0F172A\\|enterprise' | sort -u | head -20"),
]

for label, cmd in checks:
    _, stdout, stderr = client.exec_command(cmd, timeout=30)
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    print(f"\n--- {label} ---")
    print((out or err or "(empty)")[:1000])

client.close()

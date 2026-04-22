import paramiko

HOST = "5.223.67.236"
USER = "root"
PASS = "856Reey@nsh"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, username=USER, password=PASS, timeout=30)

checks = [
    ("nextjs git log", "cd /opt/srp-smartrecruit-auth && git log --oneline -5"),
    ("nextjs git status", "cd /opt/srp-smartrecruit-auth && git status --short"),
    ("dashboard dir", "ls /opt/srp-smartrecruit-auth/app/dashboard/"),
    ("dashboard page size", "wc -l /opt/srp-smartrecruit-auth/app/dashboard/page.tsx 2>/dev/null || echo 'not found'"),
    ("docker image date", "docker images srp-smartrecruit-auth --format '{{.Repository}}:{{.Tag}} {{.CreatedAt}}'"),
    ("container env check", "docker exec srp-auth-app env | grep -E '(DATABASE|NEXTAUTH|NODE_ENV)' | head -10"),
    ("env.local exists", "cat /opt/srp-smartrecruit-auth/.env.local 2>/dev/null | grep -v SECRET | grep -v KEY | grep -v PASS | head -10 || echo 'no .env.local'"),
]

for label, cmd in checks:
    _, stdout, stderr = client.exec_command(cmd)
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    print(f"\n--- {label} ---")
    print(out or err or "(empty)")

client.close()

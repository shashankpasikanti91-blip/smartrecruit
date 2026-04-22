import paramiko

HOST = "5.223.67.236"
USER = "root"
PASS = "856Reey@nsh"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, username=USER, password=PASS, timeout=30)

checks = [
    # Full nginx config (no truncation)
    ("nginx full config", "cat /etc/nginx/sites-enabled/recruit.srpailabs.com"),
    # Test curl login page to see actual HTML
    ("login page html", "curl -sk https://recruit.srpailabs.com/login | grep -o 'class=\\\"[^\"]*\\\"\\|Plus Jakarta\\|0F172A\\|enterprise\\|Sign In' | sort -u | head -20"),
    # check what version of next.config.js is in the container
    ("next config in container", "docker exec srp-auth-app cat /app/next.config.js 2>/dev/null | head -20 || echo 'cannot exec'"),
    # Check if any nginx cache exists
    ("nginx cache", "ls /var/cache/nginx/ 2>/dev/null || echo 'no nginx cache dir'"),
    # Look at actual JS bundle to see if enterprise features are in it
    ("bundle has enterprise", "docker exec srp-auth-app grep -r 'JD Intelligence\\|audit_logs\\|STAGE_LIGHT' /app/.next/server/ --include='*.js' -l 2>/dev/null | head -5 || echo 'cannot exec or not found'"),
]

for label, cmd in checks:
    _, stdout, stderr = client.exec_command(cmd, timeout=30)
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    print(f"\n--- {label} ---")
    print((out or err or "(empty)")[:1200])

client.close()

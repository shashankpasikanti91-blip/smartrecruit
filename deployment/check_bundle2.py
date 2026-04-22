import paramiko

HOST = "5.223.67.236"
USER = "root"
PASS = "856Reey@nsh"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, username=USER, password=PASS, timeout=30)

checks = [
    # Check what's inside the container via find (not exec)
    ("docker cp rsc directly", "docker cp srp-auth-app:/app/.next/server/app/dashboard.rsc /tmp/d.rsc && wc -c /tmp/d.rsc"),
    ("grep rsc content", "docker cp srp-auth-app:/app/.next/server/app/dashboard.rsc /tmp/d.rsc && strings /tmp/d.rsc | grep -i 'JD Intelligence\\|audit\\|STAGE_LIGHT\\|0F172A\\|JobsTab' | head -10"),
    # Try to get the main JS bundle content
    ("check biggest js", "docker cp srp-auth-app:/app/.next/server/app/dashboard.html /tmp/d.html 2>&1 || echo 'cp failed'; ls -la /tmp/d.html 2>/dev/null"),
    # Look at server-side chunk with dashboard code
    ("find dashboard chunk", "find /opt/srp-smartrecruit-auth/.next 2>/dev/null -name '*.js' | head -5 || echo 'no .next on host'"),
    # Check if standalone exists on host
    ("host app structure", "ls /opt/srp-smartrecruit-auth/"),
    # Check last docker build log 
    ("docker build log tail", "journalctl -u docker --since '2h ago' --no-pager 2>/dev/null | grep -i 'srp-smartrecruit-auth\\|compile\\|build' | tail -20 || docker inspect srp-auth-app --format='{{.State.StartedAt}} {{.Image}}' 2>/dev/null"),
]

for label, cmd in checks:
    _, stdout, stderr = client.exec_command(cmd, timeout=30)
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    print(f"\n--- {label} ---")
    print((out or err or "(empty)")[:800])

client.close()

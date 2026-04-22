import paramiko

HOST = "5.223.67.236"
USER = "root"
PASS = "856Reey@nsh"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, username=USER, password=PASS, timeout=30)

checks = [
    # Check full nginx config for recruit
    ("nginx config full", "cat /etc/nginx/sites-enabled/recruit.srpailabs.com"),
    # See what the actual HTML response looks like for /dashboard
    ("dashboard html snippet", "curl -sk https://recruit.srpailabs.com/dashboard -H 'Cookie: ' | grep -o '<title>.*</title>\\|enterprise\\|JD Intelligence\\|audit' | head -20"),
    # Check if the build output has the new components
    ("nextjs build exists", "ls -la /opt/srp-smartrecruit-auth/.next/server/app/ 2>/dev/null | head -20 || echo 'no .next dir inside container'"),
    # Check inside running container what files are there
    ("container dashboard check", "docker exec srp-auth-app ls /app/app/dashboard/ 2>/dev/null || echo 'cannot exec'"),
    # Check if there's a standalone build
    ("container build check", "docker exec srp-auth-app ls /app/.next/server/app/ 2>/dev/null | head -20 || echo 'no .next'"),
    # Check if there's a different nextjs running on 3000
    ("port 3000 container", "docker ps --format '{{.Names}}\t{{.Ports}}' | grep 3000"),
]

for label, cmd in checks:
    _, stdout, stderr = client.exec_command(cmd, timeout=30)
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    print(f"\n--- {label} ---")
    print((out or err or "(empty)")[:800])

client.close()

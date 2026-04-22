import paramiko

HOST = "5.223.67.236"
USER = "root"
PASS = "856Reey@nsh"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, username=USER, password=PASS, timeout=30)

checks = [
    # What is on port 3004?
    ("port 3004 process", "ss -tlnp | grep :3004 || echo 'nothing on 3004'"),
    # Full srpailabs.conf recruit block (more lines)
    ("srpailabs.conf full", "cat /etc/nginx/sites-enabled/srpailabs.conf | grep -n 'recruit.srpailabs\\|location\\|proxy_pass\\|server_name' | head -40"),
    # FastAPI startup logs
    ("fastapi startup", "docker logs srp-ats-app --tail 50 2>&1 | head -50"),
    # What does the server send for an authenticated-looking request
    ("test dashboard direct", "curl -sk http://localhost:3010/dashboard -o /dev/null -w 'HTTP %{http_code}'"),
    # Check NextJS env vars in running container
    ("nextjs database env", "docker exec srp-auth-app printenv DATABASE_URL NEXTAUTH_URL NODE_ENV 2>/dev/null || echo 'cannot exec'"),
    # Check DB migration_v6 ran properly
    ("migration status", "docker exec srp-auth-db psql -U srp_auth -d srp_auth -c \"SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY table_name;\" 2>/dev/null"),
]

for label, cmd in checks:
    _, stdout, stderr = client.exec_command(cmd, timeout=30)
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    print(f"\n--- {label} ---")
    print((out or err or "(empty)")[:800])

client.close()

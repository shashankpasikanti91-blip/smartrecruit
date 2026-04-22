import paramiko

HOST = "5.223.67.236"
USER = "root"
PASS = "856Reey@nsh"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, username=USER, password=PASS, timeout=30)

checks = [
    # Full srpailabs.conf recruit block
    ("srpailabs.conf recruit block", "awk '/server_name recruit.srpailabs.com;/,/^}/' /etc/nginx/sites-enabled/srpailabs.conf 2>/dev/null | head -80"),
    # FastAPI app logs
    ("fastapi logs", "docker logs srp-ats-app --tail 30 2>&1"),
    # Next.js app logs
    ("nextjs logs", "docker logs srp-auth-app --tail 20 2>&1"),
    # Test key API endpoints
    ("test /api/jd route", "curl -sk -o /dev/null -w 'HTTP %{http_code}' https://recruit.srpailabs.com/api/jd"),
    ("test /api/candidates route", "curl -sk -o /dev/null -w 'HTTP %{http_code}' https://recruit.srpailabs.com/api/candidates"),
    ("test /api/jobs route", "curl -sk -o /dev/null -w 'HTTP %{http_code}' https://recruit.srpailabs.com/api/jobs"),
    ("test /api/boolean-search route", "curl -sk -o /dev/null -w 'HTTP %{http_code}' https://recruit.srpailabs.com/api/boolean-search"),
    ("test /api/import route", "curl -sk -o /dev/null -w 'HTTP %{http_code}' https://recruit.srpailabs.com/api/import"),
    ("test /api/integrations route", "curl -sk -o /dev/null -w 'HTTP %{http_code}' https://recruit.srpailabs.com/api/integrations"),
    ("test /api/comm route", "curl -sk -o /dev/null -w 'HTTP %{http_code}' https://recruit.srpailabs.com/api/comm"),
    ("test /api/audit route", "curl -sk -o /dev/null -w 'HTTP %{http_code}' https://recruit.srpailabs.com/api/audit"),
]

for label, cmd in checks:
    _, stdout, stderr = client.exec_command(cmd, timeout=30)
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    print(f"\n--- {label} ---")
    print((out or err or "(empty)")[:600])

client.close()

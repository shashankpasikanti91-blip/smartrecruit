import paramiko

HOST = "5.223.67.236"
USER = "root"
PASS = "856Reey@nsh"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, username=USER, password=PASS, timeout=30)

checks = [
    ("FastAPI service status", "systemctl is-active srp-smartrecruit"),
    ("FastAPI port 8000", "ss -tlnp | grep 8000 || echo 'not listening'"),
    ("FastAPI port 8001", "ss -tlnp | grep 8001 || echo 'not listening'"),
    ("FastAPI any port", "ss -tlnp | grep gunicorn || echo 'gunicorn not found'"),
    ("FastAPI health 8000", "curl -s http://localhost:8000/health || echo 'no response'"),
    ("FastAPI health 8001", "curl -s http://localhost:8001/health || echo 'no response'"),
    ("systemctl status", "systemctl status srp-smartrecruit --no-pager | head -20"),
]

for label, cmd in checks:
    _, stdout, stderr = client.exec_command(cmd)
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    print(f"\n--- {label} ---")
    print(out or err or "(empty)")

client.close()

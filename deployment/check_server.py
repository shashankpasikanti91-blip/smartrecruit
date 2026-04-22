import paramiko

HOST = "5.223.67.236"
USER = "root"
PASS = "856Reey@nsh"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, username=USER, password=PASS, timeout=30)

checks = [
    ("All listening ports", "ss -tlnp | grep -E '(LISTEN)' | awk '{print $4, $6}'"),
    ("FastAPI on 8009", "curl -s http://127.0.0.1:8009/health"),
    ("Docker containers", "docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'"),
    ("nginx sites enabled", "ls /etc/nginx/sites-enabled/"),
    ("nginx config recruit", "cat /etc/nginx/sites-enabled/recruit.srpailabs.com 2>/dev/null | head -50 || cat /etc/nginx/sites-enabled/default | head -50"),
]

for label, cmd in checks:
    _, stdout, stderr = client.exec_command(cmd)
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    print(f"\n--- {label} ---")
    print(out or err or "(empty)")

client.close()

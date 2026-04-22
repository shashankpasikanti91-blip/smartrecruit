import paramiko

HOST = "5.223.67.236"
USER = "root"
PASS = "856Reey@nsh"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, username=USER, password=PASS, timeout=30)

checks = [
    ("symlink check", "ls -la /etc/nginx/sites-enabled/recruit.srpailabs.com"),
    ("available vs enabled diff", "diff /etc/nginx/sites-available/recruit.srpailabs.com /etc/nginx/sites-enabled/recruit.srpailabs.com 2>&1 | head -5 || echo 'same file or diff error'"),
    ("app location in enabled", "grep -n 'location /app\\|location = /app' /etc/nginx/sites-enabled/recruit.srpailabs.com"),
    ("srpailabs conf check", "grep -n 'location /app\\|recruit.srpailabs' /etc/nginx/sites-enabled/srpailabs.conf 2>/dev/null | head -10 || echo 'no srpailabs.conf'"),
    ("all configs with /app", "grep -rn 'location /app\\|location = /app' /etc/nginx/ 2>/dev/null"),
]

for label, cmd in checks:
    _, stdout, stderr = client.exec_command(cmd, timeout=15)
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    print(f"\n--- {label} ---")
    print((out or err or "(empty)")[:600])

client.close()

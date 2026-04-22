import paramiko

HOST = "5.223.67.236"
USER = "root"
PASS = "856Reey@nsh"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, username=USER, password=PASS, timeout=30)

checks = [
    # Grep all JS chunks for enterprise keywords    
    ("grep enterprise in chunks", "docker exec srp-auth-app grep -rl 'JD Intelligence\\|STAGE_LIGHT\\|audit_logs\\|0F172A' /app/.next/static/chunks/ 2>/dev/null | head -5 || echo 'cannot exec'"),
    # Try copying the static dir and grepping
    ("grep static dir", "find /tmp/chunks_check 2>/dev/null -name '*.js' -exec grep -l 'JD Intelligence' {} \\; | head -5 || echo 'not found'"),    
    # Let's check the actual source files on server
    ("server dashboard page lines", "wc -l /opt/srp-smartrecruit-auth/app/dashboard/page.tsx"),
    ("server dashboard enterprise check", "grep -c 'JD Intelligence\\|STAGE_LIGHT\\|0F172A\\|audit_logs' /opt/srp-smartrecruit-auth/app/dashboard/page.tsx 2>/dev/null || echo 'not found'"),
    ("server dashboard tabs", "grep -o \"tab: '[^']*'\" /opt/srp-smartrecruit-auth/app/dashboard/page.tsx | sort -u"),
    # Check app/globals.css on server
    ("server globals css", "grep -c '0F172A\\|2563EB\\|Plus Jakarta' /opt/srp-smartrecruit-auth/app/globals.css 2>/dev/null || echo '0 or not found'"),
]

for label, cmd in checks:
    _, stdout, stderr = client.exec_command(cmd, timeout=30)
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    print(f"\n--- {label} ---")
    print((out or err or "(empty)")[:800])

client.close()

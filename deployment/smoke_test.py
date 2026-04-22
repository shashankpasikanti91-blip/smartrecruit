import paramiko

HOST = "5.223.67.236"
USER = "root"
PASS = "856Reey@nsh"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, username=USER, password=PASS, timeout=30)

checks = [
    ("Next.js health", "curl -s http://localhost:3010/api/health"),
    ("FastAPI health", "curl -s http://localhost:8009/health"),
    ("HTTPS health", "curl -sk https://recruit.srpailabs.com/api/health"),
    ("audit_logs table", 'docker exec srp-auth-db psql -U srp_auth -d srp_auth -c "SELECT COUNT(*) FROM audit_logs;"'),
    ("short_id column job_posts", 'docker exec srp-auth-db psql -U srp_auth -d srp_auth -c "SELECT column_name FROM information_schema.columns WHERE table_name=\'job_posts\' AND column_name=\'short_id\';"'),
    ("audit_logs columns", 'docker exec srp-auth-db psql -U srp_auth -d srp_auth -c "SELECT column_name FROM information_schema.columns WHERE table_name=\'audit_logs\';"'),
]

print("\n=== E2E Smoke Test ===\n")
all_pass = True
for label, cmd in checks:
    _, stdout, stderr = client.exec_command(cmd)
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    result = out or err
    status = "PASS" if result and "error" not in result.lower() and "fail" not in result.lower() else "FAIL"
    if status == "FAIL":
        all_pass = False
    print(f"  [{status}] {label}: {result[:120]}")

print()
print("=== " + ("ALL CHECKS PASSED" if all_pass else "SOME CHECKS FAILED") + " ===")
client.close()

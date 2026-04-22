import paramiko
HOST='5.223.67.236'; USER='root'; PASS='856Reey@nsh'
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, username=USER, password=PASS, timeout=30)

# Check app logs for profile errors
checks = [
    ('app logs recent', 'docker logs srp-auth-app --tail 30 2>&1'),
    ('profile health unauthenticated', 'curl -sk https://recruit.srpailabs.com/api/profile'),
    ('screen_results exists?', 'docker exec srp-auth-db psql -U srp_auth -d srp_auth -tAc "SELECT COUNT(*) FROM information_schema.tables WHERE table_name=\'screen_results\';"'),
    ('resumes cols', 'docker exec srp-auth-db psql -U srp_auth -d srp_auth -tAc "SELECT column_name FROM information_schema.columns WHERE table_name=\'resumes\' ORDER BY ordinal_position;" | head -20'),
]
for label, cmd in checks:
    _,s,e = client.exec_command(cmd)
    out = s.read().decode()[:1000]
    err = e.read().decode()[:200]
    print(f'\n--- {label} ---')
    print(out or err)
client.close()

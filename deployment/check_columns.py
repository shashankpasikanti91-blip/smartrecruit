import paramiko
HOST='5.223.67.246'
HOST='5.223.67.236'; USER='root'; PASS='856Reey@nsh'
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, username=USER, password=PASS, timeout=30)

checks = [
    ('token_usage cols', 'docker exec srp-auth-db psql -U srp_auth -d srp_auth -tAc "SELECT column_name FROM information_schema.columns WHERE table_name=\'token_usage\';"'),
    ('screen_results cols', 'docker exec srp-auth-db psql -U srp_auth -d srp_auth -tAc "SELECT column_name FROM information_schema.columns WHERE table_name=\'screen_results\';"'),
    ('audit cols', 'docker exec srp-auth-db psql -U srp_auth -d srp_auth -tAc "SELECT column_name FROM information_schema.columns WHERE table_name=\'audit_logs\';"'),
    ('profile api test', 'docker exec srp-auth-app wget -qO- http://localhost:3000/api/profile 2>&1 | head -5'),
]
for label, cmd in checks:
    _,s,e = client.exec_command(cmd)
    out = s.read().decode()[:800]
    err = e.read().decode()[:200]
    print(label+':', out or err)
client.close()

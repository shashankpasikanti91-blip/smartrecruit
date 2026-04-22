import paramiko
HOST='5.223.67.236'; USER='root'; PASS='856Reey@nsh'
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, username=USER, password=PASS, timeout=30)
checks = [
    ('tables', "docker exec srp-auth-db psql -U srp_auth -d srp_auth -c 'SELECT table_name FROM information_schema.tables WHERE table_schema=chr(39)||chr(112)||chr(117)||chr(98)||chr(108)||chr(105)||chr(99) ORDER BY table_name;'"),
    ('tables2', 'docker exec srp-auth-db psql -U srp_auth -d srp_auth -tAc "SELECT table_name FROM information_schema.tables WHERE table_schema=\'public\' ORDER BY table_name;"'),
]
for label, cmd in checks:
    _,s,e = client.exec_command(cmd)
    out = s.read().decode()[:800]
    err = e.read().decode()[:200]
    print(label+':', out or err)
client.close()

import paramiko

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('5.223.67.236', username='root', password='856Reey@nsh', timeout=15)

def run(cmd):
    _, o, e = client.exec_command(cmd, timeout=25)
    return o.read().decode(errors='replace').strip()

print('=== TABLES IN srp_auth ===')
print(run("docker exec srp-auth-db psql -U srp_auth -d srp_auth -c '\\dt' 2>&1"))

print('\n=== FASTAPI ROUTES ===')
print(run("docker exec srp-ats-app curl -s http://localhost:8009/openapi.json 2>/dev/null | python3 -c \"import json,sys; d=json.load(sys.stdin); [print(p) for p in list(d.get('paths',{}).keys())]\"  2>&1"))

print('\n=== NOTIFY ROUTE ===')
print(run("ls /root/srp-smartrecruit-auth/app/api/ 2>/dev/null"))
print(run("cat /root/srp-smartrecruit-auth/app/api/notify/route.ts 2>/dev/null || echo 'file not found'"))

print('\n=== UPLOAD DIR ===')
print(run("docker exec srp-auth-app ls / 2>&1 | head -20"))
print(run("docker inspect srp-auth-app --format '{{range .Mounts}}{{.Source}} -> {{.Destination}}{{end}}'"))

print('\n=== NEXT.JS LOCALHOST ===')
print(run("curl -s -o /dev/null -w '%{http_code}' http://localhost:3010/api/health"))

print('\n=== FASTAPI LOG TAIL ===')
print(run("docker logs srp-ats-app --tail 20 2>&1"))

client.close()

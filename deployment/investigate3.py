import paramiko

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('5.223.67.236', username='root', password='856Reey@nsh', timeout=15)

def run(cmd):
    _, o, e = client.exec_command(cmd, timeout=30)
    out = o.read().decode(errors='replace').strip()
    err = e.read().decode(errors='replace').strip()
    return out or err

# Files inside Docker containers
print('=== NEXTJS APP API DIR ===')
print(run("docker exec srp-auth-app ls /app/app/api/ 2>&1"))

print('\n=== FASTAPI ROUTERS DIR ===')
print(run("docker exec srp-ats-app ls /app/app/routers/ 2>&1"))

print('\n=== FASTAPI MAIN.PY (router includes) ===')
print(run("docker exec srp-ats-app grep -n 'include_router\\|prefix\\|router' /app/app/main.py 2>&1 | head -30"))

print('\n=== NEXTJS RESUMES ROUTE ===')
print(run("docker exec srp-auth-app cat /app/app/api/resumes/route.ts 2>&1 | head -50"))

print('\n=== NEXTJS NOTIFY ROUTE ===')
print(run("docker exec srp-auth-app cat /app/app/api/notify/route.ts 2>&1"))

print('\n=== UPLOAD DIR IN CONTAINER ===')
print(run("docker exec srp-auth-app ls /app/uploads/ 2>&1 || docker exec srp-auth-app ls /tmp/uploads/ 2>&1"))

print('\n=== ENV VAR UPLOAD PATH ===')
print(run("docker exec srp-auth-app printenv | grep -iE 'upload|storage|file' 2>&1"))

client.close()

import paramiko

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('5.223.67.236', username='root', password='856Reey@nsh', timeout=15)

def run(cmd):
    _, o, e = client.exec_command(cmd, timeout=25)
    return o.read().decode(errors='replace').strip()

# FastAPI actual routes from source
print('=== FASTAPI ROUTER FILES ===')
print(run("ls /root/smartrecruit/backend/app/routers/ 2>/dev/null"))

print('\n=== FASTAPI main.py include_router calls ===')
print(run("grep -n 'include_router\\|prefix' /root/smartrecruit/backend/app/main.py 2>/dev/null"))

# Check notify route creation status
print('\n=== NEXT.JS API LISTING ===')
print(run("ls /root/srp-smartrecruit-auth/app/api/ 2>/dev/null"))

# Check the actual notify route (maybe it's a different path)
print('\n=== NOTIFY ROUTE CHECK ===')
print(run("find /root/srp-smartrecruit-auth -name '*.ts' -path '*/api/*' | grep -i notif 2>/dev/null"))

# Check upload volume/path
print('\n=== NEXT.JS UPLOAD CONFIG ===')
print(run("grep -rn 'upload\\|formData\\|multipart\\|writeFile\\|mkdirSync' /root/srp-smartrecruit-auth/app/api/resumes/route.ts 2>/dev/null | head -20"))
print(run("cat /root/srp-smartrecruit-auth/app/api/resumes/route.ts 2>/dev/null | head -60"))

# FastAPI routes via Python
print('\n=== FASTAPI ROUTES VIA PYTHON ===')
print(run("cd /root/smartrecruit && docker exec srp-ats-app python3 -c \"import sys; sys.path.insert(0,'/app'); from app.main import app; [print(r.path) for r in app.routes]\" 2>&1 | head -50"))

client.close()

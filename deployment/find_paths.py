import paramiko

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect('5.223.67.236', username='root', password='856Reey@nsh', timeout=15)

def run(cmd):
    _, o, e = client.exec_command(cmd, timeout=25)
    out = o.read().decode(errors='replace').strip()
    err = e.read().decode(errors='replace').strip()
    return out or err

# Find where repos are
print('=== ROOT DIR ===')
print(run("ls /root/"))

print('\n=== FIND SMARTRECRUIT REPO ===')
print(run("find / -name 'main.py' -path '*/smartrecruit*' 2>/dev/null | head -5"))

print('\n=== FIND NEXTJS REPO ===')
print(run("find / -name 'next.config.js' 2>/dev/null | head -5"))

print('\n=== FIND APP ROUTERS ===')
print(run("find / -name 'ai_assistant.py' 2>/dev/null | head -3"))

client.close()

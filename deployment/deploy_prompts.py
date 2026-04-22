import paramiko, os

HOST='5.223.67.236'; USER='root'; PASS='856Reey@nsh'
LOCAL_FILE = r'C:\Users\User\Desktop\SRP Smartrecruit\backend\system_prompts.txt'

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, username=USER, password=PASS, timeout=30)

print('Connected to server')

# Upload the new system_prompts.txt to both known paths
sftp = client.open_sftp()

# Find the FastAPI app dir
_,s,_ = client.exec_command('find /opt -name "system_prompts.txt" 2>/dev/null')
paths = s.read().decode().strip().split('\n')
print('Found paths:', paths)

for path in paths:
    if path.strip():
        sftp.put(LOCAL_FILE, path.strip())
        print(f'Uploaded to {path.strip()}')

sftp.close()

# Restart the FastAPI service to reload the prompts
_,s,e = client.exec_command('cd /opt/srp-ats && docker compose restart app 2>&1 && echo RESTART_OK')
print('Restart:\n', s.read().decode() + e.read().decode())

# Verify new content is loaded
_,s,_ = client.exec_command("grep -c 'World-Class' " + paths[0] if paths and paths[0].strip() else "echo 'no path'")
print('World-Class count in file (should be 2):', s.read().decode().strip())

# Quick health check
_,s,_ = client.exec_command('sleep 5 && curl -s http://127.0.0.1:8009/health')
print('FastAPI health:', s.read().decode().strip())

client.close()
print('Done')
